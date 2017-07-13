import os


def get_key(key_name):
    key = open(key_name, 'r')
    contents = key.read()
    return contents

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SEFT_RABBITMQ_HOST', 'localhost'),
    port=os.getenv('SEFT_RABBITMQ_PORT', 5672),
    user=os.getenv('SEFT_RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('SEFT_RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('SEFT_RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL]

RABBIT_QUEUE = os.getenv("SEFT_RABBIT_QUEUE", "Seft.Responses")
RABBIT_EXCHANGE = os.getenv('SEFT_RABBITMQ_EXCHANGE', 'message')
RABBIT_QUARANTINE_QUEUE = os.getenv("SEFT_RABBIT_QUARANTINE_QUEUE", "Seft.Responses.Quarantine")

# ras keys
RAS_SEFT_PUBLIC_KEY = get_key(os.getenv('RAS_SEFT_PUBLIC_KEY', "./test_keys/sdc-seft-signing-ras-public-key.pem"))

# sdx keys
SDX_SEFT_PRIVATE_KEY = get_key(os.getenv('SDX_SEFT_PRIVATE_KEY', "./test_keys/sdc-seft-encryption-sdx-private-key.pem"))
SDX_SEFT_PRIVATE_KEY_PASSWORD = os.getenv("SDX_SEFT_PRIVATE_KEY_PASSWORD", "digitaleq")

FTP_HOST = os.getenv('SEFT_FTP_HOST', 'localhost')
FTP_PORT = int(os.getenv('SEFT_FTP_PORT', '2021'))
FTP_USER = os.getenv('SEFT_FTP_USER', 'ons')
FTP_PASS = os.getenv('SEFT_FTP_PASS', 'ons')
FTP_FOLDER = os.getenv('SEFT_FTP_FOLDER', '.')
