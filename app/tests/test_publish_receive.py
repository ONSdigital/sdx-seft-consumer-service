import base64
import filecmp
import json
import logging
import os
from os import listdir
from os.path import isfile, join
import time
import unittest
from threading import Thread

import pika
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import UnixFilesystem
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer

from app import settings
from app.consumer import Consumer
from app.tests import test_settings
from app.tests.encrypter import Encrypter
from app.tests import TEST_FILES_PATH

logger = logging.getLogger(__name__)


# TODO this can be moved to the common rabbit library and reused from there
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


class FTPThread(Thread):
    def __init__(self):
        super().__init__()
        authorizer = DummyAuthorizer()
        authorizer.add_user("ons", "ons", "./ftp", perm="elradfmw")

        handler = FTPHandler
        handler.authorizer = authorizer
        handler.abstracted_fs = UnixFilesystem
        self.server = ThreadedFTPServer(("0.0.0.0", os.getenv('PORT', '2021')), handler)

    def run(self):
        logger.debug("Calling enter")
        try:
            self.server.serve_forever()
        except OSError:
            logger.debug("Thrown during shut down")
            exit()

    def stop(self):
        logger.debug("Calling exit")
        self.server.close_all()


class ConsumerThread(Thread):
    def __init__(self):
        super().__init__()
        self._consumer = Consumer()

    def run(self):
        self._consumer.run()

    def stop(self):
        self._consumer.stop()


class EndToEndTest(unittest.TestCase):
    '''
    End to end test - spins up a consumer and FTP server. Encrypts a message including a encoded spread sheet and takes the
    decrypted and reassemble file are the same files.

    This test requires a rabbit mq server to be running locally with the default settings
    '''
    @unittest.skip("This test needs a locally running rabbit mq")
    def test_end_to_end(self):
        consumer_thread = ConsumerThread()
        consumer_thread.start()

        ftp_thread = FTPThread()
        ftp_thread.start()
        files = [f for f in listdir(TEST_FILES_PATH) if isfile(join(TEST_FILES_PATH, f)) and (f.endswith(".xls") or f.endswith(".xlsx"))]
        for file in files:
            with open(join(TEST_FILES_PATH, file), "rb") as fb:
                contents = fb.read()
                encoded_contents = base64.b64encode(contents)

                payload = '{"filename":"' + file + '", "file":"' + encoded_contents.decode() + '"}'

            encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                                  test_settings.RAS_SEFT_PRIVATE_KEY,
                                  test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

            payload_as_json = json.loads(payload)
            jwt = encrypter.encrypt(payload_as_json)

            queue_publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUEUE)
            queue_publisher.publish_message(jwt)

            time.sleep(1)
            self.assertTrue(filecmp.cmp(join(TEST_FILES_PATH, file), "./ftp/" + file))
        time.sleep(5)
        consumer_thread.stop()
        ftp_thread.stop()
