from sdx.common.logger_config import logger_initial_config

from app import settings

__version__ = "1.0.0"

logger_initial_config(service_name='sdx-seft-consumer-service',
                      log_level=settings.LOGGING_LEVEL)