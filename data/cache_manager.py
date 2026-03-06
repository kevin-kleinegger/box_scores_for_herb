"""File-based cache management with expiration and validation.

This module provides a robust caching system that stores data in files
with metadata for expiration tracking and validation.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional
from data.serializer import DataSerializer
from utils.logger import Logger
from utils.exceptions import CacheException

logger = Logger.get_logger(__name__)


class CacheManager:
    """Manages file-based caching with expiration and validation.
    
    Features:
    - File-based storage with JSON serialization
    - Automatic expiration based on TTL
    - SHA256 hashing of keys for safe filenames
    - Metadata tracking (timestamp, cache_type, key)
    - Automatic cache directory creation
    """
    
    def __init__(self, config, serializer: DataSerializer):
        """Initialize cache manager with configuration and serializer.
        
        Args:
            config: ConfigurationManager instance
            serializer: DataSerializer instance for JSON serialization
        """
        self.config = config
        self.serializer = serializer
        self.cache_dir = config.get_cache_dir()
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"Created cache directory: {self.cache_dir}")
            except OSError as e:
                raise CacheException(f"Failed to create cache directory: {e}")
    
    def get(self, key: str, cache_type: str) -> Optional[Any]:
        """Retrieve cached data if valid and not expired.
        
        Args:
            key: Cache key (will be hashed for filename)
            cache_type: Type of cache (e.g., 'player_stats', 'box_scores')
            
        Returns:
            Cached data if valid and not expired, None otherwise
            
        Example:
            data = cache.get('player_stats_2024', 'player_stats')
        """
        cache_path = self._get_cache_path(key)
        
        # Check if cache file exists
        if not os.path.exists(cache_path):
            logger.debug(f"Cache miss: {key}")
            return None
        
        try:
            # Read cache file
            with open(cache_path, 'r') as f:
                cache_content = f.read()
            
            # Deserialize cache entry
            cache_entry = self.serializer.deserialize(cache_content)
            
            # Validate structure
            if not self.serializer.validate_structure(cache_entry, dict):
                logger.warning(f"Invalid cache entry structure: {key}")
                return None
            
            # Check if required fields exist
            if 'metadata' not in cache_entry or 'data' not in cache_entry:
                logger.warning(f"Missing required fields in cache entry: {key}")
                return None
            
            # Check if expired
            if self._is_expired(cache_entry['metadata'], cache_type):
                logger.debug(f"Cache expired: {key}")
                return None
            
            logger.debug(f"Cache hit: {key}")
            return cache_entry['data']
            
        except (IOError, OSError) as e:
            logger.error(f"Cache read error: {e}", extra={'key': key})
            return None
        except Exception as e:
            logger.error(f"Unexpected cache error: {e}", extra={'key': key})
            return None
    
    def set(self, key: str, data: Any, cache_type: str) -> bool:
        """Store data in cache with metadata.
        
        Args:
            key: Cache key (will be hashed for filename)
            data: Data to cache (must be JSON-serializable)
            cache_type: Type of cache (e.g., 'player_stats', 'box_scores')
            
        Returns:
            True if successfully cached, False otherwise
            
        Example:
            success = cache.set('player_stats_2024', stats_data, 'player_stats')
        """
        cache_path = self._get_cache_path(key)
        
        # Create cache entry with metadata
        cache_entry = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'cache_type': cache_type,
                'key': key
            },
            'data': data
        }
        
        try:
            # Serialize cache entry
            cache_content = self.serializer.serialize(cache_entry)
            
            # Write to file
            with open(cache_path, 'w') as f:
                f.write(cache_content)
            
            logger.debug(f"Cache set: {key}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"Cache write error: {e}", extra={'key': key})
            raise CacheException(f"Failed to write cache file: {e}")
        except Exception as e:
            logger.error(f"Unexpected cache error: {e}", extra={'key': key})
            return False
    
    def invalidate(self, key: str) -> bool:
        """Remove specific cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if cache entry was removed, False if it didn't exist
            
        Example:
            cache.invalidate('player_stats_2024')
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return False
        
        try:
            os.remove(cache_path)
            logger.info(f"Cache invalidated: {key}")
            return True
        except OSError as e:
            logger.error(f"Failed to invalidate cache: {e}", extra={'key': key})
            return False
    
    def clear_expired(self) -> int:
        """Remove all expired cache entries.
        
        Returns:
            Number of cache entries removed
            
        Example:
            removed_count = cache.clear_expired()
        """
        if not os.path.exists(self.cache_dir):
            return 0
        
        removed_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                cache_path = os.path.join(self.cache_dir, filename)
                
                # Skip if not a file
                if not os.path.isfile(cache_path):
                    continue
                
                try:
                    # Read and check expiration
                    with open(cache_path, 'r') as f:
                        cache_content = f.read()
                    
                    cache_entry = self.serializer.deserialize(cache_content)
                    
                    if 'metadata' in cache_entry:
                        cache_type = cache_entry['metadata'].get('cache_type', 'unknown')
                        
                        if self._is_expired(cache_entry['metadata'], cache_type):
                            os.remove(cache_path)
                            removed_count += 1
                            logger.debug(f"Removed expired cache: {filename}")
                
                except Exception as e:
                    logger.warning(f"Error checking cache file {filename}: {e}")
                    continue
            
            if removed_count > 0:
                logger.info(f"Cleared {removed_count} expired cache entries")
            
            return removed_count
            
        except OSError as e:
            logger.error(f"Error clearing expired cache: {e}")
            return removed_count
    
    def _get_cache_path(self, key: str) -> str:
        """Generate file path for cache key using SHA256 hash.
        
        Args:
            key: Cache key
            
        Returns:
            Full path to cache file
        """
        # Use SHA256 hash to create safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")
    
    def _is_expired(self, metadata: dict, cache_type: str) -> bool:
        """Check if cache entry has expired based on TTL.
        
        Args:
            metadata: Cache entry metadata
            cache_type: Type of cache for TTL lookup
            
        Returns:
            True if expired, False otherwise
        """
        if 'created_at' not in metadata:
            return True
        
        try:
            created_at = datetime.fromisoformat(metadata['created_at'])
            ttl_seconds = self.config.get_cache_ttl(cache_type)
            expiration_time = created_at + timedelta(seconds=ttl_seconds)
            
            is_expired = datetime.now() > expiration_time
            
            if is_expired:
                logger.debug(
                    f"Cache expired",
                    extra={
                        'cache_type': cache_type,
                        'created_at': created_at.isoformat(),
                        'ttl_seconds': ttl_seconds
                    }
                )
            
            return is_expired
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid created_at timestamp: {e}")
            return True
