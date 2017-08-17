import base64

from app import create_and_wrap_logger
from app import settings
from app.sdxftp import SDXFTP
from sdc.crypto.decrypter import decrypt
from sdc.crypto.key_store import KeyStore, validate_required_keys
from sdc.crypto.exceptions import CryptoError, InvalidTokenException
from sdc.rabbit.publisher import QueuePublisher
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
from sdc.rabbit.consumers import MessageConsumer

import yaml

logger = create_and_wrap_logger(__name__)

KEY_PURPOSE_CONSUMER = "inbound"


class ConsumerError(Exception):
    pass


class SeftConsumer:
    def __init__(self, keys):
        self.key_store = KeyStore(keys)

        self._ftp = SDXFTP(logger,
                           settings.FTP_HOST,
                           settings.FTP_USER,
                           settings.FTP_PASS,
                           settings.FTP_PORT)

        self.publisher = QueuePublisher(urls=settings.RABBIT_URLS, queue=settings.RABBIT_QUARANTINE_QUEUE)
        self.consumer = MessageConsumer(durable_queue=True, exchange=settings.RABBIT_EXCHANGE, exchange_type="topic",
                                        rabbit_queue=settings.RABBIT_QUEUE,
                                        rabbit_urls=settings.RABBIT_URLS, quarantine_publisher=self.publisher,
                                        process=self.process)

    def process(self, encrypted_jwt, tx_id=None):

        logger.debug("Message Received", tx_id=tx_id)

        try:
            decrypted_payload = self._decrypt(encrypted_jwt, tx_id)

            decoded_contents, file_name = self._extract_file(decrypted_payload, tx_id)

            self._send_to_ftp(decoded_contents, file_name, tx_id)

        except ConsumerError:
            logger.error("Unable to process message", tx_id=tx_id)

    def _send_to_ftp(self, decoded_contents, file_name, tx_id):
        try:
            self._ftp.deliver_binary(settings.FTP_FOLDER, file_name, decoded_contents)
            logger.debug("Delivered to FTP server", tx_id=tx_id)
        except IOError as e:
            logger.error("Unable to deliver to the FTP server",
                         action="nack",
                         exception=e,
                         tx_id=tx_id)
            raise RetryableError()

    def _extract_file(self, decrypted_payload, tx_id):
        try:
            file_contents = decrypted_payload['file']
            file_name = decrypted_payload['filename']
            if not file_name or not file_contents:
                logger.error("Empty claims in message",
                             file_name=file_name,
                             file_contents="Encoded data" if file_contents else file_contents)
                raise ConsumerError()
            logger.debug("Decrypted file", file_name=file_name, tx_id=tx_id)
            decoded_contents = base64.b64decode(file_contents)
            return decoded_contents, file_name
        except (KeyError, ConsumerError) as e:
            logger.error("Required claims missing quarantining message",
                         exception=e,
                         keys=decrypted_payload.keys(),
                         action="quarantined",
                         tx_id=tx_id)
            raise QuarantinableError()

    def _decrypt(self, encrypted_jwt, tx_id):
        try:
            return decrypt(encrypted_jwt, self.key_store, KEY_PURPOSE_CONSUMER)
        except (InvalidTokenException, ValueError) as e:
            logger.error("Bad decrypt",
                         action="quarantined",
                         exception=e,
                         tx_id=tx_id)
            raise QuarantinableError()
        except Exception as e:
            logger.error("Failed to process",
                         action="retry",
                         exception=e,
                         tx_id=tx_id)
            raise QuarantinableError()

    def run(self):
        self.consumer.run()

    def stop(self):
        self.consumer.stop()


def main():
    logger.debug("Starting SEFT consumer service")

    with open(settings.SDX_KEYS_FILE) as file:
            keys = yaml.safe_load(file)

    try:
        validate_required_keys(keys, KEY_PURPOSE_CONSUMER)
        seft_consumer = SeftConsumer(keys)
        seft_consumer.run()

    except CryptoError as e:
        logger.critical("Unable to find valid keys", error=e)
    except KeyboardInterrupt:
        logger.debug("SEFT consumer service stopping")
        seft_consumer.stop()
        logger.debug("SEFT consumer service stopped")

if __name__ == '__main__':
    main()
