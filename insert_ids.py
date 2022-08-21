from db import ids

for user in ids.find():
    ids.update_one({"_id": user['_id']},
                   {"$set": {
                       "coeff": 0.75
                   }})


