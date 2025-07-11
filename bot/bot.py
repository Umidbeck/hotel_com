import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import json
import asyncio
import uuid
import datetime
from decouple import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from asgiref.sync import sync_to_async
import aiohttp
import channels.layers
import websockets

from qr_auth.models import Room
from chat.models import Message


# ======= DATABASE FUNCTIONS =======
@sync_to_async
def save_or_update_room(number: str, chat_id: str):
    room, created = Room.objects.get_or_create(number=number)
    room.telegram_chat_id = chat_id
    room.save()
    return created

@sync_to_async
def get_all_rooms():
    return list(Room.objects.all().values_list('number', flat=True))

@sync_to_async
def get_chat_id_by_room(room_number: str):
    try:
        room = Room.objects.get(number=room_number)
        return room.telegram_chat_id
    except Room.DoesNotExist:
        return None

@sync_to_async
def delete_messages_in_room(room_number: str):
    try:
        room = Room.objects.get(number=room_number)
        Message.objects.filter(chatroom=room).delete()
        return True
    except Room.DoesNotExist:
        return False

@sync_to_async
def get_room_by_chat_id(chat_id: str):
    try:
        return Room.objects.get(telegram_chat_id=chat_id)
    except Room.DoesNotExist:
        return None


# ======= COMMANDS =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot ishga tushdi. Xonani ro‘yxatdan o‘tkazish uchun:\n\n/register 101")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❗ Format: /register <xona_raqami>")
        return

    room_number = args[0]
    chat_id = str(update.effective_chat.id)

    created = await save_or_update_room(room_number, chat_id)
    msg = f"✅ Yangi xona yaratildi: {room_number}" if created else f"♻️ Xona yangilandi: {room_number}"
    await update.message.reply_text(msg)

async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_rooms = await get_all_rooms()
    if not all_rooms:
        await update.message.reply_text("📭 Hali xona yo‘q.")
        return

    buttons = [
        [InlineKeyboardButton(f"Xona {room}", callback_data=f"room_{room}")]
        for room in all_rooms
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📋 Xonalar ro‘yxati:", reply_markup=markup)


# ======= CALLBACK HANDLER =======
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("room_"):
        room_number = data.split("_")[1]
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Xabarlarni o‘chirish", callback_data=f"clear_{room_number}")],
        ])
        await query.edit_message_text(f"Xona: {room_number}", reply_markup=markup)

    elif data.startswith("clear_"):
        room_number = data.split("_")[1]
        success = await delete_messages_in_room(room_number)
        msg = f"🧹 Xabarlar o‘chirildi: {room_number}" if success else "❌ Xona topilmadi."
        await query.edit_message_text(msg)


# ======= MESSAGE HANDLER (Telegram ➡ Web) =======
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = str(message.chat_id)
    text = message.text.strip()

    if message.from_user.is_bot or not text or text.startswith('[web]'):
        return

    room = await get_room_by_chat_id(chat_id)
    if not room:
        await message.reply_text("❗ Bu guruh ro‘yxatdan o‘tmagan.")
        return

    uuid_str = str(uuid.uuid4())

    try:
        # WebSocket orqali yuborish
        channel_layer = channels.layers.get_channel_layer()
        await channel_layer.group_send(f"chat_{room.number}", {
            'type': 'chat_message',
            'message': text,
            'sender': 'bot',
            'uuid': uuid_str,
            'time': datetime.datetime.now().strftime('%H:%M')
        })

        # API orqali bazaga yozish
        async with aiohttp.ClientSession() as session:
            await session.post(f"http://localhost:8000/api/messages/{room.number}/send/", json={
                "text": text,
                "is_from_customer": False,
                "uuid": uuid_str
            })

    except Exception as e:
        print(f"[Telegram ➡ WebSocket xato]: {e}")


# ======= Web ➡ Telegram Listener =======
async def start_ws_listeners(application):
    rooms = await get_all_rooms()
    for room_number in rooms:
        chat_id = await get_chat_id_by_room(room_number)
        if chat_id:
            asyncio.create_task(websocket_listener(room_number, chat_id, application.bot))

async def websocket_listener(room_number: str, chat_id: str, bot):
    uri = f"ws://localhost:8000/ws/chat/{room_number}/"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                print(f"🔗 WS ulandi: {uri}")
                async for message in ws:
                    try:
                        data = json.loads(message)
                        if data.get('sender') == 'me' and 'message' in data:
                            await bot.send_message(chat_id=chat_id, text=data['message'])
                    except Exception as e:
                        print(f"[WS xabar xatosi]: {e}")
        except Exception as e:
            print(f"[WS uzildi]: {e}")
            await asyncio.sleep(5)


# ======= BOT START =======
def main():
    app = Application.builder().token(config("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("rooms", rooms))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.post_init = start_ws_listeners
    app.run_polling()

if __name__ == "__main__":
    main()



