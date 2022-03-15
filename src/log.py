import errno
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.environ["SPOTIFY_SYNC_LOG_LEVEL"] if os.environ.get("SPOTIFY_SYNC_LOG_LEVEL") is not None else 'INFO'
LOG_PATH = os.environ["SPOTIFY_SYNC_LOG_PATH"] if os.environ.get("SPOTIFY_SYNC_LOG_PATH") is not None else ''

# Configure root logger
logFormatter = logging.Formatter('[%(asctime)s] %(levelname)-9s %(name)-12s : %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(LOG_LEVEL)

# Console logger, log to stdout instead of stderr
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

# File logger
if LOG_PATH == '':
    log_file = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'logs', 'spotify_sync.log'))
else:
    log_file = LOG_PATH

if not os.path.exists(os.path.dirname(log_file)):
    try:
        os.makedirs(os.path.dirname(log_file))
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

fileHandler = RotatingFileHandler(
    log_file,
    maxBytes=2097152,
    backupCount=5,
    encoding='utf-8'
)

fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# Set external module logging policy
if LOG_LEVEL == 'DEBUG':
    #logging.getLogger('urllib3').setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('spotipy').setLevel(logging.DEBUG)
    logging.getLogger('deemix').propagate = True
else:
    # Decrease modules logging
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('spotipy').setLevel(logging.ERROR)
    logging.getLogger('deemix').propagate = False
