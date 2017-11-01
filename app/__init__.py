import logging

from sdx.common.logger_config import logger_initial_config
from structlog import wrap_logger

from app import settings

__version__ = "1.1.0"
__service__ = "sdx-seft-consumer-service"

logger_initial_config(service_name=__service__, log_level=settings.LOGGING_LEVEL)


def create_and_wrap_logger(logger_name):
    logger = wrap_logger(logging.getLogger(logger_name))
    logger.info("START", version=__version__)
    return logger
