import base64
import unittest
import pika
import logging
import json
import _thread
import time

from app import settings
from app.consumer import Consumer
from app.tests import test_settings
from app.tests.encrypter import Encrypter


logger = logging.getLogger(__name__)


class QueuePublisher(object):

    DURABLE_QUEUE = True

    def __init__(self, logger, urls, queue, arguments=None):
        self._logger = logger
        self._urls = urls
        self._queue = queue
        self._arguments = arguments
        self._connection = None
        self._channel = None

    def _connect(self):
        self._logger.debug("Connecting to queue")
        for url in self._urls:
            try:
                self._connection = pika.BlockingConnection(pika.URLParameters(url))
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=self._queue,
                                            durable=self.DURABLE_QUEUE,
                                            arguments=self._arguments)
                self._logger.debug("Connected to queue")
                return True

            except pika.exceptions.AMQPConnectionError as e:
                self._logger.error("Unable to connect to queue", exception=repr(e))
                continue

        return False

    def _disconnect(self):
        try:
            self._connection.close()
            self._logger.debug("Disconnected from queue")

        except Exception as e:
            self._logger.error("Unable to close connection", exception=repr(e))

    def _publish(self, message, content_type=None, headers=None):
        try:
            self._channel.basic_publish(exchange='',
                                        routing_key=self._queue,
                                        properties=pika.BasicProperties(
                                            content_type=content_type,
                                            headers=headers,
                                            delivery_mode=2
                                        ),
                                        body=message)
            self._logger.debug("Published message")
            return True

        except Exception as e:
            self._logger.error("Unable to publish message", exception=repr(e))
            return False

    def publish_message(self, message, content_type=None, headers=None):
        self._logger.debug("Sending message")
        if not self._connect():
            return False

        if not self._publish(message, headers=headers):
            return False

        self._disconnect()
        return True


class EndToEndTest(unittest.TestCase):

    def test_end_to_end(self):
        consumer = Consumer()
        try:
            _thread.start_new(consumer.run())
        except:
            self.fail("Unable to start consumer thread")

        with open("./test_files/testing.xls", "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"testing.xls", "file":"' + encoded_contents.decode() + '"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        jwt = encrypter.encrypt(payload_as_json)

        queue_publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUEUE)
        queue_publisher.publish_message(jwt)

        time.sleep(1)
        consumer.stop()

