#!/usr/bin/env python3
"""
Cache warming script for box scores application.

This script pre-fetches all data needed for the website, warming the cache
so that user requests are served instantly. Designed to be run on a schedule
(e.g., daily at 6am) via PythonAnywhere scheduled tasks or cron.

Usage:
    python3 warm_cache.py
"""

from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.box_score_generator import BoxScoreGenerator
from services.standings_generator import StandingsGenerator
from services.leaderboard_generator import LeaderboardGenerator
from services.stats_calculator import StatsCalculator
from utils.logger import Logger


def main():
    """Warm the cache by fetching all data."""
    # Initialize dependencies
    config = ConfigurationManager()
    logger = Logger.setup(config)
    logger.info("Starting cache warming...")
    
    serializer = DataSerializer()
    cache = CacheManager(config, serializer)
    api_client = MLBStatsAPIClient(config, cache)
    stats_calculator = StatsCalculator()
    
    # Fetch today's box scores
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info("Fetching box scores...")
    box_score_gen = BoxScoreGenerator(api_client)
    box_scores, _ = box_score_gen.generate_for_date(today)
    logger.info(f"Cached {len(box_scores)} box scores")
    
    # Fetch current standings
    logger.info("Fetching standings...")
    standings_gen = StandingsGenerator(api_client)
    standings = standings_gen.generate_for_date(today)
    logger.info(f"Cached standings for {len(standings['divisions'])} divisions")
    
    # Fetch current season leaderboards
    logger.info("Fetching leaderboards...")
    leaderboard_gen = LeaderboardGenerator(api_client, stats_calculator)
    leaderboards = leaderboard_gen.generate_all()
    logger.info(f"Cached {len(leaderboards)} leaderboards")
    
    logger.info("Cache warming complete!")


if __name__ == "__main__":
    main()
