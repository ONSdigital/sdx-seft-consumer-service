import unittest

from app.tests.encrypter import Encrypter
from app.decrypter import Decrypter
from app import settings
from app.tests import test_settings
import json


class DecrypterTests(unittest.TestCase):

    def test_decrypt(self):
        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                              settings.SDX_SEFT_PRIVATE_KEY,
                              settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

        data = json.loads('{"test":"yay"}')

        encrypted_data = encrypter.encrypt(data)
        print(encrypted_data)

        decrypted_data = decrypter.decrypt(encrypted_data.decode())

        print(decrypted_data)
        self.assertEquals(data, decrypted_data)