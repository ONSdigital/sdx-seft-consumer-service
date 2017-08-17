import base64
import filecmp
import json
import unittest
from os import listdir
from os.path import isfile, join

from app.main import KEY_PURPOSE_CONSUMER
from app.tests import TEST_FILES_PATH, TEST_FILES_RECOVERED_PATH
from sdc.crypto.key_store import KeyStore
from sdc.crypto.encrypter import encrypt
from sdc.crypto.decrypter import decrypt

import yaml


class SeftTests(unittest.TestCase):
    '''
    Loops through all files in ./test_files puts them throught the encryption and decryption
    process and make sure the outputted files in ./seft_files match
    '''

    def setUp(self):
        with open("./sdx_test_keys/keys.yml") as file:
            self.sdx_keys = yaml.safe_load(file)
        with open("./ras_test_keys/keys.yml") as file:
            self.ras_keys = yaml.safe_load(file)
        self.ras_key_store = KeyStore(self.ras_keys)
        self.sdx_key_store = KeyStore(self.sdx_keys)

    def test_encrypt_transfer_decrypt(self):
        files = [f for f in listdir(TEST_FILES_PATH) if isfile(join(TEST_FILES_PATH, f))]

        for file in files:
            with open(TEST_FILES_PATH + file, "rb") as fb:
                contents = fb.read()
                encoded_contents = base64.b64encode(contents)

                payload = '{"file":"' + encoded_contents.decode() + '"}'

                payload_as_json = json.loads(payload)
                jwt = encrypt(payload_as_json, self.ras_key_store, KEY_PURPOSE_CONSUMER)

                decrypted_payload = decrypt(jwt, self.sdx_key_store, KEY_PURPOSE_CONSUMER)

                file_contents = decrypted_payload.get("file")
                decoded_contents = base64.b64decode(file_contents)

                self.assertEqual(contents, decoded_contents)

            with open(TEST_FILES_RECOVERED_PATH + file, "wb") as fb:
                fb.write(decoded_contents)

            self.assertTrue(filecmp.cmp(TEST_FILES_PATH + file, TEST_FILES_RECOVERED_PATH + file))
