import logging
import os
import re
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)
from telegram import InputMediaPhoto
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_google_sheets(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def save_user_info(user_id, first_name, last_name, username, language):
    sheet = connect_to_google_sheets("DrinkStock")
    existing_data = sheet.get_all_values()
    next_row = len(existing_data) + 1
    sheet.append_row([user_id, first_name, last_name, username, language], table_range=f"A{next_row}:E{next_row}")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

CONTACT, BACK_TO_START, MAP, OFFER, REVIEW, COCKTAIL_RECIPE, CHANGE_ADDRESSES, CHANGE_ADMINS, CHANGE_COCKTAIL_RECIPE, CHANGE_CONTACT_INFO, CHANGE_START_MESSAGE, CHANGE_REVIEW = range(12)

def read_file(file_name: str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        return file.read()

def read_file_lines(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_new_content(file_path: str, content: str):
    url_pattern = re.compile(r'(.*?)(https?://\S+)\)')
    content = url_pattern.sub(r'<a href="\2">\1</a>', content)
    content = content.replace(' (', '')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

async def handle_change(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str, prompt: str, next_state: int) -> int:
    await update.callback_query.answer()
    current_content = read_file(file_path)
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        f"Current content:\n\n{current_content}\n\n{prompt}",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return next_state

async def handle_save(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str) -> int:
    new_content = update.message.text
    save_new_content(file_path, new_content)
    await update.message.reply_text("Content updated successfully.")
    return await start(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user if update.message else update.callback_query.from_user
    save_user_info(user.id, user.first_name, user.last_name or '', user.username or 'N/A', user.language_code)
    logger.info(f"User Info Saved: ID={user.id}, Name={user.first_name} {user.last_name or ''}, "
                f"Username={user.username or 'N/A'}, Language={user.language_code}")
    admins = read_file_lines('admins.txt')
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
        keyboard.append([InlineKeyboardButton('Schimba recenzia', callback_data='change_review')])
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
    return await handle_change(update, context, 'map_locations.html', "Please send the new addresses.", CHANGE_ADDRESSES)

async def save_new_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'map_locations.html')

async def change_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_change(update, context, 'admins.txt', "Please send the new admin usernames, one per line.", CHANGE_ADMINS)

async def save_new_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'admins.txt')

async def change_cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_change(update, context, 'cocktail_recipe.html', "Please send the new cocktail recipe in HTML format.", CHANGE_COCKTAIL_RECIPE)

async def save_new_cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'cocktail_recipe.html')

async def change_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_change(update, context, 'contact_info.html', "Please send the new contact information in HTML format.", CHANGE_CONTACT_INFO)

async def save_new_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'contact_info.html')

async def change_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_change(update, context, 'start_text.html', "Please send the new start message in HTML format.", CHANGE_START_MESSAGE)

async def save_new_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'start_text.html')

async def change_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_change(update, context, 'review.html', "Please send the new review message in HTML format.", CHANGE_REVIEW)

async def save_new_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_save(update, context, 'review.html')

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    contact_info = read_file('contact_info.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(contact_info, parse_mode='HTML', reply_markup=reply_markup)
    return BACK_TO_START

async def map_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    districts_info = read_file('map_locations.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(districts_info, parse_mode='HTML', reply_markup=reply_markup)
    return BACK_TO_START

async def offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    offer_photos_dir = 'offers'
    offer_photos = [os.path.join(offer_photos_dir, file) for file in os.listdir(offer_photos_dir) if file.endswith(('jpg', 'jpeg', 'png'))]
    media = [InputMediaPhoto(open(photo, 'rb')) for photo in offer_photos]
    await context.bot.send_media_group(chat_id=update.callback_query.from_user.id, media=media)
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Acestea sunt ofertele lunii! Apasă 'Înapoi' pentru a reveni.", reply_markup=reply_markup)
    return BACK_TO_START

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    review_info = read_file('review.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(review_info, parse_mode='HTML', reply_markup=reply_markup)
    return BACK_TO_START

async def cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    recipe_info = read_file('cocktail_recipe.html')
    keyboard = [[InlineKeyboardButton("Înapoi", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(recipe_info, parse_mode='HTML', reply_markup=reply_markup)
    return BACK_TO_START

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    user = update.callback_query.from_user
    admins = read_file_lines('admins.txt')
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
        keyboard.append([InlineKeyboardButton('Schimba recenzia', callback_data='change_review')])
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
                CallbackQueryHandler(change_start_message, pattern='change_start_message'),
                CallbackQueryHandler(change_review, pattern='change_review')
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
            ],
            CHANGE_REVIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_review),
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