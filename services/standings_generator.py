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
        
        Organizes standings by division and adds highlighting metadata
        for the specified team.
        
        Args:
            date: Date string in YYYY-MM-DD format
            highlight_team: Team name to highlight (default: "New York Mets")
            
        Returns:
            Dictionary containing:
                - date: The date used
                - divisions: Dict mapping division name to list of team records
                - highlighted_team: Name of team to highlight
        """
        self.logger.info(f"Generating standings for date: {date}")
        
        # Fetch standings from API (raw response)
        api_response = self.api_client.get_standings(date)
        
        if not api_response or 'records' not in api_response:
            self.logger.warning(f"No standings data found for {date}")
            return {
                'date': date,
                'divisions': {},
                'highlighted_team': highlight_team
            }
        
        # Normalize API response and organize by division
        divisions_with_metadata = self._organize_by_division(api_response, highlight_team)
        
        self.logger.info(f"Generated standings for {len(divisions_with_metadata)} divisions")
        
        # Convert date back to MM/DD/YYYY format for display
        from datetime import datetime
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        display_date = date_obj.strftime("%m/%d/%Y")
        
        return {
            'date': display_date,
            'divisions': divisions_with_metadata,
            'highlighted_team': highlight_team
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
