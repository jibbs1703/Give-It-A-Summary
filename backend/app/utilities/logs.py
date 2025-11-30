"""Give-It-A-Summary logging utility module."""

import logging
import sys
from pathlib import Path


def get_logger(
    name: str, level: int = logging.INFO, log_to_file: bool = False, log_dir: str = "logs"
) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        if log_to_file:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(Path(log_dir) / f"{name}.log")
            file_handler.setLevel(level)
            file_format = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)

    return logger
