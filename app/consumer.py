import base64
import logging

from sdx.common.async_consumer import AsyncConsumer
from structlog import wrap_logger

from app import settings
from app.decrypter import Decrypter
from app.sdxftp import SDXFTP

logger = wrap_logger(logging.getLogger(__name__))

'''
The AsyncConsumer will automatically pick up the RABBIT queue from a file called settings with var RABBIT_QUEUE
TODO this really needs to change
'''
QUEUE = settings.RABBIT_QUEUE


class Consumer(AsyncConsumer):

    def __init__(self, log=None):
        super().__init__(log)
        self._decrypter = Decrypter(settings.RAS_SEFT_PUBLIC_KEY,
                                    settings.SDX_SEFT_PRIVATE_KEY,
                                    settings.SDX_SEFT_PRIVATE_KEY_PASSWORD)

        self._ftp = SDXFTP(logger, settings.FTP_HOST, settings.FTP_USER, settings.FTP_PASS, settings.FTP_PORT)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        encrypted_jwt = body.decode("utf-8")
        
        decrypted_payload = self._decrypter.decrypt(encrypted_jwt)
        logger.debug("Decrypted file", decrypted_payload=decrypted_payload)

        file_contents = decrypted_payload.get("file")
        file_name = decrypted_payload.get("filename")

        decoded_contents = base64.b64decode(file_contents)

        with open("./seft_files/"+file_name, "wb") as fb:
            fb.write(decoded_contents)

        self._ftp.deliver_binary(settings.FTP_FOLDER, file_name, decoded_contents)


def main():
    consumer = Consumer()
    try:
        consumer.run()
    except KeyboardInterrupt:
        consumer.stop()

if __name__ == '__main__':
    main()
