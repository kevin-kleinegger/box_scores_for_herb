"""Unit tests for DataSerializer."""

import json
from datetime import datetime
from data.serializer import DataSerializer


class TestDataSerializer:
    """Test suite for DataSerializer class."""
    
    def test_serialize_basic_dict(self):
        """Test serializing a basic dictionary."""
        data = {'name': 'Ohtani', 'hr': 44, 'team': 'Dodgers'}
        json_str = DataSerializer.serialize(data)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed == data
    
    def test_serialize_basic_list(self):
        """Test serializing a list."""
        data = ['Ohtani', 'Judge', 'Trout']
        json_str = DataSerializer.serialize(data)
        
        parsed = json.loads(json_str)
        assert parsed == data
    
    def test_serialize_nested_structure(self):
        """Test serializing nested dictionaries and lists."""
        data = {
            'player': 'Ohtani',
            'stats': {
                'batting': {'hr': 44, 'avg': 0.304},
                'pitching': {'era': 3.14, 'so': 167}
            },
            'teams': ['Angels', 'Dodgers']
        }
        json_str = DataSerializer.serialize(data)
        
        parsed = json.loads(json_str)
        assert parsed == data
        assert parsed['stats']['batting']['hr'] == 44
    
    def test_serialize_datetime(self):
        """Test serializing datetime objects."""
        now = datetime(2026, 3, 6, 12, 30, 45)
        data = {'timestamp': now, 'event': 'game_start'}
        
        json_str = DataSerializer.serialize(data)
        parsed = json.loads(json_str)
        
        # Datetime should be converted to ISO format string
        assert parsed['timestamp'] == '2026-03-06T12:30:45'
        assert parsed['event'] == 'game_start'
    
    def test_serialize_primitives(self):
        """Test serializing various primitive types."""
        data = {
            'string': 'hello',
            'integer': 42,
            'float': 3.14,
            'boolean': True,
            'null': None
        }
        json_str = DataSerializer.serialize(data)
        parsed = json.loads(json_str)
        
        assert parsed == data
    
    def test_deserialize_valid_json(self):
        """Test deserializing valid JSON string."""
        json_str = '{"player": "Judge", "hr": 62}'
        data = DataSerializer.deserialize(json_str)
        
        assert data == {'player': 'Judge', 'hr': 62}
    
    def test_deserialize_empty_string(self):
        """Test deserializing empty string returns empty dict."""
        result = DataSerializer.deserialize('')
        assert result == {}
        
        result = DataSerializer.deserialize('   ')
        assert result == {}
    
    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON returns empty dict."""
        invalid_json = 'not valid json {'
        result = DataSerializer.deserialize(invalid_json)
        
        assert result == {}
    
    def test_deserialize_malformed_json(self):
        """Test deserializing various malformed JSON strings."""
        malformed_cases = [
            '{key: value}',  # Missing quotes
            '{"key": undefined}',  # JavaScript undefined
            "{'key': 'value'}",  # Single quotes
            '{,}',  # Invalid syntax
        ]
        
        for case in malformed_cases:
            result = DataSerializer.deserialize(case)
            assert result == {}, f"Failed for case: {case}"
    
    def test_round_trip_serialization(self):
        """Test that serialize -> deserialize preserves data."""
        original = {
            'player': 'Trout',
            'stats': {'hr': 40, 'avg': 0.283},
            'active': True
        }
        
        # Serialize then deserialize
        json_str = DataSerializer.serialize(original)
        restored = DataSerializer.deserialize(json_str)
        
        assert restored == original
    
    def test_validate_structure_dict(self):
        """Test structure validation for dictionaries."""
        data = {'key': 'value'}
        
        assert DataSerializer.validate_structure(data, dict) is True
        assert DataSerializer.validate_structure(data, list) is False
        assert DataSerializer.validate_structure(data, str) is False
    
    def test_validate_structure_list(self):
        """Test structure validation for lists."""
        data = [1, 2, 3]
        
        assert DataSerializer.validate_structure(data, list) is True
        assert DataSerializer.validate_structure(data, dict) is False
    
    def test_validate_structure_primitives(self):
        """Test structure validation for primitive types."""
        assert DataSerializer.validate_structure('hello', str) is True
        assert DataSerializer.validate_structure(42, int) is True
        assert DataSerializer.validate_structure(3.14, float) is True
        assert DataSerializer.validate_structure(True, bool) is True
    
    def test_serialize_large_data(self):
        """Test serializing larger data structures."""
        # Create a list of 100 player records
        data = [
            {'player': f'Player{i}', 'hr': i, 'avg': 0.250 + (i * 0.001)}
            for i in range(100)
        ]
        
        json_str = DataSerializer.serialize(data)
        restored = DataSerializer.deserialize(json_str)
        
        assert len(restored) == 100
        assert restored[0]['player'] == 'Player0'
        assert restored[99]['player'] == 'Player99'
    
    def test_serialize_special_characters(self):
        """Test serializing strings with special characters."""
        data = {
            'name': 'José Ramírez',
            'team': 'Guardians',
            'quote': 'He said, "Great game!"',
            'newline': 'Line 1\nLine 2'
        }
        
        json_str = DataSerializer.serialize(data)
        restored = DataSerializer.deserialize(json_str)
        
        assert restored == data
        assert 'José' in restored['name']
