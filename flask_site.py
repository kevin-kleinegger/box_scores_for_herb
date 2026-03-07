"""
Flask Application Entry Point

Initializes the Flask application with all routes and services.
"""

from flask import Flask
from config.config_manager import ConfigurationManager
from data.cache_manager import CacheManager
from data.serializer import DataSerializer
from data.api_client import MLBStatsAPIClient
from services.box_score_generator import BoxScoreGenerator
from services.standings_generator import StandingsGenerator
from services.leaderboard_generator import LeaderboardGenerator
from services.stats_calculator import StatsCalculator
from routes.box_scores import init_box_scores_routes
from routes.stats import init_stats_routes
from utils.logger import Logger

# Initialize Flask app
app = Flask(__name__)

# Initialize configuration and logging
config = ConfigurationManager()
logger = Logger.setup(config)

# Initialize data layer
serializer = DataSerializer()
cache = CacheManager(config, serializer)
api_client = MLBStatsAPIClient(config, cache)

# Initialize services
box_score_gen = BoxScoreGenerator(api_client)
standings_gen = StandingsGenerator(api_client)
stats_calculator = StatsCalculator()
leaderboard_gen = LeaderboardGenerator(api_client, stats_calculator)

# Register blueprints
box_scores_bp = init_box_scores_routes(box_score_gen, standings_gen)
stats_bp = init_stats_routes(leaderboard_gen)

app.register_blueprint(box_scores_bp)
app.register_blueprint(stats_bp)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return "Internal server error", 500

if __name__ == '__main__':
    app.run(debug=True)
