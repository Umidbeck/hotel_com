"""
Telegram ↔ Web chat integratsiyasi
Har qanday yangi /register <raqam> uchun Web ↔ Telegram xabarlari darhol ishlaydi
"""
import os
import django
import asyncio
import json
import uuid as uuid_lib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from decouple import config
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from asgiref.sync import sync_to_async
import websockets
from channels.layers import get_channel_layer
from django.utils import timezone

from qr_auth.models import Room
from chat.models import Message

# --------------------- konstantalar ---------------------
STATE_CLEAR, STATE_LINK = "clear_messages", "get_link"
BACKEND_WS = config("BACKEND_WS", default="ws://localhost:8000")

# --------------------- klaviaturalar ---------------------
ADMIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("📋 Hona ro‘yxati"), KeyboardButton("🔗 Hona linki")]],
    resize_keyboard=True,
)
ROOM_KB = lambda rooms: ReplyKeyboardMarkup(
    [[KeyboardButton(str(r.number))] for r in rooms] + [[KeyboardButton("🔙 Ortga")]],
    resize_keyboard=True,
)
ORTGA_KB = ReplyKeyboardMarkup([[KeyboardButton("🔙 Ortga")]], resize_keyboard=True)

# --------------------- DB yordamchilari ---------------------
@sync_to_async
def get_or_create_room(number: str, tg_chat_id: str):
    room, created = Room.objects.get_or_create(
        number=number,
        defaults={
            "telegram_chat_id": tg_chat_id,
            "token": uuid_lib.uuid4().hex
        }
    )
    if not room.token:               # agar oldin null bo‘lsa
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
def clear_web_chat(room: Room) -> int:
    return Message.objects.filter(chatroom=room).delete()[0]

# --------------------- Telegram handlerlari ---------------------
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
    tg_chat_id = str(update.effective_chat.id)
    room, created = await get_or_create_room(room_number, tg_chat_id)

    # Yangi hona uchun listenerni darhol yaratamiz
    if created:
        asyncio.create_task(websocket_listener(room, ctx.application.bot))

    url = f"{config('FRONTEND_URL', default='http://localhost:3000')}/chat/{room.number}?token={room.token}"
    await update.message.reply_text(f"✅ Xona {room.number} qo‘shildi.\n🔗 URL: {url}")

# ---------- Botda oddiy tugma bosilganida ishlov beruvchi ----------
async def handle_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        return
    text = update.message.text.strip()

    if text == "📋 Hona ro‘yxati":
        ctx.user_data["state"] = STATE_CLEAR
        rooms = await get_all_rooms()
        if not rooms:
            await update.message.reply_text("📭 Hali xona yo‘q.", reply_markup=ADMIN_KB)
            return
        rooms_text = "\n".join(f"• {r.number}" for r in rooms)
        await update.message.reply_text(
            f"📋 Mavjud honalar:\n{rooms_text}\n\n"
            f"Xabarlarni o‘chirish uchun xona raqamini yozing:",
            reply_markup=ORTGA_KB
        )
        return

    if text == "🔗 Hona linki":
        ctx.user_data["state"] = STATE_LINK
        rooms = await get_all_rooms()
        if not rooms:
            await update.message.reply_text("📭 Hona yo‘q.", reply_markup=ADMIN_KB)
            return
        await update.message.reply_text(
            "Linkni olish uchun xona raqamini tanlang:",
            reply_markup=ROOM_KB(rooms)
        )
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

    state = ctx.user_data.get("state")
    if state == STATE_CLEAR:
        deleted = await clear_web_chat(room)
        await update.message.reply_text(
            f"✅ {room.number} dagi {deleted} ta xabar tozalandi.",
            reply_markup=ADMIN_KB
        )
        ctx.user_data["state"] = None
        return

    elif state == STATE_LINK:
        url = f"{config('FRONTEND_URL', default='http://localhost:3000')}/chat/{room.number}?token={room.token}"
        await update.message.reply_text(url, reply_markup=ADMIN_KB)
        ctx.user_data["state"] = None
        return

    else:
        await update.message.reply_text("ℹ️ Iltimos, tugmalardan foydalaning.", reply_markup=ADMIN_KB)

# --------------------- Guruhdan Web chatga ---------------------
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
        chatroom=room,
        text=text,
        uuid=uuid_str,
        is_from_customer=False,
        status="delivered"
    )
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"chat_{room.number}",
        {
            "type": "chat_message",
            "message": text,
            "sender": "bot",
            "time": timezone.now().strftime('%H:%M'),
            "uuid": uuid_str,
        }
    )

# --------------------- Web chat → Telegram guruhga ---------------------
async def websocket_listener(room: Room, bot):
    uri = f"{BACKEND_WS}/ws/chat/{room.number}/?token={room.token}"
    target_chat_id = room.telegram_chat_id
    while True:
        try:
            async with websockets.connect(
                uri,
                origin=config("ALLOWED_ORIGIN", default="http://localhost:3000")
            ) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    if data.get("sender") == "me":
                        await bot.send_message(chat_id=target_chat_id, text=data["message"])
        except Exception as e:
            print(f"[WS retry {room.number}] {e}")
            await asyncio.sleep(5)

# --------------------- Botni ishga tushirish ---------------------
def main():
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=10, read_timeout=10)
    app = Application.builder().token(config("BOT_TOKEN")).request(request).build()

    app.add_handlers([
        CommandHandler("start", start),
        CommandHandler("register", register),
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


