from random import choice
import string
import re
import time
from datetime import datetime, timedelta
import calendar


def case_by_num(num: int, c1: str, c2: str, c3: str) -> str:
    if 11 <= num <= 14:
        return c3
    if num % 10 == 1:
        return c1
    if 2 <= num % 10 <= 4:
        return c2
    return c3


def get_current_period():
    now = datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    if 1 <= now.day <= 15:
        start_time = datetime(year=now.year, month=now.month,
                              day=1, hour=0, minute=0, second=0).timestamp()
        end_time = datetime(year=now.year, month=now.month,
                            day=15, hour=23, minute=59, second=59).timestamp()
    else:
        start_time = datetime(year=now.year, month=now.month,
                              day=16, hour=0, minute=0, second=0).timestamp()
        end_time = datetime(year=now.year, month=now.month,
                            day=days_in_month, hour=23, minute=59, second=59).timestamp()
    return start_time, end_time


def get_past_period():
    now = datetime.now()
    new_date = now - timedelta(days=15)
    days_in_month = calendar.monthrange(new_date.year, new_date.month)[1]
    if 1 <= now.day <= 15:
        start_time = datetime(year=new_date.year, month=new_date.month,
                              day=16, hour=0, minute=0, second=0).timestamp()
        end_time = datetime(year=new_date.year, month=new_date.month,
                            day=days_in_month, hour=23, minute=59, second=59).timestamp()
    else:
        start_time = datetime(year=new_date.year, month=new_date.month,
                              day=1, hour=0, minute=0, second=0).timestamp()
        end_time = datetime(year=new_date.year, month=new_date.month,
                            day=15, hour=23, minute=59, second=59).timestamp()
    return start_time, end_time


def time_checker(func):
    def temp(*args, **kwargs):
        start_time = time.time()
        return_value = func(*args, **kwargs)
        print(time.time()-start_time)
        return return_value
    return temp


def is_float(x):
    try:
        float(x)
        return True
    except:
        return False


def is_date(x):
    try:
        datetime.strptime(x, "%d.%m.%Y")
        return True
    except:
        return False


def is_phone(x):
    try:
        if x[0] == "+" and x[1:].isdigit() and len(x[1:]) in [11, 12]:
            return True
        else:
            return False
    except:
        return False


def is_duration(x):
    try:
        x,y = x.split(":")
        if 0 <= int(y) <= 60:
            return True
        return False
    except:
        return False


def is_link(x):
    regex = re.compile('^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+(?:[A-Z]{2,6}\\.?|[A-Z0-9-]{2,}\\.?)|localhost|\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})(?::\\d+)?(?:/?|[/?]\\S+)$', re.IGNORECASE)
    return re.match(regex, x) is not None


def gen_id():
    while 1:
        random = ''.join([choice(string.digits) for n in range(6)])
        return random
