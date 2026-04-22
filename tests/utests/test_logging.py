import logging
import re
import pytest
from pytest import CaptureFixture
from app.logging import setup_logging
from app.config.schemas import LoggingConfig


@pytest.fixture
def logging_config() -> LoggingConfig:
    return LoggingConfig(loglevel_default="DEBUG", loglevel_app="INFO")


def test_max_core_logger_is_renamed(
    capsys: CaptureFixture[str], logging_config: LoggingConfig
) -> None:
    setup_logging(logging_config)
    logger = logging.getLogger("max_core.module")

    logger.info("Hello MaxCore")

    captured = capsys.readouterr()
    output: str = captured.err
    assert "Hello MaxCore" in output
    assert "app.max_core.module" in output


def test_random_logger(
    capsys: CaptureFixture[str], logging_config: LoggingConfig
) -> None:
    setup_logging(logging_config)
    logger = logging.getLogger("random.module")

    logger.info("Hello random logger")

    captured = capsys.readouterr()
    output = captured.err
    assert "Hello random logger" in output
    assert "random.module" in output


def test_root_logger_respects_default_level(
    capsys: CaptureFixture[str], logging_config: LoggingConfig
) -> None:
    setup_logging(logging_config)
    root_logger = logging.getLogger()

    root_logger.debug("Debug message")
    root_logger.info("Info message")

    captured = capsys.readouterr()
    output = captured.err
    assert "Debug message" in output
    assert "Info message" in output


def test_named_loggers_use_app_level(
    capsys: CaptureFixture[str], logging_config: LoggingConfig
) -> None:
    setup_logging(logging_config)
    for name in ["app", "max_core", "uvicorn"]:
        logger = logging.getLogger(name)
        logger.info(f"Test message for {name}")

    captured = capsys.readouterr()
    output = captured.err
    for name in ["app", "max_core", "uvicorn"]:
        assert f"Test message for {name}" in output
        expected_name = "app.max_core" if name == "max_core" else name
        assert expected_name in output


def test_multiple_loggers_together(
    capsys: CaptureFixture[str], logging_config: LoggingConfig
) -> None:
    setup_logging(logging_config)
    max_core_logger = logging.getLogger("max_core.module")
    other_logger = logging.getLogger("other.module")

    max_core_logger.info("Message 1")
    other_logger.info("Message 2")

    captured = capsys.readouterr()
    output = captured.err

    assert "Message 1" and "app.max_core.module" in output
    assert "Message 2" and "other.module" in output
