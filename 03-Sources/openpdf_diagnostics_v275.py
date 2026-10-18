"""Centralized diagnostics, without document content logging. Author: Abdelhalim Talbi."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import traceback

LOGGER_NAME = "openpdf_studio"

def configure_logging(directory=None):
    if directory is None:
        directory = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "state") / "OpenPDF-Studio" / "logs"
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    expected_path = (directory / "openpdf.log").resolve()
    for existing in list(logger.handlers):
        if getattr(existing, "baseFilename", None) != str(expected_path):
            logger.removeHandler(existing)
            existing.close()
    if not logger.handlers:
        handler = RotatingFileHandler(directory / "openpdf.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger

def log_exception(logger, operation, error):
    """Log exception type and traceback; do not log PDF contents or input paths."""
    logger.error("Operation %s failed (%s)", operation, type(error).__name__)
    logger.debug("Exception detail: %s", "".join(traceback.format_exception(type(error), error, error.__traceback__)))
