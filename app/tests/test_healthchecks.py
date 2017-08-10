import unittest
from unittest.mock import patch
from app.main import HealthCheck
from app.sdxftp import SDXFTP
from ftplib import Error


class TestHealthCheck(unittest.TestCase):

    @unittest.skip("This test needs a locally running rabbit mq")
    def test_rabbit_mq_health_check(self):
        self.assertEqual(HealthCheck.rabbit_health(), "ok")

    @patch.object(SDXFTP, '_connect')
    def test_ftp_healthcheck_success(self, mock_conn):
        self.assertEqual(HealthCheck.ftp_health(), "ok")

    @patch.object(SDXFTP, '_connect', side_effect=Error)
    def test_on_ftp_healthcheck_error_ftp_health_fails(self, mock_conn):
        self.assertEqual(HealthCheck.ftp_health(), "failed")
