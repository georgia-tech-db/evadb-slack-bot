import os

import logging


def setup_logger(name):
    if not os.path.exists(".log"):
        os.mkdir(".log")

    logger = logging.getLogger(f"evadb_slack_bot_{name}_logger")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(f".log/{name}.log")
    fh.setLevel(logging.INFO)

    logger.addHandler(fh)
    return logger


QUERY_LOGGER = setup_logger("query")
APP_LOGGER = setup_logger("app")
