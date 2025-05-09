import logging
import sys
from typing import Optional


def setup_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Set up and configure a logger with the given name and log level.
    
    Args:
        name: The name of the logger
        log_level: The logging level (defaults to INFO if not specified)
        
    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = logging.INFO
        
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name. If it doesn't exist, create it.
    
    Args:
        name: The name of the logger
        
    Returns:
        Logger instance
    """
    return setup_logger(name)