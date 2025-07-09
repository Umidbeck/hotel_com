import asyncio
import json
import os
import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from decouple import config
import aiohttp
import websockets

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_com.config.settings')
django.setup()

from qr_auth.models import Room
from asgiref.sync import sync_to_async
import channels.layers

# ======== Komandalar ========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text="Xush kelibsiz! /messages bilan xabarlarni ko‘ring.")


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/messages/101/") as response:
                if response.status == 200:
                    data = await response.json()
                    for msg in data:
                        await context.bot.send_message(chat_id=update.message.chat_id,
                                                       text=f"{msg['chatroom']}: {msg['text']}")
                else:
                    await update.message.reply_text(f"Xabarlar topilmadi. Status: {response.status}")
    except Exception as e:
        await update.message.reply_text(f"❌ Server bilan ulanishda xato: {e}")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    default_chat_id = config('DEFAULT_CHAT_ID', default=None)
    if not default_chat_id:
        await update.message.reply_text("❌ .env faylida DEFAULT_CHAT_ID belgilanmagan.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8000/api/messages/101/send/",
                                    json={'text': message, 'is_from_customer': False}) as response:
                if response.status == 201:
                    await update.message.reply_text("✅ Javob yuborildi.")
                else:
                    await update.message.reply_text(f"❌ Xato. Status: {response.status}")
    except Exception as e:
        await update.message.reply_text(f"❌ Server bilan ulanishda xato: {e}")

    try:
        channel_layer = channels.layers.get_channel_layer()
        await channel_layer.group_send('chat_101', {
            'type': 'chat_message',
            'message': f"Bot: {message}",
            'sender': 'bot',
            'time': datetime.datetime.now().strftime('%H:%M')
        })
    except Exception as e:
        print(f"[channel_layer xato]: {e}")


# ======== /addroom komanda logikasi ========

@sync_to_async
def create_room_if_not_exists(number, chat_id):
    room, created = Room.objects.get_or_create(
        number=number,
        defaults={'telegram_chat_id': chat_id}
    )
    if not created:
        room.telegram_chat_id = chat_id
        room.save()
    return created

async def add_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("❗ Format: /addroom <xona_raqami> <chat_id>")
            return

        room_number = args[0]
        telegram_chat_id = args[1]

        created = await create_room_if_not_exists(room_number, telegram_chat_id)

        if created:
            await update.message.reply_text(f"✅ Yangi xona yaratildi: {room_number}")
        else:
            await update.message.reply_text(f"ℹ️ Xona yangilandi: {room_number}")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


# ======== WebSocketdan kelgan xabarlarni guruhga yuborish ========

async def websocket_listener(application):
    uri = "ws://localhost:8000/ws/chat/101/"
    default_chat_id = config('DEFAULT_CHAT_ID', default=None)
    if not default_chat_id:
        print("❌ .env da DEFAULT_CHAT_ID belgilanmagan.")
        return

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data.get('message'):
                        await application.bot.send_message(chat_id=default_chat_id, text=data['message'])
        except websockets.ConnectionClosed:
            print("WebSocket uzildi. 2 sekunddan so‘ng qayta ulanish...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"WebSocket xato: {e}")
            await asyncio.sleep(2)


# ======== Botni ishga tushirish ========

def main():
    application = Application.builder().token(config('BOT_TOKEN')).build()

    # Komandalarni ro‘yxatdan o‘tkazamiz
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("messages", messages))
    application.add_handler(CommandHandler("addroom", add_room))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.create_task(websocket_listener(application))

    try:
        application.run_polling()
    except Exception as e:
        print(f"Bot polling xato: {e}")


if __name__ == '__main__':
    main()
