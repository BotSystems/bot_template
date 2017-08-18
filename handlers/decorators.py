# -*- coding: utf-8 -*-
import os

from botanio import botan

from models import Chanel

BOTAN_TOKEN = os.getenv('BOTAN_TOKEN')


def save_chanel_decorator(fn):
    def wrapper(bot, update):
        chanel = Chanel.get_or_create(chanel_id=update.message.chat.id, defaults={'chanel_id': update.message.chat.id})
        print(chanel)
        return fn(bot, update)

    return wrapper


def botan_decorator(event_name):
    def real_decorator(fn):
        def wrapper(bot, update, *args, **kwargs):
            chat_id = update.message.chat_id
            message = update.message.text
            # try:
            #     botan.track(BOTAN_TOKEN, chat_id, message, event_name)
            # except Exception as e:
            #     print(e)
            #     # TODO: add logger
            #     pass
            return fn(bot, update)

        return wrapper

    return real_decorator
