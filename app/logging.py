import logging
from .config.schemas import LoggingConfig


class MaxCoreFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.name = record.name.replace("max_core", "app.max_core", 1)
        return super().format(record)


def setup_logging(logging_config: LoggingConfig) -> None:
    base_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    base_formatter = logging.Formatter(base_format)

    # Root handler (everything except max_core)
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(base_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging_config.loglevel_default)
    root_logger.handlers = [root_handler]

    # max_core handler with special formatter
    max_core_handler = logging.StreamHandler()
    max_core_handler.setFormatter(MaxCoreFormatter(base_format))

    max_core_logger = logging.getLogger("max_core")
    max_core_logger.setLevel(logging_config.loglevel_app)
    max_core_logger.handlers = [max_core_handler]
    max_core_logger.propagate = False  # prevent double logging

    # other application loggers
    for name in ["app", "uvicorn"]:
        logger = logging.getLogger(name)
        logger.setLevel(logging_config.loglevel_app)
        logger.propagate = True
