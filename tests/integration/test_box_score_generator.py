#!/usr/bin/env python3
"""Integration tests for BoxScoreGenerator"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.box_score_generator import BoxScoreGenerator
from utils.logger import Logger


@pytest.fixture
def box_score_generator():
    """Create BoxScoreGenerator instance for testing."""
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    return BoxScoreGenerator(api_client)


def test_regular_season_date(box_score_generator):
    """Test fetching games on a regular season date."""
    game_data, actual_date = box_score_generator.generate_for_date("2024-07-01")
    
    assert len(game_data) > 0, "Should find games on regular season date"
    assert actual_date == "2024-07-01", "Should use requested date"
    
    # Check structure of returned data
    first_game = game_data[0]
    assert 'game' in first_game
    assert 'box_score' in first_game
    assert 'is_mets_game' in first_game
    
    # Verify game object has required attributes
    assert hasattr(first_game['game'], 'away_team')
    assert hasattr(first_game['game'], 'home_team')
    assert hasattr(first_game['game'], 'game_id')


def test_mets_prioritization(box_score_generator):
    """Test that Mets games appear first when present."""
    game_data, actual_date = box_score_generator.generate_for_date("2024-07-01")
    
    # July 1, 2024 had a Mets game (Mets @ Nationals)
    assert len(game_data) > 0
    first_game = game_data[0]
    
    # First game should be the Mets game
    assert first_game['is_mets_game'] == True, "Mets game should be prioritized first"
    game = first_game['game']
    assert (game.away_team.name == "New York Mets" or 
            game.home_team.name == "New York Mets")


def test_all_star_break_fallback(box_score_generator):
    """Test offseason handling during All-Star break."""
    game_data, actual_date = box_score_generator.generate_for_date("2024-07-15")
    
    # July 15, 2024 was All-Star break (no games)
    assert len(game_data) > 0, "Should find games by falling back"
    assert actual_date != "2024-07-15", "Should fall back to different date"
    assert actual_date == "2024-07-14", "Should fall back to July 14 (last game before break)"


def test_offseason_fallback(box_score_generator):
    """Test offseason handling in December."""
    game_data, actual_date = box_score_generator.generate_for_date("2024-12-01")
    
    # December 1, 2024 is offseason
    assert len(game_data) > 0, "Should find games by falling back"
    assert actual_date != "2024-12-01", "Should fall back to different date"
    
    # Should fall back to late October (World Series)
    assert actual_date.startswith("2024-10"), "Should fall back to October (end of season)"


if __name__ == "__main__":
    # Allow running directly for quick manual testing
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    generator = BoxScoreGenerator(api_client)
    
    print("Test 1: Regular season date (2024-07-01)")
    game_data, actual_date = generator.generate_for_date("2024-07-01")
    print(f"  Found {len(game_data)} games on {actual_date}")
    if game_data:
        print(f"  First game: {game_data[0]['game'].away_team.name} @ {game_data[0]['game'].home_team.name}")
        print(f"  Is Mets game first? {game_data[0]['is_mets_game']}")
    
    print("\nTest 2: All-Star break (2024-07-15)")
    game_data, actual_date = generator.generate_for_date("2024-07-15")
    print(f"  Found {len(game_data)} games on {actual_date}")
    print(f"  Fell back to: {actual_date}")
    
    print("\nTest 3: Offseason (2024-12-01)")
    game_data, actual_date = generator.generate_for_date("2024-12-01")
    print(f"  Found {len(game_data)} games on {actual_date}")
    print(f"  Fell back to: {actual_date}")
