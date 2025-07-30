"""Logging configuration for pixel detector."""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to
    """
    if format_string is None:
        # Default format includes timestamp, level, module name, and message
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(format_string))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# CLI-specific logging setup for cleaner output
def setup_cli_logging() -> None:
    """Set up logging for CLI with cleaner format."""
    # Simpler format for CLI output
    cli_format = "%(message)s"
    
    # Set up basic configuration
    logging.basicConfig(
        level=logging.INFO,
        format=cli_format,
        handlers=[]
    )
    
    # Console handler with custom formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(cli_format))
    
    # Add handler to root logger
    logging.getLogger().addHandler(console_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("pixel_detector").setLevel(logging.INFO)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)