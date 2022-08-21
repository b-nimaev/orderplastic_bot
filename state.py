#!/usr/bin/python
# -*- coding: utf-8 -*-
from telebot import types
from config import bot, WEBHOOK_URL_BASE, ADMINS
from lang import lang, Languages
from models import User, Saver, AccountsMsg, get_stat_msg, AdminIdMsg
from db import ids, spot_trades, future_trades, users
from utils import *
from datetime import datetime, timedelta
from csv_updater import load_spot, load_ids, delete_collections, export_stats
import calendar
import os
from time import sleep
import zipfile

import logging
import logging.handlers

my_logger = logging.getLogger('MyLogger')
# handler = logging.handlers.SysLogHandler(address = '/var/log/messages')


class State:
    def __init__(self, message, first=False):
        my_logger.critical("init")
        self.first = first
        self.message = message
        self.user = User(message)
        self.lang = self.user['lang']
        self.saver = Saver(message)
        self.chat_id = self.user["chat_id"]
        self.options = None
        self.execute(first)

    def execute(self, first):
        my_logger.critical("execute")
        self.first = first
        self.options = self.user["state"].split(":")[1:]
        getattr(self, self.user["state"].split(":")[0])(*self.options)

    def to_state(self, state, first=True):
        my_logger.critical("to_state")
        self.user["state"] = state
        self.execute(first=first)

    def r_kb(self):
        my_logger.critical("r_kb")
        return types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    def r_btn(self, text):
        my_logger.critical("r_btn")
        if type(text) == str:
            return types.KeyboardButton(text)
        else:
            return [types.KeyboardButton(i) for i in text]

    def i_kb(self):
        my_logger.critical("i_kb")
        return types.InlineKeyboardMarkup()

    def i_btn(self, text, callback_data=None, url=None):
        my_logger.critical("i_btn")
        return types.InlineKeyboardButton(text, url, callback_data)

    def send_msg(self, text=None, chat_id=None, kb=None):
        my_logger.critical("send_msg")
        if not chat_id:
            chat_id = self.chat_id
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="markdown")


class StateHandler(State):
    def start(self):
        my_logger.critical("start")
        self.send_msg(lang[self.lang]["start_msg"])
        self.to_state("set_language")

    def set_language(self):
        my_logger.critical("set_language")
        if self.first:
            msg = "Выберите язык:\n\n" \
                  "Choose language:"
            kb = self.r_kb()
            for name in Languages.keys():
                kb.add(self.r_btn(name))

            self.send_msg(msg, kb=kb)
        elif self.message.text in Languages.keys():
            self.user['lang'] = Languages[self.message.text]
            self.lang = self.user['lang']
            self.user.save()
            self.to_state("menu")
        else:
            self.send_msg(lang[self.lang]['error_msg'])

    def menu(self):
        my_logger.critical("menu")
        if self.first:
            msg = lang[self.lang]["menu_msg"]
            kb = self.r_kb()
            kb.add(*self.r_btn(lang[self.lang]["menu_btns"]))
            if self.user["chat_id"] in ADMINS:
                kb.add(lang[self.lang]["admin_btn"])
            self.send_msg(msg, kb=kb)
        elif self.message.text == lang[self.lang]["menu_btns"][0]:
            msg, kb = AccountsMsg.main_msg(self.user)
            self.send_msg(msg, kb=kb)
        elif self.message.text == lang[self.lang]["menu_btns"][1]:
            self.to_state("stat")
        elif self.message.text == lang[self.lang]["menu_btns"][2]:
            msg = lang[self.lang]['info_msg']
            self.send_msg(msg)
        elif self.user['chat_id'] in ADMINS and self.message.text == lang[self.lang]["admin_btn"]:
            self.to_state("admin")
        else:
            self.send_msg(chat_id=self.chat_id, text=lang[self.lang]["error_msg"])
            self.to_state("menu")

    def add_account(self):
        my_logger.critical("add_account")
        if self.first:
            msg = lang[self.user['lang']]['enter_id_msg']
            kb = self.r_kb()
            kb.add(self.r_btn(lang[self.user['lang']]["back_btn"]))
            self.send_msg(msg, kb=kb)
        elif is_float(self.message.text):
            temp_id = int(self.message.text)
            acc = ids.find_one({"id": temp_id})
            if acc:
                kb = self.i_kb()
                msg = lang[self.user['lang']]["check_email"].format(acc['binance_id'])
                kb.add(self.i_btn(lang[self.user['lang']]["yes"], callback_data=f"confirm:{acc['id']}"),
                       self.i_btn(lang[self.user['lang']]["no"], callback_data="to_state:add_account"))
                self.send_msg(msg, kb=kb)
            else:
                self.send_msg(lang[self.user['lang']]["id_error"])
        elif self.message.text == lang["back_btn"]:
            self.to_state("menu")
        else:
            self.send_msg(lang[self.user['lang']]["id_error"])

    def stat(self):
        my_logger.critical("stat")
        if self.first:
            if not self.user['accounts']:
                self.send_msg(lang[self.user['lang']]["empty_accounts"])
                self.to_state("menu")
                return
            spot_time = spot_trades.find_one({}, sort=[("d", -1)])['d']
            future_time = future_trades.find_one({}, sort=[("d", -1)])['d']
            msg = {
                "ru": f"Спот: обновлено {datetime.fromtimestamp(spot_time).strftime('%d.%m %H:%M')}\n"
                      f"Futures: обновлено {datetime.fromtimestamp(future_time).strftime('%d.%m %H:%M')}\n\n"
                      "Выберите период, за который хотите получить статистику:",
                "en": f"Spot: updated at {datetime.fromtimestamp(spot_time).strftime('%d.%m %H:%M')}\n"
                      f"Futures: updated at {datetime.fromtimestamp(future_time).strftime('%d.%m %H:%M')}\n\n"
                      "Select the period for which you want to get statistics:"
            }[self.user['lang']]
            kb = self.r_kb()
            kb.add(*self.r_btn(lang[self.user['lang']]["period_btns"]))
            kb.add(self.r_btn(lang[self.user['lang']]["back_btn"]))
            self.send_msg(msg, kb=kb)
        elif self.message.text in lang[self.user['lang']]["period_btns"]:
            start_time = end_time = None
            if self.message.text == lang[self.user['lang']]["period_btns"][0]:
                start_time, end_time = get_current_period()
            elif self.message.text == lang[self.user['lang']]["period_btns"][1]:
                start_time, end_time = get_past_period()
            elif self.message.text == lang[self.user['lang']]["period_btns"][2]:
                self.to_state("enter_stat_dates")
                return
            msg = get_stat_msg(start_time, end_time, self.user)
            self.send_msg(msg)
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("menu")
        else:
            self.send_msg(lang[self.user['lang']]["error_msg"])

    def enter_stat_dates(self):
        my_logger.critical("enter_stat_dates")
        kb = self.r_kb()
        kb.add(self.r_btn(lang[self.user['lang']]["back_btn"]))
        if self.first:
            self.saver["from"] = 0
            msg = {
                "ru": f"Введите дату дату *ОТ* в формате _12.12.2020_ (время считается с 00:00):",
                "en": f"Enter date date *FROM* in the format _12.12.2020_ (time is counted from 00:00):"
            }[self.user['lang']]
            self.send_msg(msg, kb=kb)
        elif is_date(self.message.text) and not self.saver["from"]:
            self.saver["from"] = datetime.strptime(self.message.text, "%d.%m.%Y").timestamp()
            msg = {
                "ru": f"Введите дату дату *ДО* в формате _13.12.2020_ (время считается до 23:59):",
                "en": f"Enter the date date *TO* in the format _13.12.2020_ (time counts until 23:59):"
            }[self.user['lang']]
            self.send_msg(msg, kb=kb)
        elif is_date(self.message.text):
            start_time = self.saver["from"]
            end_time = datetime.strptime(self.message.text, "%d.%m.%Y") + timedelta(hours=23, minutes=59, seconds=59)
            end_time = end_time.timestamp()
            msg = get_stat_msg(start_time, end_time, self.user)
            self.send_msg(msg)
            self.to_state("stat")
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("stat")
        else:
            self.send_msg(lang[self.user['lang']]['error_msg'])

    def admin(self):
        # my_logger.critical("admin " + self.message.text)
        if self.first:
            kb = self.r_kb()
            kb.add(*self.r_btn(lang[self.user['lang']]["admin_btns"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg("Админка", kb=kb)
        elif self.message.text == lang[self.user['lang']]["admin_btns"][0]:  # обновить спот и фьючерсы
            self.to_state("update_spot")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][1]:  # Добавить ИД
            self.to_state("add_id:email")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][2]:  # статистика
            self.to_state("admin_stat")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][3]:  # Найти ИД
            self.to_state("find_id")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][4]:  # Рассылка
            self.to_state("broadcast")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][5]:  # Удалить споты и фьючерсы
            self.to_state("delete_data")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][6]:  # Выгрузить картотеку
            self.to_state("get_statistics")
        elif self.message.text == lang[self.user['lang']]["admin_btns"][7]:  # Загрузить картотеку
            self.to_state("update_ids")
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("menu")
        else:
            self.to_state("admin")

    def get_statistics(self):
        my_logger.critical("get_statistics")
        if self.first:
            kb = self.r_kb()
            kb.add(self.r_btn(lang[self.user['lang']]['back_btn']))
            try:
                export_stats(str(self.chat_id)+".csv")
                try:
                    with open(str(self.chat_id)+".csv", 'rb') as file:
                        bot.send_document(self.chat_id, file)
                    self.send_msg("Держи статистику", kb=kb)
                except Exception as e:
                    self.send_msg("Very large file")
            except Exception as e:
                my_logger.critical(e)
                self.send_msg("Коллекция пуста или был загружен файл без заголовков!")
            self.to_state("admin")
    def delete_data(self):
        my_logger.critical("delete_data")
        if self.first:
            kb = self.r_kb()
            kb.add(self.r_btn(lang[self.user['lang']]['back_btn']))
            self.send_msg("Введите дату *ОТ* в формате _12.12.2020_ (время считается с 00:00):", kb=kb)

        elif self.message.text == lang[self.user['lang']]['back_btn']:
            self.to_state("admin")

        elif is_date(self.message.text):
            self.send_msg("Начинаем чистить данные...")
            deleted_spots, deleted_future =  delete_collections(self.message.text)
            self.send_msg("Удалили {0} спотов и {1} фьючеров".format(str(deleted_spots), str(deleted_future)))
            self.to_state("admin")
        else:
            self.send_msg("Неверный формат даты")


    #  kb = self.r_kb()
    #     kb.add(self.r_btn(lang[self.user['lang']]["back_btn"]))
    #     if self.first:
    #         self.saver["start_time"] = 0
    #         self.saver["end_time"] = 0
    #         self.send_msg("Введите дату дату *ОТ* в формате _12.12.2020_ (время считается с 00:00):", kb=kb)
    #     elif is_date(self.message.text) and not self.saver["start_time"]:
    #         self.saver["start_time"] = int(datetime.strptime(self.message.text, "%d.%m.%Y").timestamp())
    #         self.send_msg("Введите дату дату *ДО* в формате _13.12.2020_ (время считается до 23:59):", kb=kb)
    #     elif is_date(self.message.text) and not self.saver["end_time"]:
    #         self.saver["end_time"] = int((datetime.strptime(self.message.text, "%d.%m.%Y") + timedelta(hours=23,
    #                                                                                                    minutes=59,
    #                                                                                                    seconds=59)).timestamp())
    #         self.to_state("show_admin_stat")
    #     elif self.message.text == lang[self.user['lang']]["back_btn"]:
    #         self.to_state("admin")
    #     else:
    #         self.send_msg("Неверный формат даты")

    def broadcast(self):
        my_logger.critical("broadcast")
        if self.first:
            kb = self.r_kb()
            kb.add(self.r_btn(lang[self.user['lang']]['back_btn']))
            self.send_msg("Введите текст рассылки:", kb=kb)
        elif self.message.text == lang[self.user['lang']]['back_btn']:
            self.to_state("admin")
        elif self.message.text:
            self.to_state("admin")
            self.send_msg("Рассылка начата...")
            for user in users.find():
                try:
                    bot.send_message(user['chat_id'], self.message.text, parse_mode="html")
                except Exception as e:
                    print(f"Error on user: {user['chat_id']}")
                sleep(.05)
            self.send_msg("Рассылка закончена!")

    def find_id(self):
        my_logger.critical("find_id")
        if self.first:
            kb = self.r_kb()
            kb.add(self.r_btn(lang[self.user['lang']]['back_btn']))
            self.send_msg("Введите ИД:", kb=kb)
        elif self.message.text == lang[self.user['lang']]['back_btn']:
            self.to_state("admin")
        elif self.message.text.isdigit() and ids.find_one({"id": int(self.message.text)}):
            msg, kb = AdminIdMsg().def_msg(int(self.message.text))
            self.send_msg(msg, kb=kb)
        else:
            self.send_msg("Не могу найти такого")

    def admin_stat(self):
        my_logger.critical("admin_stat")
        kb = self.r_kb()
        if self.first:
            self.saver["start_time"] = None
            self.saver["end_time"] = None
            self.saver["type"] = None
            self.saver["acc"] = None
            self.saver["coeff"] = 0.75

            msg = "Для какого аккаунта"
            kb.add(*self.r_btn(lang[self.user['lang']]['acc_nums']))
            kb.add(self.r_btn(lang[self.user['lang']]["acc_nums_all"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(msg, kb=kb)
        elif not self.saver["acc"] and self.message.text in lang[self.user['lang']]["acc_nums"]:
            self.saver["acc"] = lang[self.user['lang']]['acc_nums'].index(self.message.text) + 1

            msg = "Какой рынок"
            kb.add(*self.r_btn(lang[self.user['lang']]["acc_types"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(msg, kb=kb)
        elif not self.saver['acc'] and self.message.text == lang[self.user['lang']]['acc_nums_all']:
            self.saver["acc"] = "all"

            self.saver["type"] = "all"
            msg = "Период"
            kb.add(*self.r_btn(lang[self.user['lang']]["period_btns"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(msg, kb=kb)
        elif not self.saver["type"] and self.message.text in lang[self.user['lang']]["acc_types"]:
            self.saver["type"] = "spot" if self.message.text == lang[self.user['lang']]["acc_types"][0] else "future"

            msg = "Период"
            kb.add(*self.r_btn(lang[self.user['lang']]["period_btns"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(msg, kb=kb)
        elif (not self.saver["start_time"] or not self.saver["end_time"]) and self.message.text in lang[self.user['lang']]["period_btns"]:
            if self.message.text == lang[self.user['lang']]["period_btns"][0]:
                start, end = get_current_period()
                self.saver["start_time"] = start
                self.saver["end_time"] = end
                self.to_state("show_admin_stat")
            elif self.message.text == lang[self.user['lang']]["period_btns"][1]:
                start, end = get_past_period()
                self.saver["start_time"] = start
                self.saver["end_time"] = end
                self.to_state("show_admin_stat")
            elif self.message.text == lang[self.user['lang']]["period_btns"][2]:
                self.to_state("enter_admin_dates")
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("admin")
        else:
            self.send_msg(lang["error_msg"])

    def enter_admin_dates(self):
        my_logger.critical("enter_admin_dates")
        kb = self.r_kb()
        kb.add(self.r_btn(lang[self.user['lang']]["back_btn"]))
        if self.first:
            self.saver["start_time"] = 0
            self.saver["end_time"] = 0
            self.send_msg("Введите дату дату *ОТ* в формате _12.12.2020_ (время считается с 00:00):", kb=kb)
        elif is_date(self.message.text) and not self.saver["start_time"]:
            self.saver["start_time"] = int(datetime.strptime(self.message.text, "%d.%m.%Y").timestamp())
            self.send_msg("Введите дату дату *ДО* в формате _13.12.2020_ (время считается до 23:59):", kb=kb)
        elif is_date(self.message.text) and not self.saver["end_time"]:
            self.saver["end_time"] = int((datetime.strptime(self.message.text, "%d.%m.%Y") + timedelta(hours=23,
                                                                                                       minutes=59,
                                                                                                       seconds=59)).timestamp())
            self.to_state("show_admin_stat")
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("admin")
        else:
            self.send_msg("Неверный формат даты")

    def show_admin_stat(self):
        my_logger.critical("show_admin_stat")
        coins = ["BNB", "USDT"]
        global_db_bnb = global_db_usdt = 0
        if self.saver["type"] == "spot":
            databases = [spot_trades]
        elif self.saver["type"] == "future":
            databases = [future_trades]
        else:
            databases = [spot_trades, future_trades]

        for i in coins:
            for select_db in databases:
                if self.saver["acc"] == "all":
                    account = {"$in": [1, 2]}
                else:
                    account = self.saver["acc"]

                pipe = [{"$match": {"a": i, "t": account,
                                    "d": {"$gt": self.saver["start_time"], "$lt": self.saver["end_time"]}}},
                        {'$group': {'_id': None, 'total': {'$sum': '$v'}}}]
                result = list(select_db.aggregate(pipeline=pipe))
                print(pipe)
                try:
                    if i == coins[0]:
                        global_db_bnb += result[0]['total']
                    else:
                        global_db_usdt += result[0]['total']
                except:
                    pass
        if self.saver["type"] == "spot" and self.saver["acc"] == 1:
            total_bnb = global_db_bnb * 30 / 41
            total_usdt = global_db_usdt * 30 / 41
        else:
            total_bnb = global_db_bnb * 0.75
            total_usdt = global_db_usdt * 0.75

        from_string = datetime.fromtimestamp(self.saver["start_time"]).strftime("%d.%m.%y %H:%M")
        print(from_string)

        to_string = datetime.fromtimestamp(self.saver["end_time"]).strftime("%d.%m.%y %H:%M")
        print(to_string)
        
        msg = f"Всего заработано с *{from_string}* по *{to_string}* на {self.saver['type']} {self.saver['acc']} аккаунта:\n\n" \
              f"*{global_db_bnb:.3f} BNB/{global_db_usdt:.3f} USDT*\n\n" \
              f"К выплате *{total_bnb:.3f} BNB/{total_usdt:.3f} USDT*\n\n"
        kb = None
        if self.saver['acc'] != "all" and self.saver['type'] != "all":
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton(text="Выгрузить статистику", callback_data=f"s:{self.saver['start_time']}:"
                                                                                      f"{self.saver['end_time']}:"
                                                                                      f"{self.saver['acc']}:"
                                                                                      f"{self.saver['type']}"))
        self.send_msg(msg, kb=kb)
        self.to_state("admin")

    def update_spot(self):
        my_logger.critical("update_spot")
        kb = self.r_kb()
        if self.first:
            self.saver["acc_num"] = 0
            kb.add(*self.r_btn(lang[self.user['lang']]["acc_nums"]))
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg("Для какого аккаунта обновляем?", kb=kb)
        elif not self.saver["acc_num"] and self.message.text in lang[self.user['lang']]["acc_nums"]:
            self.saver["acc_num"] = lang[self.user['lang']]['acc_nums'].index(self.message.text) + 1
            try:
                last_update_time = spot_trades.find_one({"t": self.saver["acc_num"]}, sort=[("d", -1)])["d"]
                last_update = datetime.fromtimestamp(last_update_time).strftime("%d.%m.%Y %H:%M:%S")
            except:
                last_update = "Никогда"
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(
                f"Жду .zip файл (до 20мб) для {self.saver['acc_num']} аккаунта (последнее обновление {last_update}):",
                kb=kb)
        elif self.saver["acc_num"] and self.message.document:
            doc = self.message.document
            if doc.file_name.split(".")[-1] != "zip":
                self.send_msg("Это не похоже на zip файл. Попробуйте еще раз")
                return
            try:
                os.remove(f"{self.saver['acc_num']}.zip")
            except:
                pass
            try:
                file_info = bot.get_file(doc.file_id)
            except:
                self.send_msg("Файл слишком большой. Ограничение 20мб")
                return
            self.send_msg("Скачиваю файл...")
            downloaded_file = bot.download_file(file_info.file_path)

            with open(f"{self.saver['acc_num']}.zip", 'wb') as new_file:
                new_file.write(downloaded_file)

            try:
                with zipfile.ZipFile(f"{self.saver['acc_num']}.zip" , 'r') as zipObj:
                    listOfFileNames = zipObj.namelist()
                    for fileName in listOfFileNames:
                        if fileName.endswith('.csv'):
                            try:
                                os.remove(fileName)
                                os.remove(str(self.saver["acc_num"])+".csv")
                            except:
                                pass

                            t = zipObj.extract(fileName)
                            filename = t.split('\\')[-1]
                            os.rename(filename,str(self.saver["acc_num"])+".csv")
            except Exception as e:
                pass

            self.send_msg("Загружаю в БД...")
            futures, spots = load_spot(self.saver["acc_num"])

            try:
                os.remove(str(self.saver["acc_num"])+".csv")
                os.remove(str(self.saver["acc_num"])+".zip")
            except:
                pass

            kb.add(*self.r_btn(lang[self.user['lang']]["admin_btns"]))
            self.send_msg(f"Готово! Загружено фьючерсов {str(futures)}. Загружено спотов {str(spots)}", kb=kb)
            self.to_state("admin")
            
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("admin")
        else:
            self.to_state("update_spot")
            
    def update_ids(self):
        my_logger.critical("update_ids")
        kb = self.r_kb()
        if self.first:
            kb.add(lang[self.user['lang']]["back_btn"])
            self.send_msg(f"Жду .csv файл:", kb=kb)
        elif self.message.document:
            doc = self.message.document
            if doc.file_name.split(".")[-1] != "csv":
                self.send_msg("Это не похоже на csv файл. Попробуйте еще раз")
                return
            
            try:
                os.remove(doc.file_name)
            except:
                pass
            
            try:
                file_info = bot.get_file(doc.file_id)
            except:
                self.send_msg("Файл слишком большой. Ограничение 20мб")
                return
            
            self.send_msg("Скачиваю файл...")
            downloaded_file = bot.download_file(file_info.file_path)

            with open(doc.file_name, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            my_logger.critical(doc.file_name)

            self.send_msg("Загружаю в БД...")
            try:
                load_ids(doc.file_name)
                os.remove(doc.file_name)
                kb.add(*self.r_btn(lang[self.user['lang']]["admin_btns"]))
                self.send_msg(f"Готово!", kb=kb)
            except:
                self.send_msg(f"Убедитесь, что файл нужного формата!")

            self.to_state("admin")
            
        elif self.message.text == lang[self.user['lang']]["back_btn"]:
            self.to_state("admin")
        else:
            self.to_state("update_ids")

    def add_id(self, step, edit=False, acc_id=None):
        my_logger.critical("add_id")
        steps = ["email", "binance_id", "type", "account", "address1", "address2", "coeff"]
        next_state = steps[steps.index(step) + 1] if step != steps[-1] else 'admin'
        success = False

        if not self.first and self.message:
            if self.message.text == lang[self.user['lang']]["back_btn"]:
                self.to_state(f"add_id:{steps[max(0, steps.index(step) - 1)]}")
                return
            elif self.message.text == lang[self.user['lang']]["cancel_btn"]:
                self.to_state("admin")
                return

        kb = self.r_kb()
        kb.add(*self.r_btn([lang[self.user['lang']]['back_btn'], lang[self.user['lang']]['cancel_btn'],
                            lang[self.user['lang']]['skip_btn']]))

        if self.first and step == "email":
            self.send_msg("Отправьте Email:", kb=kb)
        elif step == "email" and "@" in str(self.message.text):
            self.saver['email'] = self.message.text
            success = True
        elif self.message.text == lang[self.user['lang']]['skip_btn']:
            self.saver['email'] = None
            success = True

        elif self.first and step == "binance_id":
            self.send_msg("Отправьте Binance ID:", kb=kb)
        elif step == "binance_id" and str(self.message.text).isdigit():
            self.saver['binance_id'] = int(self.message.text)
            success = True
        elif self.message.text == lang[self.user['lang']]['skip_btn']:
            self.saver['binance_id'] = None
            success = True

        elif self.first and step == "type":
            kb.add(*self.r_btn(lang[self.user['lang']]["acc_types"]))
            self.send_msg("Выберите тип аккаунта:", kb=kb)
        elif step == "type" and self.message.text:
            self.saver['type'] = "spot" if self.message.text == lang[self.user['lang']]["acc_types"][0] else "future"
            success = True

        elif self.first and step == "account":
            kb.add(*self.r_btn(lang[self.user['lang']]["acc_nums"]))
            self.send_msg("Для какого аккаунта:", kb=kb)
        elif step == "account" and self.message.text in lang[self.user['lang']]['acc_nums']:
            self.saver['account'] = lang[self.user['lang']]['acc_nums'].index(self.message.text) + 1
            success = True

        elif self.first and step == "address1":
            self.send_msg("Введите ADDRESS1 кошелек:", kb=kb)
        elif step == "address1" and self.message.text:
            self.saver['address1'] = self.message.text
            success = True

        elif self.first and step == "address2":
            self.send_msg("Введите ADDRESS2:", kb=kb)
        elif step == "address2" and self.message.text:
            self.saver['address2'] = self.message.text
            success = True
        elif self.first and step == "coeff":
            self.send_msg("Введите коэфициент:", kb=kb)
        elif step == "coeff" and is_float(self.message.text):
            self.saver['coeff'] = float(self.message.text)
            success = True
        else:
            self.send_msg(lang[self.user['lang']]["error_msg"])

        if not self.first and success:
            if not edit:
                if next_state == 'admin':
                    data = {"id": int(gen_id())}
                    for i in steps:
                        try:
                            data[i] = self.saver[i]
                        except:
                            pass
                    ids.insert_one(data)
                    msg, kb = AdminIdMsg().def_msg(data['id'])
                    self.send_msg(msg, kb=kb)
                    self.to_state("admin")
                else:
                    self.to_state("add_id:" + next_state)
            else:
                acc = ids.find_one({"id": int(acc_id)})
                acc[step] = self.saver[step]
                ids.save(acc)
                msg, kb = AdminIdMsg().def_msg(acc_id)
                self.send_msg(msg, kb=kb)
                self.to_state("admin")
