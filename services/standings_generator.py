"""
Standings Generator Service

Generates formatted standings data organized by division with team highlighting.
"""

from typing import Dict, List
from data.api_client import MLBStatsAPIClient
from utils.logger import Logger


class StandingsGenerator:
    """Generates standings data organized by division."""
    
    def __init__(self, api_client: MLBStatsAPIClient):
        """
        Initialize StandingsGenerator.
        
        Args:
            api_client: MLBStatsAPIClient instance for fetching standings data
        """
        self.api_client = api_client
        self.logger = Logger.get_logger(__name__)

    
    def generate_for_date(self, date: str, highlight_team: str = "New York Mets") -> Dict:
        """
        Generate standings data for a specific date.
        
        Fetches AL and NL standings separately for side-by-side display.
        Uses cached API client methods for better performance.
        
        Args:
            date: Date string in YYYY-MM-DD format
            highlight_team: Team name to highlight (default: "New York Mets")
            
        Returns:
            Dictionary containing:
                - date: The date used
                - al_standings: American League standings text
                - nl_standings: National League standings text
        """
        from datetime import datetime
        
        self.logger.info(f"Generating standings for date: {date}")
        
        # Convert date format for display
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        display_date = date_obj.strftime("%m/%d/%Y")
        
        try:
            # Fetch AL standings (leagueId 103) - uses cached method
            al_standings = self.api_client.get_standings_text_by_league(date, "103")
            
            # Fetch NL standings (leagueId 104) - uses cached method
            nl_standings = self.api_client.get_standings_text_by_league(date, "104")
            
            self.logger.info(f"Generated standings for {date}")
            
            return {
                'date': display_date,
                'al_standings': al_standings,
                'nl_standings': nl_standings
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch standings: {e}")
            return {
                'date': display_date,
                'al_standings': '',
                'nl_standings': ''
            }
    
    def _organize_by_division(self, api_response: Dict, highlight_team: str) -> Dict[str, List[Dict]]:
        """
        Organize API response by division and add highlighting metadata.
        
        Args:
            api_response: Raw API response
            highlight_team: Team name to highlight
            
        Returns:
            Dict mapping division name to list of team data with metadata
        """
        from models.game import TeamRecord
        
        divisions = {}
        
        for record in api_response.get('records', []):
            teams_data = []
            
            for team_record in record.get('teamRecords', []):
                team = team_record.get('team', {})
                team_name = team.get('name', 'Unknown')
                
                # Get division name from team object
                division_info = team.get('division', {})
                division_name = division_info.get('name', 'Unknown')
                
                # Handle games_back ('-' for first place)
                games_back_str = team_record.get('gamesBack', '0.0')
                games_back = 0.0 if games_back_str == '-' else float(games_back_str)
                
                # Create TeamRecord object
                team_obj = TeamRecord(
                    team_id=team.get('id', 0),
                    team_name=team_name,
                    wins=team_record.get('wins', 0),
                    losses=team_record.get('losses', 0),
                    winning_percentage=float(team_record.get('winningPercentage', '0.000')),
                    games_back=games_back,
                    division_rank=team_record.get('divisionRank', 0),
                    league_rank=team_record.get('leagueRank', 0),
                    streak=team_record.get('streak', {}).get('streakCode', '')
                )
                
                # Add to appropriate division
                if division_name not in divisions:
                    divisions[division_name] = []
                
                divisions[division_name].append({
                    'team': team_obj,
                    'is_highlighted': team_name == highlight_team
                })
        
        return divisions
