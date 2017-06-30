import base64

from sdx.common.async_consumer import AsyncConsumer

from app import create_and_wrap_logger
from app import settings
from app.decrypter import Decrypter, DecryptError
from app.sdxftp import SDXFTP
from app.publisher import QueuePublisher

logger = create_and_wrap_logger(__name__)

'''
The AsyncConsumer will automatically pick up the RABBIT queue from a file called settings with var RABBIT_QUEUE
TODO this really needs to change
'''
QUEUE = settings.RABBIT_QUEUE


class Consumer(AsyncConsumer):

    def __init__(self, log=None):
        super().__init__(log)
        self._decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                    settings.SDX_SEFT_PRIVATE_KEY,
                                    settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

        self.quarantine_publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUARANTINE_QUEUE)

        self._ftp = SDXFTP(logger, settings.FTP_HOST, settings.FTP_USER, settings.FTP_PASS, settings.FTP_PORT)

    def on_message(self, unused_channel, basic_deliver, properties, body):

        delivery_count = self.get_delivery_count_from_properties(properties)
        try:
            tx_id = self.get_tx_id_from_properties(properties)
        except KeyError as e:
            self.quarantine_publisher.publish_message(body)
            self.reject_message(basic_deliver.delivery_tag, tx_id=tx_id)
            logger.error("No tx_id so quarantining message",
                         action="quarantined",
                         exception=e,
                         tx_id=tx_id,
                         delivery_count=delivery_count)

        encrypted_jwt = body.decode("utf-8")
        logger.debug("Message Received", tx_id=tx_id)

        try:
            decrypted_payload = self._decrypter.decrypt(encrypted_jwt)
        except DecryptError as e:
            # Move to the quarantine queue
            self.quarantine_publisher.publish_message(body)
            self.reject_message(basic_deliver.delivery_tag, tx_id=tx_id)
            logger.error("Bad decrypt",
                         action="quarantined",
                         exception=e,
                         tx_id=tx_id,
                         delivery_count=delivery_count)
        except Exception as e:
            self.nack_message(basic_deliver.delivery_tag, tx_id=tx_id)
            logger.error("Failed to process",
                         action="nack",
                         exception=e,
                         tx_id=tx_id,
                         delivery_count=delivery_count)

        file_contents = decrypted_payload.get("file")
        file_name = decrypted_payload.get("filename")
        logger.debug("Decrypted file", file_name=file_name, tx_id=tx_id)

        decoded_contents = base64.b64decode(file_contents)

        try:
            self._ftp.deliver_binary(settings.FTP_FOLDER, file_name, decoded_contents)
            logger.debug("Delivered to FTP server", tx_id=tx_id)
            self.acknowledge_message(basic_deliver.delivery_tag)
        except IOError as e:
            logger.exception("Unable to deliver to the FTP server", e)
            self.nack_message(basic_deliver.delivery_tag, tx_id=tx_id)

    @staticmethod
    def get_tx_id_from_properties(properties):
        """
        Returns the tx_id for a message from a rabbit queue. The value is
        auto-set by rabbitmq.
        """
        try:
            tx_id = properties.headers['tx_id']
            logger.info("Retrieved tx_id from message properties", tx_id=tx_id)
            return tx_id
        except KeyError as e:
            logger.error("No tx_id in message properties. Sending message to quarantine")
            raise e

    @staticmethod
    def get_delivery_count_from_properties(properties):
        """
        Returns the delivery count for a message from the rabbit queue. The
        value is auto-set by rabbitmq.
        """
        delivery_count = 0
        if properties.headers and 'x-delivery-count' in properties.headers:
            delivery_count = properties.headers['x-delivery-count']
        return delivery_count + 1


def main():
    logger.debug("Starting SEFT consumer service")
    consumer = Consumer()
    try:
        consumer.run()
    except KeyboardInterrupt:
        logger.debug("SEFT consumer service stopping")
        consumer.stop()
        logger.debug("SEFT consumer service stopped")

if __name__ == '__main__':
    main()
