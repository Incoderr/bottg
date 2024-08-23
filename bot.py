# 7371499267:AAFbnSUHyqPDGJjcSQaf1seKYGR9iWSQbEM
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests

# Получите токен вашего Telegram-бота от BotFather
TOKEN = "7371499267:AAFbnSUHyqPDGJjcSQaf1seKYGR9iWSQbEM"

# Словарь для хранения пользовательских фильтров
user_filters = {}


# Функция для запроса к API Rule34 с учетом фильтров
def get_rule34_images(query, exclude_tags, limit=5):
    exclude_query = " ".join([f"-{tag}" for tag in exclude_tags])
    search_query = f"{query} {exclude_query}"

    url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&tags={search_query}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return [post['file_url'] for post in data[:limit]]
        else:
            return ["No results found."]
    else:
        return ["Error retrieving data from Rule34."]


# Команда start с кнопками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Set Filters", callback_data='set_filter'),
            InlineKeyboardButton("Search", callback_data='search')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)


# Обработка нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'set_filter':
        await query.edit_message_text('Please enter the tags you want to exclude (separated by spaces):')
        context.user_data['awaiting_filter'] = True

    elif query.data == 'search':
        await query.edit_message_text('Please enter your search query:')
        context.user_data['awaiting_search'] = True


# Обработка текстовых сообщений для фильтров и поиска
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Установка фильтров
    if context.user_data.get('awaiting_filter'):
        exclude_tags = update.message.text.split()
        user_filters[user_id] = exclude_tags
        save_filters(user_filters)
        context.user_data['awaiting_filter'] = False
        await update.message.reply_text(f'Filters set: {", ".join(exclude_tags)}')

    # Поиск изображений
    elif context.user_data.get('awaiting_search'):
        query = update.message.text
        exclude_tags = user_filters.get(user_id, [])
        images = get_rule34_images(query, exclude_tags)
        for img in images:
            await update.message.reply_text(img)
        context.user_data['awaiting_search'] = False


# Сохранение фильтров в файл
def save_filters(filters):
    with open('filters.json', 'w') as file:
        json.dump(filters, file)


# Загрузка фильтров из файла
def load_filters():
    try:
        with open('filters.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Инициализация фильтров
user_filters = load_filters()

# Основной код для запуска бота
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

