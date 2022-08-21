from db import ids
# {
#     "_id": {
#         "$oid": "5e42b9969e49bffd84bf58aa"
#     },
#     "id": 878936,
#     "email": "****@**.ru",
#     "type": "spot",
#     "account": 1,
#     "xlm": "GDNKUZHZKY7IOONKNQ56V4FA4CEQZ4EZLB3OHVDZ73PDP4I4GEU2AT4Z",
#     "xlm_memo": "0",
#     "coeff": 0.6
# }
mails = """ro***************tc@*****.com	45419403
ak*********in@*****.com	42009798
1m******in@*****.com	47848379
ro****************92@*****.com	50140914
xz****55@*****.com	49340428
pi*******09@******.ru	47508685
of**sy@******.ru	44785728
gl*****ul@*****.com	43462179
de******80@*****.com	47882481
al**************37@*****.com	44525427
n4**4d@******.ru	43524914
n2**2d@******.ru	43527410
n9**9d@******.ru	43400574
n3**3d@******.ru	43526289
le*****dr@******.ru	42884673
n5**5d@******.ru	43522646
n6**6d@******.ru	43521858
vi*******78@*****.com	42691655
se**78@*****.com	45464255
pi*******09@*****.com	45946635
n8**8d@******.ru	43400391
ba*****id@******.ua	42260236
gr**mv@*****.com	46583777
n7**8d@******.ru	43400083
t.************88@*****.com	44360606
s1******ow@***.net	42836699
ro***********s2@*****.com	47725123
dj*******e0@*****.com	45544947
be*************32@****.ru	44492311
pr******18@*****.com	46845370
zx****55@*****.com	47490536
rv****55@*****.com	44914729
vr****55@*****.com	45299843
be*************33@****.ru	46523482"""
# for i in mails.split("\n"):
#     try:
#         email, new_id = i.split("\t")
#     except:
#         continue
#     ids.update_one({"account": 3, "email": email},
#                    {"$set": {"binance_id": int(new_id)}})
for i in ids.find():
    print(i['binance_id'])