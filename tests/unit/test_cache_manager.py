"""Unit tests for CacheManager."""

import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from config.config_manager import ConfigurationManager
from data.serializer import DataSerializer
from data.cache_manager import CacheManager
from utils.exceptions import CacheException
import pytest


class TestCacheManager:
    """Test suite for CacheManager class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir, monkeypatch):
        """Create a CacheManager instance with temporary cache directory."""
        # Mock the config to use temp directory
        config = ConfigurationManager()
        monkeypatch.setenv('BASEBALL_CACHE__DIRECTORY', temp_cache_dir)
        
        # Reload config to pick up env var
        config = ConfigurationManager()
        serializer = DataSerializer()
        
        return CacheManager(config, serializer)
    
    def test_cache_directory_creation(self, temp_cache_dir):
        """Test that cache directory is created if it doesn't exist."""
        # Remove the temp directory
        shutil.rmtree(temp_cache_dir)
        assert not os.path.exists(temp_cache_dir)
        
        # Create cache manager - should create directory
        config = ConfigurationManager()
        config._config['cache']['directory'] = temp_cache_dir
        serializer = DataSerializer()
        cache = CacheManager(config, serializer)
        
        assert os.path.exists(temp_cache_dir)
    
    def test_set_and_get_cache(self, cache_manager):
        """Test basic cache set and get operations."""
        test_data = {'player': 'Ohtani', 'hr': 44}
        
        # Set cache
        success = cache_manager.set('test_key', test_data, 'player_stats')
        assert success is True
        
        # Get cache
        retrieved = cache_manager.get('test_key', 'player_stats')
        assert retrieved == test_data
    
    def test_cache_miss(self, cache_manager):
        """Test that non-existent cache returns None."""
        result = cache_manager.get('nonexistent_key', 'player_stats')
        assert result is None
    
    def test_cache_with_different_types(self, cache_manager):
        """Test caching different data types."""
        # Dict
        dict_data = {'key': 'value'}
        cache_manager.set('dict_key', dict_data, 'player_stats')
        assert cache_manager.get('dict_key', 'player_stats') == dict_data
        
        # List
        list_data = [1, 2, 3, 4, 5]
        cache_manager.set('list_key', list_data, 'player_stats')
        assert cache_manager.get('list_key', 'player_stats') == list_data
        
        # String
        string_data = 'test string'
        cache_manager.set('string_key', string_data, 'player_stats')
        assert cache_manager.get('string_key', 'player_stats') == string_data
    
    def test_cache_invalidation(self, cache_manager):
        """Test cache invalidation removes entry."""
        test_data = {'player': 'Judge'}
        
        # Set cache
        cache_manager.set('test_key', test_data, 'player_stats')
        assert cache_manager.get('test_key', 'player_stats') == test_data
        
        # Invalidate
        success = cache_manager.invalidate('test_key')
        assert success is True
        
        # Should return None after invalidation
        assert cache_manager.get('test_key', 'player_stats') is None
    
    def test_invalidate_nonexistent_key(self, cache_manager):
        """Test invalidating non-existent key returns False."""
        success = cache_manager.invalidate('nonexistent_key')
        assert success is False
    
    def test_multiple_cache_entries(self, cache_manager):
        """Test managing multiple cache entries."""
        # Set multiple entries
        cache_manager.set('player1', {'name': 'Ohtani'}, 'player_stats')
        cache_manager.set('player2', {'name': 'Judge'}, 'player_stats')
        cache_manager.set('game1', {'score': '5-3'}, 'box_scores')
        
        # Retrieve all
        assert cache_manager.get('player1', 'player_stats')['name'] == 'Ohtani'
        assert cache_manager.get('player2', 'player_stats')['name'] == 'Judge'
        assert cache_manager.get('game1', 'box_scores')['score'] == '5-3'
    
    def test_cache_expiration(self, cache_manager, monkeypatch):
        """Test that expired cache entries return None."""
        test_data = {'player': 'Trout'}
        
        # Set cache
        cache_manager.set('test_key', test_data, 'player_stats')
        
        # Mock the TTL to be very short (1 second)
        def mock_get_cache_ttl(cache_type):
            return 1  # 1 second TTL
        
        monkeypatch.setattr(cache_manager.config, 'get_cache_ttl', mock_get_cache_ttl)
        
        # Should still be valid immediately
        assert cache_manager.get('test_key', 'player_stats') == test_data
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache_manager.get('test_key', 'player_stats') is None
    
    def test_clear_expired_entries(self, cache_manager, monkeypatch):
        """Test clearing expired cache entries."""
        # Set multiple entries
        cache_manager.set('player1', {'name': 'Ohtani'}, 'player_stats')
        cache_manager.set('player2', {'name': 'Judge'}, 'player_stats')
        cache_manager.set('game1', {'score': '5-3'}, 'box_scores')
        
        # Mock TTL to be very short
        def mock_get_cache_ttl(cache_type):
            return 1  # 1 second TTL
        
        monkeypatch.setattr(cache_manager.config, 'get_cache_ttl', mock_get_cache_ttl)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Clear expired
        removed_count = cache_manager.clear_expired()
        assert removed_count == 3
        
        # All should be gone
        assert cache_manager.get('player1', 'player_stats') is None
        assert cache_manager.get('player2', 'player_stats') is None
        assert cache_manager.get('game1', 'box_scores') is None
    
    def test_corrupted_cache_file(self, cache_manager):
        """Test that corrupted cache files are handled gracefully."""
        # Create a corrupted cache file
        cache_path = cache_manager._get_cache_path('corrupted_key')
        with open(cache_path, 'w') as f:
            f.write('not valid json {')
        
        # Should return None for corrupted file
        result = cache_manager.get('corrupted_key', 'player_stats')
        assert result is None
    
    def test_cache_file_missing_metadata(self, cache_manager):
        """Test cache file with missing metadata field."""
        # Create cache file without metadata
        cache_path = cache_manager._get_cache_path('bad_key')
        with open(cache_path, 'w') as f:
            f.write('{"data": {"player": "Ohtani"}}')
        
        # Should return None
        result = cache_manager.get('bad_key', 'player_stats')
        assert result is None
    
    def test_cache_file_missing_data(self, cache_manager):
        """Test cache file with missing data field."""
        # Create cache file without data
        cache_path = cache_manager._get_cache_path('bad_key')
        with open(cache_path, 'w') as f:
            f.write('{"metadata": {"created_at": "2026-03-06T12:00:00", "cache_type": "player_stats", "key": "bad_key"}}')
        
        # Should return None
        result = cache_manager.get('bad_key', 'player_stats')
        assert result is None
    
    def test_sha256_hashing(self, cache_manager):
        """Test that cache keys are hashed with SHA256."""
        test_key = 'test_player_stats_2024'
        cache_path = cache_manager._get_cache_path(test_key)
        
        # Should be a SHA256 hash (64 hex characters)
        filename = os.path.basename(cache_path)
        hash_part = filename.replace('.json', '')
        assert len(hash_part) == 64
        assert all(c in '0123456789abcdef' for c in hash_part)
    
    def test_different_cache_types_different_ttl(self, cache_manager):
        """Test that different cache types can have different TTLs."""
        # player_stats has 3600 second TTL
        # box_scores has 86400 second TTL
        
        player_ttl = cache_manager.config.get_cache_ttl('player_stats')
        box_score_ttl = cache_manager.config.get_cache_ttl('box_scores')
        
        assert player_ttl == 3600
        assert box_score_ttl == 86400
        assert player_ttl != box_score_ttl
