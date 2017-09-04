import datetime
import logging

from sdx.common.logger_config import logger_initial_config
from structlog import wrap_logger
from structlog.processors import JSONRenderer
from structlog.stdlib import filter_by_level, add_log_level

from app import settings

__version__ = "1.0.0"
__service__ = "sdx-seft-consumer-service"

logger_initial_config(service_name=__service__, log_level=settings.LOGGING_LEVEL)


def add_timestamp(_, __, event_dict):
    event_dict['created'] = datetime.datetime.utcnow().isoformat()
    return event_dict


def add_service_and_version(_, __, event_dict):
    event_dict['service'] = __service__
    event_dict['version'] = __version__
    return event_dict


def create_and_wrap_logger(logger_name):
    logger = wrap_logger(logging.getLogger(logger_name),
                         processors=[add_log_level,
                         filter_by_level,
                         add_timestamp,
                         add_service_and_version,
                         JSONRenderer(indent=1, sort_keys=True)])
    return logger
