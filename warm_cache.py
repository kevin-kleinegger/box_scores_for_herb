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
    
    # Fetch box scores for last 7 days
    from datetime import datetime, timedelta
    
    logger.info("Fetching box scores for last 7 days...")
    box_score_gen = BoxScoreGenerator(api_client)
    
    for days_ago in range(7):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        try:
            box_scores, actual_date = box_score_gen.generate_for_date(date)
            logger.info(f"Cached {len(box_scores)} box scores for {actual_date}")
        except Exception as e:
            logger.warning(f"Failed to cache box scores for {date}: {e}")
    
    # Fetch current standings
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("Fetching standings...")
    standings_gen = StandingsGenerator(api_client)
    standings = standings_gen.generate_for_date(today)
    logger.info("Cached standings")
    
    # Fetch current season leaderboards
    logger.info("Fetching leaderboards...")
    leaderboard_gen = LeaderboardGenerator(api_client, stats_calculator)
    leaderboards = leaderboard_gen.generate_all()
    logger.info(f"Cached {len(leaderboards)} leaderboards")
    
    logger.info("Cache warming complete!")


if __name__ == "__main__":
    main()
