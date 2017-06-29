import json
import unittest

from app import settings
from app.decrypter import Decrypter
from app.tests import test_settings
from app.tests.encrypter import Encrypter


class DecrypterTests(unittest.TestCase):
    '''
    Tests for the encryption/decryption process
    '''

    def test_decrypt(self):
        encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY,
                              test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                              settings.SDX_SEFT_PRIVATE_KEY,
                              settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

        data = json.loads('{"test":"yay"}')

        encrypted_data = encrypter.encrypt(data)
        decrypted_data = decrypter.decrypt(encrypted_data.decode())

        self.assertEqual(data, decrypted_data)
