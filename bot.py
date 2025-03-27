import random
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler, CallbackQueryHandler
from telegram.ext import PicklePersistence
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a persistence object to store data across bot restarts
persistence = PicklePersistence('user_data')

# Constants for stages in ConversationHandler
GENDER, LANGUAGE, ADMIN_PANEL = range(3)

# Define user data storage (gender, language)
user_data = {}

# Banned users storage
banned_users = set()

# Admin ID (Replace this with your Telegram user ID)
ADMIN_ID = 'your_telegram_user_id'  # Replace with actual admin ID

# Define the languages
LANGUAGES = {
    'en': {'start': 'Welcome! Please select your gender.', 'male': 'You are male!', 'female': 'You are female!'},
    'ru': {'start': 'Добро пожаловать! Пожалуйста, выберите ваш пол.', 'male': 'Вы мужчина!', 'female': 'Вы женщина!'},
    'id': {'start': 'Selamat datang! Silakan pilih jenis kelamin Anda.', 'male': 'Anda pria!', 'female': 'Anda wanita!'}
}

def start(update: Update, context: CallbackContext) -> int:
    """Start conversation and ask gender"""
    user_id = update.message.from_user.id
    update.message.reply_text("Please select your gender:\n1. Male\n2. Female", reply_markup=gender_keyboard())
    return GENDER

def gender_keyboard():
    """Create gender selection keyboard"""
    return [
        ['Male', 'Female']
    ]

def set_gender(update: Update, context: CallbackContext) -> int:
    """Save the user's gender preference"""
    user_id = update.message.from_user.id
    gender = update.message.text.lower()

    if gender == 'male' or gender == 'female':
        user_data[user_id] = {'gender': gender}
        update.message.reply_text(f"Your gender is {gender}. Please select your language.")
        return LANGUAGE
    else:
        update.message.reply_text("Please select a valid option.")

def set_language(update: Update, context: CallbackContext) -> int:
    """Save the user's language preference"""
    user_id = update.message.from_user.id
    language = update.message.text.lower()

    if language in LANGUAGES:
        user_data[user_id]['language'] = language
        update.message.reply_text(LANGUAGES[language]['start'])
        return ConversationHandler.END
    else:
        update.message.reply_text("Please choose a valid language: English, Russian, or Indonesian.")

def match_users(update: Update, context: CallbackContext):
    """Match users randomly based on gender"""
    user_id = update.message.from_user.id
    current_user_gender = user_data.get(user_id, {}).get('gender')

    if not current_user_gender:
        update.message.reply_text("Please set your gender and language first.")
        return

    # Find random user of the opposite gender
    opposite_gender = 'male' if current_user_gender == 'female' else 'female'
    matched_user = random.choice([uid for uid, data in user_data.items() if data.get('gender') == opposite_gender])

    update.message.reply_text(f"You've been matched with User {matched_user}. Have a chat!")

# Admin commands
def admin_panel(update: Update, context: CallbackContext):
    """Show the admin panel"""
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("You are not authorized to access this panel.")
        return

    update.message.reply_text(
        "Welcome to the Admin Panel.\n\n"
        "Choose an option:\n"
        "/ban <user_id> - Ban a user\n"
        "/unban <user_id> - Unban a user\n"
        "/list_users - List all users\n"
        "/send_notice <message> - Send a notice to all users"
    )

def ban_user(update: Update, context: CallbackContext):
    """Ban a user"""
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("You are not authorized to perform this action.")
        return

    try:
        target_user_id = int(context.args[0])
        banned_users.add(target_user_id)
        update.message.reply_text(f"User {target_user_id} has been banned.")
    except (IndexError, ValueError):
        update.message.reply_text("Please provide a valid user ID to ban.")

def unban_user(update: Update, context: CallbackContext):
    """Unban a user"""
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("You are not authorized to perform this action.")
        return

    try:
        target_user_id = int(context.args[0])
        banned_users.discard(target_user_id)
        update.message.reply_text(f"User {target_user_id} has been unbanned.")
    except (IndexError, ValueError):
        update.message.reply_text("Please provide a valid user ID to unban.")

def list_users(update: Update, context: CallbackContext):
    """List all registered users"""
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("You are not authorized to perform this action.")
        return

    users_list = "\n".join([str(uid) for uid in user_data.keys()])
    update.message.reply_text(f"List of all users:\n{users_list}")

def send_notice(update: Update, context: CallbackContext):
    """Send a notice to all users"""
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("You are not authorized to perform this action.")
        return

    notice_message = " ".join(context.args)
    if not notice_message:
        update.message.reply_text("Please provide a message to send to all users.")
        return

    for user_id in user_data.keys():
        if user_id not in banned_users:
            context.bot.send_message(user_id, notice_message)
    
    update.message.reply_text("Notice sent to all users.")

def main():
    """Start the bot"""
    application = Application.builder().token('YOUR_BOT_API_KEY').persistence(persistence).build()

    # Add the conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(Filters.text, set_gender)],
            LANGUAGE: [MessageHandler(Filters.text, set_language)],
        },
        fallbacks=[],
    )

    # Register handlers
    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler('match', match_users))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(CommandHandler('ban', ban_user))
    application.add_handler(CommandHandler('unban', unban_user))
    application.add_handler(CommandHandler('list_users', list_users))
    application.add_handler(CommandHandler('send_notice', send_notice))

    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()
    
