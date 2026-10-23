"""
logger.py
=========================================
Unified logging utility.
"""

import os
from loguru import logger


def setup_logger(log_dir, name="train"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}.log")

    logger.remove()
    logger.add(log_file, level="INFO")
    logger.add(lambda msg: print(msg, end=""), level="INFO")

    return logger
