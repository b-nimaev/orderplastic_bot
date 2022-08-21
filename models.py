from db import users, saver, ids, future_trades, spot_trades
from db_model import DbWorker
from telebot import types
from lang import lang
from utils import is_float
from datetime import datetime
import xlsxwriter


class User(DbWorker):
    def __init__(self, message):
        if is_float(message):
            self.key = {'chat_id': int(message)}
        else:
            self.key = {'chat_id': message.chat.id}
        self.db = users
        self.default_data = {'chat_id': self.key["chat_id"],
                             'state': 'start',
                             'lang': 'ru',
                             'accounts': []}
        self.find_or_create()


class Saver(DbWorker):
    def __init__(self, message):
        self.key = {'chat_id': message if is_float(message) else message.chat.id}
        self.db = saver
        self.default_data = self.key
        self.find_or_create()


class AccountsMsg:
    @staticmethod
    def main_msg(user):

        msg = {'ru': 'Ваши аккаунты:\n\n',
               'en': 'Your accounts:\n\n'}[user['lang']]
        kb = types.InlineKeyboardMarkup()
        if user["accounts"]:
            for i in ids.find({"id": {"$in": user['accounts']}}):
                msg += f"`{i['email']} - {i['binance_id']}` ({i['id']})\n"
                kb.add(types.InlineKeyboardButton(str(i['binance_id'] if i['binance_id'] else i['email']), callback_data=f"to_msg:account:{i['id']}"))
        else:
            msg += {'ru': '*Не найдено*',
                    'en': '*Not found*'}[user['lang']]
        kb.add(types.InlineKeyboardButton({'ru': 'Добавить аккаунт',
                                           'en': 'Add account'}[user['lang']], callback_data='to_state:add_account'))

        return msg, kb


class AdminIdMsg:
    @staticmethod
    def def_msg(acc_id, delete=False):
        acc = ids.find_one({"id": int(acc_id)})
        try:

            msg = f"ИД: {acc['id']}\n" \
                  f"Email: `{acc['email']}`\n" \
                  f"Binance ID: `{int(acc['binance_id'])}`\n" \
                  f"Рынок: {acc['type']}\n" \
                  f"Аккаунт: {acc['account']}\n\n" \
                  f"ADDRESS1: `{acc['address1']}`\n" \
                  f"ADDRESS2: `{acc['address2']}`\n" \
                  f"Коэфициент: `{acc['coeff']}`"
        except:
            msg = f"`{str(acc)}`"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="Изменить", callback_data=f"to_msg:edit_id:{acc['id']}"))
        if not delete:
            kb.add(types.InlineKeyboardButton(text="Удалить", callback_data=f"to_msg:admin_id_del:{acc['id']}"))
        else:
            kb.add(types.InlineKeyboardButton(text="ДА, УДАЛИТЬ!", callback_data=f"del_id:{acc['id']}"))

        return msg, kb

    def edit_msg(self, acc_id):
        msg = f"Что будем менять у {acc_id}?"
        kb = types.InlineKeyboardMarkup()
        for i in ["email", "binance_id", "type", "account", "address1", "address2", "coeff"]:
            kb.add(types.InlineKeyboardButton(text=i, callback_data=f"to_state:add_id:{i}:1:{acc_id}"))
        kb.add(types.InlineKeyboardButton(text="Назад", callback_data=f"to_msg:show_id:{acc_id}"))
        return msg, kb


def get_stat_by_acc(acc, start_time, end_time):
    if acc['type'] == "spot":
        select_db = spot_trades
    else:
        select_db = future_trades
    pipe = [{"$match": {"e": int(acc['binance_id']) if int(acc['binance_id']) else acc['email'], "a": "BNB",
                        "t": acc['account'], "d": {"$gt": start_time, "$lt": end_time}}},
            {'$group': {'_id': None, 'total': {'$sum': '$v'}}}]
    result = list(select_db.aggregate(pipeline=pipe))
    if result:
        result_bnb = result[0]['total']
    else:
        result_bnb = 0

    pipe = [{"$match": {"e": int(acc['binance_id']) if int(acc['binance_id']) else acc['email'], "a": "USDT",
                        "t": acc['account'], "d": {"$gt": start_time, "$lt": end_time}}},
            {'$group': {'_id': None, 'total': {'$sum': '$v'}}}]
    result = list(select_db.aggregate(pipeline=pipe))
    if result:
        result_usdt = result[0]['total']
    else:
        result_usdt = 0

    total_bnb = result_bnb * acc['coeff']
    total_usdt = result_usdt * acc['coeff']
    return total_bnb, total_usdt


def get_stat_msg(start_time, end_time, user):
    from_string = datetime.fromtimestamp(start_time).strftime("%d.%m.%y %H:%M")
    to_string = datetime.fromtimestamp(end_time).strftime("%d.%m.%y %H:%M")

    msg = {'ru': f"Заработано с *{from_string}* по *{to_string}*:\n\n",
           'en': f"Earned from *{from_string}* to *{to_string}*:\n\n"}[user['lang']]
    global_bnb = global_usdt = 0
    for temp_id in user['accounts']:
        acc = ids.find_one({"id": temp_id})
        total_bnb, total_usdt = get_stat_by_acc(acc, start_time, end_time)

        global_bnb += total_bnb
        global_usdt += total_usdt
        msg += f"{('Spot', 'Futures')[acc['type'] == 'future']} `{int(acc['binance_id']) if int(acc['binance_id']) else acc['email']}`  {total_bnb:.3f} BNB / {total_usdt:.3f} USDT\n"
    msg += {'ru': "\n"
                  f"Всего: {global_bnb:.3f} BNB/{global_usdt:.3f} USDT\n\n"
                  "Кэшбэк от Джуниора: @Juniorcashback\n"
                  "Лучший терминал для трейдинга: @MoonBotSettings",
            'en': "\n"
                  f"Total: {global_bnb:.3f} BNB/{global_usdt:.3f} USDT\n\n"
                  "Cashback from Junior: @Juniorcashback\n"
                  "The best terminal for trading: @MoonBotSettings"}[user['lang']]
    return msg
