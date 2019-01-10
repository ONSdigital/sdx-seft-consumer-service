import unittest

import requests
import responses
from sdc.rabbit.exceptions import QuarantinableError, RetryableError, BadMessageError

from app import settings
from app.anti_virus_check import AntiVirusCheck
from app.main import Payload


class AntiVirusCheckTests(unittest.TestCase):

    @responses.activate
    def test_api_key(self):
        settings.ANTI_VIRUS_API_KEY = "test"

        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id,
                      json={
                          'scan_results': {'scan_all_result_i': 0},
                          'process_info': {'progress_percentage': 100, 'result': 'Allowed'}
                      }, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        self.assertTrue(anti_virus.send_for_av_scan(payload))
        self.assertEqual(responses.calls[0].request.headers['apikey'], settings.ANTI_VIRUS_API_KEY)

    @responses.activate
    def test_send_for_av_scan_success(self):
        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id,
                      json={
                          'scan_results': {'scan_all_result_i': 0},
                          'process_info': {'progress_percentage': 100, 'result': 'Allowed'}
                      }, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        self.assertTrue(anti_virus.send_for_av_scan(payload))

    @responses.activate
    def test_send_for_av_scan_request_exception(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, body=requests.RequestException())

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_get_results_returns_request_exception(self):
        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id, body=requests.RequestException())

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            self.assertTrue(anti_virus.send_for_av_scan(payload))

    @responses.activate
    def test_send_for_av_scan_json_decode_error(self):
        # should be json not raw text so this should throw a retryable error
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json=None, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_type_error(self):
        # should be json not raw text so this should throw a retryable error
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, body='test', status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_failure(self):
        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id,
                      json={
                          'scan_results': {'scan_all_result_i': 0},
                          'process_info': {'progress_percentage': 100, 'result': 'Blocked'}
                      }, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(QuarantinableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_returns_err(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'err': 'unavailable'}, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_not_ready_hits_max_attempts(self):
        settings.ANTI_VIRUS_WAIT_TIME = 0.1
        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id,
                      json={
                          'scan_results': {'scan_all_result_i': 0},
                          'process_info': {'progress_percentage': 50, 'result': 'Allowed'}
                      }, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            self.assertTrue(anti_virus.send_for_av_scan(payload))

    @responses.activate
    def test_send_for_av_scan_forbidden_bad_api_key(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=401)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_bad_request(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=400)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(BadMessageError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_not_found(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=404)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_forbidden(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=403)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_internal_server_error(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=500)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_service_unavailable(self):
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, status=503)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)

    @responses.activate
    def test_send_for_av_scan_causes_type_error(self):
        data_id = '123'
        responses.add(responses.POST, settings.ANTI_VIRUS_BASE_URL, json={'data_id': data_id}, status=200)

        responses.add(responses.GET, settings.ANTI_VIRUS_BASE_URL + "/" + data_id,
                      json={
                          'scan_results': {'scan_all_result_i': 0},
                          'process_info': {'progress_percentage': 'incorrect-value', 'result': 'Allowed'}
                      }, status=200)

        anti_virus = AntiVirusCheck(tx_id=1)

        payload = Payload(decoded_contents="test", file_name="test", case_id="1", survey_id="1")

        with self.assertRaises(RetryableError):
            anti_virus.send_for_av_scan(payload)
