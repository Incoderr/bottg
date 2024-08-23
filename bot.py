# 6890541014:AAHft5nEIhyWAbyHjol3Uu8C3fmnEzS-Wp8
#version 0.1.8
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests

TOKEN = "6890541014:AAHft5nEIhyWAbyHjol3Uu8C3fmnEzS-Wp8"

user_data = {}


def get_rule34_images(query, exclude_tags, limit=5):
    exclude_query = " ".join([f"-{tag}" for tag in exclude_tags])
    search_query = f"{query} {exclude_query}"

    url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&tags={search_query}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        if isinstance(data, list) and data:
            return data[:limit]
        else:
            print("Unexpected data format or empty response.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    filters = user_data.get(user_id, {}).get('exclude_tags', [])

    keyboard = [
        [InlineKeyboardButton(f"Filters: {', '.join(filters) if filters else 'None'}", callback_data='set_filter')],
        [InlineKeyboardButton("Search", callback_data='search')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith('result_'):
        index = int(query.data.split('_')[1])
        if 'search_results' in user_data[user_id]:
            result = user_data[user_id]['search_results'][index]
            await query.message.reply_photo(photo=result['file_url'])
        await start(update, context)

    elif query.data == 'set_filter':
        await query.edit_message_text('Please enter the tags you want to exclude, separated by spaces:')
        context.user_data['awaiting_filter'] = True

    elif query.data == 'search':
        await query.edit_message_text('Please enter your search query:')
        context.user_data['awaiting_search'] = True

    elif query.data == 'more':
        last_query = user_data[user_id].get('last_query', '')
        last_tags = user_data[user_id].get('exclude_tags', [])
        start_index = user_data[user_id].get('last_index', 0)
        limit = 5  # Number of additional images to fetch

        images = get_rule34_images(last_query, last_tags, limit=limit)
        user_data[user_id]['last_index'] = start_index + limit
        user_data[user_id]['search_results'] = user_data[user_id].get('search_results', []) + images
        save_user_data(user_data)

        media = [InputMediaPhoto(media=result['file_url']) for result in user_data[user_id]['search_results']]
        if media:
            await query.message.reply_media_group(media=media)
        else:
            await query.message.reply_text('No more images found.')

        keyboard = [
            [InlineKeyboardButton("More", callback_data='more')],
            [InlineKeyboardButton("Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text('More images:', reply_markup=reply_markup)

    elif query.data == 'back':
        await start(update, context)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if context.user_data.get('awaiting_filter'):
        new_tags = [tag.strip() for tag in update.message.text.split()]
        current_tags = user_data.get(user_id, {}).get('exclude_tags', [])
        all_tags = list(set(current_tags + new_tags))  # Объединение и удаление дубликатов
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]['exclude_tags'] = all_tags
        save_user_data(user_data)
        context.user_data['awaiting_filter'] = False
        await update.message.reply_text(f'Filters updated: {", ".join(all_tags)}')

        await start(update, context)

    elif context.user_data.get('awaiting_search'):
        query = update.message.text
        exclude_tags = user_data.get(user_id, {}).get('exclude_tags', [])
        search_results = get_rule34_images(query, exclude_tags)

        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]['last_query'] = query
        user_data[user_id]['search_results'] = search_results
        user_data[user_id]['last_index'] = len(search_results)
        save_user_data(user_data)

        if search_results:
            media = [InputMediaPhoto(media=result['file_url']) for result in search_results]
            await update.message.reply_media_group(media=media)

            keyboard = [
                [InlineKeyboardButton("More", callback_data='more')],
                [InlineKeyboardButton("Back", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text('Select an option:', reply_markup=reply_markup)
        else:
            await update.message.reply_text('No results found.')

        context.user_data['awaiting_search'] = False


def save_user_data(data):
    try:
        with open('user_data.json', 'w') as file:
            json.dump(data, file)
        print("User data saved successfully.")
    except Exception as e:
        print(f"Error saving user data: {e}")


def load_user_data():
    if not os.path.exists('user_data.json'):
        print("No user data file found.")
        return {}

    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
        print("User data loaded successfully.")
        return data
    except json.JSONDecodeError:
        print("Error loading user data: JSONDecodeError")
        return {}
    except Exception as e:
        print(f"Error loading user data: {e}")
        return {}


user_data = load_user_data()

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

























