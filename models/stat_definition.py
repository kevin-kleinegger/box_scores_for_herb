"""Data models for statistic definitions and metadata."""

from dataclasses import dataclass


@dataclass
class StatDefinition:
    """Metadata for a statistic."""
    name: str
    display_name: str
    stat_group: str  # "hitting", "pitching", "advanced"
    calculation_method: str  # "api", "calculated"
    sort_descending: bool
    qualification_threshold: float
    format_string: str  # e.g., ".3f" for batting average
    description: str
    data_source: str = "mlb_statsapi"  # Future: support multiple sources
    
    def format_value(self, value: float) -> str:
        """Format statistic value for display.
        
        Args:
            value: The numeric value to format
            
        Returns:
            Formatted string representation of the value
        """
        return f"{value:{self.format_string}}"



# Predefined stat definitions for leaderboards
STAT_DEFINITIONS = {
    # Hitting stats
    "batting_average": StatDefinition(
        name="batting_average",
        display_name="AVG",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".3f",
        description="Batting Average"
    ),
    "home_runs": StatDefinition(
        name="home_runs",
        display_name="HR",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,  # No qualification needed for counting stats
        format_string=".0f",
        description="Home Runs"
    ),
    "rbi": StatDefinition(
        name="rbi",
        display_name="RBI",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,
        format_string=".0f",
        description="Runs Batted In"
    ),
    "on_base_percentage": StatDefinition(
        name="on_base_percentage",
        display_name="OBP",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".3f",
        description="On-Base Percentage"
    ),
    "slugging_percentage": StatDefinition(
        name="slugging_percentage",
        display_name="SLG",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".3f",
        description="Slugging Percentage"
    ),
    "ops": StatDefinition(
        name="ops",
        display_name="OPS",
        stat_group="hitting",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".3f",
        description="On-Base Plus Slugging"
    ),
    "tbr": StatDefinition(
        name="tbr",
        display_name="TBR",
        stat_group="hitting",
        calculation_method="calculated",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".3f",
        description="Total Bases per Run (custom stat)"
    ),
    "tbr_plus": StatDefinition(
        name="tbr_plus",
        display_name="TBR+",
        stat_group="hitting",
        calculation_method="calculated",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".0f",
        description="TBR normalized to league average (100 = average)"
    ),
    
    # Pitching stats
    "era": StatDefinition(
        name="era",
        display_name="ERA",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=False,  # Lower ERA is better
        qualification_threshold=1.0,  # 1 inning per team game
        format_string=".2f",
        description="Earned Run Average"
    ),
    "wins": StatDefinition(
        name="wins",
        display_name="W",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,  # No qualification for counting stats
        format_string=".0f",
        description="Wins"
    ),
    "strikeouts_pitching": StatDefinition(
        name="strikeouts_pitching",
        display_name="K",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,
        format_string=".0f",
        description="Strikeouts"
    ),
    "saves": StatDefinition(
        name="saves",
        display_name="SV",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,
        format_string=".0f",
        description="Saves"
    ),
    "innings_pitched": StatDefinition(
        name="innings_pitched",
        display_name="IP",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=True,
        qualification_threshold=0.0,
        format_string=".1f",
        description="Innings Pitched"
    ),
    "whip": StatDefinition(
        name="whip",
        display_name="WHIP",
        stat_group="pitching",
        calculation_method="api",
        sort_descending=False,  # Lower WHIP is better
        qualification_threshold=1.0,
        format_string=".2f",
        description="Walks plus Hits per Inning Pitched"
    ),
}
