import base64
import collections
from ftplib import Error as FTPException
import json
import os
import time

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from requests.packages.urllib3.exceptions import MaxRetryError
from sdc.crypto.decrypter import decrypt
from sdc.crypto.exceptions import CryptoError, InvalidTokenException
from sdc.crypto.key_store import KeyStore, validate_required_keys
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
from sdc.rabbit.consumers import MessageConsumer
from tornado.httpclient import AsyncHTTPClient, HTTPError
import tornado.httpserver
import tornado.ioloop
import tornado.web
import yaml

from app import create_and_wrap_logger
from app import settings
from app.sdxftp import SDXFTP
from app.settings import SERVICE_REQUEST_TOTAL_RETRIES, SERVICE_REQUEST_BACKOFF_FACTOR, RM_SDX_GATEWAY_URL
from app.settings import BASIC_AUTH


logger = create_and_wrap_logger(__name__)
HEALTHCHECK_DELAY_MILLISECONDS = settings.SEFT_CONSUMER_HEALTHCHECK_DELAY

KEY_PURPOSE_CONSUMER = "inbound"


class ConsumerError(Exception):
    pass


Payload = collections.namedtuple('Payload', 'decoded_contents file_name case_id survey_id')
AVResult = collections.namedtuple('AVResult', 'safe ready')


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

        bound_logger = logger.bind(tx_id=tx_id)
        bound_logger.debug("Message Received")
        try:
            bound_logger.info("Decrypting message")
            decrypted_payload = self._decrypt(encrypted_jwt, tx_id)

            bound_logger.info("Extracting file")

            payload = self.extract_file(decrypted_payload, tx_id)
            # self._send_receipt(payload.case_id, tx_id)

            bound_logger.info("Sending for AV check")
            data_id = self.send_for_anti_virus_check(payload.file_name, payload.decoded_contents)
            # data_id ="ZDE4MDExN0hKZzc0dUtGMkVNUzEtUU5fdHQyTno"

            bound_logger.info("Retrieve results")
            ready = False
            while not ready:
                results = self.get_anti_virus_result(data_id)
                ready = results.ready
                if not ready:
                    time.sleep(settings.ANTI_VIRUS_WAIT_TIME)
                elif not results.safe:
                    error = "Unsafe file detected for case id {} with filename {}".format(payload.case_id, payload.file_name)
                    bound_logger.error(error)
                    raise QuarantinableError()

            file_path = self._get_ftp_file_path(payload.survey_id)
            bound_logger.info("Send {} to ftp server.".format(payload.file_name))
            self._send_to_ftp(payload.decoded_contents, file_path, payload.file_name, tx_id)

        except QuarantinableError:
            bound_logger.error("Unable to process message")
            raise
        except TypeError:
            bound_logger.exception()
            raise

    def send_for_anti_virus_check(self, filename, contents):
        url = settings.ANTI_VIRUS_BASE_URL + "file"
        headers = {
            "apikey": settings.ANTI_VIRUS_API_KEY,
            "filename": filename,
        }
        response = requests.post(url=url, headers=headers, data=contents)
        logger.info("Response received {}".format(response.text))
        result = response.json()

        if result.get("err"):
            logger.error("Unable to send file for anti virus scan: {}".format(result.get("err")))
            logger.info("Waiting before attempting again")
            time.sleep(settings.ANTI_VIRUS_WAIT_TIME)
            logger.info("Return message to rabbit")
            raise RetryableError()
        else:
            data_id = result.get("data_id")
            logger.info("File sent successfully for anti virus scan", data_id=data_id)
            return data_id

    def get_anti_virus_result(self, data_id):
        ready = False
        safe = False

        url = settings.ANTI_VIRUS_BASE_URL + "file/" + data_id
        headers = {
            "apikey": settings.ANTI_VIRUS_API_KEY
        }

        response = requests.get(url=url, headers=headers)

        logger.info("Response from AV {}".format(response.text))

        result = response.json()
        scan_results = result.get("scan_results")

        if scan_results:
            progress_percentage = scan_results.get("progress_percentage")
            if 100 == int(progress_percentage):
                ready = True
                logger.info("Anti virus scan complete: {}".format(scan_results.get("scan_all_result_a")))
                scan_all_result_i = scan_results.get("scan_all_result_i")
                if int(scan_all_result_i) == 0:
                    logger.info("File is safe")
                    safe = True
                else:
                    logger.error("File is not safe")
            else:
                logger.info("Scan not yet complete")
        else:
            logger.info("Results not yet available")

        return AVResult(safe=safe, ready=ready)

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


class GetHealth:
    """This handles all the healthcheck functionality for the application.

       The status of the application is determined by the rabbitmq health and ftp health.
       This is done by performing a healthcheck on rabbitmq and checking the application
       has a live ftp connection. This check is done in the background after a delay.
       When the healthcheck endpoint endpoint is hit a 200 status is returned with
       app status as well as the dependencies of rabbitmq and ftp."""

    def __init__(self):
        self.ftp = SDXFTP(logger,
                          settings.FTP_HOST,
                          settings.FTP_USER,
                          settings.FTP_PASS,
                          settings.FTP_PORT,
                          )
        self.rabbit_status = False
        self.ftp_status = False
        self.app_health = False
        self.determine_health()

    @tornado.gen.coroutine
    def determine_rabbit_status(self):
        try:
            response = yield AsyncHTTPClient().fetch(settings.RABBIT_HEALTHCHECK_URL)

            self.rabbit_status_callback(response)

        except HTTPError as e:
            logger.error("Error receiving rabbit health ", error=str(e))
            raise tornado.gen.Return(None)
        except Exception as e:
            logger.error("Unknown exception occurred when receiving rabbit health", error=str(e))
            raise tornado.gen.Return(None)
        return

    def rabbit_status_callback(self, response):
        self.rabbit_status = False
        if response:
            resp = response.body.decode()
            res = json.loads(resp)
            status = res.get('status')
            logger.info("Rabbit MQ health check response {}".format(status))
            if status == "ok":
                logger.info("Rabbit MQ health ok")
                self.rabbit_status = True

    def determine_ftp_status(self):
        try:
            self.ftp_status = False
            conn = self.ftp.get_connection()
            if conn:
                logger.info("FTP health ok")
                self.ftp_status = True
        except FTPException as e:
            logger.error("FTP exception raised", error=str(e))
        except Exception as e:
            logger.error("Unknown exception occurred when receiving ftp health", error=str(e))

    def determine_health(self):
        self.determine_rabbit_status()
        self.determine_ftp_status()

        if self.rabbit_status and self.ftp_status:
            self.app_health = True
        else:
            self.app_health = False

        logger.info("Checked app health", app=self.app_health,
                    rabbit=self.rabbit_status, ftp=self.ftp_status)


class HealthCheck(tornado.web.RequestHandler):

    def __init__(self):
        self.set_health = None

    def initialize(self):
        self.set_health = GetHealth()

    def get(self):
        self.write({"status": self.set_health.app_health,
                    "dependencies": {"rabbitmq": self.set_health.rabbit_status,
                                     "ftp": self.set_health.ftp_status}})


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
