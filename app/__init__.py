import logging

import app.settings

from structlog import wrap_logger


__version__ = "2.3.2"

__service__ = "sdx-seft-consumer-service"

logging.basicConfig(format=app.settings.LOGGING_FORMAT,
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    level=app.settings.LOGGING_LEVEL)


def create_and_wrap_logger(logger_name):
    logger = wrap_logger(logging.getLogger(logger_name))
    logger.info("START", version=__version__)
    return logger
