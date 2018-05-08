import json
from ftplib import Error as FTPException

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.web import RequestHandler

from app import create_and_wrap_logger
from app import settings
from app.sdxftp import SDXFTP

logger = create_and_wrap_logger(__name__)


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

    @gen.coroutine
    def determine_rabbit_status(self):
        try:
            response = yield AsyncHTTPClient().fetch(settings.RABBIT_HEALTHCHECK_URL)

            self.rabbit_status_callback(response)

        except HTTPError as e:
            logger.error("Error receiving rabbit health ", error=str(e))
            raise gen.Return(None)
        except Exception as e:
            logger.error("Unknown exception occurred when receiving rabbit health", error=str(e))
            raise gen.Return(None)
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


class HealthCheck(RequestHandler):

    def get(self):
        health = GetHealth()
        self.write({"status": "OK"})
