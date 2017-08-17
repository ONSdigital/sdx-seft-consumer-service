import base64
import json
import unittest
import uuid
from os.path import join
from sdc.rabbit.exceptions import QuarantinableError
from sdc.crypto.key_store import KeyStore
from sdc.crypto.encrypter import encrypt

from app.main import SeftConsumer, KEY_PURPOSE_CONSUMER
from app.tests import TEST_FILES_PATH
import yaml


class ConsumerTests(unittest.TestCase):

    def setUp(self):
        with open("./sdx_test_keys/keys.yml") as file:
            self.sdx_keys = yaml.safe_load(file)
        with open("./ras_test_keys/keys.yml") as file:
            self.ras_keys = yaml.safe_load(file)
        self.ras_key_store = KeyStore(self.ras_keys)
        self.consumer = SeftConsumer(self.sdx_keys)

    def test_on_message_fails_with_empty_filename(self):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_file_contents(self):
        payload = '{"filename":"test", "file":""}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_filename(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"file":"' + encoded_contents.decode() + '"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_file_contents(self):
        payload = '{"filename":"test"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())
