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
    def display_stats():
        """
        Display stat leaderboards for current season.
        
        Shows leaderboards for all standard and custom stats (TBR, TBR+).
        """
        try:
            # Generate all leaderboards for current season
            leaderboards = leaderboard_gen.generate_all()
            
            return render_template(
                'stats_new.html',
                leaderboards=leaderboards
            )
        except Exception as e:
            logger.error(f"Error generating leaderboards: {e}")
            return render_template('error.html', error_message=str(e)), 500
    
    return stats_bp
