from tornado import testing

import unittest
import pika
import pika.exceptions

from app.main import GetHealth
from app import settings


def rabbit_running():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))
        connection.channel()
        return True
    except pika.exceptions.AMQPError:
        return False


class HealthCheckTest(testing.AsyncTestCase):

    def setUp(self):
        super(HealthCheckTest, self).setUp()
        self.get_health = GetHealth()

    @unittest.skipIf(not rabbit_running(), 'Requires locally running rabbit server')
    @testing.gen_test(timeout=10)
    def test_get_rabbit_status(self):
        yield self.get_health.get_rabbit_status()
        self.assertEqual(self.get_health.rabbit_status, True)

    @unittest.skipIf(not rabbit_running(), 'Requires locally running rabbit server')
    def test_set_ftp_status(self):
        self.get_health.set_ftp_status()
        self.assertEqual(self.get_health.ftp_status, True)

    @unittest.skipIf(not rabbit_running(), 'Requires locally running rabbit server')
    @testing.gen_test(timeout=10)
    def test_get_health_app_health(self):
        # Set rabbit status to true
        yield self.get_health.get_rabbit_status()

        # Set App Health
        self.get_health.get_health()
        self.assertEqual(self.get_health.app_health, True)
