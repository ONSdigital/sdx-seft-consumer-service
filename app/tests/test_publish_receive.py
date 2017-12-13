import base64
import filecmp
import json
import logging
import time
import unittest
import uuid
from os import listdir
from os.path import isfile, join
from threading import Thread
from unittest.mock import MagicMock

import pika
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import UnixFilesystem
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore
from sdc.rabbit.publisher import QueuePublisher
import tornado
import yaml

from app import settings
from app.main import SeftConsumer, KEY_PURPOSE_CONSUMER
from app.tests import TEST_FILES_PATH

logger = logging.getLogger(__name__)


def rabbit_running():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))
        connection.channel()
        return True
    except pika.exceptions.AMQPError:
        return False


class FTPThread(Thread):
    def __init__(self):
        super().__init__()
        authorizer = DummyAuthorizer()
        authorizer.add_user("ons", "ons", "./ftp", perm="elradfmw")

        handler = FTPHandler
        handler.authorizer = authorizer
        handler.abstracted_fs = UnixFilesystem
        self.server = ThreadedFTPServer((settings.FTP_HOST, str(settings.FTP_PORT)), handler)

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
    def __init__(self, keys):
        super().__init__()
        self._consumer = SeftConsumer(keys)
        self._consumer._send_receipt = MagicMock(return_value=None)

    def run(self):
        self._consumer.run()

    def stop(self):
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.stop()
        self._consumer.stop()


class EndToEndTest(unittest.TestCase):

    def setUp(self):
        with open("./sdx_test_keys/keys.yml") as file:
            self.sdx_keys = yaml.safe_load(file)
        with open("./ras_test_keys/keys.yml") as file:
            self.ras_keys = yaml.safe_load(file)
        self.ras_key_store = KeyStore(self.ras_keys)

    '''
    End to end test - spins up a consumer and FTP server. Encrypts a message including a encoded spread sheet and takes the
    decrypted and reassemble file are the same files.

    This test requires a rabbit mq server to be running locally with the default settings
    '''
    @unittest.skipIf(not rabbit_running(), "This test needs a locally running rabbit mq")
    def test_end_to_end(self):
        consumer_thread = ConsumerThread(self.sdx_keys)
        consumer_thread.start()

        ftp_thread = FTPThread()
        ftp_thread.start()
        files = [f for f in listdir(TEST_FILES_PATH) if isfile(join(TEST_FILES_PATH, f)) and (f.endswith(".xls") or f.endswith(".xlsx"))]
        for file in files:
            with open(join(TEST_FILES_PATH, file), "rb") as fb:
                contents = fb.read()
                encoded_contents = base64.b64encode(contents)

                payload = '{"filename":"' + file + '", "file":"' + encoded_contents.decode() + \
                          '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34","survey_id": "221"}'

            payload_as_json = json.loads(payload)
            jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)

            queue_publisher = QueuePublisher(settings.RABBIT_URLS, settings.RABBIT_QUEUE)
            headers = {'tx_id': str(uuid.uuid4())}
            queue_publisher.publish_message(jwt, headers=headers)

            time.sleep(1)
            self.assertTrue(filecmp.cmp(join(TEST_FILES_PATH, file), "./ftp/" + file))
        time.sleep(5)
        consumer_thread.stop()
        ftp_thread.stop()
