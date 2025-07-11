# bot.py
import os
import django
import json
import asyncio
import datetime
from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async
import websockets
import channels.layers
import aiohttp
import uuid

# Django init
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_com.config.settings')
django.setup()

from qr_auth.models import Room

# === ROOM FUNCTIONS ===
@sync_to_async
def get_chat_id_by_room(room_number: str):
    try:
        room = Room.objects.get(number=room_number)
        return room.telegram_chat_id
    except Room.DoesNotExist:
        return None

@sync_to_async
def get_all_rooms():
    return list(Room.objects.all().values_list('number', flat=True))

@sync_to_async
def save_or_update_room(number: str, chat_id: str):
    room, created = Room.objects.get_or_create(number=number)
    room.telegram_chat_id = chat_id
    room.save()
    return created

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xush kelibsiz! /addroom bilan xona ulang.")

async def addroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❗ Format: /addroom <xona_raqami> <chat_id>")
        return

    room_number = args[0]
    telegram_chat_id = args[1]

    created = await save_or_update_room(room_number, telegram_chat_id)
    if created:
        await update.message.reply_text(f"✅ Yangi xona yaratildi: {room_number}")
    else:
        await update.message.reply_text(f"ℹ️ Xona yangilandi: {room_number}")

# === TELEGRAM ➡ WebSocket
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.from_user.is_bot or message.text.startswith('[web]'):
        return

    text = message.text.strip()
    if not text:
        return

    chat_id = str(message.chat_id)

    try:
        room = await sync_to_async(Room.objects.get)(telegram_chat_id=chat_id)
        room_number = room.number
    except Room.DoesNotExist:
        await message.reply_text("❌ Bu guruh ro'yxatdan o'tmagan.")
        return

    # ✅ UUID yaratamiz
    message_id = str(uuid.uuid4())

    try:
        channel_layer = channels.layers.get_channel_layer()
        await channel_layer.group_send(f"chat_{room_number}", {
            'type': 'chat_message',
            'id': message_id,  # ⬅️ qo‘shildi
            'message': text,
            'sender': 'bot',
            'time': datetime.datetime.now().strftime('%H:%M')
        })
        print(f"✅ Guruhdan kelgan xabar WebChatga yuborildi (xona {room_number})")

        # 🔽 API orqali saqlash
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"http://localhost:8000/api/messages/{room_number}/send/",
                json={
                    "text": text,
                    "is_from_customer": False,
                    "uuid": message_id  # ⬅️ saqlash uchun ham yuboramiz
                }
            )

    except Exception as e:
        print(f"[channel_layer yoki API xato]: {e}")
# === WebSocket ➡ Telegram
async def websocket_listener(room_number: str, chat_id: str, bot):
    uri = f"ws://localhost:8000/ws/chat/{room_number}/"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ WebSocket ulandi: {uri}")
                async for message in websocket:
                    try:
                        data = json.loads(message)

                        # Faqat mijozdan kelgan xabarni Telegram guruhga yuboramiz
                        if data.get('sender') == 'me' and 'message' in data:
                            await bot.send_message(chat_id=chat_id, text=data['message'])

                    except Exception as e:
                        print(f"Xabarni o‘qishda xato: {e}")
        except Exception as e:
            print(f"🔁 WS uzildi ({uri}): {e}")
            await asyncio.sleep(10)

# === BOT START
def main():
    app = Application.builder().token(config('BOT_TOKEN')).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addroom", addroom))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    async def start_ws_listeners(application):
        rooms = await get_all_rooms()
        for room_number in rooms:
            chat_id = await get_chat_id_by_room(room_number)
            if chat_id:
                asyncio.create_task(websocket_listener(room_number, chat_id, application.bot))

    app.post_init = start_ws_listeners
    app.run_polling()

if __name__ == "__main__":
    main()

