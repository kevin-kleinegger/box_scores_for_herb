#!/usr/bin/env python3
"""Integration tests for StandingsGenerator"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.standings_generator import StandingsGenerator
from utils.logger import Logger


@pytest.fixture
def standings_generator():
    """Create StandingsGenerator instance for testing."""
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    return StandingsGenerator(api_client)


def test_regular_season_standings(standings_generator):
    """Test fetching standings on a regular season date."""
    result = standings_generator.generate_for_date("2024-07-01")
    
    assert result['date'] == "07/01/2024", "Should return formatted date"
    assert 'divisions' in result
    assert len(result['divisions']) > 0, "Should have divisions"
    assert result['highlighted_team'] == "New York Mets"
    
    # Check structure of divisions
    for division_name, teams in result['divisions'].items():
        assert len(teams) > 0, f"Division {division_name} should have teams"
        
        # Check first team structure
        first_team = teams[0]
        assert 'team' in first_team
        assert 'is_highlighted' in first_team
        
        # Verify team record has required fields
        team_record = first_team['team']
        assert hasattr(team_record, 'team_name')
        assert hasattr(team_record, 'wins')
        assert hasattr(team_record, 'losses')
        assert hasattr(team_record, 'winning_percentage')


def test_mets_highlighting(standings_generator):
    """Test that Mets are properly highlighted."""
    result = standings_generator.generate_for_date("2024-07-01")
    
    # Find the Mets in the standings
    mets_found = False
    for division_name, teams in result['divisions'].items():
        for team_data in teams:
            if team_data['team'].team_name == "New York Mets":
                assert team_data['is_highlighted'] == True, "Mets should be highlighted"
                mets_found = True
            else:
                assert team_data['is_highlighted'] == False, "Non-Mets teams should not be highlighted"
    
    assert mets_found, "Mets should be found in standings"


def test_custom_team_highlighting(standings_generator):
    """Test highlighting a different team."""
    result = standings_generator.generate_for_date("2024-07-01", highlight_team="New York Yankees")
    
    assert result['highlighted_team'] == "New York Yankees"
    
    # Find the Yankees in the standings
    yankees_found = False
    for division_name, teams in result['divisions'].items():
        for team_data in teams:
            if team_data['team'].team_name == "New York Yankees":
                assert team_data['is_highlighted'] == True, "Yankees should be highlighted"
                yankees_found = True
    
    assert yankees_found, "Yankees should be found in standings"


if __name__ == "__main__":
    # Allow running directly for quick manual testing
    config = ConfigurationManager()
    Logger.setup(config)
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    generator = StandingsGenerator(api_client)
    
    print("Test: Regular season standings (2024-07-01)")
    result = generator.generate_for_date("2024-07-01")
    print(f"  Date: {result['date']}")
    print(f"  Divisions: {len(result['divisions'])}")
    print(f"  Highlighted team: {result['highlighted_team']}")
    
    for division_name, teams in result['divisions'].items():
        print(f"\n  {division_name}:")
        for team_data in teams[:3]:  # Show top 3 teams
            team = team_data['team']
            print(f"    {team.division_rank}. {team.team_name}: {team.wins}-{team.losses}")
