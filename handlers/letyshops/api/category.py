import json
import os
import urllib.parse

import requests
from os.path import dirname, join

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.letyshops.api.relogin.token_helpers import AUTH_TOKENS_STORAGE
from telegram.ext import BaseFilter, ConversationHandler, MessageHandler, CallbackQueryHandler

from handlers.letyshops.api.relogin.token_helpers import token_updater
from handlers.letyshops.api.shops import get_shop_by_category, get_shop_by_id, render_shop

GET_ALL_CATEGORIES_ROUTE = 'shop-categories'



@token_updater
def get_categories(storage, *args, **kwarg):
    url = urllib.parse.urljoin(os.getenv('API_URL'), GET_ALL_CATEGORIES_ROUTE)
    access_token = storage['access_token']
    return requests.get(url, headers={'Authorization': 'Bearer ' + access_token}, verify=False)


CATEGORIES = get_categories(AUTH_TOKENS_STORAGE)

def build_keyboard(category_list):
    category_list = json.loads(category_list.content.decode("utf-8"))['data']
    category_list = list(filter(lambda category: int(category['parent_id']), category_list))
    category_list = sorted(category_list, key = lambda category: category['name'])
    categories = []
    for (category) in category_list:
        category_keyboard = [InlineKeyboardButton(category['name'], callback_data='show_category.' + category['id'])]
        categories.append(category_keyboard)
    return categories

def show_all(bot, update):
    reply_markup = InlineKeyboardMarkup(build_keyboard(CATEGORIES))
    update.message.reply_text(u"Выберите категорию для поиска", reply_markup=reply_markup)

def choice_category(bot, update):
    selected_category_id = update.callback_query.data.split('.')[1]

    query = update.callback_query

    shops = json.loads(get_shop_by_category(AUTH_TOKENS_STORAGE, category_id=selected_category_id).content.decode("utf-8"))['data']
    prepare_for_render = []

    for shop in shops:
        prepare_for_render.append((shop['name'], shop['id']))

    buttons = []
    for (shop_name, shop_id) in prepare_for_render:
        buttons.append([InlineKeyboardButton(shop_name, callback_data='show_shop_info.' + shop_id)])
    markup = InlineKeyboardMarkup(buttons, resize_keyboard=True)
    bot.send_message(chat_id=query.message.chat_id, text='Результат:', reply_markup=markup)

def show_shop(bot, update):
    selected_shop_id = update.callback_query.data.split('.')[1]
    query = update.callback_query

    shop = get_shop_by_id(AUTH_TOKENS_STORAGE, shop_id = selected_shop_id)
    if (shop.status_code == 200):
        shop_full_data = json.loads(shop.content.decode("utf-8"))['data']
        return bot.send_message(chat_id=query.message.chat_id, text=render_shop(shop_full_data), parse_mode='Markdown')


class CategoryFilter(BaseFilter):
    def filter(self, message):
        return 'Категории' in message.text


category_handler = ConversationHandler(
    entry_points=[MessageHandler(CategoryFilter(), show_all)],
    states={
        'CHOICE_CATEGORY': [CallbackQueryHandler(choice_category)],
        'SHOW_SHOP': [CallbackQueryHandler(show_shop)],
    },
    fallbacks=[],
    allow_reentry=True
)