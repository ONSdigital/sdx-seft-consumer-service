import os
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def get_key(key_name):
    key = open(key_name, 'r')
    contents = key.read()
    return contents


LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")

RM_SDX_GATEWAY_URL = os.getenv("RM_SDX_GATEWAY_URL", "http://localhost:8191/receipts")

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SEFT_RABBITMQ_HOST', 'localhost'),
    port=os.getenv('SEFT_RABBITMQ_PORT', 5672),
    user=os.getenv('SEFT_RABBITMQ_DEFAULT_USER', 'guest'),
    password=os.getenv('SEFT_RABBITMQ_DEFAULT_PASS', 'guest'),
    vhost=os.getenv('SEFT_RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL]

RABBIT_QUEUE = os.getenv("SEFT_RABBIT_CONSUMER_QUEUE", "Seft.Responses")
RABBIT_EXCHANGE = os.getenv('SEFT_RABBITMQ_EXCHANGE', 'message')
RABBIT_QUARANTINE_QUEUE = os.getenv("SEFT_RABBIT_CONSUMER_QUARANTINE_QUEUE", "Seft.Responses.Quarantine")

# ras keys
RAS_SEFT_CONSUMER_PUBLIC_KEY = get_key(os.getenv('RAS_SEFT_CONSUMER_PUBLIC_KEY', "./test_keys/sdc-seft-signing-ras-public-key.pem"))

# sdx keys
SDX_SEFT_CONSUMER_PRIVATE_KEY = get_key(os.getenv('SDX_SEFT_CONSUMER_PRIVATE_KEY', "./test_keys/sdc-seft-encryption-sdx-private-key.pem"))

FTP_HOST = os.getenv('SEFT_FTP_HOST', 'localhost')
FTP_PORT = int(os.getenv('SEFT_FTP_PORT', '2021'))
FTP_USER = os.getenv('SEFT_FTP_USER', 'ons')
FTP_PASS = os.getenv('SEFT_FTP_PASS', 'ons')
FTP_FOLDER = os.getenv('SEFT_CONSUMER_FTP_FOLDER', '.')

# Configure the number of retries attempted before failing call
session = requests.Session()
retries = Retry(total=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
