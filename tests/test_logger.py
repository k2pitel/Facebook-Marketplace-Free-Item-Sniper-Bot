import io
import logging

from utils.logger import get_logger


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger("test_logger_unique")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_unique"

    def test_does_not_add_duplicate_handlers(self):
        logger1 = get_logger("shared_logger")
        count1 = len(logger1.handlers)
        logger2 = get_logger("shared_logger")
        assert len(logger2.handlers) == count1

    def test_info_level_output(self, capsys):
        logger = get_logger("output_test_logger")
        logger.info("hello world")
        captured = capsys.readouterr()
        assert "hello world" in captured.out
