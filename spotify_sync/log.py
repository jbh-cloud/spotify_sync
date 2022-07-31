import errno
import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

ROOT_LOGGER = None
LOG_LEVEL = (
    os.environ["LOG_LEVEL"] if os.environ.get("LOG_LEVEL") is not None else "INFO"
)
LOG_PATH = (
    Path(os.environ["LOG_PATH"]) if os.environ.get("LOG_PATH") is not None else ""
)


def get_logger() -> logging.Logger:
    global ROOT_LOGGER

    if ROOT_LOGGER is None:
        # Configure root logger
        log_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-9s %(name)-16s : %(message)s"
        )
        ROOT_LOGGER = logging.getLogger()
        ROOT_LOGGER.setLevel(LOG_LEVEL)

        # Console logger, log to stdout instead of stderr
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(log_formatter)
        ROOT_LOGGER.addHandler(consoleHandler)

        # File logger
        if LOG_PATH == "":
            log_file = Path(os.getcwd()) / "spotify_sync.log"
        else:
            log_file = LOG_PATH

        if not os.path.exists(os.path.dirname(log_file)):
            try:
                os.makedirs(os.path.dirname(log_file))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        fileHandler = RotatingFileHandler(
            log_file, maxBytes=2097152, backupCount=5, encoding="utf-8"
        )

        fileHandler.setFormatter(log_formatter)
        ROOT_LOGGER.addHandler(fileHandler)

    return ROOT_LOGGER


def _setup_external_logging() -> None:
    # Set external module logging policy
    if LOG_LEVEL == "DEBUG":
        # logging.getLogger('urllib3').setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("spotipy").setLevel(logging.DEBUG)
        logging.getLogger("deemix").propagate = True
    else:
        # Decrease modules logging
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("spotipy").setLevel(logging.ERROR)
        logging.getLogger("deemix").propagate = False


_setup_external_logging()
