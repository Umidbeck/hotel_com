# bot/bot.py
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import json, asyncio, re
from decouple import config
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from asgiref.sync import sync_to_async
import websockets
from telegram.request import HTTPXRequest

from qr_auth.models import Room
from chat.models import Message

# === FOYDALANUVCHI HOLATLARI ===
STATE_CLEAR = "clear_messages"
STATE_LINK = "get_link"

# === FOYDALI FUNKSIYALAR ===
def clean_group_id(raw: str) -> str:
    return re.sub(r'^-100', 'g', raw)

@sync_to_async
def get_or_create_room_by_chat(chat_id: str, title: str) -> Room:
    room, _ = Room.objects.get_or_create(
        number=clean_group_id(chat_id),
        defaults={"telegram_chat_id": chat_id}
    )
    return room

@sync_to_async
def get_all_rooms():
    return list(Room.objects.all())

@sync_to_async
def get_room_by_number(number: str):
    return Room.objects.filter(number=number).first()

@sync_to_async
def clear_web_chat(room: Room) -> int:
    return Message.objects.filter(chatroom=room).delete()[0]

# === TUGMALAR ===
ADMIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("📋 Hona ro‘yxati"), KeyboardButton("🔗 Hona linki")]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

ROOM_KB = lambda rooms: ReplyKeyboardMarkup(
    [[KeyboardButton(str(r.number))] for r in rooms] + [[KeyboardButton("🔙 Ortga")]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

ORTGA_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("🔙 Ortga")]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# === /start komandasi ===
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ("group", "supergroup"):
        return
    await update.message.reply_text("👋 Admin! Tugmalardan birini tanlang:", reply_markup=ADMIN_KB)

# === /register komandasi ===
async def register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❗ Bu buyruq faqat guruhda ishlaydi.")
        return

    args = ctx.args
    if len(args) != 1:
        await update.message.reply_text("❗ Format: /register <raqam>")
        return

    room_number = args[0]
    chat_id = str(update.effective_chat.id)
    clean_id = clean_group_id(chat_id)

    room, created = await sync_to_async(Room.objects.get_or_create)(
        number=room_number,
        defaults={"telegram_chat_id": clean_id}
    )
    if not created:
        room.telegram_chat_id = clean_id
        await sync_to_async(room.save)()

    url = f"http://localhost:3000/chat/{clean_id}"
    await update.message.reply_text(
        f"✅ Xona {room_number} qo‘shildi.\n🔗 URL: {url}"
    )

# === JAVOBLARNI QABUL QILISH ===
async def handle_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        return

    text = update.message.text.strip()

    # 📋 Hona ro'yxati tanlandi
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

    # 🔗 Hona linki tanlandi
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

    # 🔙 Ortga bosildi
    if text == "🔙 Ortga":
        ctx.user_data["state"] = None
        await update.message.reply_text("🔙 Bosh menyuga qaytdingiz.", reply_markup=ADMIN_KB)
        return

    # Foydalanuvchi raqam yubordi
    room = await get_room_by_number(clean_group_id(text))
    if not room:
        await update.message.reply_text("❌ Xona topilmadi.", reply_markup=ADMIN_KB)
        ctx.user_data["state"] = None
        return

    state = ctx.user_data.get("state")

    # faqat xabarlarni tozalash
    if state == STATE_CLEAR:
        deleted = await clear_web_chat(room)
        await update.message.reply_text(
            f"✅ {room.number} dagi {deleted} ta xabar tozalandi.",
            reply_markup=ADMIN_KB
        )
        ctx.user_data["state"] = None
        return

    # faqat link yuborish
    elif state == STATE_LINK:
        url = f"http://localhost:3000/chat/{room.telegram_chat_id or room.number}"
        await update.message.reply_text(
            f"{url}",
            reply_markup=ADMIN_KB
        )
        ctx.user_data["state"] = None
        return

    # tugma tanlanmagan holatda noto'g'ri raqam yuborildi
    else:
        await update.message.reply_text("ℹ️ Iltimos, tugmalardan foydalaning.", reply_markup=ADMIN_KB)

# === WebSocket listener ===
async def websocket_listener(room: Room, bot):
    uri = f"ws://localhost:8000/ws/chat/{room.number}/"
    target_chat_id = room.telegram_chat_id or room.number
    while True:
        try:
            async with websockets.connect(uri) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    if data.get("sender") == "me":
                        await bot.send_message(chat_id=target_chat_id, text=data["message"])
        except Exception as e:
            print(f"[WS retry {room.number}] {e}")
            await asyncio.sleep(5)

# === Botni ishga tushirish ===
def main():
    request = HTTPXRequest(connect_timeout=10, read_timeout=10)

    app = (
        Application.builder()
        .token(config("BOT_TOKEN"))
        .request(request)
        .build()
    )

    app.add_handlers([
        CommandHandler("start", start),
        CommandHandler("register", register),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply),
    ])

    async def post_init(app):
        rooms = await sync_to_async(list)(Room.objects.all())
        for room in rooms:
            asyncio.create_task(websocket_listener(room, app.bot))

    app.post_init = post_init

    app.run_polling()

if __name__ == "__main__":
    main()



