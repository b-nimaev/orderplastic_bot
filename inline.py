from state import StateHandler
from models import User, AccountsMsg, get_stat_by_acc, AdminIdMsg
from config import bot, WEBHOOK_URL_BASE
from lang import lang
from telebot import types
from db import ids, users
import xlsxwriter
from config import binance_cli
import time


class InlineHandler:
    def __init__(self, reply):
        self.reply = reply
        self.message = reply.message
        if self.message:
            self.user = User(self.message)
        else:
            self.user = User(self.reply.from_user.id)
        self.text = None
        self.show_alert = False
        cmd = reply.data.split(":")[0]
        self.other = reply.data.split(":")[1:]
        getattr(self, cmd)(*self.other)
        bot.answer_callback_query(callback_query_id=self.reply.id, text=self.text, show_alert=self.show_alert)

    def to_state(self, *state):
        try:
            bot.delete_message(
                chat_id=self.user["chat_id"],
                message_id=self.message.message_id
            )
        except:
            pass
        self.user["state"] = ":".join([str(i) for i in state])
        StateHandler(self.user["chat_id"], first=True)

    def edit(self, new_msg, new_kb=None):
        if self.message:
            bot.edit_message_text(chat_id=self.message.chat.id,
                                  message_id=self.message.message_id,
                                  text=new_msg,
                                  reply_markup=new_kb,
                                  parse_mode="markdown")
        else:
            bot.edit_message_text(chat_id=None,
                                  inline_message_id=self.reply.inline_message_id,
                                  text=new_msg,
                                  reply_markup=new_kb,
                                  parse_mode="markdown")

    def show_msg(self, msg_type):
        if msg_type == "card":
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="Как получить?", url="http://slither.io/"))
            bot.send_message(self.user["chat_id"], text=lang["card_msg"], reply_markup=kb)

    def to_msg(self, msg_type, param=None):
        kb = types.InlineKeyboardMarkup()
        msg = None
        if msg_type == "account":
            acc = ids.find_one({"id": int(param)})
            msg = f"Email: `{acc['email']}`\n" \
                  f"Binance ID: `{int(acc['binance_id'])}`\n" \
                  f"Type: {'Spot' if acc['type'] == 'spot' else 'Futures'}"
            kb.add(types.InlineKeyboardButton(text=lang[self.user['lang']]['del_btn'],
                                              callback_data=f"del_acc:{acc['id']}"))
            kb.add(types.InlineKeyboardButton(text=lang[self.user['lang']]['back_btn'],
                                              callback_data=f"to_msg:all_accounts"))
        elif msg_type == "all_accounts":
            msg, kb = AccountsMsg.main_msg(self.user)
        elif msg_type == "admin_id_del":
            self.text = {
                "ru": "Вы уверены что хотите удалить этот ИД?",
                "en": "Are you sure you want to delete this ID?"
            }[self.user['lang']]
            self.show_alert = True
            msg, kb = AdminIdMsg().def_msg(param, delete=True)
        elif msg_type == "show_id":
            msg, kb = AdminIdMsg().def_msg(param)
        elif msg_type == "edit_id":
            msg, kb = AdminIdMsg().edit_msg(param)


        self.edit(msg, kb)

    def del_id(self, acc_id):
        ids.delete_one({"id": int(acc_id)})
        for user in users.find({"accounts": int(acc_id)}):
            user['accounts'].remove(int(acc_id))
            users.save(user)
        self.edit("Deleted.")

    def del_acc(self, temp_id):
        temp_id = int(temp_id)
        acc = ids.find_one({"id": temp_id})
        self.user['accounts'].remove(temp_id)
        self.user.save()
        msg = {"ru": f"`{acc['email']}` удален из вашего списка.",
               "en": f"`{acc['email']}` deleted."}[self.user['lang']]
        bot.send_message(self.user['chat_id'], msg, parse_mode='markdown')
        self.to_state("menu")

    def confirm(self, temp_id):
        temp_id = int(temp_id)
        acc = ids.find_one({"id": temp_id})
        self.user['accounts'].append(temp_id)
        self.user.save()
        msg = {"ru": f"`{acc['email']}` добавлен для отслеживания!",
               "en": f"`{acc['email']}` added!"}[self.user['lang']]
        bot.send_message(self.user['chat_id'], msg, parse_mode='markdown')
        self.to_state('menu')

    def s(self, start_time, end_time, acc_num, acc_type):
        bot.send_message(self.user['chat_id'], "Начинаю сбор статистики, это может занять время...")
        workbook = xlsxwriter.Workbook('stat.xlsx')
        bold = workbook.add_format({'bold': True})
        number_format = workbook.add_format({'num_format': '0.000'})

        worksheet = workbook.add_worksheet()
        worksheet.write_string('A1', 'ID', bold)
        worksheet.write_string('B1', 'E-Mail', bold)
        worksheet.write_string('C1', 'ADDRESS1', bold)
        worksheet.write_string('D1', 'ADDRESS2', bold)
        worksheet.write_string('E1', 'К выплате XLM', bold)
        worksheet.write_string('F1', 'К выплате BTC', bold)
        worksheet.write_string('G1', 'К выплате USDT', bold)
        worksheet.write_string('H1', 'BNB на XLM', bold)
        worksheet.write_string('I1', 'USDT на XLM', bold)
        worksheet.write_string('J1', 'BNB на BTC', bold)
        worksheet.write_string('K1', 'USDT на BTC', bold)
        worksheet.write_string('L1', 'BNB на USDT', bold)
        worksheet.write_string('M1', 'USDT на USDT', bold)

        worksheet.write_string('N1', 'Коэфициент', bold)

        worksheet.write_string('P1', 'Курс:', bold)
        worksheet.write_string('Q1', 'Binance ID:', bold)

        worksheet.write_string('O2', 'XLM/BNB', bold)
        worksheet.write_number('P2', float(binance_cli.get_avg_price(symbol='XLMBNB')['price']), bold)
        worksheet.write_string('O3', 'XLM/USDT', bold)
        worksheet.write_number('P3', float(binance_cli.get_avg_price(symbol='XLMUSDT')['price']), bold)
        worksheet.write_string('O4', 'BNB/BTC', bold)
        worksheet.write_number('P4', float(binance_cli.get_avg_price(symbol='BNBBTC')['price']), bold)
        worksheet.write_string('O5', 'BTC/USDT', bold)
        worksheet.write_number('P5', float(binance_cli.get_avg_price(symbol='BTCUSDT')['price']), bold)
        worksheet.write_string('O6', 'BNB/USDT', bold)
        worksheet.write_number('P6', round(float(binance_cli.get_avg_price(symbol='BNBUSDT')['price'])), bold)

        row = 1
        col = 0

        # Iterate over the data and write it out row by row.
        accounts = list(ids.find({"account": int(acc_num), "type": acc_type}))
        for acc in accounts:
            try:
                total_bnb, total_usdt = get_stat_by_acc(acc, float(start_time), float(end_time))
                worksheet.write_string(row, col, str(acc['id']))
                worksheet.write_string(row, col + 1, acc['email'])
                worksheet.write_string(row, col + 2, acc['address1'])
                worksheet.write_string(row, col + 3, acc['address2'])
                if str(acc['address2']).lower() == "btc":
                    worksheet.write_formula(row, col + 5, f"=ROUND((J{row+1}*P4)+(K{row+1}/P5), 8)")
                    worksheet.write(row, col + 9, f"=ROUND({total_bnb}, 3)")
                    worksheet.write(row, col + 10, f"=ROUND({total_usdt}, 3)")

                elif str(acc['address2']).lower() == "usdt":
                    worksheet.write_formula(row, col + 6, f"=ROUND((L{row + 1}*P6)+M{row + 1}, 2)")
                    worksheet.write(row, col + 11, f"=ROUND({total_bnb}, 3)")
                    worksheet.write(row, col + 12, f"=ROUND({total_usdt}, 3)")
                else:
                    worksheet.write(row, col + 4, f"=ROUND((H{row+1}/P2)+(I{row+1}/P3), 0)")
                    worksheet.write_formula(row, col + 7, f"=ROUND({total_bnb}, 3)")
                    worksheet.write(row, col + 8, f"=ROUND({total_usdt}, 3)")
                worksheet.write(row, col + 13, f"{acc['coeff']:.2f}")

                worksheet.write(row, col + 16, f"{int(acc['binance_id'])}")
                print(row+ "из "+str(len(accounts)))
            except:
                print(acc['id'])
            row += 1
        row += 1
        worksheet.write_string(f'A{row}', 'ИТОГО:', bold)
        for i in ["E", "F", "G", "H", "I", "J", "K", "L", "M"]:
            worksheet.write_formula(f'{i}{row}', f"=SUM({i}2:{i}{row-1})", bold)
        workbook.close()
        bot.send_document(self.user["chat_id"], open('stat.xlsx', 'rb'))

    def skip(self):
        pass
