import asyncio
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from decouple import config
import aiohttp
import websockets
import channels.layers
import django

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_com.config.settings')
django.setup()

import datetime


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text="Xush kelibsiz! /messages bilan xabarlarni ko‘ring.")


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/api/messages/101/") as response:
                if response.status == 200:
                    data = await response.json()
                    for msg in data:
                        await context.bot.send_message(chat_id=update.message.chat_id,
                                                       text=f"{msg['chatroom']}: {msg['text']}")
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=f"Xabarlar topilmadi. Status: {response.status}")
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text=f"Server bilan ulanishda xato: {str(e)}")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    default_chat_id = config('DEFAULT_CHAT_ID', default=None)
    if not default_chat_id:
        await context.bot.send_message(chat_id=update.message.chat_id, text="XATO: DEFAULT_CHAT_ID aniqlanmadi.")
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://localhost:8000/api/messages/101/send/",
                                    json={'text': message, 'is_from_customer': False}) as response:
                if response.status == 201:
                    await context.bot.send_message(chat_id=update.message.chat_id, text="Javob yuborildi.")
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=f"Xato yuz berdi. Status: {response.status}")
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text=f"Server bilan ulanishda xato: {str(e)}")

    try:
        channel_layer = channels.layers.get_channel_layer()
        print(f"Jo'natilayotgan xabar: {message}")  # To‘liq xabar loglanadi
        await channel_layer.group_send('chat_101', {
            'type': 'chat_message',
            'message': f"Bot: {message}",
            'sender': 'bot',
            'time': datetime.datetime.now().strftime('%H:%M')
        })
    except Exception as e:
        print(f"Channel layer xatosi: {e}")


async def websocket_listener(application):
    uri = "ws://localhost:8000/ws/chat/101/"
    default_chat_id = config('DEFAULT_CHAT_ID', default=None)
    if not default_chat_id:
        print("XATO: DEFAULT_CHAT_ID aniqlanmadi. .env faylida belgilang.")
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
            print("WebSocket ulanishi uzildi, qayta urinish...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"WebSocket xatosi: {e}")
            await asyncio.sleep(2)


def main():
    application = Application.builder().token(config('BOT_TOKEN')).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("messages", messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(websocket_listener(application))

    try:
        application.run_polling()
    except Exception as e:
        print(f"Polling xatosi: {e}")


if __name__ == '__main__':
    main()