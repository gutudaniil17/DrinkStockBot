import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define states
CONTACT, BACK_TO_START = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and greets the user."""
    reply_keyboard = [['Contacte', 'Principala']]  # Added "Principala" button

    await update.message.reply_photo(
        photo='https://libercard.md/storage/partner/February2021/78tUbaCsWGg58W9D0L1D.jpg',  # Replace with your image URL
        caption='<b>Salut, suntem bucurosi ca ai ajuns aici!</b>',
        parse_mode='HTML'
    )

    await update.message.reply_text(
        'Alege o opțiune de mai jos:',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return BACK_TO_START

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays contact information."""
    contact_info = (
        "<b>Contacte:</b>\n"
        "Pentru mai multe informații, ne poți contacta la:\n"
        "📞 Telefon: 068181144\n"
        "🌐 Website: <a href='https://drinkstock.md/?fbclid=IwZXh0bgNhZW0CMTAAAR2PP-IPBbMym_YwbBRe2yURHANoqLCEdsQMB5_Pk_pr3ajozJPoAntHLxA_aem_Y62C0TqFKvBh-1V67hVE2Q'>Drink Stock</a>\n"
        "📘 Facebook: <a href='https://www.facebook.com/drinkstock.md'>Drink Stock Facebook</a>\n"
        "📸 Instagram: <a href='https://www.instagram.com/drinkstock.md/'>Drink Stock Instagram</a>\n"
        "Dacă dorești să te întorci, apasă butonul de mai jos."
    )

    keyboard = [[InlineKeyboardButton("Inapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(contact_info, parse_mode='HTML', reply_markup=reply_markup)

    return CONTACT

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the back button to return to the start message."""
    await start(update, context)
    return BACK_TO_START

async def handle_principala(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the Principala button to return to the start message."""
    await start(update, context)
    return BACK_TO_START

def main() -> None:
    """Run the bot."""
    application = Application.builder().token("8145932962:AAH1afhx6Le4crhX10fhfr_Cn6TMpAH6LGw").build()

    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BACK_TO_START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex('^Contacte$'), contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex('^Principala$'), handle_principala)
            ],
            CONTACT: [CallbackQueryHandler(handle_back, pattern='back')]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text('Conversation cancelled.',
                                                                                              reply_markup=ReplyKeyboardRemove()))],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
