
import pandas
from datetime import timedelta, datetime
import time
from db import spot_trades,future_trades
import zipfile
import os
from utils import get_current_period

filename = ''
with zipfile.ZipFile('1.zip', 'r') as zipObj:
   listOfFileNames = zipObj.namelist()
   for fileName in listOfFileNames:
       if fileName.endswith('.csv'):
           t = zipObj.extract(fileName)
           filename = t.split('\\')[-1]


def format_data(d, t):
    data = {"e": int(d[0]),
            "d": datetime.strptime(d[1], "%Y-%m-%d %H:%M:%S").timestamp(),
            "v": float(d[2]),
            "a": d[3],
            "t": t
            }
    return data

df = pandas.read_table(filename, sep=",", skiprows=0)

start, end = get_current_period()

pipe = [{"$match": {"a": "BNB", "t": 1,
    "d": {"$gt": start, "$lt": end}}},
    {'$group': {'_id': None, 'total': {'$sum': '$v'}}}]

result = list(spot_trades.aggregate(pipeline=pipe))


futures = df.loc[df['type'] == 'futures']
del futures['parent_id']
del futures['type']
del futures['reg_time']
del futures['referral_code']


spots = df.loc[df['type'] != 'futures']
del spots['parent_id']
del spots['type']
del spots['reg_time']
del spots['referral_code']

spots = [format_data(i, 1) for i in spots.values]
spot_trades.insert_many(spots)

futures = [format_data(i, 1) for i in futures.values]
future_trades.insert_many(futures)

try:
    os.remove(filename)
except Exception as e:
    print(str(e))

