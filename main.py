import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)
from telegram import InputMediaPhoto

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define states
CONTACT, BACK_TO_START, MAP, OFFER, REVIEW, COCKTAIL_RECIPE = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and greets the user."""
    keyboard = [
        [InlineKeyboardButton('Contacte', callback_data='contact')],
        [InlineKeyboardButton('Harta magazinelor', callback_data='map')],
        [InlineKeyboardButton('Oferta lunii', callback_data='offer')],
        [InlineKeyboardButton('Lăsați o recenzie anonimă', callback_data='review')],
        [InlineKeyboardButton('Rețetă cocktail pe viitor', callback_data='cocktail')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open('start_text.html', 'r', encoding='utf-8') as file:
        start_text = file.read()

    await update.message.reply_photo(
        photo='https://libercard.md/storage/partner/February2021/78tUbaCsWGg58W9D0L1D.jpg',
        caption=start_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return BACK_TO_START


async def cocktail_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the cocktail recipe with a link to the YouTube video."""
    with open('cocktail_recipe.html', 'r', encoding='utf-8') as file:
        recipe_info = file.read()

    keyboard = [[InlineKeyboardButton("Inapoi", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(recipe_info, parse_mode='HTML', reply_markup=reply_markup)

    return COCKTAIL_RECIPE


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays contact information."""
    with open('contact_info.html', 'r', encoding='utf-8') as file:
        contact_info = file.read()

    keyboard = [[InlineKeyboardButton("Inapoi", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(contact_info, parse_mode='HTML', reply_markup=reply_markup)

    return CONTACT


async def map_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the list of city districts and addresses with Google Maps links."""
    with open('map_locations.html', 'r', encoding='utf-8') as file:
        districts_info = file.read()

    keyboard = [[InlineKeyboardButton("Inapoi", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(districts_info, parse_mode='HTML', reply_markup=reply_markup)

    return MAP


async def offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays a series of photos for the offer of the month as a single message."""
    offer_photos = [
        'https://scontent.fkiv8-1.fna.fbcdn.net/v/t39.30808-6/474901039_1197331885731034_8905770824111627649_n.jpg?_nc_cat=110&ccb=1-7&_nc_sid=833d8c&_nc_ohc=9wrXsl1-NiAQ7kNvgHCYYxO&_nc_zt=23&_nc_ht=scontent.fkiv8-1.fna&_nc_gid=ANYOHkiuDLCA609SR_Vf2iY&oh=00_AYDLZ1IlKCZ71BeCiGIt3xo3T2cbccao5_GrkIvLGab-Bg&oe=679DCD52',
        'https://scontent.fkiv8-1.fna.fbcdn.net/v/t39.30808-6/473289075_1197331932397696_4280668545222018533_n.jpg?_nc_cat=102&ccb=1-7&_nc_sid=833d8c&_nc_ohc=JrMQDoERQ0gQ7kNvgGGVXOI&_nc_zt=23&_nc_ht=scontent.fkiv8-1.fna&_nc_gid=Aw4avg_GtlvsKGye2mmoXwb&oh=00_AYBiZLfxqo3PPeq7WHNfihM8sw2OuOhG4_CeP3JNpD4Etw&oe=679DC38E'
    ]

    media = [InputMediaPhoto(photo) for photo in offer_photos]

    await context.bot.send_media_group(chat_id=update.callback_query.from_user.id, media=media)

    await update.callback_query.message.reply_text("Acestea sunt ofertele lunii!")

    return OFFER


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the review message with a link to the Google Form."""
    with open('review.html', 'r', encoding='utf-8') as file:
        review_info = file.read()

    keyboard = [[InlineKeyboardButton("Inapoi", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(review_info, parse_mode='HTML', reply_markup=reply_markup)

    return REVIEW


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the back button to return to the start message."""
    await start(update, context)
    return BACK_TO_START


def main() -> None:
    """Run the bot."""
    with open('.env', 'r', encoding='utf-8') as file:
        API_KEY = file.read()
    application = Application.builder().token(API_KEY).build()

    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BACK_TO_START: [
                CallbackQueryHandler(contact, pattern='contact'),  # Handle the Contacte button
                CallbackQueryHandler(map_locations, pattern='map'),  # Handle the Harta magazinelor button
                CallbackQueryHandler(offer, pattern='offer'),  # Handle the Oferat lunii button
                CallbackQueryHandler(review, pattern='review'),  # Handle the Lăsați o recenzie anonimă button
                CallbackQueryHandler(cocktail_recipe, pattern='cocktail')  # Handle the Lăsați o recenzie anonimă button
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
