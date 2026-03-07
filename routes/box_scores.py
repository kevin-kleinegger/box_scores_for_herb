"""
Box Scores Route Handler

Handles the main box scores page route, integrating BoxScoreGenerator
and StandingsGenerator services.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for
from services.box_score_generator import BoxScoreGenerator
from services.standings_generator import StandingsGenerator
from utils.logger import Logger

# Create blueprint
box_scores_bp = Blueprint('box_scores', __name__)

# Module-level logger
logger = Logger.get_logger(__name__)


def init_box_scores_routes(box_score_gen: BoxScoreGenerator, standings_gen: StandingsGenerator):
    """
    Initialize box scores routes with service dependencies.
    
    Args:
        box_score_gen: BoxScoreGenerator instance
        standings_gen: StandingsGenerator instance
    """
    
    @box_scores_bp.route('/')
    def index():
        """
        Display box scores for yesterday's games (default).
        
        Uses yesterday's date (current time - 28 hours) to account for:
        - Late night games finishing after midnight
        - Timezone differences (GMT conversion)
        """
        # Default to yesterday (28 hours ago to account for late games + timezone)
        default_date = (datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')
        
        # Generate last 7 dates for quick navigation
        last_7_dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
        
        try:
            # Generate box scores and standings
            game_data, actual_date = box_score_gen.generate_for_date(default_date)
            standings_data = standings_gen.generate_for_date(actual_date)
            
            return render_template(
                'index_new.html',
                box_scores=game_data,
                standings=standings_data,
                default_date=actual_date,
                last_7_dates=last_7_dates
            )
        except Exception as e:
            logger.error(f"Error generating box scores for {default_date}: {e}")
            return render_template('error.html', error_message=str(e)), 500
    
    
    @box_scores_bp.route('/date/<date>')
    def display_box_scores(date):
        """
        Display box scores for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
        """
        # Generate last 7 dates for quick navigation
        last_7_dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
        
        try:
            # Validate date format
            datetime.strptime(date, '%Y-%m-%d')
            
            # Generate box scores and standings
            game_data, actual_date = box_score_gen.generate_for_date(date)
            standings_data = standings_gen.generate_for_date(actual_date)
            
            return render_template(
                'index_new.html',
                box_scores=game_data,
                standings=standings_data,
                default_date=actual_date,
                last_7_dates=last_7_dates
            )
        except ValueError:
            logger.warning(f"Invalid date format: {date}")
            return render_template('error.html', error_message="Invalid date format. Use YYYY-MM-DD"), 400
        except Exception as e:
            logger.error(f"Error generating box scores for {date}: {e}")
            return render_template('error.html', error_message=str(e)), 500
    
    
    @box_scores_bp.route('/submit_date', methods=['POST'])
    def submit_date():
        """
        Handle date submission from form.
        
        Validates the date and redirects to the appropriate route.
        Rejects future dates and invalid formats.
        """
        input_date = request.form.get('input_date')
        
        if not input_date:
            return render_template('error.html', error_message="No date provided"), 400
        
        try:
            # Validate date format
            parsed_date = datetime.strptime(input_date, "%Y-%m-%d").date()
            
            # Reject future dates
            if parsed_date >= datetime.now().date():
                return render_template(
                    'error.html',
                    error_message="Date must be in the past (not today or future)"
                ), 400
            
            # Redirect to the date-specific route
            return redirect(url_for('box_scores.display_box_scores', date=input_date))
            
        except ValueError:
            logger.warning(f"Invalid date format submitted: {input_date}")
            return render_template('error.html', error_message="Invalid date format. Use YYYY-MM-DD"), 400
    
    return box_scores_bp
