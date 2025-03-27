import os
import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # Bot token from BotFather
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Your Telegram User ID

queue = {"male": [], "female": []}  # Stores users waiting for match
active_chats = {}  # Stores ongoing chats
banned_users = set()  # Stores banned users
last_messages = {}  # Prevents spam

GENDER, CHAT = range(2)  # Conversation states

def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in banned_users:
        update.message.reply_text("🚫 You are banned from using this bot.")
        return

    update.message.reply_text(
        "👋 Welcome to Anonymous Chat!\nChoose your gender:",
        reply_markup=ReplyKeyboardMarkup([["Male", "Female"]], one_time_keyboard=True)
    )
    return GENDER

def select_gender(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    gender = update.message.text.lower()
    if gender not in ["male", "female"]:
        update.message.reply_text("❌ Invalid choice. Please select Male or Female.")
        return GENDER

    context.user_data["gender"] = gender
    update.message.reply_text("✅ Gender saved. Use /find to start chatting.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def find(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    gender = context.user_data.get("gender", None)

    if user_id in active_chats:
        update.message.reply_text("⚠ You are already in a chat!")
        return

    other_gender = "female" if gender == "male" else "male"
    
    if queue[other_gender]:
        partner_id = queue[other_gender].pop(0)
    elif queue[gender]:
        partner_id = queue[gender].pop(0)
    else:
        queue[gender].append(user_id)
        update.message.reply_text("⏳ Searching for a partner...")
        return

    active_chats[user_id] = partner_id
    active_chats[partner_id] = user_id

    context.bot.send_message(chat_id=user_id, text="🎉 Connected! Say hi!")
    context.bot.send_message(chat_id=partner_id, text="🎉 Connected! Say hi!")

def message_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in active_chats:
        update.message.reply_text("⚠ You're not in a chat. Use /find to start.")
        return

    partner_id = active_chats[user_id]
    now = time.time()
    if user_id in last_messages and now - last_messages[user_id] < 1.5:
        update.message.reply_text("⚠ Slow down! Wait before sending again.")
        return
    last_messages[user_id] = now

    context.bot.send_message(chat_id=partner_id, text=update.message.text)

def end(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in active_chats:
        update.message.reply_text("⚠ You are not in a chat.")
        return

    partner_id = active_chats.pop(user_id)
    active_chats.pop(partner_id, None)

    context.bot.send_message(chat_id=partner_id, text="🔴 Chat ended.")
    update.message.reply_text("🔴 Chat ended.")

def ban(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        update.message.reply_text("🚫 Only the bot owner can ban users.")
        return

    try:
        user_id = int(context.args[0])
        banned_users.add(user_id)
        update.message.reply_text(f"✅ User {user_id} has been banned.")
    except:
        update.message.reply_text("❌ Usage: /ban <user_id>")

def unban(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        update.message.reply_text("🚫 Only the bot owner can unban users.")
        return

    try:
        user_id = int(context.args[0])
        banned_users.discard(user_id)
        update.message.reply_text(f"✅ User {user_id} has been unbanned.")
    except:
        update.message.reply_text("❌ Usage: /unban <user_id>")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={GENDER: [MessageHandler(Filters.text & ~Filters.command, select_gender)]},
        fallbacks=[]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("find", find))
    dp.add_handler(CommandHandler("end", end))
    dp.add_handler(CommandHandler("ban", ban, pass_args=True))
    dp.add_handler(CommandHandler("unban", unban, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
  
