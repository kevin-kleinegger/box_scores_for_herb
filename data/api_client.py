"""MLB StatsAPI client with retry logic and caching."""

import time
import requests
from typing import Optional, Dict, Any, Callable
from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from utils.logger import Logger
from utils.exceptions import APIClientException


logger = Logger.get_logger(__name__)


class MLBStatsAPIClient:
    """Client for interacting with MLB StatsAPI with retry logic and caching."""
    
    def __init__(self, config: ConfigurationManager, cache: CacheManager):
        """Initialize API client with configuration and cache.
        
        Args:
            config: Configuration manager instance
            cache: Cache manager instance
        """
        self.config = config
        self.cache = cache
        self.base_url = config.get_api_base_url()
        self.timeout = config.get_api_timeout()
        self.retry_attempts = config.get('api.retry_attempts', 3)
        self.retry_backoff_base = config.get('api.retry_backoff_base', 2)
        
        logger.info("MLBStatsAPIClient initialized", extra={
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts
        })
    
    def _retry_with_backoff(self, func: Callable, max_attempts: int = None) -> Any:
        """Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            max_attempts: Maximum number of retry attempts (uses config default if None)
            
        Returns:
            Result from successful function execution
            
        Raises:
            APIClientException: If all retry attempts fail
        """
        if max_attempts is None:
            max_attempts = self.retry_attempts
            
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except requests.RequestException as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    logger.error(f"API call failed after {max_attempts} attempts", extra={
                        "error": str(e),
                        "attempt": attempt + 1
                    })
                    raise APIClientException(
                        f"API request failed after {max_attempts} attempts: {str(e)}"
                    ) from e
                
                # Calculate wait time: base^attempt seconds
                wait_time = self.retry_backoff_base ** attempt
                logger.warning(f"API call failed, retrying in {wait_time}s", extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "wait_time": wait_time,
                    "error": str(e)
                })
                time.sleep(wait_time)
        
        # Should never reach here, but just in case
        raise APIClientException(f"Unexpected error in retry logic") from last_exception
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling.
        
        Args:
            endpoint: API endpoint path (e.g., "/schedule")
            params: Query parameters for the request
            
        Returns:
            JSON response as dictionary
            
        Raises:
            APIClientException: If request fails after all retries
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        logger.debug("Making API request", extra={
            "endpoint": endpoint,
            "params": params
        })
        
        start_time = time.time()
        
        def make_call():
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        
        try:
            result = self._retry_with_backoff(make_call)
            elapsed_time = time.time() - start_time
            
            logger.info("API request successful", extra={
                "endpoint": endpoint,
                "elapsed_time_ms": int(elapsed_time * 1000)
            })
            
            return result
            
        except APIClientException:
            elapsed_time = time.time() - start_time
            logger.error("API request failed", extra={
                "endpoint": endpoint,
                "elapsed_time_ms": int(elapsed_time * 1000)
            })
            raise

    
    def get_games_by_date(self, date: str):
        """Retrieve all games for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of Game objects for the specified date
            
        Raises:
            APIClientException: If API request fails
        """
        from models.game import Game, Team
        
        # Check cache first
        cache_key = f"games_{date}"
        cached_response = self.cache.get(cache_key, "box_scores")
        
        if cached_response is None:
            # Cache miss - fetch from API
            logger.debug(f"Cache miss for games on {date}, fetching from API")
            
            cached_response = self._make_request("/schedule", {
                "sportId": 1,
                "date": date
            })
            
            # Cache the raw API response
            self.cache.set(cache_key, cached_response, "box_scores")
        else:
            logger.debug(f"Cache hit for games on {date}")
        
        # Normalize response to Game objects (happens on both cache hit and miss)
        games = []
        if 'dates' in cached_response and len(cached_response['dates']) > 0:
            for game_data in cached_response['dates'][0].get('games', []):
                # Extract team info
                away_team_data = game_data['teams']['away']['team']
                home_team_data = game_data['teams']['home']['team']
                
                away_team = Team(
                    team_id=away_team_data['id'],
                    name=away_team_data['name'],
                    abbreviation=away_team_data.get('abbreviation', away_team_data['name'][:3].upper())
                )
                
                home_team = Team(
                    team_id=home_team_data['id'],
                    name=home_team_data['name'],
                    abbreviation=home_team_data.get('abbreviation', home_team_data['name'][:3].upper())
                )
                
                # Create Game object
                game = Game(
                    game_id=game_data['gamePk'],
                    game_date=date,
                    home_team=home_team,
                    away_team=away_team,
                    home_score=game_data['teams']['home'].get('score', 0),
                    away_score=game_data['teams']['away'].get('score', 0),
                    status=game_data['status']['detailedState'],
                    inning=game_data.get('linescore', {}).get('currentInning')
                )
                
                games.append(game)
        
        logger.info(f"Returning {len(games)} games for {date}")
        
        return games

    
    def get_box_score(self, game_id: int):
        """Retrieve detailed box score for a game.
        
        Args:
            game_id: MLB game ID (gamePk)
            
        Returns:
            BoxScore object with complete game details
            
        Raises:
            APIClientException: If API request fails
        """
        from models.game import BoxScore, BatterStats, PitcherStats, InningScore
        
        # Check cache first
        cache_key = f"box_score_{game_id}"
        cached_response = self.cache.get(cache_key, "box_scores")
        
        if cached_response is None:
            # Cache miss - fetch from API
            logger.debug(f"Cache miss for box score {game_id}, fetching from API")
            
            cached_response = self._make_request(f"/game/{game_id}/boxscore")
            
            # Cache the raw API response
            self.cache.set(cache_key, cached_response, "box_scores")
        else:
            logger.debug(f"Cache hit for box score {game_id}")
        
        # TODO: Normalize response to BoxScore object
        # For now, return the raw response
        logger.info(f"Returning box score for game {game_id}")
        
        return cached_response

    
    def get_standings(self, date: str):
        """Retrieve standings as of a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Raw API response with standings data (normalization deferred to StandingsGenerator)
            
        Raises:
            APIClientException: If API request fails
        """
        from datetime import datetime
        
        # Check cache first
        cache_key = f"standings_{date}"
        cached_response = self.cache.get(cache_key, "standings")
        
        if cached_response is None:
            # Cache miss - fetch from API
            logger.debug(f"Cache miss for standings on {date}, fetching from API")
            
            # Convert YYYY-MM-DD to MM/DD/YYYY for API
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            api_date = date_obj.strftime("%m/%d/%Y")
            year = date_obj.year
            
            cached_response = self._make_request("/standings", {
                "leagueId": "103,104",  # AL and NL
                "season": year,
                "date": api_date,
                "standingsTypes": "regularSeason",
                "hydrate": "team"  # Get full team names
            })
            
            # If no records returned (postseason date), get final regular season standings
            if 'records' not in cached_response or len(cached_response['records']) == 0:
                logger.debug(f"No standings for {date} (likely postseason), fetching final regular season standings")
                cached_response = self._make_request("/standings", {
                    "leagueId": "103,104",
                    "season": year,
                    "standingsTypes": "regularSeason",
                    "hydrate": "team"
                })
            
            # Cache the raw API response
            self.cache.set(cache_key, cached_response, "standings")
        else:
            logger.debug(f"Cache hit for standings on {date}")
        
        logger.info(f"Returning standings for {date}")
        
        return cached_response
