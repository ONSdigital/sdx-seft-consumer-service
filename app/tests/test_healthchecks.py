from tornado import testing

import unittest
import pika
import pika.exceptions
from ftplib import FTP

from app.main import GetHealth, make_app
from app import settings


def rabbit_running():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))
        connection.channel()
        return True
    except pika.exceptions.AMQPError:
        return False


def ftp_available():
    try:
        _conn = FTP()
        _conn.connect(settings.FTP_HOST, settings.FTP_PORT)
        _conn.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)
        return True
    except Exception as e:
        return False


class HealthCheckTest(testing.AsyncTestCase):

    def setUp(self):
        super(HealthCheckTest, self).setUp()
        self.get_health = GetHealth()

    @unittest.skipIf(not rabbit_running() or not ftp_available(), 'Requires locally running rabbit and ftp server')
    @testing.gen_test(timeout=10)
    def test_get_rabbit_status(self):
        yield self.get_health.get_rabbit_status()
        self.assertEqual(self.get_health.rabbit_status, True)

    @unittest.skipIf(not rabbit_running() or not ftp_available(), 'Requires locally running rabbit and ftp server')
    def test_set_ftp_status(self):
        self.get_health.set_ftp_status()
        self.assertEqual(self.get_health.ftp_status, True)

    @unittest.skipIf(not rabbit_running() or not ftp_available(), 'Requires locally running rabbit and ftp server')
    @testing.gen_test(timeout=10)
    def test_get_health_app_health(self):
        # Set rabbit status to true
        yield self.get_health.get_rabbit_status()

        # Set App Health
        self.get_health.get_health()
        self.assertEqual(self.get_health.app_health, True)


class TestHealthcheckEndpoint(testing.AsyncHTTPTestCase):

    def get_app(self):
        return make_app()

    @unittest.skipIf(not rabbit_running() or not ftp_available(), 'Requires locally running rabbit and ftp server')
    def test_healthcheck_endpoint(self):
        response = self.fetch('/healthcheck')

        self.assertEqual(response.code, 200)
