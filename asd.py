from binance_f import RequestClient
from binance_f.model.income import Income
from datetime import datetime, timedelta
from db import future_trades



api_key = "hkaW1P16rMnEdRoVfdU8KONnoUktTYBhCSLcQrQ2qPpehUUE4GsUfAnhb5qRK9ZT"
api_secret = "4oZdYjeL728duzf3DpwhOcFADGDQHkJKDWg3kSVB1ofmGmopOunXjah8LLKLfVSg"


class Income2:
    def __init__(self):
        self.symbol = ""
        self.incomeType = ""
        self.income = 0.0
        self.asset = ""
        self.time = 0
        self.info = ""

    @staticmethod
    def json_parse(json_data):
        result = Income()
        result.symbol = json_data.get_string("symbol")
        result.incomeType = json_data.get_string("incomeType")
        result.income = json_data.get_float("income")
        result.asset = json_data.get_string("asset")
        result.time = json_data.get_int("time")
        result.info = json_data.get_string("info")

        return result


Income.info = ""
Income.json_parse = Income2.json_parse

c = RequestClient(api_key=api_key,
                  secret_key=api_secret)

def format_data(d, acc):
    return {
        "e": d.info,
        "d": int(d.time/1000),
        "v": float(d.income),
        "a": d.asset,
        "t": acc
    }
start_time = 1577829600000
while True:
    data = c.get_income_history(incomeType="REFERRAL_KICKBACK", limit=500, startTime=int(start_time))
    to_insert = [format_data(i, 2) for i in data if not future_trades.find_one(format_data(i, 2))]
    if not to_insert:
        break
    start_time = to_insert[-1]["d"]*1000
    future_trades.insert_many(to_insert)
