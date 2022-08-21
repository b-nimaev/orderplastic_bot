# from binance_f import RequestClient
# from binance_f.model.income import Income
# from datetime import datetime, timedelta
# from db import future_trades
# import time


# fut_1_keys = ("7Mcw0fjBXHPVJmbrQkGt1mQtWPVp5wUtglc0QjuE4Px6OPASRRRqiijLz1R3Xv34",
#               "RH8K4u72gFJyNkiOGO4moOj3SSXSupXkNuNOgzTm6OHJZmnxIvRhUMQiORxHD1zJ")
# fut_2_keys = ("hkaW1P16rMnEdRoVfdU8KONnoUktTYBhCSLcQrQ2qPpehUUE4GsUfAnhb5qRK9ZT",
#               "4oZdYjeL728duzf3DpwhOcFADGDQHkJKDWg3kSVB1ofmGmopOunXjah8LLKLfVSg")
# fut_3_keys = ("7BMnf7Clz9zxiQUZrZRENBHCQhBOeVAz3lY1YZZbhCdplv3FxAW94eulkSMpHF8C",
#               "Z50q2wgblZK5YE1EW831EDdAONGYzi62Q1V1q8E7pbL5qzQ2vP2xfYJrLwX6Xewn")


# def json_parse(json_data):
#     result = Income()
#     result.symbol = json_data.get_string("symbol")
#     result.incomeType = json_data.get_string("incomeType")
#     result.income = json_data.get_float("income")
#     result.asset = json_data.get_string("asset")
#     result.time = json_data.get_int("time")
#     result.info = json_data.get_string("info")

#     return result


# Income.info = ""
# Income.json_parse = json_parse

# fut_1 = RequestClient(api_key=fut_1_keys[0],
#                       secret_key=fut_1_keys[1])

# fut_2 = RequestClient(api_key=fut_2_keys[0],
#                       secret_key=fut_2_keys[1])

# fut_3 = RequestClient(api_key=fut_3_keys[0],
#                       secret_key=fut_3_keys[1])

# def format_data(d, acc):
#     return {
#         "e": d.info,
#         "d": int(d.time/1000),
#         "v": float(d.income),
#         "a": d.asset,
#         "t": acc
#     }


# def load_future(acc, acc_num):
#     try:
#         start_time = future_trades.find_one({"t": acc_num}, sort=[("d", -1)])["d"]
#     except:
#         start_time = datetime.utcnow().timestamp()-60*60*24*7

#     #reload past 3 days
#     start_time = start_time - 60*60*24*3 #3 days in seconds
#     #del past 3 days
#     future_trades.delete_many({"t": acc_num, "d": {"$gt": start_time}})

#     while True:
#         data = acc.get_income_history(incomeType="REFERRAL_KICKBACK", limit=700,
#                                       startTime=(start_time+1)*1000)
#         to_insert = [format_data(i, acc_num) for i in data]
#         if not to_insert:
#             break

#         start_time = to_insert[-1]["d"]
#         future_trades.insert_many(to_insert)
#         time.sleep(0.1)



