text_excel = '''zofu**@gmail.com	621835
umbr******@mail.ru	137335
pr*@mick.in.ua	347179
veta**@mick.in.ua	863401
'''.split("\n")
to_insert = [{"id": int(i.split()[1]), "email": i.split()[0], "type": "future", "account": 2} for i in text_excel if i]

from db import ids

ids.insert_many(to_insert)