import base64
import json
import unittest
import unittest.mock
import uuid
from os.path import join

import responses
from requests.packages.urllib3 import HTTPConnectionPool
from requests.packages.urllib3.exceptions import MaxRetryError
from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore
from sdc.crypto.exceptions import InvalidTokenException
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
import yaml

from app.main import SeftConsumer, KEY_PURPOSE_CONSUMER
from app.settings import RM_SDX_GATEWAY_URL
from app.tests import TEST_FILES_PATH
from app.sdxftp import SDXFTP


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

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_file_contents(self):
        payload = '{"filename":"test", "file":"", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_filename(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_file_contents(self):
        payload = '{"filename":"test", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_case_id(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '", "case_id": ""}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_case_id(self):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    @responses.activate
    def test_send_receipt_201(self):

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'ok'}, status=201)
        self.assertIsNone(self.consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None))
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_400(self):

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'client error'}, status=400)

        with self.assertRaises(QuarantinableError):
            self.consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)

        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_500(self):

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'server error'}, status=500)

        with self.assertRaises(RetryableError):
            self.consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)

        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_maxretryerror(self):

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, body=MaxRetryError(HTTPConnectionPool, RM_SDX_GATEWAY_URL))

        with self.assertRaises(RetryableError):
            with self.assertLogs(level="ERROR") as cm:
                self.consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)

        self.assertIn("Max retries exceeded (5)", cm[0][0].message)

    @responses.activate
    def test_send_ftp_IO_error(self):
        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'ok'}, status=201)

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch.object(SDXFTP, 'deliver_binary') as mock_method:
            mock_method.side_effect = IOError
            with self.assertRaises(RetryableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_decrypt_invalid_token_exception(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch('app.main.decrypt', side_effect=InvalidTokenException):
            with self.assertRaises(QuarantinableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_decrypt_exception(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch('app.main.decrypt', side_effect=Exception):
            with self.assertRaises(QuarantinableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())
