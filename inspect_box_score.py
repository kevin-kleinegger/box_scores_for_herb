#!/usr/bin/env python3
"""Quick script to inspect box score data structure"""

from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from utils.logger import Logger
import json

config = ConfigurationManager()
Logger.setup(config)
serializer = DataSerializer()
cache = CacheManager(config, serializer)
api_client = MLBStatsAPIClient(config, cache)

# Get a recent game
games = api_client.get_games_by_date("2026-03-05")
if games:
    game = games[0]
    print(f"Game: {game.away_team.name} @ {game.home_team.name}")
    print(f"Game ID: {game.game_id}")
    
    box_score = api_client.get_box_score(game.game_id)
    
    # Print top-level keys
    print("\nTop-level keys:")
    print(json.dumps(list(box_score.keys()), indent=2))
    
    # Print teams structure
    if 'teams' in box_score:
        print("\nTeams structure:")
        print(json.dumps(list(box_score['teams'].keys()), indent=2))
        
        if 'away' in box_score['teams']:
            print("\nAway team keys:")
            print(json.dumps(list(box_score['teams']['away'].keys()), indent=2))
