import logging
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parents[1] / "data"


# default setting for logger
logging.basicConfig(level=logging.INFO)
ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)-8s[%(name)s:%(filename)s:%(lineno)d:%(funcName)s:%(module)s] %(message)s"
)

# add formatter to ch
ch.setFormatter(formatter)


def get_logger(name):
    """Get logger with default setting."""
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.addHandler(ch)

    return logger
