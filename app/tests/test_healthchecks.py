import unittest
from unittest.mock import patch
from app.main import SetHealth
from app.sdxftp import SDXFTP
from app import settings

import pika
import pika.exceptions


def rabbit_running():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))
        connection.channel()
        return True
    except pika.exceptions.AMQPError:
        return False


class TestHealthCheck(unittest.TestCase):

    @unittest.skipIf(not rabbit_running(), "This test requires a locally running rabbitmq")
    def test_rabbit_mq_health_check(self):
        set_health = SetHealth()
        self.assertEqual(set_health.rabbit_status, True)

    @patch.object(SDXFTP, '_connect')
    def test_ftp_healthcheck_success(self, mock_conn):
        set_health = SetHealth()
        self.assertEqual(set_health.ftp_status, True)
