"""
Leaderboard Generator Service

Generates leaderboards for various baseball statistics using optimized API calls.
Uses /stats/leaders endpoint for standard stats and calculates custom stats (TBR, TBR+).
"""

from typing import List, Dict, Optional
from data.api_client import MLBStatsAPIClient
from services.stats_calculator import StatsCalculator
from utils.logger import Logger


class LeaderboardGenerator:
    """Generates stat leaderboards with optimized API usage."""
    
    def __init__(self, api_client: MLBStatsAPIClient, stats_calculator: StatsCalculator):
        """
        Initialize LeaderboardGenerator.
        
        Args:
            api_client: MLBStatsAPIClient instance for fetching data
            stats_calculator: StatsCalculator instance for custom stat calculations
        """
        self.api_client = api_client
        self.stats_calculator = stats_calculator
        self.logger = Logger.get_logger(__name__)

    
    # Standard stat categories that use /stats/leaders endpoint
    STANDARD_HITTING_STATS = [
        ('battingAverage', 'AVG'),
        ('homeRuns', 'HR'),
        ('runsBattedIn', 'RBI'),
        ('onBasePlusSlugging', 'OPS'),
        ('onBasePercentage', 'OBP'),
        ('sluggingPercentage', 'SLG'),
        ('doubles', '2B'),
        ('triples', '3B'),
        ('stolenBases', 'SB'),
        ('runs', 'R')
    ]
    
    STANDARD_PITCHING_STATS = [
        ('earnedRunAverage', 'ERA'),
        ('wins', 'W'),
        ('strikeouts', 'K'),
        ('saves', 'SV'),
        ('inningsPitched', 'IP'),
        ('walksAndHitsPerInningPitched', 'WHIP')
    ]
    
    # Pitching stats for starters (no saves)
    STARTER_PITCHING_STATS = [
        ('earnedRunAverage', 'ERA'),
        ('wins', 'W'),
        ('strikeouts', 'K'),
        ('inningsPitched', 'IP'),
        ('walksAndHitsPerInningPitched', 'WHIP')
    ]
    
    # Pitching stats for relievers (includes saves)
    RELIEVER_PITCHING_STATS = [
        ('earnedRunAverage', 'ERA'),
        ('wins', 'W'),
        ('strikeouts', 'K'),
        ('saves', 'SV'),
        ('inningsPitched', 'IP'),
        ('walksAndHitsPerInningPitched', 'WHIP')
    ]
    
    # Custom stats that need calculation
    CUSTOM_HITTING_STATS = ['TBR', 'TBR+']
    
    def generate_all(self, season: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Generate all leaderboards for a given season.
        
        Fetches standard stat leaders from API and calculates custom stats (TBR, TBR+).
        Splits pitching into separate starter and reliever leaderboards.
        
        Args:
            season: Season year (e.g., 2024). Defaults to current active season if None.
            
        Returns:
            Dictionary mapping stat name to list of player data:
            {
                'AVG': [{'player': PlayerStats, 'rank': 1, 'value': '.350'}, ...],
                'HR': [...],
                'TBR': [...],
                'SP_ERA': [...],  # Starting pitcher ERA
                'RP_ERA': [...],  # Relief pitcher ERA
                ...
            }
        """
        if season is None:
            season = self._get_current_season()
        
        self.logger.info(f"Generating all leaderboards for {season} season")
        
        leaderboards = {}
        
        # Generate standard hitting stat leaderboards
        for api_stat, display_name in self.STANDARD_HITTING_STATS:
            leaderboards[display_name] = self._generate_standard_leaderboard(
                api_stat, season, 'hitting', display_name
            )
        
        # Generate starting pitcher leaderboards
        for api_stat, display_name in self.STARTER_PITCHING_STATS:
            leaderboards[f'SP_{display_name}'] = self._generate_pitcher_leaderboard(
                api_stat, season, display_name, is_starter=True
            )
        
        # Generate relief pitcher leaderboards (fetch relievers once, then generate all stats)
        reliever_leaderboards = self._generate_reliever_leaderboards(season)
        leaderboards.update(reliever_leaderboards)
        
        # Generate custom hitting stat leaderboards (TBR, TBR+)
        # Use OPS leaders as base, then calculate TBR/TBR+
        leaderboards['TBR'], leaderboards['TBR+'] = self._generate_custom_leaderboards(season)
        
        self.logger.info(f"Generated {len(leaderboards)} leaderboards for {season}")
        
        return leaderboards
    
    def _get_current_season(self) -> int:
        """
        Determine the current active MLB season.
        
        Tries to fetch stat leaders for the current calendar year.
        If data exists, that's the active season. Otherwise, use previous year.
        
        Returns:
            Current active season year
        """
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # Try to get stat leaders for current year
        # If the season hasn't started, the API will return empty data
        try:
            response = self.api_client.get_stat_leaders('homeRuns', current_year, 'hitting', limit=1)
            
            # Check if we got actual leader data
            if response and 'leagueLeaders' in response and len(response['leagueLeaders']) > 0:
                leaders = response['leagueLeaders'][0].get('leaders', [])
                if len(leaders) > 0:
                    # We have data for current year, season is active
                    self.logger.debug(f"Stat leaders found for {current_year}, using {current_year} season")
                    return current_year
        except Exception as e:
            self.logger.debug(f"Error checking {current_year} season: {e}")
        
        # No data for current year, use previous year
        self.logger.debug(f"No stat leaders for {current_year}, using {current_year - 1} season")
        return current_year - 1

    
    def _generate_standard_leaderboard(self, api_stat: str, season: int, stat_group: str, display_name: str) -> List[Dict]:
        """
        Generate leaderboard for a standard stat using /stats/leaders endpoint.
        
        Args:
            api_stat: API stat name (e.g., 'battingAverage', 'homeRuns')
            season: Season year
            stat_group: 'hitting' or 'pitching'
            display_name: Display name for the stat (e.g., 'AVG', 'HR')
            
        Returns:
            List of player data dictionaries with rank, player info, and stat value
        """
        from models.player_stats import PlayerStats
        
        # Fetch leaders from API
        response = self.api_client.get_stat_leaders(api_stat, season, stat_group, limit=100)
        
        if not response or 'leagueLeaders' not in response:
            self.logger.warning(f"No leaders data for {display_name} in {season}")
            return []
        
        leaderboard = []
        
        for league_data in response['leagueLeaders']:
            for leader in league_data.get('leaders', []):
                rank = leader.get('rank', 0)
                value = leader.get('value', '0')
                person = leader.get('person', {})
                team = leader.get('team', {})
                
                # Get team abbreviation, fallback to generating from name
                team_abbr = team.get('abbreviation') or team.get('teamCode') or self._get_team_abbr(team.get('name', 'Unknown'))
                
                # Create simplified player data
                player_data = {
                    'rank': rank,
                    'player_id': person.get('id', 0),
                    'player_name': person.get('fullName', 'Unknown'),
                    'team_name': team.get('name', 'Unknown'),
                    'team_abbr': team_abbr,
                    'stat_value': value,
                    'stat_name': display_name
                }
                
                leaderboard.append(player_data)
        
        self.logger.debug(f"Generated {display_name} leaderboard with {len(leaderboard)} players")
        return leaderboard
    
    def _generate_pitcher_leaderboard(self, api_stat: str, season: int, display_name: str, is_starter: bool) -> List[Dict]:
        """
        Generate leaderboard for pitchers (starters or relievers) with role-specific qualification.
        
        Qualification thresholds:
        - Starters: 1.0 IP per team game
        - Relievers: 0.3 IP per team game
        
        Args:
            api_stat: API stat name (e.g., 'earnedRunAverage', 'strikeouts')
            season: Season year
            display_name: Display name for the stat (e.g., 'ERA', 'K')
            is_starter: True for starters, False for relievers
            
        Returns:
            List of player data dictionaries with rank, player info, and stat value
        """
        # Fetch more pitchers for relievers since they're less common in top rankings
        # Keep fetching in batches of 100 until we have 20 qualified players
        limit = 100
        max_fetch = 500  # Maximum pitchers to check
        response = self.api_client.get_stat_leaders(api_stat, season, 'pitching', limit=max_fetch if not is_starter else limit)
        
        if not response or 'leagueLeaders' not in response:
            self.logger.warning(f"No leaders data for {display_name} in {season}")
            return []
        
        # Get team games played for qualification threshold
        team_games = self._get_team_games_played(season)
        qualification_threshold = team_games * (1.0 if is_starter else 0.3)
        
        leaderboard = []
        
        for league_data in response['leagueLeaders']:
            for leader in league_data.get('leaders', []):
                person = leader.get('person', {})
                team = leader.get('team', {})
                player_id = person.get('id', 0)
                
                if player_id == 0:
                    continue
                
                # Fetch full stats to determine starter/reliever and check qualification
                try:
                    stats_response = self.api_client.get_player_season_stats(player_id, season, 'pitching')
                    
                    if 'stats' in stats_response and len(stats_response['stats']) > 0:
                        splits = stats_response['stats'][0].get('splits', [])
                        if len(splits) > 0:
                            stats = splits[0].get('stat', {})
                            
                            # Check if pitcher matches the role we're looking for
                            pitcher_is_reliever = self._is_reliever(stats)
                            if is_starter and pitcher_is_reliever:
                                continue  # Skip relievers when generating starter leaderboard
                            if not is_starter and not pitcher_is_reliever:
                                continue  # Skip starters when generating reliever leaderboard
                            
                            # Check qualification threshold
                            innings_pitched = float(stats.get('inningsPitched', '0'))
                            if innings_pitched < qualification_threshold:
                                continue  # Not qualified
                            
                            # Get the stat value
                            value = leader.get('value', '0')
                            team_abbr = team.get('abbreviation') or team.get('teamCode') or self._get_team_abbr(team.get('name', 'Unknown'))
                            
                            player_data = {
                                'player_id': player_id,
                                'player_name': person.get('fullName', 'Unknown'),
                                'team_name': team.get('name', 'Unknown'),
                                'team_abbr': team_abbr,
                                'stat_value': value,
                                'stat_name': display_name
                            }
                            
                            leaderboard.append(player_data)
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for pitcher {player_id}: {e}")
                    continue
        
        # Sort by stat value (ERA and WHIP ascending, others descending)
        reverse_sort = display_name not in ['ERA', 'WHIP']
        leaderboard.sort(key=lambda x: float(x['stat_value']), reverse=reverse_sort)
        
        # Add ranks and limit to top 20
        for rank, player in enumerate(leaderboard[:20], 1):
            player['rank'] = rank
        
        role = "starter" if is_starter else "reliever"
        self.logger.debug(f"Generated {display_name} {role} leaderboard with {len(leaderboard[:20])} players")
        
        return leaderboard[:20]
    
    def _generate_reliever_leaderboards(self, season: int) -> Dict[str, List[Dict]]:
        """
        Generate all reliever leaderboards by fetching relievers once.
        
        Strategy:
        1. Fetch top 200 pitchers by games played (relievers play more games)
        2. Filter for actual relievers using _is_reliever()
        3. Filter for qualified (0.3 IP per team game)
        4. Generate all 6 stat leaderboards from this pool
        
        Args:
            season: Season year
            
        Returns:
            Dictionary with RP_ERA, RP_W, RP_K, RP_SV, RP_IP, RP_WHIP leaderboards
        """
        self.logger.info(f"Fetching qualified relievers for {season}")
        
        # Fetch top 200 pitchers by games played
        response = self.api_client.get_stat_leaders('gamesPlayed', season, 'pitching', limit=200)
        
        if not response or 'leagueLeaders' not in response:
            self.logger.warning(f"No games played leaders for {season}")
            return {}
        
        # Get qualification threshold
        team_games = self._get_team_games_played(season)
        qualification_threshold = team_games * 0.3
        
        qualified_relievers = []
        
        # Process each pitcher
        for league_data in response['leagueLeaders']:
            for leader in league_data.get('leaders', []):
                person = leader.get('person', {})
                team = leader.get('team', {})
                player_id = person.get('id', 0)
                
                if player_id == 0:
                    continue
                
                try:
                    # Fetch full stats
                    stats_response = self.api_client.get_player_season_stats(player_id, season, 'pitching')
                    
                    if 'stats' in stats_response and len(stats_response['stats']) > 0:
                        splits = stats_response['stats'][0].get('splits', [])
                        if len(splits) > 0:
                            stats = splits[0].get('stat', {})
                            
                            # Check if reliever
                            if not self._is_reliever(stats):
                                continue
                            
                            # Check qualification
                            innings_pitched = float(stats.get('inningsPitched', '0'))
                            if innings_pitched < qualification_threshold:
                                continue
                            
                            # Add to qualified relievers pool
                            team_abbr = team.get('abbreviation') or team.get('teamCode') or self._get_team_abbr(team.get('name', 'Unknown'))
                            
                            reliever_data = {
                                'player_id': player_id,
                                'player_name': person.get('fullName', 'Unknown'),
                                'team_name': team.get('name', 'Unknown'),
                                'team_abbr': team_abbr,
                                'stats': stats  # Store all stats
                            }
                            
                            qualified_relievers.append(reliever_data)
                            
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for pitcher {player_id}: {e}")
                    continue
        
        self.logger.info(f"Found {len(qualified_relievers)} qualified relievers")
        
        # Generate leaderboards for each stat
        leaderboards = {}
        
        stat_mappings = [
            ('era', 'ERA', False),  # False = ascending sort
            ('wins', 'W', True),  # True = descending sort
            ('strikeOuts', 'K', True),
            ('saves', 'SV', True),
            ('inningsPitched', 'IP', True),
            ('whip', 'WHIP', False)
        ]
        
        for stat_key, display_name, reverse_sort in stat_mappings:
            # Create leaderboard for this stat
            stat_leaderboard = []
            
            for reliever in qualified_relievers:
                stat_value = reliever['stats'].get(stat_key, None)
                
                # Skip if stat is missing (but allow 0 for ERA)
                if stat_value is None or stat_value == '':
                    continue
                
                player_data = {
                    'player_id': reliever['player_id'],
                    'player_name': reliever['player_name'],
                    'team_name': reliever['team_name'],
                    'team_abbr': reliever['team_abbr'],
                    'stat_value': str(stat_value),
                    'stat_name': display_name
                }
                
                stat_leaderboard.append(player_data)
            
            # Sort and rank
            stat_leaderboard.sort(key=lambda x: float(x['stat_value']), reverse=reverse_sort)
            
            for rank, player in enumerate(stat_leaderboard[:20], 1):
                player['rank'] = rank
            
            leaderboards[f'RP_{display_name}'] = stat_leaderboard[:20]
            self.logger.debug(f"Generated RP_{display_name} leaderboard with {len(stat_leaderboard[:20])} players")
        
        return leaderboards
    
    def _generate_custom_leaderboards(self, season: int) -> tuple[List[Dict], List[Dict]]:
        """
        Generate TBR and TBR+ leaderboards using OPS leaders as base.
        
        Strategy: Fetch OPS leaders (top 100), then fetch full stats for each player
        to calculate TBR/TBR+. This requires 101 API calls but is still much better
        than fetching all 1200+ players.
        
        Args:
            season: Season year
            
        Returns:
            Tuple of (TBR leaderboard, TBR+ leaderboard)
        """
        # Fetch OPS leaders as base
        ops_response = self.api_client.get_stat_leaders('onBasePlusSlugging', season, 'hitting', limit=100)
        
        if not ops_response or 'leagueLeaders' not in ops_response:
            self.logger.warning(f"No OPS leaders data for {season}, cannot calculate TBR/TBR+")
            return [], []
        
        tbr_leaderboard = []
        tbr_plus_leaderboard = []
        
        # For each OPS leader, fetch their full stats and calculate TBR/TBR+
        for league_data in ops_response['leagueLeaders']:
            for leader in league_data.get('leaders', []):
                person = leader.get('person', {})
                team = leader.get('team', {})
                player_id = person.get('id', 0)
                
                if player_id == 0:
                    continue
                
                # Fetch full season stats for this player
                try:
                    stats_response = self.api_client.get_player_season_stats(player_id, season, 'hitting')
                    
                    # Extract stats from response
                    if 'stats' in stats_response and len(stats_response['stats']) > 0:
                        splits = stats_response['stats'][0].get('splits', [])
                        if len(splits) > 0:
                            stats = splits[0].get('stat', {})
                            
                            # Calculate TBR and TBR+
                            tbr, tbr_plus = self.stats_calculator.calculate_tbr_stats(stats)
                            
                            # Get team abbreviation
                            team_abbr = team.get('abbreviation') or team.get('teamCode') or self._get_team_abbr(team.get('name', 'Unknown'))
                            
                            player_data_tbr = {
                                'player_id': player_id,
                                'player_name': person.get('fullName', 'Unknown'),
                                'team_name': team.get('name', 'Unknown'),
                                'team_abbr': team_abbr,
                                'stat_value': f"{tbr:.3f}",
                                'stat_name': 'TBR'
                            }
                            
                            player_data_tbr_plus = {
                                'player_id': player_id,
                                'player_name': person.get('fullName', 'Unknown'),
                                'team_name': team.get('name', 'Unknown'),
                                'team_abbr': team_abbr,
                                'stat_value': f"{tbr_plus:.3f}",
                                'stat_name': 'TBR+'
                            }
                            
                            tbr_leaderboard.append(player_data_tbr)
                            tbr_plus_leaderboard.append(player_data_tbr_plus)
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for player {player_id}: {e}")
                    continue
        
        # Sort by stat value (descending)
        tbr_leaderboard.sort(key=lambda x: float(x['stat_value']), reverse=True)
        tbr_plus_leaderboard.sort(key=lambda x: float(x['stat_value']), reverse=True)
        
        # Add ranks
        for rank, player in enumerate(tbr_leaderboard, 1):
            player['rank'] = rank
        for rank, player in enumerate(tbr_plus_leaderboard, 1):
            player['rank'] = rank
        
        self.logger.debug(f"Generated TBR leaderboard with {len(tbr_leaderboard)} players")
        self.logger.debug(f"Generated TBR+ leaderboard with {len(tbr_plus_leaderboard)} players")
        
        return tbr_leaderboard, tbr_plus_leaderboard

    # Team name to abbreviation mapping
    TEAM_ABBREVIATIONS = {
        'Arizona Diamondbacks': 'ARI',
        'Atlanta Braves': 'ATL',
        'Baltimore Orioles': 'BAL',
        'Boston Red Sox': 'BOS',
        'Chicago Cubs': 'CHC',
        'Chicago White Sox': 'CWS',
        'Cincinnati Reds': 'CIN',
        'Cleveland Guardians': 'CLE',
        'Cleveland Indians': 'CLE',  # Historical name
        'Colorado Rockies': 'COL',
        'Detroit Tigers': 'DET',
        'Houston Astros': 'HOU',
        'Kansas City Royals': 'KC',
        'Los Angeles Angels': 'LAA',
        'Los Angeles Dodgers': 'LAD',
        'Miami Marlins': 'MIA',
        'Florida Marlins': 'MIA',  # Historical name
        'Milwaukee Brewers': 'MIL',
        'Minnesota Twins': 'MIN',
        'Montreal Expos': 'MON',  # Historical team
        'New York Mets': 'NYM',
        'New York Yankees': 'NYY',
        'Oakland Athletics': 'OAK',
        'Philadelphia Phillies': 'PHI',
        'Pittsburgh Pirates': 'PIT',
        'San Diego Padres': 'SD',
        'San Francisco Giants': 'SF',
        'Seattle Mariners': 'SEA',
        'St. Louis Cardinals': 'STL',
        'Tampa Bay Rays': 'TB',
        'Tampa Bay Devil Rays': 'TB',  # Historical name
        'Texas Rangers': 'TEX',
        'Toronto Blue Jays': 'TOR',
        'Washington Nationals': 'WSH'
    }
    
    def _get_team_abbr(self, team_name: str) -> str:
        """
        Get team abbreviation from team name.
        
        Args:
            team_name: Full team name
            
        Returns:
            Team abbreviation (e.g., 'NYY' for 'New York Yankees')
        """
        return self.TEAM_ABBREVIATIONS.get(team_name, 'UNK')
    
    def _is_reliever(self, stats: dict) -> bool:
        """
        Determine if a pitcher is a reliever based on their stats.
        
        A pitcher is considered a reliever if ANY of these are true:
        - Games Started (GS) = 0 (pure reliever)
        - GS / Games Played (G) < 0.5 (mostly relieves)
        - IP / G < 3.0 (doesn't pitch deep into games, handles openers)
        
        Args:
            stats: Dictionary of pitcher stats
            
        Returns:
            True if reliever, False if starter
        """
        games_started = int(stats.get('gamesStarted', 0))
        games_played = int(stats.get('gamesPlayed', 0))
        innings_pitched = float(stats.get('inningsPitched', '0'))
        
        # Pure reliever (no starts)
        if games_started == 0:
            return True
        
        # Mostly relieves (less than half games are starts)
        if games_played > 0 and (games_started / games_played) < 0.5:
            return True
        
        # Doesn't pitch deep (handles openers and swing guys)
        if games_played > 0 and (innings_pitched / games_played) < 3.0:
            return True
        
        return False
    
    def _get_team_games_played(self, season: int) -> int:
        """
        Get the number of games played by a team in the season.
        
        Uses a sample team (Mets, team ID 121) to determine games played.
        All teams play the same number of games in a season (162 for full season).
        
        Args:
            season: Season year
            
        Returns:
            Number of games played (defaults to 162 if unable to fetch)
        """
        try:
            # Fetch team stats for a sample team (Mets)
            import requests
            url = f'https://statsapi.mlb.com/api/v1/teams/121/stats'
            params = {
                'season': season,
                'group': 'hitting',
                'stats': 'season'
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'stats' in data and len(data['stats']) > 0:
                splits = data['stats'][0].get('splits', [])
                if len(splits) > 0:
                    games_played = splits[0]['stat'].get('gamesPlayed', 162)
                    return games_played
        except Exception as e:
            self.logger.warning(f"Failed to get team games played for {season}: {e}")
        
        # Default to 162 (full season)
        return 162
