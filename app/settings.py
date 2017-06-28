import os


def get_key(key_name):
    key = open(key_name, 'r')
    contents = key.read()
    return contents

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST', 'localhost'),
    port=os.getenv('RABBITMQ_PORT', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URL2 = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST2', 'localhost'),
    port=os.getenv('RABBITMQ_PORT2', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL, RABBIT_URL2]

RABBIT_QUEUE = "Seft.Responses"
RABBIT_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'message')
# ras keys
RAS_SEFT_PUBLIC_KEY = get_key(os.getenv('RAS_SEFT_PUBLIC_KEY', "./test_keys/sdc-seft-signing-ras-public-key.pem"))

# sdx keys
SDX_SEFT_PRIVATE_KEY = get_key(os.getenv('PRIVATE_KEY', "./test_keys/sdc-seft-encryption-sdx-private-key.pem"))
SDX_SEFT_PRIVATE_KEY_PASSWORD = os.getenv("PRIVATE_KEY_PASSWORD", "digitaleq")

FTP_HOST = os.getenv('FTP_HOST', 'localhost')
FTP_PORT = os.getenv('FTP_PORT', 2021)
FTP_USER = os.getenv('FTP_USER', 'ons')
FTP_PASS = os.getenv('FTP_PASS', 'ons')
FTP_FOLDER = os.getenv('FTP_FOLDER', '.')


