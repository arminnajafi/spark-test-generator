import logging
from pathlib import Path

ROOT_DIRECTORY = Path.cwd()


def set_up_logging():
    logging.basicConfig(level=logging.INFO)


set_up_logging()
