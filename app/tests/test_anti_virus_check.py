import unittest

import requests
import requests_mock
from sdc.rabbit.exceptions import QuarantinableError, RetryableError, BadMessageError

from app import settings
from app.anti_virus_check import AntiVirusCheck
from app.main import Payload

session = requests.Session()
adapter = requests_mock.Adapter()
session.mount('mock', adapter)


class AntiVirusCheckTests(unittest.TestCase):

    @requests_mock.mock()
    def test_send_for_av_scan_success(self, mock_request):
        data_id = '123'
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", json={'data_id': data_id})

        mock_request.get(settings.ANTI_VIRUS_BASE_URL + "file/" + data_id,
                         json={'scan_results': {'progress_percentage': 100, 'scan_all_result_i': 0}})

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        self.assertTrue(anti_virus.send_for_av_scan(payload))

    @requests_mock.mock()
    def test_send_for_av_scan_failure(self, mock_request):
        data_id = '123'
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", json={'data_id': data_id})

        mock_request.get(settings.ANTI_VIRUS_BASE_URL + "file/" + data_id,
                         json={'scan_results': {'progress_percentage': 100, 'scan_all_result_i': 1}})

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(QuarantinableError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_not_ready_hits_max_attempts(self, mock_request):
        settings.ANTI_VIRUS_WAIT_TIME = 0.1
        data_id = '123'
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", json={'data_id': data_id})

        mock_request.get(settings.ANTI_VIRUS_BASE_URL + "file/" + data_id,
                         json={'scan_results': {'progress_percentage': 50, 'scan_all_result_i': 0}})

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            self.assertTrue(anti_virus.send_for_av_scan(payload))

    @requests_mock.mock()
    def test_send_for_av_scan_forbidden_bad_api_key(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=401)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_bad_request(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=400)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(BadMessageError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_not_found(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=404)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_forbidden(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=403)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(BadMessageError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_internal_server_error(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=500)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @requests_mock.mock()
    def test_send_for_av_scan_service_unavailable(self, mock_request):
        mock_request.post(settings.ANTI_VIRUS_BASE_URL + "file", status_code=503)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)
