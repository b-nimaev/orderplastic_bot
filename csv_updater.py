import pandas
import json
from datetime import datetime
from db import spot_trades, future_trades, ids
from utils import *
import os

def format_data(d, t):
    data = {"e": int(d[0]),
            "d": datetime.strptime(d[1], "%Y-%m-%d %H:%M:%S").timestamp(),
            "v": float(d[2]),
            "a": d[3],
            "t": t
            }
    return data
import numpy as np
def export_stats(output_file):
    today = datetime.today()
    today = today.strftime("%m-%d-%Y")
    # make an API call to the MongoDB server
    mongo_docs = ids.find()

    df = pandas.DataFrame(mongo_docs)
    df = df.astype({"account": "Int64"})
    df = df.astype({"binance_id": "Int64"})

    df.pop("_id")

    df.to_csv(output_file, ",", index=False) # CSV delimited by commas

def delete_collections(t):

    today = datetime.strptime(datetime.now().strftime("%d.%m.%Y"),"%d.%m.%Y").timestamp()
    print("today "+str(today))

    yesterday = datetime.strptime(t, "%d.%m.%Y").timestamp()
    print("yesterday "+str(yesterday))

    deleted_spots = spot_trades.delete_many({"d":{"$gt":yesterday}})
    print("deleted spots count "+str(deleted_spots.deleted_count))

    deleted_future = future_trades.delete_many({"d":{"$gt":yesterday}})
    print("deleted future count "+str(deleted_future.deleted_count))
    return deleted_spots.deleted_count, deleted_future.deleted_count

    

def load_spot(t):

    df = pandas.read_table(f"./{t}.csv", sep=",", skiprows=0)

    start, end = get_current_period()

    pipe = [{"$match": {"a": "BNB", "t": t,
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

    spots = [format_data(i, t) for i in spots.values]
    spot_trades.insert_many(spots)

    futures = [format_data(i, t) for i in futures.values]
    future_trades.insert_many(futures)
    

    return len(futures),len(spots)
    
def load_ids(filepath):
    cdir = os.path.dirname(__file__)
    file_res = os.path.join(cdir, filepath)
    data = pandas.read_csv(file_res, encoding='ISO-8859-1')
    data_json = json.loads(data.to_json(orient='records'))
    ids.remove()
    ids.insert(data_json)
