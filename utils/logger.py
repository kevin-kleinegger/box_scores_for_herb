"""Structured logging setup for the baseball statistics application.

This module provides centralized logging configuration with support for
file output, log rotation, and structured context information.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Manages application logging with structured output and rotation.
    
    Provides a centralized way to configure logging across the application
    with support for different log levels, file output, and automatic rotation.
    """
    
    _configured = False
    
    @staticmethod
    def setup(config) -> logging.Logger:
        """Configure and return application logger.
        
        Sets up logging with:
        - Console output (stdout)
        - File output with rotation
        - Structured formatting with timestamps
        - Configurable log levels
        
        Args:
            config: ConfigurationManager instance with logging settings
            
        Returns:
            Configured root logger instance
        """
        if Logger._configured:
            return logging.getLogger()
        
        # Get configuration values
        log_level = config.get('logging.level', 'INFO')
        log_file = config.get('logging.file', './logs/app.log')
        max_bytes = config.get('logging.max_bytes', 10485760)  # 10MB default
        backup_count = config.get('logging.backup_count', 5)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Create formatter with timestamp and context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        Logger._configured = True
        
        root_logger.info(f"Logging configured: level={log_level}, file={log_file}")
        
        return root_logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance for specific module.
        
        Args:
            name: Logger name (typically __name__ from calling module)
            
        Returns:
            Logger instance for the specified name
            
        Example:
            logger = Logger.get_logger(__name__)
            logger.info("Processing started", extra={'user_id': 123})
        """
        return logging.getLogger(name)
