import base64
import unittest
from unittest.mock import MagicMock
import json
from os.path import join
import uuid

from pika.spec import BasicProperties
from pika.spec import Basic

from app.consumer import Consumer
from app.tests.encrypter import Encrypter
from app.tests import test_settings
from app.tests import TEST_FILES_PATH


class ConsumerTests(unittest.TestCase):

    def test_on_message_fails_with_missing_filename(self):
        consumer = Consumer()
        consumer.quarantine_publisher = MagicMock()
        consumer.reject_message = MagicMock()
        consumer._channel = MagicMock()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        jwt = encrypter.encrypt(payload_as_json)
        headers = {'tx_id': str(uuid.uuid4())}
        properties = BasicProperties(headers=headers)
        basic_deliver = Basic.Deliver()

        consumer.on_message(unused_channel=None, basic_deliver=basic_deliver, properties=properties, body=jwt)

        self.assertTrue(consumer.quarantine_publisher.publish_message.called)
        self.assertTrue(consumer.reject_message.called)

    def test_on_message_fails_with_missing_file_contents(self):
        consumer = Consumer()
        consumer.quarantine_publisher = MagicMock()
        consumer.reject_message = MagicMock()
        consumer._channel = MagicMock()

        payload = '{"filename":"test", "file":""}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        jwt = encrypter.encrypt(payload_as_json)
        headers = {'tx_id': str(uuid.uuid4())}
        properties = BasicProperties(headers=headers)
        basic_deliver = Basic.Deliver()

        consumer.on_message(unused_channel=None, basic_deliver=basic_deliver, properties=properties, body=jwt)

        self.assertTrue(consumer.quarantine_publisher.publish_message.called)
        self.assertTrue(consumer.reject_message.called)
