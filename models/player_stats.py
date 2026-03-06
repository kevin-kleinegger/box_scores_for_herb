"""Data models for player statistics."""

from dataclasses import dataclass


@dataclass
class PlayerStats:
    """Season statistics for a player.
    
    This model handles both hitting and pitching statistics.
    Fields are populated based on the stat_group value.
    """
    player_id: int
    player_name: str
    team: str
    season: int
    stat_group: str  # "hitting", "pitching", "fielding"
    
    # Offensive stats (populated when stat_group="hitting")
    games: int = 0
    plate_appearances: int = 0
    at_bats: int = 0
    runs: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    stolen_bases: int = 0
    batting_average: float = 0.0
    on_base_percentage: float = 0.0
    slugging_percentage: float = 0.0
    ops: float = 0.0
    
    # Custom calculated hitting stats
    total_bases: int = 0
    tbr: float = 0.0
    tbr_plus: int = 0
    
    # Pitching stats (populated when stat_group="pitching")
    wins: int = 0
    losses: int = 0
    era: float = 0.0
    games_pitched: int = 0
    games_started: int = 0
    saves: int = 0
    innings_pitched: float = 0.0
    strikeouts_pitching: int = 0  # Separate from batting strikeouts
    walks_allowed: int = 0
    hits_allowed: int = 0
    earned_runs: int = 0
    home_runs_allowed: int = 0
    whip: float = 0.0
    
    def is_qualified(self, threshold: float, team_games: int) -> bool:
        """Check if player meets qualification threshold.
        
        For hitters: threshold * team_games plate appearances required (e.g., 3.1)
        For pitchers: threshold * team_games innings pitched required (e.g., 1.0)
        
        Args:
            threshold: Qualification threshold (PA per game for hitters, IP per game for pitchers)
            team_games: Number of games played by team
            
        Returns:
            True if player has enough plate appearances or innings to qualify
        """
        if self.stat_group == "hitting":
            required_pa = threshold * team_games
            return self.plate_appearances >= required_pa
        elif self.stat_group == "pitching":
            required_ip = threshold * team_games
            return self.innings_pitched >= required_ip
        else:
            return False
