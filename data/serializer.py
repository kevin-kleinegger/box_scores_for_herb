"""Safe data serialization using JSON.

This module provides secure serialization and deserialization of data
for caching, replacing the unsafe ast.literal_eval() approach.
"""

import json
from datetime import datetime
from typing import Any, Optional
from utils.logger import Logger

logger = Logger.get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects.
    
    Converts datetime objects to ISO format strings for JSON serialization.
    """
    
    def default(self, obj):
        """Override default encoding for datetime objects.
        
        Args:
            obj: Object to encode
            
        Returns:
            ISO format string for datetime, or default encoding for other types
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class DataSerializer:
    """Handles safe serialization and deserialization of data using JSON.
    
    Provides secure alternatives to ast.literal_eval() with validation
    and error handling.
    """
    
    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to JSON string.
        
        Args:
            data: Python object to serialize (dict, list, primitives)
            
        Returns:
            JSON string representation of data
            
        Raises:
            TypeError: If data contains non-serializable types
            
        Example:
            json_str = DataSerializer.serialize({'key': 'value', 'count': 42})
        """
        try:
            return json.dumps(data, cls=DateTimeEncoder, indent=2)
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization failed: {e}", extra={'data_type': type(data).__name__})
            raise
    
    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Deserialize JSON string to Python object.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            Python object (dict, list, primitives), or empty dict on failure
            
        Example:
            data = DataSerializer.deserialize('{"key": "value"}')
        """
        if not json_str or not json_str.strip():
            logger.warning("Attempted to deserialize empty string")
            return {}
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Deserialization failed: {e}", extra={'json_preview': json_str[:100]})
            return {}
    
    @staticmethod
    def validate_structure(data: Any, expected_type: type) -> bool:
        """Validate deserialized data matches expected structure.
        
        Args:
            data: Deserialized data to validate
            expected_type: Expected Python type (dict, list, etc.)
            
        Returns:
            True if data matches expected type, False otherwise
            
        Example:
            is_valid = DataSerializer.validate_structure(data, dict)
        """
        is_valid = isinstance(data, expected_type)
        
        if not is_valid:
            logger.warning(
                f"Data structure validation failed",
                extra={
                    'expected_type': expected_type.__name__,
                    'actual_type': type(data).__name__
                }
            )
        
        return is_valid
