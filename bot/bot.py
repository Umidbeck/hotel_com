import os
import json
import asyncio
import datetime
import django
import aiohttp
import websockets

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from decouple import config
from asgiref.sync import sync_to_async
  # models.py da bo'lishi kerak

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_com.config.settings')
django.setup()
from qr_auth.models import Room

# ===== ROOM HELPER FUNCTIONS =====

@sync_to_async
def get_telegram_chat_id(room_number):
    try:
        room = Room.objects.get(number=room_number)
        return room.telegram_chat_id
    except Room.DoesNotExist:
        return None

@sync_to_async
def get_room_by_chat_id(chat_id):
    try:
        return Room.objects.get(telegram_chat_id=chat_id)
    except Room.DoesNotExist:
        return None

@sync_to_async
def create_or_update_room(number, chat_id):
    room, created = Room.objects.get_or_create(number=number)
    room.telegram_chat_id = chat_id
    room.save()
    return created

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Xush kelibsiz! /addroom bilan xonani bog‘lang.")

async def add_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❗ Format: /addroom <xona_raqami> <chat_id>")
        return

    room_number = args[0]
    telegram_chat_id = int(args[1])

    created = await create_or_update_room(room_number, telegram_chat_id)
    if created:
        await update.message.reply_text(f"✅ Yangi xona yaratildi: {room_number}")
    else:
        await update.message.reply_text(f"♻️ Xona yangilandi: {room_number}")

# ===== MESSAGE HANDLER FROM TELEGRAM GROUP =====

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    message = update.message.text
    room = await get_room_by_chat_id(chat_id)
    if not room:
        await update.message.reply_text("❗ Ushbu guruh ro'yxatdan o'tmagan.")
        return

    room_number = room.number
    ws_uri = f"ws://localhost:8000/ws/chat/{room_number}/"

    try:
        async with websockets.connect(ws_uri) as websocket:
            await websocket.send(json.dumps({
                'message': message,
                'sender': 'bot',
                'time': datetime.datetime.now().strftime('%H:%M')
            }))
    except Exception as e:
        print(f"❌ WebSocketga yuborishda xato: {e}")

# ===== LISTEN WEBSOCKET AND SEND TO TELEGRAM GROUP =====

async def listen_websockets_and_forward(app: Application):
    while True:
        rooms = await sync_to_async(list)(Room.objects.all())
        for room in rooms:
            room_number = room.number
            telegram_chat_id = room.telegram_chat_id
            ws_uri = f"ws://localhost:8000/ws/chat/{room_number}/"

            asyncio.create_task(forward_ws_to_telegram(ws_uri, telegram_chat_id, app))
        await asyncio.sleep(10)  # Har 10 sekundda tekshir

async def forward_ws_to_telegram(ws_uri, chat_id, app):
    while True:
        try:
            async with websockets.connect(ws_uri) as websocket:
                print(f"✅ WebSocket ulandi: {ws_uri}")
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    if data.get("message"):
                        await app.bot.send_message(chat_id=chat_id, text=data["message"])
        except Exception as e:
            print(f"🔁 WS uzildi ({ws_uri}): {e}")
            await asyncio.sleep(3)

# ===== MAIN FUNCTION =====

def main():
    app = Application.builder().token(config("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addroom", add_room))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(listen_websockets_and_forward(app))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
