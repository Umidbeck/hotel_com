#bot/handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from chat.models import Message
from qr_auth.models import Room

@sync_to_async
def save_room(room_number: str, chat_id: str):
    room, created = Room.objects.get_or_create(number=room_number)
    room.telegram_chat_id = chat_id
    room.save()
    return created

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❗ Format: /register <xona_raqami>")
        return

    room_number = args[0]
    chat_id = str(update.effective_chat.id)

    created = await save_room(room_number, chat_id)

    if created:
        msg = f"✅ Yangi xona qo‘shildi: {room_number}"
    else:
        msg = f"♻️ Xona yangilandi: {room_number}"

    await update.message.reply_text(msg, reply_markup=room_menu(room_number))

def room_menu(room_number: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Xabarlarni o‘chirish", callback_data=f"clear_{room_number}")],
        [InlineKeyboardButton("🔁 Guruhni yangilash", callback_data=f"update_{room_number}")],
    ])

@sync_to_async
def clear_room_messages(room_number):
    room = Room.objects.get(number=room_number)
    Message.objects.filter(chatroom=room).delete()
    return True

@sync_to_async
def update_room_chat_id(room_number, chat_id):
    room = Room.objects.get(number=room_number)
    room.telegram_chat_id = chat_id
    room.save()
    return True

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("clear_"):
        room_number = data.split("_")[1]
        await clear_room_messages(room_number)
        await query.edit_message_text(f"✅ {room_number} uchun xabarlar tozalandi.")
    elif data.startswith("update_"):
        room_number = data.split("_")[1]
        chat_id = str(update.effective_chat.id)
        await update_room_chat_id(room_number, chat_id)
        await query.edit_message_text(f"✅ {room_number} uchun guruh yangilandi.")