import unittest
from unittest.mock import patch
from app.main import SetHealth
from app.sdxftp import SDXFTP
from ftplib import Error
import pika
import pika.exceptions


def connect_to_rabbit():
    try:
        pika.BlockingConnection(pika.URLParameters('amqp://admin:admin@0.0.0.0:5672'))
        return "ok"
    except pika.exceptions.ConnectionClosed:
        return "fail"


class TestHealthCheck(unittest.TestCase):

    @unittest.skipIf(connect_to_rabbit() == "fail", "no running rabbitmq")
    def test_rabbit_mq_health_check(self):
        set_health = SetHealth()
        self.assertEqual(set_health.rabbit_status(), True)

    @patch.object(SDXFTP, '_connect')
    def test_ftp_healthcheck_success(self, mock_conn):
        set_health = SetHealth()
        self.assertEqual(set_health.ftp_status(), True)

    @patch.object(SDXFTP, '_connect', side_effect=Error)
    def test_on_ftp_healthcheck_error_ftp_health_fails(self, mock_conn):
        set_health = SetHealth()
        self.assertEqual(set_health.ftp_status(), False)
