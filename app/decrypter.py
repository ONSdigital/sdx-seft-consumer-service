import base64

import jwt
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import AlreadyFinalized, InvalidKey, InvalidSignature, InvalidTag, UnsupportedAlgorithm, InternalError, NotYetFinalized

from app import create_and_wrap_logger

IV_EXPECTED_LENGTH = 12
CEK_EXPECT_LENGTH = 32


logger = create_and_wrap_logger(__name__)

# TODO this is a copy of the code in sdx-decrypt, we need to change this asap and either shift the code into sdx-common or
# allow decrypt to process both EQ and RAS files (preferable)


class DecryptError(Exception):
    pass


class Decrypter(object):
    def __init__(self, public_key, private_key, private_key_password):
        self.public_key = serialization.load_pem_public_key(
            public_key.encode(),
            backend=backend
        )
        self.private_key = serialization.load_pem_private_key(
            private_key.encode(),
            password=self._to_bytes(private_key_password),
            backend=backend
        )

    @staticmethod
    def _to_bytes(bytes_or_str):
        if isinstance(bytes_or_str, str):
            value = bytes_or_str.encode()
        else:
            value = bytes_or_str
        return value

    def decrypt(self, token):
        try:
            tokens = token.split('.')
            if len(tokens) != 5:
                raise ValueError("Incorrect number of tokens")
            jwe_protected_header = tokens[0]
            encrypted_key = tokens[1]
            encoded_iv = tokens[2]
            encoded_cipher_text = tokens[3]
            encoded_tag = tokens[4]

            decrypted_key = self._decrypt_key(encrypted_key)
            iv = self._base64_decode(encoded_iv)
            tag = self._base64_decode(encoded_tag)
            cipher_text = self._base64_decode(encoded_cipher_text)

            signed_token = self._decrypt_cipher_text(cipher_text, iv, decrypted_key, tag, jwe_protected_header)
            return jwt.decode(signed_token, self.public_key, algorithms=['RS256'])
        except (AlreadyFinalized, InvalidKey, InvalidSignature, InvalidTag, UnsupportedAlgorithm, InternalError, NotYetFinalized) as e:
            logger.error("Failed to decrypt message")
            logger.exception(e)
            raise DecryptError()

    def _decrypt_key(self, encrypted_key):
        decoded_key = self._base64_decode(encrypted_key)
        key = self.private_key.decrypt(decoded_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None))
        return key

    @staticmethod
    def _decrypt_cipher_text(cipher_text, iv, key, tag, jwe_protected_header):
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=backend)
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(jwe_protected_header.encode())
        decrypted_token = decryptor.update(cipher_text) + decryptor.finalize()
        return decrypted_token

    @staticmethod
    def _base64_decode(text):
        # if the text is not a multiple of 4 pad with trailing =
        # some base64 libraries don't pad data but Python is strict
        # and will throw a incorrect padding error if we don't do this
        if len(text) % 4 != 0:
            while len(text) % 4 != 0:
                text += "="
        return base64.urlsafe_b64decode(text)
