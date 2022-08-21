import subprocess
from config import bot


def db_backuper():
    channel_id = -1001166830252
    process = subprocess.Popen("mongodump --username user --password Ololosha123 --authenticationDatabase admin --db junior --gzip --archive=junior.archive".split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    try:
        with open('./junior.archive', 'rb') as file:
            bot.send_document(channel_id, file)
    except Exception as e:
        print("Very large file...")
    return stdout
