from distutils.util import strtobool
import os

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-seft-consumer-service: %(message)s"

SEFT_CONSUMER_HEALTHCHECK_DELAY = int(os.getenv("SEFT_CONSUMER_HEALTHCHECK_DELAY", "5000"))

RABBIT_QUEUE = "Seft.Responses"
RABBIT_EXCHANGE = 'message'
RABBIT_QUARANTINE_QUEUE = "Seft.Responses.Quarantine"

FTP_HOST = os.getenv('SEFT_FTP_HOST', 'localhost')
FTP_PORT = int(os.getenv('SEFT_FTP_PORT', '2021'))
FTP_USER = os.getenv('SEFT_FTP_USER', 'ons')
FTP_PASS = os.getenv('SEFT_FTP_PASS', 'ons')

FTP_FOLDER = os.getenv('SEFT_CONSUMER_FTP_FOLDER', '.')

SDX_SEFT_CONSUMER_KEYS_FILE = os.getenv('SDX_SEFT_CONSUMER_KEYS_FILE', './sdx_test_keys/keys.yml')

# Configure the number of retries attempted before failing call
SERVICE_REQUEST_TOTAL_RETRIES = 5
SERVICE_REQUEST_BACKOFF_FACTOR = 0.1

ANTI_VIRUS_ENABLED = bool(strtobool(os.getenv("ANTI_VIRUS_ENABLED", "True")))
ANTI_VIRUS_BASE_URL = os.getenv("ANTI_VIRUS_BASE_URL", "https://scan.metadefender.com/v2/file")
ANTI_VIRUS_API_KEY = os.getenv("ANTI_VIRUS_API_KEY")
ANTI_VIRUS_CA_CERT = os.getenv("ANTI_VIRUS_CA_CERT")
ANTI_VIRUS_WAIT_TIME = int(os.getenv('ANTI_VIRUS_WAIT_TIME', '5'))
ANTI_VIRUS_MAX_ATTEMPTS = int(os.getenv('ANTI_VIRUS_MAX_ATTEMPTS', '20'))
ANTI_VIRUS_RULE = os.getenv("ANTI_VIRUS_RULE", "Password Protected Allowed")
ANTI_VIRUS_USER_AGENT = os.getenv("ANTI_VIRUS_USER_AGENT", "sdc")


RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SEFT_RABBITMQ_HOST', '127.0.0.1'),
    port=os.getenv('SEFT_RABBITMQ_PORT', 5672),
    user=os.getenv('SEFT_RABBITMQ_DEFAULT_USER', 'guest'),
    password=os.getenv('SEFT_RABBITMQ_DEFAULT_PASS', 'guest'),
    vhost='%2f'
)

RABBIT_HEALTHCHECK_URL = "http://{user}:{password}@{hostname}:{port}/api/healthchecks/node".format(
    user=os.getenv("SEFT_RABBITMQ_MONITORING_USER", "monitor"),
    password=os.getenv("SEFT_RABBITMQ_MONITORING_PASS", "monitor"),
    hostname=os.getenv('SEFT_RABBITMQ_HOST', 'localhost'),
    port=os.getenv('SEFT_RABBITMQ_HEALTHCHECK_PORT', 15672)
)

RABBIT_URLS = [RABBIT_URL]
