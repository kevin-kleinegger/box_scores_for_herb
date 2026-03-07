#!/usr/bin/env python3
"""Integration tests for LeaderboardGenerator"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.stats_calculator import StatsCalculator
from services.leaderboard_generator import LeaderboardGenerator
from utils.logger import Logger


@pytest.fixture
def leaderboard_generator():
    """Create LeaderboardGenerator instance for testing."""
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    stats_calculator = StatsCalculator()
    return LeaderboardGenerator(api_client, stats_calculator)


def test_generate_all_2024_season(leaderboard_generator):
    """Test generating all leaderboards for 2024 season."""
    leaderboards = leaderboard_generator.generate_all(season=2024)
    
    # Check we have all expected leaderboards
    expected_stats = ['AVG', 'HR', 'RBI', 'OPS', 'OBP', 'SLG', '2B', '3B', 'SB', 'R',  # Hitting
                      'ERA', 'W', 'K', 'SV', 'IP', 'WHIP',  # Pitching
                      'TBR', 'TBR+']  # Custom
    
    for stat in expected_stats:
        assert stat in leaderboards, f"{stat} leaderboard should be present"
        assert len(leaderboards[stat]) > 0, f"{stat} leaderboard should have players"
    
    # Check structure of a hitting leaderboard
    avg_leaders = leaderboards['AVG']
    first_player = avg_leaders[0]
    assert 'rank' in first_player
    assert 'player_name' in first_player
    assert 'team_abbr' in first_player
    assert 'stat_value' in first_player
    assert first_player['rank'] == 1, "First player should be rank 1"


def test_custom_stats_calculated(leaderboard_generator):
    """Test that TBR and TBR+ are calculated correctly."""
    leaderboards = leaderboard_generator.generate_all(season=2024)
    
    tbr_leaders = leaderboards['TBR']
    tbr_plus_leaders = leaderboards['TBR+']
    
    assert len(tbr_leaders) > 0, "TBR leaderboard should have players"
    assert len(tbr_plus_leaders) > 0, "TBR+ leaderboard should have players"
    
    # Check that values are numeric and reasonable
    first_tbr = float(tbr_leaders[0]['stat_value'])
    first_tbr_plus = float(tbr_plus_leaders[0]['stat_value'])
    
    assert first_tbr > 0, "TBR should be positive"
    assert first_tbr_plus > 0, "TBR+ should be positive"
    
    # TBR+ should generally be higher than TBR (includes runs and RBIs)
    assert first_tbr_plus > first_tbr, "TBR+ should be higher than TBR"


def test_current_season_detection(leaderboard_generator):
    """Test that current season is detected correctly."""
    # Call without season parameter - should detect current season
    leaderboards = leaderboard_generator.generate_all()
    
    # Should return 2024 season (since we're in March 2026 but 2026 season hasn't started)
    # We can verify by checking that we got data
    assert len(leaderboards) > 0, "Should generate leaderboards for detected season"
    assert 'AVG' in leaderboards, "Should have AVG leaderboard"


if __name__ == "__main__":
    # Allow running directly for quick manual testing
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    stats_calculator = StatsCalculator()
    generator = LeaderboardGenerator(api_client, stats_calculator)
    
    print("Test: Generate all leaderboards for 2024")
    leaderboards = generator.generate_all(season=2024)
    print(f"  Generated {len(leaderboards)} leaderboards")
    
    for stat_name in ['AVG', 'HR', 'TBR', 'TBR+']:
        leaders = leaderboards[stat_name]
        print(f"\n  {stat_name} Leaders (Top 3):")
        for player in leaders[:3]:
            print(f"    {player['rank']}. {player['player_name']} ({player['team_abbr']}): {player['stat_value']}")
