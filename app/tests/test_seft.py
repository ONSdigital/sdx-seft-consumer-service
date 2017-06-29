import base64
import filecmp
import json
import unittest
from os import listdir
from os.path import isfile, join

from app import settings
from app.decrypter import Decrypter
from app.tests import test_settings
from app.tests.encrypter import Encrypter
from app.tests import TEST_FILES_PATH, TEST_FILES_RECOVERED_PATH


class SeftTests(unittest.TestCase):
    '''
    Loops through all files in ./test_files puts them throught the encryption and decryption
    process and make sure the outputted files in ./seft_files match
    '''

    def test_encrypt_transfer_decrypt(self):
        files = [f for f in listdir(TEST_FILES_PATH) if isfile(join(TEST_FILES_PATH, f))]

        for file in files:
            with open(TEST_FILES_PATH + file, "rb") as fb:
                contents = fb.read()
                encoded_contents = base64.b64encode(contents)

                payload = '{"file":"' + encoded_contents.decode() + '"}'
                encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                                      test_settings.RAS_SEFT_PRIVATE_KEY,
                                      test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

                payload_as_json = json.loads(payload)
                jwt = encrypter.encrypt(payload_as_json)

                decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                      settings.SDX_SEFT_PRIVATE_KEY,
                                      settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

                decrypted_payload = decrypter.decrypt(jwt.decode())

                file_contents = decrypted_payload.get("file")
                decoded_contents = base64.b64decode(file_contents)

                self.assertEqual(contents, decoded_contents)

            with open(TEST_FILES_RECOVERED_PATH + file, "wb") as fb:
                fb.write(decoded_contents)

            self.assertTrue(filecmp.cmp(TEST_FILES_PATH + file, TEST_FILES_RECOVERED_PATH + file))
