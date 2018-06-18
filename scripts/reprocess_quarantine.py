from pika import BlockingConnection
from pika import URLParameters
from sdc.rabbit.publishers import QueuePublisher, PublishMessageError

from app import create_and_wrap_logger
from app import settings

logger = create_and_wrap_logger(__name__)


def reprocess():
    connection = BlockingConnection(URLParameters(settings.RABBIT_URL))
    channel = connection.channel()
    method, properties, body = channel.basic_get(settings.RABBIT_QUARANTINE_QUEUE)
    if method:
        try:
            logger.info("Recovered quarantine message", body=body, headers=properties.headers)
            publisher = QueuePublisher(urls=settings.RABBIT_URLS,
                                       queue=settings.RABBIT_QUEUE)

            publisher.publish_message(body, headers=properties.headers)
            logger.info("Message successfully reprocess")

            channel.basic_ack(method.delivery_tag)
            logger.info("Message ACK")
        except PublishMessageError:
            logger.exception()
            channel.basic_nack(method.delivery_tag)
    else:
        logger.info('No message found on quarantine queue')


if __name__ == '__main__':
    reprocess()
