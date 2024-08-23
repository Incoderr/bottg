# 6890541014:AAHft5nEIhyWAbyHjol3Uu8C3fmnEzS-Wp8

import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests

# Получите токен вашего Telegram-бота от BotFather
TOKEN = "6890541014:AAHft5nEIhyWAbyHjol3Uu8C3fmnEzS-Wp8"

# Словарь для хранения пользовательских фильтров и последних запросов
user_data = {}


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
            InlineKeyboardButton("Search", callback_data='search'),
            InlineKeyboardButton("View Filters", callback_data='view_filters')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)


# Обработка нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'set_filter':
        await query.edit_message_text('Please enter the tags you want to exclude, separated by commas:')
        context.user_data['awaiting_filter'] = True

    elif query.data == 'search':
        await query.edit_message_text('Please enter your search query:')
        context.user_data['awaiting_search'] = True

    elif query.data == 'view_filters':
        user_id = query.from_user.id
        filters = user_data.get(user_id, {}).get('exclude_tags', [])
        if filters:
            await query.edit_message_text(f'Your current filters: {", ".join(filters)}')
        else:
            await query.edit_message_text('You have no filters set.')

        keyboard = [
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('What would you like to do next?', reply_markup=reply_markup)

    elif query.data == 'more':
        user_id = query.from_user.id

        last_query = user_data[user_id]['last_query']
        last_tags = user_data[user_id].get('exclude_tags', [])  # Используем пустой список, если фильтры не установлены

        images = get_rule34_images(last_query, last_tags)
        await query.edit_message_text('More results:')
        for img in images:
            await query.message.reply_text(img)

        keyboard = [
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('What would you like to do next?', reply_markup=reply_markup)

    elif query.data == 'back':
        await start(update, context)


# Обработка текстовых сообщений для фильтров и поиска
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Установка фильтров
    if context.user_data.get('awaiting_filter'):
        exclude_tags = [tag.strip() for tag in update.message.text.split(',')]
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]['exclude_tags'] = exclude_tags
        save_user_data(user_data)
        context.user_data['awaiting_filter'] = False
        await update.message.reply_text(f'Filters set: {", ".join(exclude_tags)}')

        # Показать кнопки для возврата или нового поиска
        keyboard = [
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('What would you like to do next?', reply_markup=reply_markup)

    # Поиск изображений
    elif context.user_data.get('awaiting_search'):
        query = update.message.text
        exclude_tags = user_data.get(user_id, {}).get('exclude_tags', [])
        images = get_rule34_images(query, exclude_tags)

        # Сохранение последнего запроса пользователя
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]['last_query'] = query
        save_user_data(user_data)

        keyboard = [
            [InlineKeyboardButton("More", callback_data='more')],
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        for img in images:
            await update.message.reply_text(img)

        await update.message.reply_text('Click "More" for additional results or "Back" to return.',
                                        reply_markup=reply_markup)
        context.user_data['awaiting_search'] = False


# Сохранение данных пользователя в файл
def save_user_data(data):
    with open('user_data.json', 'w') as file:
        json.dump(data, file)


# Загрузка данных пользователя из файла с обработкой ошибок
def load_user_data():
    if not os.path.exists('user_data.json'):
        return {}

    try:
        with open('user_data.json', 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}


# Инициализация данных пользователя
user_data = load_user_data()

# Основной код для запуска бота
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()








