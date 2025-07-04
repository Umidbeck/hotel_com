# bot/bot.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from decouple import config
import aiohttp

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Xush kelibsiz! /messages bilan xabarlarni ko‘ring."
    )

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8004/api/messages/101/") as response:
            if response.status == 200:
                data = await response.json()
                for msg in data:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"{msg['chatroom']}: {msg['text']}"
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Xabarlar topilmadi."
                )

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8004/api/messages/101/send/",
            json={'text': message, 'is_from_customer': False}
        ) as response:
            if response.status == 201:
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Javob yuborildi."
                )
            else:
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Xato yuz berdi."
                )

def main():
    app = Application.builder().token(config('BOT_TOKEN')).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("messages", messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.run_polling()

if __name__ == '__main__':
    main()