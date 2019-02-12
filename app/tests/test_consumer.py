import base64
import json
import unittest
import unittest.mock
import uuid
from os.path import join
from unittest.mock import patch

from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore
from sdc.crypto.exceptions import InvalidTokenException
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
import yaml

from app.main import SeftConsumer, KEY_PURPOSE_CONSUMER
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

    @patch('app.anti_virus_check.AntiVirusCheck.send_for_av_scan')
    @patch('app.sdxftp.SDXFTP.deliver_binary')
    def test_valid_message_writes_to_log_after_ftp(self, mock_deliver_binary, mock_send_for_av_scan):
        """Validate that the log entry is written after a successful ftp write"""
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'
        with self.assertLogs(level="DEBUG") as cm:
            payload_as_json = json.loads(payload)
            encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)

            self.consumer.process(encrypted_jwt, uuid.uuid4())
        self.assertTrue(ConsumerTests._contains_statement_in_log_file("Delivered to FTP server", cm.output))
        self.assertTrue(mock_deliver_binary.called)
        self.assertTrue(mock_send_for_av_scan.called)

    @staticmethod
    def _contains_statement_in_log_file(statement, output):
        return [statement for line in output if statement in line]

    @patch('app.anti_virus_check.AntiVirusCheck.send_for_av_scan')
    @patch('app.sdxftp.SDXFTP.deliver_binary')
    def test_file_sent_to_av_and_ftp(self, mock_deliver_binary, mock_send_for_av_scan):
        """Validate the message gets sent to the av and ftp"""
        tx_id = uuid.uuid4()
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "SomeSurveyId"}'
            payload_as_json = json.loads(payload)
            encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
            self.consumer.process(encrypted_jwt, tx_id)

        self.assertTrue(mock_deliver_binary.called)
        self.assertTrue(mock_send_for_av_scan.called)

    @patch('app.anti_virus_check.AntiVirusCheck.send_for_av_scan')
    @patch('app.sdxftp.SDXFTP.deliver_binary')
    def test_valid_message_ftp_path_includes_survey_id(self, mock_deliver_binary, mock_send_for_av_scan):
        """Validates that the correct path and filename are used to deliver the ftp i.e that the survey_id is part
        of the path
        ..note:: Pycharm will pass this test even if the url is manually changed to the wrong string. It appears to be
        a bug in pycharm with multiple patches. The test fails under the same circumstances when run via make .
        """
        self.consumer._ftp.deliver_binary = mock_deliver_binary
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "SomeSurveyId"}'
            payload_as_json = json.loads(payload)
            encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
            self.consumer.process(encrypted_jwt, uuid.uuid4())
        mock_deliver_binary.assert_called_with("./SomeSurveyId", 'test1.xls', unittest.mock.ANY)
        self.assertTrue(mock_send_for_av_scan.called)

    def test_on_message_fails_with_empty_filename(self):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_file_contents(self):
        payload = '{"filename":"test", "file":"", "case_id": ' \
                  '"601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_filename(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"file":"' + encoded_contents.decode() +\
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_file_contents(self):
        payload = '{"filename":"test", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_empty_case_id(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "", "survey_id": "221"}'

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

    def test_on_message_fails_with_empty_survey_id(self):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": ""}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_on_message_fails_with_missing_survey_id(self):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1.xls", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with self.assertRaises(QuarantinableError):
            self.consumer.process(encrypted_jwt, uuid.uuid4())

    @patch('app.anti_virus_check.AntiVirusCheck.send_for_av_scan')
    def test_send_ftp_IO_error(self, mock_send_for_av_scan):
        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34","survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch.object(SDXFTP, 'deliver_binary') as mock_method:
            mock_method.side_effect = IOError
            with self.assertRaises(RetryableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())
        self.assertTrue(mock_send_for_av_scan.called)

    def test_decrypt_invalid_token_exception(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id":"221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch('app.main.decrypt', side_effect=InvalidTokenException):
            with self.assertRaises(QuarantinableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())

    def test_decrypt_exception(self):

        with open(join(TEST_FILES_PATH, "test1.xls"), "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"filename":"test1", "file":"' + encoded_contents.decode() + \
                      '", "case_id": "601c4ee4-83ed-11e7-bb31-be2e44b06b34", "survey_id": "221"}'

        payload_as_json = json.loads(payload)
        encrypted_jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)
        with unittest.mock.patch('app.main.decrypt', side_effect=Exception):
            with self.assertRaises(QuarantinableError):
                self.consumer.process(encrypted_jwt, uuid.uuid4())
