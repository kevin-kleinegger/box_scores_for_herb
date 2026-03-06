"""Unit tests for ConfigurationManager."""

import os
import pytest
import tempfile
from config.config_manager import ConfigurationManager


class TestConfigurationManager:
    """Test suite for ConfigurationManager class."""
    
    def test_load_valid_configuration(self):
        """Test loading a valid configuration file."""
        config = ConfigurationManager("config/settings.yaml")
        
        # Verify configuration loaded
        assert config.get('cache.directory') == './cache'
        assert config.get('api.timeout') == 10
        assert config.get('api.base_url') == 'https://statsapi.mlb.com/api/v1'
    
    def test_get_with_default(self):
        """Test get() returns default for missing keys."""
        config = ConfigurationManager("config/settings.yaml")
        
        # Non-existent key should return default
        assert config.get('does.not.exist', 'default') == 'default'
        assert config.get('also.missing') is None
    
    def test_nested_key_access(self):
        """Test accessing nested configuration keys with dot notation."""
        config = ConfigurationManager("config/settings.yaml")
        
        # Test nested access
        assert config.get('cache.ttl.player_stats') == 3600
        assert config.get('cache.ttl.box_scores') == 86400
        assert config.get('theme.name') == 'newspaper'
    
    def test_convenience_methods(self):
        """Test convenience methods for common config access."""
        config = ConfigurationManager("config/settings.yaml")
        
        assert config.get_cache_dir() == './cache'
        assert config.get_api_timeout() == 10
        assert config.get_api_base_url() == 'https://statsapi.mlb.com/api/v1'
        assert config.get_cache_ttl('player_stats') == 3600
        assert config.get_cache_ttl('box_scores') == 86400
        
        theme = config.get_theme_settings()
        assert isinstance(theme, dict)
        assert theme['name'] == 'newspaper'
    
    def test_environment_variable_override(self):
        """Test environment variables override configuration values."""
        # Set environment variables
        os.environ['BASEBALL_API__TIMEOUT'] = '25'
        os.environ['BASEBALL_CACHE__DIRECTORY'] = '/custom/cache'
        
        try:
            config = ConfigurationManager("config/settings.yaml")
            
            # Environment variables should override config file
            assert config.get_api_timeout() == '25'  # Note: env vars are strings
            assert config.get_cache_dir() == '/custom/cache'
            
            # Non-overridden values should still work
            assert config.get_api_base_url() == 'https://statsapi.mlb.com/api/v1'
        finally:
            # Clean up environment variables
            del os.environ['BASEBALL_API__TIMEOUT']
            del os.environ['BASEBALL_CACHE__DIRECTORY']
    
    def test_missing_configuration_file(self):
        """Test error handling when configuration file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ConfigurationManager("nonexistent.yaml")
    
    def test_invalid_yaml(self):
        """Test error handling for invalid YAML syntax."""
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # yaml.YAMLError or similar
                ConfigurationManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_empty_configuration_file(self):
        """Test error handling for empty configuration file."""
        # Create a temporary empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Configuration file is empty"):
                ConfigurationManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_cache_ttl_with_default(self):
        """Test get_cache_ttl() returns default for unknown cache types."""
        config = ConfigurationManager("config/settings.yaml")
        
        # Unknown cache type should return default (3600)
        assert config.get_cache_ttl('unknown_type') == 3600
