import base64
import json
import unittest
import uuid
from os.path import join
from sdc.rabbit.exceptions import QuarantinableError


from app.main import SeftConsumer
from app.tests import TEST_FILES_PATH
from app.tests import test_settings
from app.tests.encrypter import Encrypter


class ConsumerTests(unittest.TestCase):

    def test_on_message_fails_with_empty_filename(self):
        consumer = SeftConsumer()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_file_contents(self):
        consumer = SeftConsumer()

        payload = '{"filename":"test", "file":""}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_filename(self):
        consumer = SeftConsumer()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"file":"' + encoded_contents.decode() + '"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_file_contents(self):
        consumer = SeftConsumer()

        payload = '{"filename":"test"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())
