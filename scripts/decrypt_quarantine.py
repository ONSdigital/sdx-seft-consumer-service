import yaml
from pika import BlockingConnection
from pika import URLParameters
from sdc.crypto.decrypter import decrypt
from sdc.crypto.exceptions import InvalidTokenException
from sdc.crypto.key_store import KeyStore

from app import create_and_wrap_logger
from app import settings
from app.main import KEY_PURPOSE_CONSUMER
from app.main import SeftConsumer

logger = create_and_wrap_logger(__name__)


def decrypt_and_write():
    with open(settings.SDX_SEFT_CONSUMER_KEYS_FILE) as file:
        keys = yaml.safe_load(file)
    key_store = KeyStore(keys)
    connection = BlockingConnection(URLParameters(settings.RABBIT_URL))
    channel = connection.channel()
    method, properties, body = channel.basic_get(settings.RABBIT_QUARANTINE_QUEUE)
    if method:
        logger.info("Recovered quarantine message", body=body, headers=properties.headers)
        try:
            decrypted_message = decrypt(body.decode("utf-8"), key_store, KEY_PURPOSE_CONSUMER)
            payload = SeftConsumer.extract_file(decrypted_message, properties.headers['tx_id'])
            with open('/tmp/{}'.format(payload.file_name), 'wb') as recovered_file:
                recovered_file.write(payload.decoded_contents)
            channel.basic_ack(method.delivery_tag)
            logger.info("Message ACK")

        except (InvalidTokenException, ValueError):
            logger.exception("Bad decrypt")
            channel.basic_nack(method.delivery_tag)
            logger.info("Nacking message")
        except Exception:
            logger.exception("Failed to process")
            channel.basic_nack(method.delivery_tag)
            logger.info("Nacking message")
    else:
        logger.info('No message found on quarantine queue')


if __name__ == '__main__':
    decrypt_and_write()
