"""Configuration management for the baseball statistics application.

This module provides centralized configuration loading from YAML files
with support for environment variable overrides.
"""

import os
import yaml
from typing import Any, Optional


class ConfigurationManager:
    """Manages application configuration from YAML file with environment overrides.
    
    Configuration can be overridden using environment variables with the prefix
    'BASEBALL_'. For nested keys, use double underscores.
    
    Example:
        BASEBALL_CACHE__DIRECTORY=/custom/cache
        BASEBALL_API__TIMEOUT=20
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to the YAML configuration file (relative to project root)
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        # Convert relative path to absolute path based on project root
        if not os.path.isabs(config_path):
            # Get the directory containing this file (config/)
            config_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to project root
            project_root = os.path.dirname(config_dir)
            # Join with the config path
            config_path = os.path.join(project_root, config_path)
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file.
        
        Returns:
            Dictionary containing configuration values
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ValueError(f"Configuration file is empty: {self.config_path}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default.
        
        Supports nested keys using dot notation (e.g., 'cache.directory').
        Checks for environment variable override first (BASEBALL_CACHE__DIRECTORY).
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default if not found
        """
        # Check for environment variable override
        env_key = f"BASEBALL_{key.upper().replace('.', '__')}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # Navigate nested dictionary using dot notation
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_cache_dir(self) -> str:
        """Get cache directory path.
        
        Returns:
            Absolute path to cache directory
        """
        cache_dir = self.get('cache.directory', './cache')
        
        # Convert relative path to absolute based on project root
        if not os.path.isabs(cache_dir):
            # Get project root (parent of config directory)
            config_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(config_dir)
            cache_dir = os.path.join(project_root, cache_dir)
        
        return cache_dir
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """Get cache TTL in seconds for specific cache type.
        
        Args:
            cache_type: Type of cache (e.g., 'player_stats', 'box_scores')
            
        Returns:
            TTL in seconds, defaults to 3600 (1 hour) if not configured
        """
        return self.get(f'cache.ttl.{cache_type}', 3600)
    
    def get_api_timeout(self) -> int:
        """Get API request timeout in seconds.
        
        Returns:
            Timeout in seconds
        """
        return self.get('api.timeout', 10)
    
    def get_api_base_url(self) -> str:
        """Get MLB StatsAPI base URL.
        
        Returns:
            Base URL for MLB StatsAPI
        """
        return self.get('api.base_url', 'https://statsapi.mlb.com/api/v1')
    
    def get_theme_settings(self) -> dict:
        """Get theme and styling configuration.
        
        Returns:
            Dictionary containing theme settings
        """
        return self.get('theme', {})
