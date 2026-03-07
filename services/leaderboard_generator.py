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
    
    # Custom stats that need calculation
    CUSTOM_HITTING_STATS = ['TBR', 'TBR+']
    
    def generate_all(self, season: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Generate all leaderboards for a given season.
        
        Fetches standard stat leaders from API and calculates custom stats (TBR, TBR+).
        
        Args:
            season: Season year (e.g., 2024). Defaults to current active season if None.
            
        Returns:
            Dictionary mapping stat name to list of player data:
            {
                'AVG': [{'player': PlayerStats, 'rank': 1, 'value': '.350'}, ...],
                'HR': [...],
                'TBR': [...],
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
        
        # Generate standard pitching stat leaderboards
        for api_stat, display_name in self.STANDARD_PITCHING_STATS:
            leaderboards[display_name] = self._generate_standard_leaderboard(
                api_stat, season, 'pitching', display_name
            )
        
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
        'Colorado Rockies': 'COL',
        'Detroit Tigers': 'DET',
        'Houston Astros': 'HOU',
        'Kansas City Royals': 'KC',
        'Los Angeles Angels': 'LAA',
        'Los Angeles Dodgers': 'LAD',
        'Miami Marlins': 'MIA',
        'Milwaukee Brewers': 'MIL',
        'Minnesota Twins': 'MIN',
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
