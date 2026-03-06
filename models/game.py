"""Data models for games, teams, box scores, and standings."""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Team:
    """Represents a baseball team."""
    team_id: int
    name: str
    abbreviation: str


@dataclass
class Game:
    """Represents a baseball game."""
    game_id: int
    game_date: str
    home_team: Team
    away_team: Team
    home_score: int
    away_score: int
    status: str  # "Final", "In Progress", "Scheduled"
    inning: Optional[int] = None


@dataclass
class BatterStats:
    """Batting statistics for a single game."""
    player_id: int
    player_name: str
    position: str
    at_bats: int
    runs: int
    hits: int
    rbi: int
    walks: int
    strikeouts: int


@dataclass
class PitcherStats:
    """Pitching statistics for a single game."""
    player_id: int
    player_name: str
    innings_pitched: float
    hits: int
    runs: int
    earned_runs: int
    walks: int
    strikeouts: int
    pitch_count: int


@dataclass
class InningScore:
    """Score by inning."""
    inning: int
    home_runs: int
    away_runs: int


@dataclass
class BoxScore:
    """Detailed box score for a game."""
    game: Game
    home_batting: List[BatterStats]
    away_batting: List[BatterStats]
    home_pitching: List[PitcherStats]
    away_pitching: List[PitcherStats]
    scoring_summary: List[InningScore]


@dataclass
class TeamRecord:
    """Team record and standings information."""
    team_id: int
    team_name: str
    wins: int
    losses: int
    winning_percentage: float
    games_back: float
    division_rank: int
    league_rank: int
    streak: str  # e.g., "W3", "L2"


@dataclass
class Standings:
    """Team standings organized by division."""
    date: str
    divisions: Dict[str, List[TeamRecord]]
