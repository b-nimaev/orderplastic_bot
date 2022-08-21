from telebot import TeleBot
from binance.client import Client


binance_cli = Client()

API_KEY = "5718719985:AAH-A3v36S-xThgu4BFn01J4QvTiCsKWiO4"


bot = TeleBot(API_KEY)

ADMINS = [152950074, 509884280, 10902074, 141518724, 5431291155]


WEBHOOK_HOST = '91.132.230.20'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# WEBHOOK_SSL_CERT = '/etc/ssl/certs/nginx.crt'  # Path to the ssl certificate
# WEBHOOK_SSL_PRIV = '/etc/ssl/private/nginx.key'  # Path to the ssl private key


# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_KEY)

