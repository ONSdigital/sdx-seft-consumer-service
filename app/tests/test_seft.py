import unittest
import base64
import json
import filecmp

from app.tests.encrypter import Encrypter
from app.tests import test_settings
from app.decrypter import Decrypter
from app import settings


class SeftTests(unittest.TestCase):

    def test_encrypt_transfer_decrypt(self):
        with open("./test_files/testing.xls", "rb") as fb:
            contents = fb.read()
            encoded_contents = base64.b64encode(contents)

            payload = '{"file":"' + encoded_contents.decode() + '"}'
            print(payload)

            encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                                  test_settings.RAS_SEFT_PRIVATE_KEY,
                                  test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

            payload_as_json = json.loads(payload)
            jwt = encrypter.encrypt(payload_as_json)
            with open("./test_files/testing.jwt", "wb") as j:
                j.write(jwt)


            decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                  settings.SDX_SEFT_PRIVATE_KEY,
                                  settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

            decrypted_payload = decrypter.decrypt(jwt.decode())

            file_contents = decrypted_payload.get("file")
            print(file_contents)
            decoded_contents = base64.b64decode(file_contents)

            self.assertEquals(contents, decoded_contents)

        with open("./test_files/lewis.xls", "wb") as fb:
            fb.write(decoded_contents)

        self.assertTrue(filecmp.cmp("./test_files/book0.xlsx", "./test_files/test2.xlsx"))