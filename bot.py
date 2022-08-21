#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import *
from state import StateHandler
from inline import InlineHandler
from telebot import types
from models import User
from flask import Flask
import time
import flask
# from binance_updater import load_future, fut_1, fut_2, fut_3
from timeloop import Timeloop
from datetime import timedelta
from backup_db import db_backuper

import logging
import logging.handlers

my_logger = logging.getLogger('MyLogger')
# handler = logging.handlers.SysLogHandler(address = '/var/log/messages')

app = Flask(__name__)
tl = Timeloop()

my_logger.critical("bot started")

@tl.job(interval=timedelta(minutes=1440))
def db_updater():
    try:
        db_backuper()
    except:
        pass


@bot.message_handler(commands=["start"])
def start_cmd(message):
    my_logger.critical("start")
    if message.chat.id < 0:
        return
    user = User(message)
    user["state"] = "start"
    StateHandler(message)
    
@bot.message_handler(commands=["test"])
def start_cmd(message):
    my_logger.critical("test")
    if message.chat.id < 0:
        return
    bot.send_message(message.chat.id,"Привет ✌️ ")   

@bot.message_handler(content_types=["text", "document"])
def all_text(message):
    if message.chat.id < 0:
        return
    StateHandler(message)

@bot.callback_query_handler(func=lambda call: True)
def callback(reply):
    InlineHandler(reply)


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


tl.start()
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))


if __name__ == "__main__":
    bot.delete_webhook()
    bot.polling()
