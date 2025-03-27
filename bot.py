import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, PicklePersistence, ConversationHandler
from telegram.ext import ContextTypes
from telegram.ext import CommandHandler, MessageHandler, filters, Application
import pickle

# Constants for conversation states
GENDER, LANGUAGE, MATCHING = range(3)

# Dictionary to hold user data in memory
user_data = {}

# Banned users
banned_users = set()

# Admin ID (replace with your admin Telegram user ID)
ADMIN_ID = 123456789

# Language settings
LANGUAGES = {
    'en': 'English',
    'ru': 'Russian',
    'id': 'Indonesian'
}

async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    
    if user_id in banned_users:
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome! Please select your gender.\n\n"
        "1. Male\n"
        "2. Female"
    )
    
    return GENDER

async def gender(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    
    if user_id in banned_users:
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    # Save the gender preference
    gender = update.message.text.lower()
    if gender == '1' or gender == 'male':
        user_data[user_id] = {'gender': 'male'}
    elif gender == '2' or gender == 'female':
        user_data[user_id] = {'gender': 'female'}
    else:
        await update.message.reply_text("Invalid gender option. Please select '1' for Male or '2' for Female.")
        return GENDER

    await update.message.reply_text(
        "Now, please select your language.\n\n"
        "1. English\n"
        "2. Russian\n"
        "3. Indonesian"
    )
    
    return LANGUAGE

async def language(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    
    if user_id in banned_users:
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    # Save the language preference
    lang = update.message.text.lower()
    if lang == '1' or lang == 'english':
        user_data[user_id]['language'] = 'en'
    elif lang == '2' or lang == 'russian':
        user_data[user_id]['language'] = 'ru'
    elif lang == '3' or lang == 'indonesian':
        user_data[user_id]['language'] = 'id'
    else:
        await update.message.reply_text("Invalid language option. Please select '1' for English, '2' for Russian, or '3' for Indonesian.")
        return LANGUAGE

    await update.message.reply_text("You are all set! Looking for a match...")

    # Match the user with someone of the opposite gender
    return await match_user(update, context)

async def match_user(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in banned_users:
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    user_gender = user_data[user_id].get('gender')
    user_lang = user_data[user_id].get('language')
    
    # Find users of the opposite gender
    available_users = [
        user for user, data in user_data.items() 
        if data['gender'] != user_gender and data['language'] == user_lang and user != user_id
    ]

    if not available_users:
        await update.message.reply_text("Sorry, no matches available right now. Please try again later.")
        return ConversationHandler.END
    
    # Randomly match with someone
    matched_user = random.choice(available_users)
    matched_user_name = f"User {matched_user}"
    
    await update.message.reply_text(f"Congratulations! You have been matched with {matched_user_name}.")
    return ConversationHandler.END

# Admin panel commands
async def admin_panel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to access the admin panel.")
        return

    await update.message.reply_text("Admin Panel:\n\n"
                                    "/ban <user_id> - Ban a user\n"
                                    "/unban <user_id> - Unban a user\n"
                                    "/list_users - List all users\n"
                                    "/send_notice <message> - Send a notice to all users")

async def ban_user(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide the user_id to ban.")
        return

    user_id = int(context.args[0])
    
    if user_id in banned_users:
        await update.message.reply_text("This user is already banned.")
        return

    banned_users.add(user_id)
    await update.message.reply_text(f"User {user_id} has been banned.")

async def unban_user(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide the user_id to unban.")
        return

    user_id = int(context.args[0])
    
    if user_id not in banned_users:
        await update.message.reply_text("This user is not banned.")
        return

    banned_users.remove(user_id)
    await update.message.reply_text(f"User {user_id} has been unbanned.")

async def list_users(update: Update, context: CallbackContext):
    users_list = "\n".join([str(user) for user in user_data.keys()])
    await update.message.reply_text(f"List of users:\n\n{users_list}")

async def send_notice(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide the message to send.")
        return

    message = ' '.join(context.args)
    for user_id in user_data.keys():
        try:
            await context.bot.send_message(user_id, message)
        except:
            continue
    await update.message.reply_text("Notice sent to all users.")

def main():
    # Set up persistence
    persistence = PicklePersistence("bot_data")

    # Create the application and add handlers
    application = Application.builder().token('YOUR_BOT_API_KEY').persistence(persistence).build()

    # Add conversation handlers
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language)],
            MATCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, match_user)]
        },
        fallbacks=[]
    )

    # Add admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(CommandHandler("send_notice", send_notice))

    # Add conversation handler to the application
    application.add_handler(conversation_handler)

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
