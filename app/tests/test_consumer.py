import base64
import json
import unittest
import uuid
from os.path import join

import responses
from requests.packages.urllib3 import HTTPConnectionPool
from requests.packages.urllib3.exceptions import MaxRetryError
from sdc.rabbit.exceptions import QuarantinableError, RetryableError


from app.main import SeftConsumer
from app.settings import RM_SDX_GATEWAY_URL
from app.tests import TEST_FILES_PATH
from app.tests import test_settings
from app.tests.encrypter import Encrypter


class ConsumerTests(unittest.TestCase):

    def test_on_message_fails_with_empty_filename(self):
        consumer = SeftConsumer()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_file_contents(self):
        consumer = SeftConsumer()

        payload = '{"filename":"test", "file":"", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

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

            payload = '{"file":"' + encoded_contents.decode() + '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_file_contents(self):
        consumer = SeftConsumer()

        payload = '{"filename":"test", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_case_id(self):
        consumer = SeftConsumer()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '", "case_id": ""}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_case_id(self):
        consumer = SeftConsumer()

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + '"}'

        encrypter = Encrypter(test_settings.SDX_SEFT_CONSUMER_PUBLIC_KEY,
                              test_settings.RAS_SEFT_CONSUMER_PRIVATE_KEY)

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypter.encrypt(payload_as_json)
        jwt = encrypted_jwt.decode("utf-8")

        with self.assertRaises(QuarantinableError):
            consumer.process(jwt, uuid.uuid4())

    @responses.activate
    def test_send_receipt_201(self):
        consumer = SeftConsumer()

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'ok'}, status=201)
        self.assertIsNone(consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None))
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_400(self):
        consumer = SeftConsumer()

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'client error'}, status=400)

        with self.assertRaises(QuarantinableError):
            consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_500(self):
        consumer = SeftConsumer()

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, json={'status': 'server error'}, status=500)

        with self.assertRaises(RetryableError):
            consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_send_receipt_maxretryerror(self):
        consumer = SeftConsumer()

        responses.add(responses.POST, RM_SDX_GATEWAY_URL, body=MaxRetryError(HTTPConnectionPool, RM_SDX_GATEWAY_URL))

        with self.assertRaises(RetryableError):
            with self.assertLogs(level="ERROR") as cm:
                consumer._send_receipt(case_id="601c4ee4-83ed-11e7-bb31-be2e44b06b34", tx_id=None)

        self.assertIn("Max retries exceeded (5)", cm[0][0].message)
