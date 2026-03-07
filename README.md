# Baseball Box Scores for Herb

A Flask web application that displays baseball box scores and statistics leaderboards, featuring custom metrics like TBR (Total Base Rate). Built with a clean architecture emphasizing separation of concerns, comprehensive caching, and robust error handling.

## Features

- **Box Scores Page**: Daily baseball box scores with inning-by-inning linescores and Mets games prioritized
- **Standings**: Side-by-side AL/NL division standings (hidden during offseason/spring training)
- **Stats Page**: Player leaderboards for 18+ statistics including custom TBR/TBR+ metrics
- **Historical Data**: View any season's leaderboards (1900-2030)
- **Quick Navigation**: One-click access to last 7 days of box scores
- **Newspaper Theme**: Typewriter font with aged paper aesthetic
- **Smart Caching**: 24-hour cache reduces API calls from 1200+ to ~113, with <1s page loads
- **Offseason Fallback**: Automatically displays most recent games when no games scheduled

## Architecture

### Clean Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Routes                         │
│              (routes/box_scores.py, stats.py)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Service Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ BoxScoreGenerator│  │StandingsGenerator│            │
│  └──────────────────┘  └──────────────────┘            │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │LeaderboardGen    │  │StatsCalculator   │            │
│  └──────────────────┘  └──────────────────┘            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Data Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ MLBStatsAPIClient│  │  CacheManager    │            │
│  └──────────────────┘  └──────────────────┘            │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  DataSerializer  │  │ ConfigManager    │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Key Components

**Services** (`services/`)
- `BoxScoreGenerator`: Fetches and formats box scores with Mets prioritization
- `StandingsGenerator`: Retrieves AL/NL standings with team highlighting
- `LeaderboardGenerator`: Generates top 20 player leaderboards for 18 stats
- `StatsCalculator`: Computes custom metrics (TBR, TBR+)

**Data Layer** (`data/`)
- `MLBStatsAPIClient`: Centralized API access with caching
- `CacheManager`: JSON-based file caching with TTL support
- `DataSerializer`: Safe JSON serialization (replaces pickle)
- `ConfigurationManager`: YAML-based configuration

**Models** (`models/`)
- `Game`, `TeamRecord`: Box score and standings data structures
- `PlayerStats`: Player statistics with qualification checking
- `StatDefinition`: Metadata for leaderboard stats

**Routes** (`routes/`)
- `box_scores.py`: Main page, date selection, quick navigation
- `stats.py`: Leaderboards with season selection

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd box_scores_for_herb
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - Flask (web framework)
   - PyYAML (configuration)
   - requests (HTTP client)
   - MLB-StatsAPI (baseball data)
   - pytest, hypothesis (testing)

3. **Verify installation**
   ```bash
   python3 -c "import flask, yaml, requests, statsapi; print('✓ All dependencies installed')"
   ```

4. **Run the application**
   ```bash
   python flask_site.py
   ```
   
   The app will be available at `http://localhost:5000`

5. **Warm the cache (optional but recommended)**
   ```bash
   python warm_cache.py
   ```
   
   This pre-fetches data for instant page loads (~33 seconds, caches 7 days + standings + leaderboards)

### Configuration

Configuration is managed in `config/settings.yaml`. Key settings:

- **Cache TTL**: How long to cache data (default: 24 hours for all data)
- **API Settings**: Timeout and retry configuration for MLB StatsAPI
- **Logging**: Log level and file location (`logs/app.log`)
- **Highlighted Team**: Team to prioritize/highlight (default: "New York Mets")

To override settings, you can use environment variables (prefixed with `BASEBALL_`).

### Directory Structure

```
box_scores_for_herb/
├── config/              # Configuration management
│   ├── config_manager.py
│   └── settings.yaml
├── data/                # API client, caching, serialization
│   ├── api_client.py
│   ├── cache_manager.py
│   └── serializer.py
├── services/            # Business logic (generators, calculators)
│   ├── box_score_generator.py
│   ├── standings_generator.py
│   ├── leaderboard_generator.py
│   └── stats_calculator.py
├── routes/              # Flask route handlers
│   ├── box_scores.py
│   └── stats.py
├── models/              # Data models
│   ├── game.py
│   ├── player_stats.py
│   └── stat_definition.py
├── utils/               # Logging and error handling
│   ├── logger.py
│   └── exceptions.py
├── static/              # CSS styling
│   └── style.css
├── templates/           # HTML templates
│   ├── index.html       # Box scores page
│   ├── stats.html       # Leaderboards page
│   └── error.html
├── tests/               # Unit, integration, and property tests
│   ├── unit/
│   ├── integration/
│   └── property/
├── cache/               # Cached data (auto-created, not in git)
├── logs/                # Application logs (auto-created, not in git)
├── flask_site.py        # Main Flask application
├── warm_cache.py        # Cache warming script
└── requirements.txt     # Python dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

**Test Coverage:**
- Unit tests: serializer, cache_manager, config_manager
- Integration tests: box_score_generator, leaderboard_generator, standings_generator

### Deployment (PythonAnywhere)

1. **Pull the latest code**
   ```bash
   git pull
   ```

2. **Install/update dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up scheduled cache warming**
   - Go to PythonAnywhere → Tasks
   - Add daily task at 6:00 AM: `/path/to/python warm_cache.py`
   - This ensures instant page loads throughout the day

4. **Update WSGI configuration**
   - Point to `flask_site.py` as the main application
   - Ensure `cache/` and `logs/` directories exist and are writable

5. **Reload the web app**
   - From PythonAnywhere dashboard, click "Reload"

The `cache/` and `logs/` directories will be created automatically on first run.

## Pages

- **`/`** - Box Scores for Herb (yesterday's games by default)
- **`/date/<YYYY-MM-DD>`** - Box scores for specific date
- **`/stats-for-kevin`** - Current season leaderboards
- **`/stats-for-kevin/<season>`** - Historical season leaderboards (e.g., `/stats-for-kevin/2019`)

## Statistics

### Hitting Leaders (10 stats)
- AVG, HR, RBI, OPS, OBP, SLG, 2B, 3B, SB, R

### Pitching Leaders (6 stats)
- ERA, W, K, SV, IP, WHIP

### Custom Statistics (2 stats)
- **TBR (Total Bases per Run)**: Measures offensive efficiency by weighting hits, walks, steals, and outs
- **TBR+**: Enhanced TBR that includes runs and RBIs in the calculation

All leaderboards show top 20 players with team abbreviations. Mets players are highlighted in light blue.

## Performance

- **API Calls**: Reduced from 1200+ to ~113 per leaderboard generation
- **Cache Hit Speed**: <1 second for cached pages
- **Cache Miss Speed**: ~19 seconds for first leaderboard load, ~33 seconds for cache warming
- **Cache Duration**: 24 hours (newspaper-style daily updates)

## License

Personal project for displaying baseball statistics.
