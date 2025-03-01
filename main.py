import logging
import re
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
    sheet = client.open(sheet_name).sheet1  # Access the first sheet
    return sheet

def save_user_info(user_id, first_name, last_name, username, language):
    sheet = connect_to_google_sheets("DrinkStock")
    existing_data = sheet.get_all_values()
    next_row = len(existing_data) + 1  # First row is for headers, so start appending from row 2
    sheet.append_row([user_id, first_name, last_name, username, language], table_range=f"A{next_row}:E{next_row}")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states
CONTACT, BACK_TO_START, MAP, OFFER, REVIEW, COCKTAIL_RECIPE, CHANGE_ADDRESSES, CHANGE_ADMINS, CHANGE_COCKTAIL_RECIPE, CHANGE_CONTACT_INFO, CHANGE_START_MESSAGE = range(11)

def read_file(file_name: str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        return file.read()

def read_admins(file_path):
    with open(file_path, 'r') as file:
        admins = [line.strip() for line in file if line.strip()]
    return admins

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and logs user info to Google Sheets."""
    user = update.message.from_user if update.message else update.callback_query.from_user
    save_user_info(user.id, user.first_name, user.last_name or '', user.username or 'N/A', user.language_code)
    logger.info(f"User Info Saved: ID={user.id}, Name={user.first_name} {user.last_name or ''}, "
                f"Username={user.username or 'N/A'}, Language={user.language_code}")
    admins = read_admins('admins.txt')
    is_admin = user.username in admins
    keyboard = [
        [InlineKeyboardButton('Harta magazinelor', callback_data='map'),
         InlineKeyboardButton('Oferta lunii', callback_data='offer')],
        [InlineKeyboardButton('Contacte', callback_data='contact')],
        [InlineKeyboardButton('Lăsați o recenzie anonimă', callback_data='review'),
         InlineKeyboardButton('Rețetă cocktail pe viitor', callback_data='cocktail')],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton('Schimba adresele', callback_data='change_addresses')])
        keyboard.append([InlineKeyboardButton('Modifica administratori', callback_data='change_admins')])
        keyboard.append([InlineKeyboardButton('Schimba rețeta cocktailului', callback_data='change_cocktail_recipe')])
        keyboard.append([InlineKeyboardButton('Schimba contactele', callback_data='change_contact_info')])
        keyboard.append([InlineKeyboardButton('Schimba mesaj de start', callback_data='change_start_message')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    start_text = read_file('start_text.html')
    if update.message:
        await update.message.reply_photo(
            photo='https://libercard.md/storage/partner/February2021/78tUbaCsWGg58W9D0L1D.jpg',
            caption=start_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.answer()
        await handle_back(update, context)
    return BACK_TO_START

async def change_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the current addresses and prompts the admin to send new data."""
    await update.callback_query.answer()  # Acknowledge the callback query
    current_addresses = read_file('map_locations.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "Current addresses:\n\n" + current_addresses + "\n\nPlease send the new addresses.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CHANGE_ADDRESSES

async def save_new_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new addresses to map_locations.html and returns to the start."""
    new_addresses = update.message.text
    url_pattern = re.compile(r'(📍.*?)(https?://\S+)\)')
    new_addresses = url_pattern.sub(r'<a href="\2">\1</a>', new_addresses)
    new_addresses = new_addresses.replace(' (', '')
    with open('map_locations.html', 'w', encoding='utf-8') as file:
        file.write(new_addresses)
    await update.message.reply_text("Addresses updated successfully.")
    return await start(update, context)

async def change_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the current admins and prompts the admin to send new data."""
    await update.callback_query.answer()  # Acknowledge the callback query
    current_admins = read_file('admins.txt')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "Current admins:\n\n" + current_admins + "\n\nPlease send the new admin usernames, one per line.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CHANGE_ADMINS

async def save_new_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new admin usernames to admins.txt and returns to the start."""
    new_admins = update.message.text
    with open('admins.txt', 'w', encoding='utf-8') as file:
        file.write(new_admins)
    await update.message.reply_text("Admins updated successfully.")
    return await start(update, context)

async def change_cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the current cocktail recipe and prompts the admin to send new data."""
    await update.callback_query.answer()  # Acknowledge the callback query
    current_recipe = read_file('cocktail_recipe.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "Current cocktail recipe:\n\n" + current_recipe + "\n\nPlease send the new cocktail recipe in HTML format.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CHANGE_COCKTAIL_RECIPE

async def save_new_cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new cocktail recipe to cocktail_recipe.html and returns to the start."""
    new_recipe = update.message.text
    url_pattern = re.compile(r'(.*?)(https?://\S+)\)')
    new_recipe = url_pattern.sub(r'<a href="\2">\1</a>', new_recipe)
    new_recipe = new_recipe.replace(' (', '')
    with open('cocktail_recipe.html', 'w', encoding='utf-8') as file:
        file.write(new_recipe)
    await update.message.reply_text("Cocktail recipe updated successfully.")
    return await start(update, context)

async def change_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the current contact information and prompts the admin to send new data."""
    await update.callback_query.answer()  # Acknowledge the callback query
    current_contact_info = read_file('contact_info.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "Current contact information:\n\n" + current_contact_info + "\n\nPlease send the new contact information in HTML format.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CHANGE_CONTACT_INFO

async def save_new_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new contact information to contact_info.html and returns to the start."""
    new_contact_info = update.message.text
    url_pattern = re.compile(r'(.*?)(https?://\S+)\)')
    new_contact_info = url_pattern.sub(r'<a href="\2">\1</a>', new_contact_info)
    new_contact_info = new_contact_info.replace(' (', '')
    with open('contact_info.html', 'w', encoding='utf-8') as file:
        file.write(new_contact_info)
    await update.message.reply_text("Contact information updated successfully.")
    return await start(update, context)

async def change_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the current start message and prompts the admin to send new data."""
    await update.callback_query.answer()  # Acknowledge the callback query
    current_start_message = read_file('start_text.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "Current start message:\n\n" + current_start_message + "\n\nPlease send the new start message in HTML format.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CHANGE_START_MESSAGE

async def save_new_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the new start message to start_text.html and returns to the start."""
    new_start_message = update.message.text
    url_pattern = re.compile(r'(.*?)(https?://\S+)\)')
    new_start_message = url_pattern.sub(r'<a href="\2">\1</a>', new_start_message)
    new_start_message = new_start_message.replace(' (', '')
    with open('start_text.html', 'w', encoding='utf-8') as file:
        file.write(new_start_message)
    await update.message.reply_text("Start message updated successfully.")
    return await start(update, context)

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
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Acestea sunt ofertele lunii! Apasă 'Înapoi' pentru a reveni.",
                                                   reply_markup=reply_markup)
    return BACK_TO_START

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
    user = update.callback_query.from_user
    admins = read_admins('admins.txt')
    is_admin = user.username in admins
    keyboard = [
        [InlineKeyboardButton('Harta magazinelor', callback_data='map'),
         InlineKeyboardButton('Oferta lunii', callback_data='offer')],
        [InlineKeyboardButton('Contacte', callback_data='contact')],
        [InlineKeyboardButton('Lăsați o recenzie anonimă', callback_data='review'),
         InlineKeyboardButton('Rețetă cocktail pe viitor', callback_data='cocktail')],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton('Schimba adresele', callback_data='change_addresses')])
        keyboard.append([InlineKeyboardButton('Modifica administratori', callback_data='change_admins')])
        keyboard.append([InlineKeyboardButton('Schimba rețeta cocktailului', callback_data='change_cocktail_recipe')])
        keyboard.append([InlineKeyboardButton('Schimba contactele', callback_data='change_contact_info')])
        keyboard.append([InlineKeyboardButton('Schimba mesaj de start', callback_data='change_start_message')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    start_text = read_file('start_text.html')
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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BACK_TO_START: [
                CallbackQueryHandler(contact, pattern='contact'),
                CallbackQueryHandler(map_locations, pattern='map'),
                CallbackQueryHandler(offer, pattern='offer'),
                CallbackQueryHandler(review, pattern='review'),
                CallbackQueryHandler(handle_back, pattern='back'),
                CallbackQueryHandler(cocktail_recipe, pattern='cocktail'),
                CallbackQueryHandler(change_addresses, pattern='change_addresses'),
                CallbackQueryHandler(change_admins, pattern='change_admins'),
                CallbackQueryHandler(change_cocktail_recipe, pattern='change_cocktail_recipe'),
                CallbackQueryHandler(change_contact_info, pattern='change_contact_info'),
                CallbackQueryHandler(change_start_message, pattern='change_start_message')
            ],
            CONTACT: [CallbackQueryHandler(handle_back, pattern='back')],
            MAP: [CallbackQueryHandler(handle_back, pattern='back')],
            OFFER: [CallbackQueryHandler(handle_back, pattern='back')],
            REVIEW: [CallbackQueryHandler(handle_back, pattern='back')],
            COCKTAIL_RECIPE: [CallbackQueryHandler(handle_back, pattern='back')],
            CHANGE_ADDRESSES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_addresses),
                CallbackQueryHandler(handle_back, pattern='back')
            ],
            CHANGE_ADMINS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_admins),
                CallbackQueryHandler(handle_back, pattern='back')
            ],
            CHANGE_COCKTAIL_RECIPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_cocktail_recipe),
                CallbackQueryHandler(handle_back, pattern='back')
            ],
            CHANGE_CONTACT_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_contact_info),
                CallbackQueryHandler(handle_back, pattern='back')
            ],
            CHANGE_START_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_start_message),
                CallbackQueryHandler(handle_back, pattern='back')
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text('Conversation cancelled.',
                                                                                              reply_markup=ReplyKeyboardRemove()))],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()