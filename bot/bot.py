# bot/bot.py
import os
import django
import asyncio
import json
import uuid as uuid_lib
import qrcode
from io import BytesIO

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from decouple import config
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from asgiref.sync import sync_to_async
import websockets
from channels.layers import get_channel_layer
from django.utils import timezone

from qr_auth.models import Room
from chat.models import Message

# =================== Konstantalar ====================
STATE_CLEAR, STATE_DELETE = "clear_messages", "delete_room"
BACKEND_WS = config("BACKEND_WS", default="ws://localhost:8000")
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = config("BACKEND_URL", default="http://localhost:8000")  # ✅ YANGI QO‘SHILDI

# =================== Klaviaturalar ====================
ADMIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📋 Hona ro‘yxati")],
        [KeyboardButton("🗑 Xonani o‘chirish")]
    ],
    resize_keyboard=True,
)
ORTGA_KB = ReplyKeyboardMarkup([[KeyboardButton("🔙 Ortga")]], resize_keyboard=True)

# =================== DB yordamchilari ====================
@sync_to_async
def get_or_create_room(number: str, tg_chat_id: str):
    room, created = Room.objects.get_or_create(
        number=number,
        defaults={
            "telegram_chat_id": tg_chat_id,
            "token": uuid_lib.uuid4().hex,
            "qr_code": uuid_lib.uuid4().hex,  # ✅ DOIMIY QR
        }
    )
    if not room.token:
        room.token = uuid_lib.uuid4().hex
        room.save()
    return room, created

@sync_to_async
def get_all_rooms():
    return list(Room.objects.all())

@sync_to_async
def get_room_by_number(number: str):
    return Room.objects.filter(number=number).first()

@sync_to_async
def clear_room_and_reset_token(room: Room):
    count, _ = Message.objects.filter(chatroom=room).delete()
    room.rotate_token()  # ✅ YANGI TOKEN
    return count

@sync_to_async
def delete_room(room: Room):
    room.delete()

def generate_qr_code(url: str) -> BytesIO:
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return buf

# =================== Bot handlerlari ====================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ("group", "supergroup"):
        return
    await update.message.reply_text("👋 Admin! Tugmalardan birini tanlang:", reply_markup=ADMIN_KB)

async def register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❗ Bu buyruq faqat guruhda ishlaydi.")
        return

    if len(ctx.args) != 1:
        await update.message.reply_text("❗ Format: /register <raqam>")
        return

    room_number = ctx.args[0]
    room, created = await get_or_create_room(room_number, str(update.effective_chat.id))

    if created:
        asyncio.create_task(websocket_listener(room, ctx.application.bot))

    url = f"{FRONTEND_URL}/chat/{room.number}?token={room.token}"
    await update.message.reply_text(f"✅ Xona {room.number} qo‘shildi.\n🔗 URL: {url}")

async def handle_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != "private":
        return

    text = update.message.text.strip()
    state = ctx.user_data.get("state")

    if text == "📋 Hona ro‘yxati":
        ctx.user_data["state"] = STATE_CLEAR
        rooms = await get_all_rooms()
        if not rooms:
            await update.message.reply_text("📭 Hali xona yo‘q.", reply_markup=ADMIN_KB)
            return
        text = "📋 Mavjud honalar:\n" + "\n".join(f"• {r.number}" for r in rooms)
        await update.message.reply_text(f"{text}\n\nXabarlarni o‘chirish uchun xona raqamini kiriting:", reply_markup=ORTGA_KB)
        return

    if text == "🗑 Xonani o‘chirish":
        ctx.user_data["state"] = STATE_DELETE
        rooms = await get_all_rooms()
        if not rooms:
            await update.message.reply_text("📭 Hali xona yo‘q.", reply_markup=ADMIN_KB)
            return
        text = "❗ O‘chirish uchun xona raqamini kiriting:\n" + "\n".join(f"• {r.number}" for r in rooms)
        await update.message.reply_text(text, reply_markup=ORTGA_KB)
        return

    if text == "🔙 Ortga":
        ctx.user_data["state"] = None
        await update.message.reply_text("🔙 Bosh menyuga qaytdingiz.", reply_markup=ADMIN_KB)
        return

    room = await get_room_by_number(text)
    if not room:
        await update.message.reply_text("❌ Xona topilmadi.", reply_markup=ADMIN_KB)
        ctx.user_data["state"] = None
        return

    if state == STATE_CLEAR:
        deleted = await clear_room_and_reset_token(room)
        await update.message.reply_text(f"✅ {room.number} dagi {deleted} ta xabar tozalandi. Yangi token yaratildi.", reply_markup=ADMIN_KB)
    elif state == STATE_DELETE:
        await delete_room(room)
        await update.message.reply_text(f"🗑 {room.number} o‘chirildi.", reply_markup=ADMIN_KB)

    ctx.user_data["state"] = None

async def qrlink_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) != 1:
        await update.message.reply_text("❗ Format: /qrlink <xona_raqami>")
        return

    room_number = ctx.args[0]
    room = await get_room_by_number(room_number)
    if not room:
        await update.message.reply_text("❌ Xona topilmadi.")
        return

    # ✅ DOIMIY QR URL – backend orqali marshrut
    qr_url = f"http://localhost:8000/qr/{room.qr_code}/"
    qr_buf = generate_qr_code(qr_url)

    await update.message.reply_photo(
        photo=InputFile(qr_buf),
        caption=f"✅ QR – bu doimiy link\n{qr_url}"
    )

# =================== Guruh va WebSocket ====================
async def on_group_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    tg_chat_id = str(update.effective_chat.id)
    room = await sync_to_async(Room.objects.filter(telegram_chat_id=tg_chat_id).first)()
    if not room:
        return
    text = update.message.text or ""
    if not text:
        return

    uuid_str = str(uuid_lib.uuid4())
    await sync_to_async(Message.objects.create)(
        chatroom=room, text=text, uuid=uuid_str, is_from_customer=False, status="delivered"
    )
    await get_channel_layer().group_send(
        f"chat_{room.number}",
        {
            "type": "chat_message",
            "message": text,
            "sender": "bot",
            "time": timezone.now().strftime('%H:%M'),
            "uuid": uuid_str,
        }
    )

async def websocket_listener(room: Room, bot):
    uri = f"{BACKEND_WS}/ws/chat/{room.number}/?token={room.token}"
    target_chat_id = room.telegram_chat_id
    while True:
        try:
            async with websockets.connect(uri, origin=config("ALLOWED_ORIGIN", default="http://localhost:3000")) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    if data.get("sender") == "me":
                        await bot.send_message(chat_id=target_chat_id, text=data["message"])
        except Exception as e:
            print(f"[WS retry {room.number}] {e}")
            await asyncio.sleep(5)

# =================== Botni ishga tushirish ====================
def main():
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=10, read_timeout=10)
    app = Application.builder().token(config("BOT_TOKEN")).request(request).build()

    app.add_handlers([
        CommandHandler("start", start),
        CommandHandler("register", register),
        CommandHandler("qrlink", qrlink_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_reply),
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, on_group_message),
    ])

    async def post_init(app):
        rooms = await sync_to_async(list)(Room.objects.all())
        for room in rooms:
            asyncio.create_task(websocket_listener(room, app.bot))

    app.post_init = post_init
    app.run_polling()

if __name__ == "__main__":
    main()




