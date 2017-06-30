import json
import unittest

from app import settings
from app.decrypter import Decrypter, DecryptError
from app.tests import test_settings
from app.tests.encrypter import Encrypter


class DecrypterTests(unittest.TestCase):
    '''
     Tests for the encryption/decryption process
    '''

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)
        self.encrypter = Encrypter(test_settings.SDX_SEFT_PUBLIC_KEY,
                                   test_settings.RAS_SEFT_PRIVATE_KEY,
                                   test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        self.decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                   settings.SDX_SEFT_PRIVATE_KEY,
                                   settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

    def test_decrypt(self):
        data = json.loads('{"test":"data"}')

        encrypted_data = self.encrypter.encrypt(data)
        decrypted_data = self.decrypter.decrypt(encrypted_data.decode())

        self.assertEqual(data, decrypted_data)

    @unittest.expectedFailure(DecryptError)
    def test_decrypt_throws_error_with_no_data(self):
        self.decrypter.decrypt(None)

    @unittest.expectedFailure(DecryptError)
    def test_decrypt_throws_error_with_incorrect_key_password(self):
        decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                              settings.SDX_SEFT_PRIVATE_KEY,
                              "incorrect password")

        data = json.loads('{"test":"data"}')
        encrypted_data = self.encrypter.encrypt(data)
        decrypter.decrypt(encrypted_data)

    @unittest.expectedFailure(DecryptError)
    def test_decrypt_throws_error_with_wrong_key_in_encryptor(self):
        self.encrypter = Encrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                   test_settings.RAS_SEFT_PRIVATE_KEY,
                                   test_settings.RAS_SEFT_PRIVATE_KEY_PASSWORD)

        data = json.loads('{"test":"data"}')
        encrypted_data = self.encrypter.encrypt(data)
        self.decrypter.decrypt(encrypted_data)
