import os


def get_key(key_name):
    key = open(key_name, 'r')
    contents = key.read()
    return contents


LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")
HEALTHCHECK_DELAY = os.getenv("HEALTHCHECK_DELAY", 300)

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SEFT_RABBITMQ_HOST', '127.0.0.1'),
    port=os.getenv('SEFT_RABBITMQ_PORT', 5672),
    user=os.getenv('SEFT_RABBITMQ_DEFAULT_USER', 'guest'),
    password=os.getenv('SEFT_RABBITMQ_DEFAULT_PASS', 'guest'),
    vhost=os.getenv('SEFT_RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_HEALTHCHECK_URL = "http://{hostname}:{port}/api/healthchecks/node".format(
    hostname=os.getenv('SEFT_RABBITMQ_HOST', 'localhost'),
    port=os.getenv('SEFT_RABBITMQ_PORT', 5672)
)

SEFT_RABBITMQ_MONITORING_USER = os.getenv('SEFT_RABBITMQ_MONITORING_USER', 'monitor')
SEFT_RABBITMQ_MONITORING_PASS = os.getenv('SEFT_RABBITMQ_MONITORING_PASS', 'monitor')

RABBIT_URLS = [RABBIT_URL]

RABBIT_QUEUE = os.getenv("SEFT_RABBIT_CONSUMER_QUEUE", "Seft.Responses")
RABBIT_EXCHANGE = os.getenv('SEFT_RABBITMQ_EXCHANGE', 'message')
RABBIT_QUARANTINE_QUEUE = os.getenv("SEFT_RABBIT_CONSUMER_QUARANTINE_QUEUE", "Seft.Responses.Quarantine")

FTP_HOST = os.getenv('SEFT_FTP_HOST', 'localhost')
FTP_PORT = int(os.getenv('SEFT_FTP_PORT', '2021'))
FTP_USER = os.getenv('SEFT_FTP_USER', 'ons')
FTP_PASS = os.getenv('SEFT_FTP_PASS', 'ons')
FTP_FOLDER = os.getenv('SEFT_CONSUMER_FTP_FOLDER', '.')

SDX_KEYS_FILE = os.getenv('SDX_KEYS_FILE', 'keys.yml')
