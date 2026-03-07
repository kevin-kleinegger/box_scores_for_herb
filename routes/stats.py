"""
Stats/Leaderboards Route Handler

Handles the stats page route, integrating LeaderboardGenerator service.
"""

from flask import Blueprint, render_template
from services.leaderboard_generator import LeaderboardGenerator
from utils.logger import Logger

# Create blueprint
stats_bp = Blueprint('stats', __name__)

# Module-level logger
logger = Logger.get_logger(__name__)


def init_stats_routes(leaderboard_gen: LeaderboardGenerator):
    """
    Initialize stats routes with service dependencies.
    
    Args:
        leaderboard_gen: LeaderboardGenerator instance
    """
    
    @stats_bp.route('/stats-for-kevin')
    @stats_bp.route('/stats-for-kevin/<int:season>')
    def display_stats(season=None):
        """
        Display stat leaderboards for specified season.
        
        Shows leaderboards for all standard and custom stats (TBR, TBR+).
        
        Args:
            season: Optional season year (e.g., 2024). Defaults to current season if None.
        """
        try:
            # Generate all leaderboards for specified season (or current if None)
            leaderboards = leaderboard_gen.generate_all(season)
            
            # Get the actual season used (for display)
            actual_season = season if season else leaderboard_gen._get_current_season()
            
            return render_template(
                'stats_new.html',
                leaderboards=leaderboards,
                current_season=actual_season
            )
        except Exception as e:
            logger.error(f"Error generating leaderboards: {e}")
            return render_template('error.html', error_message=str(e)), 500
    
    return stats_bp
