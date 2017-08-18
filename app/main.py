import base64

from app import create_and_wrap_logger
from app import settings
from app.decrypter import Decrypter, DecryptError
from app.sdxftp import SDXFTP
from sdc.rabbit.publisher import QueuePublisher
from sdc.rabbit.exceptions import QuarantinableError, RetryableError
from ftplib import Error

from sdc.rabbit.consumers import MessageConsumer

import tornado.web
import tornado.httpserver
from tornado.httpclient import HTTPClient, HTTPError
from threading import Thread, Event
import json
import os

logger = create_and_wrap_logger(__name__)
HEALTHCHECK_DELAY_SECONDS = settings.HEALTHCHECK_DELAY


class ConsumerError(Exception):
    pass


class SeftConsumer:
    def __init__(self):
        self._decrypter = Decrypter(settings.RAS_SEFT_CONSUMER_PUBLIC_KEY,
                                    settings.SDX_SEFT_CONSUMER_PRIVATE_KEY)
        self._ftp = SDXFTP(logger,
                           settings.FTP_HOST,
                           settings.FTP_USER,
                           settings.FTP_PASS,
                           settings.FTP_PORT)

        self.publisher = QueuePublisher(urls=settings.RABBIT_URLS, queue=settings.RABBIT_QUARANTINE_QUEUE)
        self.consumer = MessageConsumer(durable_queue=True, exchange=settings.RABBIT_EXCHANGE, exchange_type="topic",
                                        rabbit_queue=settings.RABBIT_QUEUE,
                                        rabbit_urls=settings.RABBIT_URLS, quarantine_publisher=self.publisher,
                                        process=self.process)

    def process(self, encrypted_jwt, tx_id=None):

        bound_logger = logger.bind(tx_id=tx_id)
        bound_logger.debug("Message Received")
        try:
            bound_logger.info("Decrypting message")
            decrypted_payload = self._decrypt(encrypted_jwt, tx_id)

            bound_logger.info("Extracting file")
            decoded_contents, file_name = self._extract_file(decrypted_payload, tx_id)

            bound_logger.info("Send {} to ftp server.".format(file_name))
            self._send_to_ftp(decoded_contents, file_name, tx_id)

        except QuarantinableError:
            bound_logger.error("Unable to process message")
            raise

    def _send_to_ftp(self, decoded_contents, file_name, tx_id):
        try:
            self._ftp.deliver_binary(settings.FTP_FOLDER, file_name, decoded_contents)
            logger.debug("Delivered to FTP server", tx_id=tx_id)
        except IOError as e:
            logger.error("Unable to deliver to the FTP server",
                         action="nack",
                         exception=e,
                         tx_id=tx_id)
            raise RetryableError()

    def _extract_file(self, decrypted_payload, tx_id):
        try:
            file_contents = decrypted_payload['file']
            file_name = decrypted_payload['filename']
            if not file_name or not file_contents:
                logger.error("Empty claims in message",
                             file_name=file_name,
                             file_contents="Encoded data" if file_contents else file_contents)
                raise ConsumerError()
            logger.debug("Decrypted file", file_name=file_name, tx_id=tx_id)
            decoded_contents = base64.b64decode(file_contents)
            return decoded_contents, file_name
        except (KeyError, ConsumerError) as e:
            logger.error("Required claims missing quarantining message",
                         exception=e,
                         keys=decrypted_payload.keys(),
                         action="quarantined",
                         tx_id=tx_id)
            raise QuarantinableError()

    def _decrypt(self, encrypted_jwt, tx_id):
        try:
            return self._decrypter.decrypt(encrypted_jwt)
        except (DecryptError, ValueError) as e:
            logger.error("Bad decrypt",
                         action="quarantined",
                         exception=e,
                         tx_id=tx_id)
            raise QuarantinableError()
        except Exception as e:
            logger.error("Failed to process",
                         action="retry",
                         exception=e,
                         tx_id=tx_id)
            raise QuarantinableError()

    def run(self):
        logger.debug("Starting consumer")
        self.consumer.run()

    def stop(self):
        logger.debug("Stopping consumer")
        self.consumer.stop()


class HealthCheck(tornado.web.RequestHandler):
    """This handles all the healthcheck functionality for the application.

       The status of the application is determined by the rabbitmq health and ftp health.
       This is done by performing a healthcheck on rabbitmq and checking the application
       has a live ftp connection. This check is done in the background after a delay.
       When the healthcheck endpoint endpoint is hit a 200 status is returned with
       app status as well as the dependencies of rabbitmq and ftp."""

    @staticmethod
    def rabbit_health():
        try:
            http_client = HTTPClient()
            resp = http_client.fetch(settings.RABBIT_HEALTHCHECK_URL,
                                     auth_username=settings.SEFT_RABBITMQ_MONITORING_USER,
                                     auth_password=settings.SEFT_RABBITMQ_MONITORING_PASS)
            body = json.loads(resp.body.decode('utf8'))
            status = body.get('status')
            if not status:
                status = "failed"
            return status
        except HTTPError as e:
            logger.error("Error receiving rabbit health " + str(e))

        return "failed"

    @staticmethod
    def ftp_health():
        ftp = SDXFTP(logger,
                     settings.FTP_HOST,
                     settings.FTP_USER,
                     settings.FTP_PASS,
                     settings.FTP_PORT)
        try:
            conn = ftp._connect()
            conn.voidcmd("NOOP")
            return "ok"
        except Error as e:
            logger.error("FTP error raised" + str(e))
            return "failed"

    def initialize(self):
        self.stop_flag = Event()
        thread = TimerThread(self.stop_flag)
        thread.run()

    def stop_timer(self):
        self.stop_flag.set()

    def get_health(self):
        self.rabbit_status = self.rabbit_health()
        self.ftp_status = self.ftp_health()
        if self.rabbit_status == "ok" and self.ftp_status == "ok":
            self.healthy = True
        else:
            self.healthy = False

    def get(self):
        self.write({"status": self.healthy,
                    "dependencies": {"rabbitmq": self.rabbit_status,
                                     "ftp": self.ftp_status}})


def make_app():
    return tornado.web.Application([
        (r"/healthcheck", HealthCheck),
    ])


class TimerThread(Thread):

    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(HEALTHCHECK_DELAY_SECONDS):
            HealthCheck.get_health()


def main():
    logger.debug("Starting SEFT consumer service")

    seft_consumer = SeftConsumer()
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.bind(int(os.getenv("PORT", '8080')))
    server.start(0)

    try:
        seft_consumer.run()
    except KeyboardInterrupt:
        logger.debug("SEFT consumer service stopping")
        seft_consumer.stop()
        logger.debug("SEFT consumer service stopped")


if __name__ == '__main__':
    main()
