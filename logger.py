import logging
import logging.handlers
import os


def _get_log_dir():
    # Avoid circular import - compute locally
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "logs")


def setup_logging():
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "weighlock.log")

    logger = logging.getLogger("weighlock")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    # file handler with rotation
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    ff = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh.setFormatter(ff)
    logger.addHandler(fh)

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(ff)
    logger.addHandler(ch)

    return logger


def get_logger(name="weighlock"):
    return logging.getLogger(name)