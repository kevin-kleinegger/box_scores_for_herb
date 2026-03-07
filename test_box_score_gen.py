#!/usr/bin/env python3
"""Quick test of BoxScoreGenerator"""

from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.box_score_generator import BoxScoreGenerator
from utils.logger import Logger

# Initialize components
config = ConfigurationManager()
Logger.setup(config)
serializer = DataSerializer()
cache = CacheManager(config, serializer)
api_client = MLBStatsAPIClient(config, cache)
generator = BoxScoreGenerator(api_client)

# Test 1: Regular season date with games
print("Test 1: Regular season date (2024-07-01)")
game_data, actual_date = generator.generate_for_date("2024-07-01")
print(f"  Found {len(game_data)} games on {actual_date}")
if game_data:
    print(f"  First game: {game_data[0]['game'].away_team.name} @ {game_data[0]['game'].home_team.name}")
    print(f"  Is Mets game first? {game_data[0]['is_mets_game']}")

print()

# Test 2: All-Star break (no games)
print("Test 2: All-Star break (2024-07-15)")
game_data, actual_date = generator.generate_for_date("2024-07-15")
print(f"  Found {len(game_data)} games on {actual_date}")
print(f"  Fell back to: {actual_date}")

print()

# Test 3: Offseason date
print("Test 3: Offseason (2024-12-01)")
game_data, actual_date = generator.generate_for_date("2024-12-01")
print(f"  Found {len(game_data)} games on {actual_date}")
print(f"  Fell back to: {actual_date}")
