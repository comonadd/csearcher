import logging

# Logging
logger = logging.getLogger("codesearch")


def configure_loggers(daemon=False):
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.setLevel(logging.INFO)
    if daemon:
        # Log to file
        f_handler = logging.FileHandler("/var/log/codesearch-daemon.log")
        f_handler.setLevel(logging.INFO)
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)
