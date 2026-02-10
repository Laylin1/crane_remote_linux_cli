# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str = "crane_controller") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  
        return logger

    logger.setLevel(logging.DEBUG)

    # Консоль
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    ))

    logger.addHandler(console)

    return logger