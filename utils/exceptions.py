"""Custom exception classes for the baseball statistics application.

This module defines domain-specific exceptions for better error handling
and debugging throughout the application.
"""


class BaseballAppException(Exception):
    """Base exception for all application-specific errors.
    
    All custom exceptions in the application should inherit from this class
    to allow for centralized exception handling.
    """
    pass


class APIClientException(BaseballAppException):
    """Raised when API client encounters an error.
    
    This includes:
    - Network failures
    - HTTP errors (4xx, 5xx)
    - Timeout errors
    - Malformed API responses
    - Rate limiting
    
    Example:
        raise APIClientException("Failed to fetch player stats after 3 retries")
    """
    pass


class CacheException(BaseballAppException):
    """Raised when cache operations fail.
    
    This includes:
    - File system permission errors
    - Corrupted cache files
    - Disk space issues
    - Invalid cache keys
    
    Example:
        raise CacheException("Unable to write cache file: permission denied")
    """
    pass


class ValidationException(BaseballAppException):
    """Raised when input validation fails.
    
    This includes:
    - Invalid date formats
    - Future dates when past dates required
    - Missing required parameters
    - Invalid stat types
    
    Example:
        raise ValidationException("Date must be in the past, got: 2026-03-10")
    """
    pass


class ConfigurationException(BaseballAppException):
    """Raised when configuration is invalid or missing.
    
    This includes:
    - Missing configuration file
    - Invalid YAML syntax
    - Missing required configuration keys
    - Invalid configuration values
    
    Example:
        raise ConfigurationException("Missing required config key: api.base_url")
    """
    pass
