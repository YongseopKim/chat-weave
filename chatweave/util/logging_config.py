"""Logging configuration for ChatWeave CLI."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configure logging for CLI.

    Args:
        verbose: Enable DEBUG level for console
        quiet: Suppress console output entirely
        log_file: Optional file path for logging

    Returns:
        Configured logger instance

    Examples:
        >>> logger = setup_logging(verbose=True)
        >>> logger.info("Processing started")
        INFO: Processing started

        >>> logger = setup_logging(quiet=True, log_file=Path("app.log"))
        >>> logger.info("This goes to file only")
    """
    logger = logging.getLogger("chatweave")
    logger.setLevel(logging.DEBUG)  # Capture all, handlers filter

    # Clear existing handlers
    logger.handlers.clear()

    # Prevent propagation to root logger
    logger.propagate = False

    # Console handler (unless quiet)
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = logging.DEBUG if verbose else logging.INFO
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(
            "%(message)s" if not verbose else "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Always capture everything
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
