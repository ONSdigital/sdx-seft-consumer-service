import base64
import filecmp
import json
import logging
from os import listdir
from os.path import isfile, join
import time
import unittest
import uuid
from threading import Thread

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import UnixFilesystem
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer

from app import settings
from app.consumer import Consumer
from app.publisher import QueuePublisher
from app.tests import test_settings
from app.tests.encrypter import Encrypter
from app.tests import TEST_FILES_PATH

logger = logging.getLogger(__name__)


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
    # @unittest.skip("This test needs a locally running rabbit mq")
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
            headers = {'tx_id': str(uuid.uuid4())}
            queue_publisher.publish_message(jwt, headers=headers)

            time.sleep(1)
            self.assertTrue(filecmp.cmp(join(TEST_FILES_PATH, file), "./ftp/" + file))
        time.sleep(5)
        consumer_thread.stop()
        ftp_thread.stop()
