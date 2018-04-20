import base64
import collections

import os


import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from requests.packages.urllib3.exceptions import MaxRetryError
from sdc.crypto.decrypter import decrypt
from sdc.crypto.exceptions import CryptoError, InvalidTokenException
from sdc.crypto.key_store import KeyStore, validate_required_keys
from sdc.rabbit.publishers import QueuePublisher
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
from sdc.rabbit.consumers import MessageConsumer

import tornado.httpserver
import tornado.ioloop
import tornado.web
import yaml

from app import create_and_wrap_logger
from app import settings
from app.anti_virus_check import AntiVirusCheck
from app.health import HealthCheck, GetHealth
from app.sdxftp import SDXFTP
from app.settings import SERVICE_REQUEST_TOTAL_RETRIES, SERVICE_REQUEST_BACKOFF_FACTOR, RM_SDX_GATEWAY_URL
from app.settings import BASIC_AUTH


logger = create_and_wrap_logger(__name__)
HEALTHCHECK_DELAY_MILLISECONDS = settings.SEFT_CONSUMER_HEALTHCHECK_DELAY

KEY_PURPOSE_CONSUMER = "inbound"


class ConfigurationError(Exception):
    pass


class ConsumerError(Exception):
    pass


Payload = collections.namedtuple('Payload', 'decoded_contents file_name case_id survey_id')


class SeftConsumer:

    @staticmethod
    def extract_file(decrypted_payload, tx_id):
        try:
            file_contents = decrypted_payload['file']
            file_name = decrypted_payload['filename']
            case_id = decrypted_payload['case_id']
            survey_id = decrypted_payload['survey_id']
            if not file_name or not file_contents or not case_id or not survey_id:
                logger.error("Empty claims in message",
                             file_name=file_name,
                             file_contents="Encoded data" if file_contents else file_contents,
                             case_id=case_id,
                             survey_id=survey_id)
                raise ConsumerError()
            logger.debug("Decrypted file", file_name=file_name,
                         tx_id=tx_id, case_id=case_id, survey_id=survey_id)
            decoded_contents = base64.b64decode(file_contents)
            return Payload(decoded_contents=decoded_contents, file_name=file_name, case_id=case_id, survey_id=survey_id)
        except (KeyError, ConsumerError) as e:
            logger.error("Required claims missing",
                         exception=str(e),
                         keys=decrypted_payload.keys(),
                         action="quarantining",
                         tx_id=tx_id)
            raise QuarantinableError()

    def __init__(self, keys):
        self.bound_logger = logger
        self.key_store = KeyStore(keys)

        self._ftp = SDXFTP(logger,
                           settings.FTP_HOST,
                           settings.FTP_USER,
                           settings.FTP_PASS,
                           settings.FTP_PORT)

        self.publisher = QueuePublisher(urls=settings.RABBIT_URLS,
                                        queue=settings.RABBIT_QUARANTINE_QUEUE)
        self.consumer = MessageConsumer(durable_queue=True, exchange=settings.RABBIT_EXCHANGE, exchange_type="topic",
                                        rabbit_queue=settings.RABBIT_QUEUE,
                                        rabbit_urls=settings.RABBIT_URLS, quarantine_publisher=self.publisher,
                                        process=self.process)
        self.session = requests.Session()
        retries = Retry(total=SERVICE_REQUEST_TOTAL_RETRIES,
                        backoff_factor=SERVICE_REQUEST_BACKOFF_FACTOR)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def process(self, encrypted_jwt, tx_id=None):

        self.bound_logger = self.bound_logger.bind(tx_id=tx_id)
        self.bound_logger.debug("Message Received")
        try:
            self.bound_logger.info("Decrypting message")
            decrypted_payload = self._decrypt(encrypted_jwt, tx_id)

            self.bound_logger.info("Extracting file")

            payload = self.extract_file(decrypted_payload, tx_id)
            self._send_receipt(payload.case_id, tx_id)

            if settings.ANTI_VIRUS_ENABLED:
                av_check = AntiVirusCheck(tx_id=tx_id)
                av_check.send_for_av_scan(payload)

            file_path = self._get_ftp_file_path(payload.survey_id)
            self.bound_logger.info("Sent to ftp server.", filename=payload.file_name)
            self._send_to_ftp(payload.decoded_contents, file_path, payload.file_name, tx_id)

        except QuarantinableError:
            self.bound_logger.error("Unable to process message")
            raise
        except TypeError:
            self.bound_logger.exception()
            raise

    def _send_to_ftp(self, decoded_contents, file_path, file_name, tx_id):
        try:
            self._ftp.deliver_binary(file_path, file_name, decoded_contents)
            logger.debug("Delivered to FTP server", tx_id=tx_id,
                         file_path=file_path, file_name=file_name)
        except IOError as e:
            logger.error("Unable to deliver to the FTP server",
                         action="nack",
                         exception=str(e),
                         tx_id=tx_id)
            raise RetryableError()

    def _decrypt(self, encrypted_jwt, tx_id):
        try:
            return decrypt(encrypted_jwt, self.key_store, KEY_PURPOSE_CONSUMER)
        except (InvalidTokenException, ValueError) as e:
            logger.error("Bad decrypt",
                         action="quarantining",
                         exception=str(e),
                         tx_id=tx_id)
            raise QuarantinableError()
        except Exception as e:
            logger.error("Failed to process",
                         action="retry",
                         exception=str(e),
                         tx_id=tx_id)
            raise QuarantinableError()

    def _send_receipt(self, case_id, tx_id):
        request_url = RM_SDX_GATEWAY_URL

        try:
            r = self.session.post(request_url, auth=BASIC_AUTH, json={'caseId': case_id})
        except MaxRetryError:
            logger.error("Max retries exceeded (5)", request_url=request_url,
                         tx_id=tx_id, case_id=case_id)
            raise RetryableError

        if r.status_code == 200 or r.status_code == 201:
            logger.info("RM sdx gateway receipt creation was a success",
                        request_url=request_url, tx_id=tx_id, case_id=case_id)
            return

        elif 400 <= r.status_code < 500:
            logger.error("RM sdx gateway returned client error, unable to receipt",
                         request_url=request_url,
                         status=r.status_code,
                         tx_id=tx_id)

        else:
            logger.error("Service error", request_url=request_url, tx_id=tx_id, case_id=case_id)
            raise RetryableError

    def run(self):
        logger.debug("Starting consumer")
        self.consumer.run()

    def stop(self):
        logger.debug("Stopping consumer")
        self.consumer.stop()

    @staticmethod
    def _get_ftp_file_path(survey_id):
        file_path = "{0}/{1}/unchecked".format(settings.FTP_FOLDER, survey_id)
        return file_path


def make_app():
    return tornado.web.Application([
        (r"/healthcheck", HealthCheck),
    ])


def main():
    logger.debug("Starting SEFT consumer service")

    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.bind(int(os.getenv("SDX_SEFT_CONSUMER_SERVICE_PORT", '8080')))
    server.start(0)

    with open(settings.SDX_SEFT_CONSUMER_KEYS_FILE) as file:
        keys = yaml.safe_load(file)

    try:

        # Create the scheduled health task

        task = GetHealth()
        sched = tornado.ioloop.PeriodicCallback(
            task.determine_health,
            HEALTHCHECK_DELAY_MILLISECONDS,
        )

        sched.start()
        logger.info("Scheduled healthcheck started.")

        # Get initial health
        loop = tornado.ioloop.IOLoop.current()
        loop.call_later(HEALTHCHECK_DELAY_MILLISECONDS, task.determine_health)

        validate_required_keys(keys, KEY_PURPOSE_CONSUMER)
        seft_consumer = SeftConsumer(keys)
        seft_consumer.run()

    except CryptoError as e:
        logger.critical("Unable to find valid keys", error=str(e))
    except KeyboardInterrupt:
        logger.debug("SEFT consumer service stopping")
        seft_consumer.stop()
        logger.debug("SEFT consumer service stopped")


if __name__ == '__main__':
    main()
