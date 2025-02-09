import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)
from telegram import InputMediaPhoto

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate with Google Sheets
def connect_to_google_sheets(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet by name
    sheet = client.open(sheet_name).sheet1  # Access the first sheet
    return sheet


def save_user_info(user_id, first_name, last_name, username, language):
    sheet = connect_to_google_sheets("DrinkStock")

    # Get existing data to find the next empty row, skipping the header row
    existing_data = sheet.get_all_values()
    next_row = len(existing_data) + 1  # First row is for headers, so start appending from row 2

    # Append user data at the next available row (below the header)
    sheet.append_row([user_id, first_name, last_name, username, language], table_range=f"A{next_row}:E{next_row}")


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define states
CONTACT, BACK_TO_START, MAP, OFFER, REVIEW, COCKTAIL_RECIPE = range(6)


def read_file(file_name: str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        return file.read()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and logs user info to Google Sheets."""
    user = update.message.from_user if update.message else update.callback_query.from_user

    # Save user info to Google Sheets
    save_user_info(user.id, user.first_name, user.last_name or '', user.username or 'N/A', user.language_code)

    logger.info(f"User Info Saved: ID={user.id}, Name={user.first_name} {user.last_name or ''}, "
                f"Username={user.username or 'N/A'}, Language={user.language_code}")

    # Проверяем, откуда вызвана команда: сообщение или колбэк
    if update.message:  # Если вызов из сообщения
        keyboard = [
            [InlineKeyboardButton('Harta magazinelor', callback_data='map'),
             InlineKeyboardButton('Oferta lunii', callback_data='offer')],
            [InlineKeyboardButton('Contacte', callback_data='contact'),
             InlineKeyboardButton('Lăsați o recenzie anonimă', callback_data='review')],
            [InlineKeyboardButton('Rețetă cocktail pe viitor', callback_data='cocktail')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        start_text = read_file('start_text.html')

        await update.message.reply_photo(
            photo='https://libercard.md/storage/partner/February2021/78tUbaCsWGg58W9D0L1D.jpg',
            caption=start_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:  # Если вызов из колбэка
        await update.callback_query.answer()
        await handle_back(update, context)

    return BACK_TO_START


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays contact information."""
    await update.callback_query.answer()  # Acknowledge the callback query
    contact_info = read_file('contact_info.html')

    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(contact_info, parse_mode='HTML', reply_markup=reply_markup)

    return BACK_TO_START


async def map_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the list of city districts and addresses with Google Maps links."""
    await update.callback_query.answer()  # Acknowledge the callback query
    districts_info = read_file('map_locations.html')

    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(districts_info, parse_mode='HTML', reply_markup=reply_markup)

    return BACK_TO_START


async def offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays a series of photos for the offer of the month as a single message."""
    offer_photos = read_file('offer_photos.txt').split('\n')

    media = [InputMediaPhoto(photo) for photo in offer_photos]

    await context.bot.send_media_group(chat_id=update.callback_query.from_user.id, media=media)

    # Add the "Înapoi" button after sending the offers
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Acestea sunt ofertele lunii! Apasă 'Înapoi' pentru a reveni.",
                                                   reply_markup=reply_markup)

    return BACK_TO_START  # Return to BACK_TO_START state


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the review message with a link to the Google Form."""
    await update.callback_query.answer()  # Acknowledge the callback query
    review_info = read_file('review.html')

    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(review_info, parse_mode='HTML', reply_markup=reply_markup)

    return BACK_TO_START


async def cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the cocktail recipe with a link to the YouTube video."""
    await update.callback_query.answer()  # Acknowledge the callback query
    recipe_info = read_file('cocktail_recipe.html')

    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(recipe_info, parse_mode='HTML', reply_markup=reply_markup)

    return BACK_TO_START


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the back button to return to the start message."""
    await update.callback_query.answer()

    keyboard = [
        [InlineKeyboardButton('Harta magazinelor', callback_data='map'),
         InlineKeyboardButton('Oferta lunii', callback_data='offer')],
        [InlineKeyboardButton('Contacte', callback_data='contact'),
         InlineKeyboardButton('Lăsați o recenzie anonimă', callback_data='review')],
        [InlineKeyboardButton('Rețetă cocktail pe viitor', callback_data='cocktail')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    start_text = read_file('start_text.html')

    # Избегаем дублирования вызова edit_media
    if update.callback_query.message.photo:
        await update.callback_query.message.edit_caption(
            caption=start_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_photo(
            photo='https://libercard.md/storage/partner/February2021/78tUbaCsWGg58W9D0L1D.jpg',
            caption=start_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    return BACK_TO_START

def main() -> None:
    """Run the bot."""
    API_KEY = read_file('.env')
    application = Application.builder().token(API_KEY).build()

    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BACK_TO_START: [
                CallbackQueryHandler(contact, pattern='contact'),  # Handle the Contacte button
                CallbackQueryHandler(map_locations, pattern='map'),  # Handle the Harta magazinelor button
                CallbackQueryHandler(offer, pattern='offer'),  # Handle the Oferta lunii button
                CallbackQueryHandler(review, pattern='review'),  # Handle the Lăsați o recenzie anonimă button
                CallbackQueryHandler(handle_back, pattern='back'),  # Handle the Inapoi button
                CallbackQueryHandler(cocktail_recipe, pattern='cocktail')  # Handle the Rețetă cocktail pe viitor button
            ],
            CONTACT: [CallbackQueryHandler(handle_back, pattern='back')],
            MAP: [CallbackQueryHandler(handle_back, pattern='back')],
            OFFER: [CallbackQueryHandler(handle_back, pattern='back')],
            REVIEW: [CallbackQueryHandler(handle_back, pattern='back')],
            COCKTAIL_RECIPE: [CallbackQueryHandler(handle_back, pattern='back')]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text('Conversation cancelled.',
                                                                                              reply_markup=ReplyKeyboardRemove()))],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
