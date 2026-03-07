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
            # Get the formatted text box score (like old implementation)
            box_score_text = self.api_client.get_box_score_text(game.game_id)
            
            # Get linescore data and format it
            linescore_text = self._create_linescore_string(game)
            
            is_mets = self._is_mets_game(game)
            
            game_data.append({
                'game': game,
                'linescore_text': linescore_text,
                'box_score_text': box_score_text,
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

    def _create_linescore_string(self, game: Game) -> str:
        """
        Create formatted linescore string showing inning-by-inning scoring.
        
        Format:
                1 2 3 4 5 6 7 8 9  -  R H E
        AWAY    0 1 0 2 0 0 0 0 1  -  4 8 0
        HOME    0 0 1 0 0 0 0 2 X  -  3 7 1
        
        Args:
            game: Game object with team information
            
        Returns:
            Formatted linescore string
        """
        try:
            # Fetch linescore data from API
            linescore = self.api_client.get_linescore(game.game_id)
            innings = linescore.get('innings', [])
            totals = linescore.get('teams', {})
            
            # Initialize strings
            header_string = ""
            away_string = ""
            home_string = ""
            
            # Build inning-by-inning scores
            for index, inning in enumerate(innings):
                away_runs = self._safely_get_stat(inning, 'away', 'runs')
                home_runs = self._safely_get_stat(inning, 'home', 'runs')
                
                # Normalize to same width
                away_runs_norm, home_runs_norm = self._normalize_strings(away_runs, home_runs)
                
                away_string += away_runs_norm + ' '
                home_string += home_runs_norm + ' '
                
                # Header shows inning number, normalized to match column width
                inning_num = str(index + 1)
                header_string += self._normalize_strings(inning_num, away_runs_norm)[0] + ' '
            
            # Get totals (R, H, E)
            away_runs_total = self._safely_get_stat(totals, 'away', 'runs')
            home_runs_total = self._safely_get_stat(totals, 'home', 'runs')
            away_hits = self._safely_get_stat(totals, 'away', 'hits')
            home_hits = self._safely_get_stat(totals, 'home', 'hits')
            away_errors = self._safely_get_stat(totals, 'away', 'errors')
            home_errors = self._safely_get_stat(totals, 'home', 'errors')
            
            # Normalize totals
            away_runs_norm, home_runs_norm = self._normalize_strings(away_runs_total, home_runs_total)
            away_hits_norm, home_hits_norm = self._normalize_strings(away_hits, home_hits)
            away_errors_norm, home_errors_norm = self._normalize_strings(away_errors, home_errors)
            
            # Add totals to strings
            away_string += " -  " + away_runs_norm + ' ' + away_hits_norm + ' ' + away_errors_norm
            home_string += " -  " + home_runs_norm + ' ' + home_hits_norm + ' ' + home_errors_norm
            
            # Build header with team names and column labels
            away_name = game.away_team.name
            home_name = game.home_team.name
            away_name_norm, home_name_norm = self._normalize_strings(away_name, home_name)
            
            # Header: leading space + inning numbers + totals labels
            leading_space = self._normalize_strings("", away_name_norm)[0]
            r_label = self._normalize_strings("R", away_runs_norm)[0]
            h_label = self._normalize_strings("H", away_hits_norm)[0]
            e_label = self._normalize_strings("E", away_errors_norm)[0]
            
            header_string = leading_space + '\t' + header_string + " -  " + r_label + ' ' + h_label + ' ' + e_label
            
            # Combine into final string
            return header_string + '\n' + away_name_norm + '\t' + away_string + '\n' + home_name_norm + '\t' + home_string + '\n'
            
        except Exception as e:
            self.logger.error(f"Failed to create linescore for game {game.game_id}: {e}")
            return ""
    
    def _safely_get_stat(self, data: dict, team: str, stat: str) -> str:
        """
        Safely extract stat from linescore data, returning 'X' if not found.
        
        Args:
            data: Dictionary containing team stats
            team: 'away' or 'home'
            stat: Stat name (e.g., 'runs', 'hits', 'errors')
            
        Returns:
            Stat value as string, or 'X' if not found
        """
        try:
            return str(data[team][stat])
        except (KeyError, TypeError):
            return "X"
    
    def _normalize_strings(self, s1: str, s2: str) -> Tuple[str, str]:
        """
        Equalize string lengths by adding leading whitespace to the shorter string.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Tuple of (s1, s2) with equal lengths
        """
        if len(s1) > len(s2):
            s2 = ' ' * (len(s1) - len(s2)) + s2
        elif len(s2) > len(s1):
            s1 = ' ' * (len(s2) - len(s1)) + s1
        
        return s1, s2
