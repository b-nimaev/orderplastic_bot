# -*- coding: utf-8 -*-

import pymongo

# config_uri = "mongodb://user:Ololosha123@45.76.32.134:27017/admin"
# client = pymongo.MongoClient(config_uri, retryWrites=True)

client = pymongo.MongoClient('localhost', 27017)

spot_trades = client["junior"]["spot_trades"]
future_trades = client["junior"]["future_trades"]
ids = client["junior"]["ids"]
users = client["junior"]["users"]
saver = client["junior"]["saver"]
