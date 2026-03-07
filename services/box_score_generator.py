"""
Box Score Generator Service

Generates formatted box scores for MLB games on a given date.
Handles Mets game prioritization and offseason date fallback.
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from data.api_client import MLBStatsAPIClient
from models.game import Game
from utils.logger import Logger


class BoxScoreGenerator:
    """Generates box scores for MLB games with Mets prioritization."""
    
    def __init__(self, api_client: MLBStatsAPIClient):
        """
        Initialize BoxScoreGenerator.
        
        Args:
            api_client: MLBStatsAPIClient instance for fetching game data
        """
        self.api_client = api_client
        self.logger = Logger.get_logger(__name__)

    
    def generate_for_date(self, date: str) -> Tuple[List[dict], str]:
        """
        Generate box scores for all games on a given date.
        
        If no games are found (offseason), falls back to most recent game date.
        Prioritizes Mets games to appear first in the list.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Tuple of (list of game data dicts, actual date used)
            Each game dict contains:
                - game: Game object with basic game info
                - box_score: Raw box score data from API
                - is_mets_game: Boolean indicating if Mets are playing
        """
        self.logger.info(f"Generating box scores for date: {date}")
        
        # Fetch games for the requested date
        games = self.api_client.get_games_by_date(date)
        
        # If no games found, handle offseason by finding most recent game
        actual_date = date
        if not games:
            self.logger.info(f"No games found for {date}, searching for most recent game")
            actual_date = self._find_most_recent_game_date(date)
            games = self.api_client.get_games_by_date(actual_date)
            
        if not games:
            self.logger.warning(f"No games found even after offseason search")
            return [], actual_date
        
        # Fetch box score data for each game
        game_data = []
        for game in games:
            box_score = self.api_client.get_box_score(game.game_id)
            is_mets = self._is_mets_game(game)
            
            game_data.append({
                'game': game,
                'box_score': box_score,
                'is_mets_game': is_mets
            })
        
        # Prioritize Mets games
        game_data = self._prioritize_mets(game_data)
        
        self.logger.info(f"Generated {len(game_data)} box scores for {actual_date}")
        return game_data, actual_date



    
    def _find_most_recent_game_date(self, start_date: str) -> str:
        """
        Find the most recent date with games using coarse-to-fine search.
        
        Strategy:
        1. Jump back 7 days at a time until games are found
        2. Walk forward day-by-day to find exact last game date
        
        Args:
            start_date: Starting date in YYYY-MM-DD format
            
        Returns:
            Date string of most recent game in YYYY-MM-DD format
        """
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Phase 1: Coarse search - jump back weekly
        self.logger.debug("Starting coarse search (weekly jumps)")
        search_date = current_date
        games_found_date = None
        
        # Limit search to 1 year back to avoid infinite loop
        max_iterations = 52  # 52 weeks = 1 year
        iteration = 0
        
        while iteration < max_iterations:
            search_date = search_date - timedelta(days=7)
            date_str = search_date.strftime("%Y-%m-%d")
            
            games = self.api_client.get_games_by_date(date_str)
            if games:
                games_found_date = search_date
                self.logger.debug(f"Found games at {date_str} during coarse search")
                break
                
            iteration += 1
        
        if not games_found_date:
            self.logger.error("No games found in past year")
            return start_date
        
        # Phase 2: Fine search - walk forward day-by-day to find exact last game
        self.logger.debug("Starting fine search (daily walk forward)")
        last_game_date = games_found_date
        
        for day_offset in range(1, 8):  # Check up to 7 days forward
            check_date = games_found_date + timedelta(days=day_offset)
            
            # Don't check beyond the original start date
            if check_date > current_date:
                break
                
            date_str = check_date.strftime("%Y-%m-%d")
            games = self.api_client.get_games_by_date(date_str)
            
            if games:
                last_game_date = check_date
                self.logger.debug(f"Found more recent games at {date_str}")
        
        result = last_game_date.strftime("%Y-%m-%d")
        self.logger.info(f"Most recent game date: {result}")
        return result

    
    def _is_mets_game(self, game: Game) -> bool:
        """
        Check if the Mets are playing in this game.
        
        Args:
            game: Game object
            
        Returns:
            True if Mets are home or away team
        """
        return (game.away_team.name == "New York Mets" or 
                game.home_team.name == "New York Mets")
    
    def _prioritize_mets(self, game_data: List[dict]) -> List[dict]:
        """
        Sort games to put Mets games first.
        
        Args:
            game_data: List of game data dictionaries
            
        Returns:
            Sorted list with Mets games first, others in original order
        """
        mets_games = [g for g in game_data if g['is_mets_game']]
        other_games = [g for g in game_data if not g['is_mets_game']]
        
        return mets_games + other_games
