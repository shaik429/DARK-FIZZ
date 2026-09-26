"""Logging setup.

Full error details (stack traces) go to the server log only - never to the user.
"""

import logging
import sys

LOGGER_NAME = "stocksense"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:  # already set up (uvicorn --reload imports twice)
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
