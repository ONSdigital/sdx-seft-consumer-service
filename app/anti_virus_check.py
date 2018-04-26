import collections
import time

import requests
from sdc.rabbit.exceptions import QuarantinableError, RetryableError, BadMessageError

from app import create_and_wrap_logger
from app import settings

logger = create_and_wrap_logger(__name__)

AVResult = collections.namedtuple('AVResult', 'safe ready scan_results')


class AntiVirusCheck:
    def __init__(self, tx_id):
        self.bound_logger = logger.bind(tx_id=tx_id)

    def send_for_av_scan(self, payload):
        self.bound_logger.debug("A/V scanned enabled {}".format(settings.ANTI_VIRUS_ENABLED))
        self.bound_logger.info("Sending for AV check")
        data_id = self._send_for_anti_virus_check(payload.file_name, payload.decoded_contents)

        attempts = 0
        while attempts <= settings.ANTI_VIRUS_MAX_ATTEMPTS:
            attempts += 1
            results = self._get_anti_virus_result(data_id)
            if not results.ready:
                time.sleep(settings.ANTI_VIRUS_WAIT_TIME)
            elif not results.safe:
                error = "Unsafe file detected for case id {} with filename {}".format(payload.case_id,
                                                                                      payload.file_name)
                self._write_scan_report(results, payload.file_name)
                self.bound_logger.error(error)
                raise QuarantinableError()
            else:
                self.bound_logger.debug(
                    "File {} for case id {} has been virus checked and confirmed safe".format(payload.case_id,
                                                                                              payload.file_name))
                return True
        else:
            # out of attempts raise retryable error to force the response back to the queue.
            self.bound_logger.error(
                "Unable to get results of Anti-virus scan for case id {} and file {} ".format(payload.case_id,
                                                                                              payload.file_name))
            raise RetryableError()

    def _add_api_key(self, headers):
        # the API key is only needed for the online cloud service
        if settings.ANTI_VIRUS_API_KEY:
            self.bound_logger.debug("Setting A/V API key")
            headers['apikey'] = settings.ANTI_VIRUS_API_KEY

    def _check_av_response(self, response):
        if response.status_code != 200:
            if response.status_code == 401:
                self.bound_logger.critical("Invalid OPSWAT API Key - unable to continue")
                raise RetryableError()
            elif response.status_code == 404:
                # this could mean that the primary A/V server has failed and we've failed over to the backup
                # in this scenario we need to start over
                self.bound_logger.critical("OPSWAT AV does not know about this scan - the primary server may have failed")
                raise RetryableError()
            elif 400 <= response.status_code < 500:
                raise BadMessageError()
            elif 300 < response.status_code >= 500:
                raise RetryableError()
        else:
            self.bound_logger.info("Response from AV OK")

    def _send_for_anti_virus_check(self, filename, contents):
        url = settings.ANTI_VIRUS_BASE_URL + "file"
        headers = {
            "filename": filename,
        }
        self._add_api_key(headers)

        self.bound_logger.info("Sending for A/V scan", url=url)
        response = requests.post(url=url, headers=headers, data=contents)

        self._check_av_response(response)

        self.bound_logger.info("Response received {}".format(response.text))
        result = response.json()

        if result.get("err"):
            self.bound_logger.error("Unable to send file for anti virus scan: {}".format(result.get("err")))
            self.bound_logger.info("Waiting before attempting again")
            time.sleep(settings.ANTI_VIRUS_WAIT_TIME)
            self.bound_logger.info("Return message to rabbit")
            raise RetryableError()
        else:
            data_id = result.get("data_id")
            self.bound_logger.info("File sent successfully for anti virus scan", data_id=data_id)
            return data_id

    def _get_anti_virus_result(self, data_id):
        url = settings.ANTI_VIRUS_BASE_URL + "file/" + data_id
        headers = {}
        self._add_api_key(headers)

        self.bound_logger.info("Getting result for A/V scan", url=url)

        response = requests.get(url=url, headers=headers)

        self._check_av_response(response)

        self.bound_logger.info("Response from AV {}".format(response.text))

        result = response.json()
        scan_results = result.get("scan_results")

        ready = False
        safe = False

        if scan_results:
            progress_percentage = scan_results.get("progress_percentage")
            if int(progress_percentage) == 100:
                ready = True
                self.bound_logger.info("Anti virus scan complete: {}".format(scan_results.get("scan_all_result_a")))
                scan_all_result_i = scan_results.get("scan_all_result_i")
                if int(scan_all_result_i) == 0:
                    self.bound_logger.info("File is safe")
                    safe = True
                else:
                    self.bound_logger.error("File is not safe")
            else:
                self.bound_logger.info("Scan not yet complete")
        else:
            self.bound_logger.info("Results not yet available")

        return AVResult(safe=safe, ready=ready, scan_results=scan_results)

    def _write_scan_report(self, av_results, filename):
        self.bound_logger.info("Writing scan report for file {}".format(filename))
        self.bound_logger.error("A/V report", report=av_results.scan_results)
