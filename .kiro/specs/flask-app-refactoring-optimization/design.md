# Design Document: Flask Baseball Statistics Application Refactoring

## Overview

This design document specifies the architecture and implementation approach for refactoring an existing Flask-based baseball statistics application. The application serves two primary user personas: Herb (60+ years old, wants simple box scores with Mets prioritization) and Kevin (wants detailed statistical leaderboards with custom metrics).

### Current State

The existing application suffers from several technical debt issues:
- Unsafe data serialization using `ast.literal_eval()`
- Hardcoded file paths and configuration values
- Performance bottleneck: 1200+ API calls for leaderboard generation
- Lack of structured logging
- Mixed concerns between routes, business logic, and data access
- Poor error handling
- Non-responsive frontend using `<pre>` tags

### Goals

This refactoring will:
1. Improve security by replacing unsafe serialization with JSON
2. Centralize configuration management
3. Optimize performance to <100 API calls and <30 second leaderboard generation
4. Implement structured logging throughout
5. Separate concerns with clean module boundaries
6. Add comprehensive error handling with retries
7. Create responsive, newspaper-style frontend
8. Establish testing infrastructure with 70%+ coverage
9. Design extensible patterns for future enhancements

### Non-Goals

- Multi-source data integration (architecture supports it, but implementation uses only MLB StatsAPI)
- Historical leaderboards (future enhancement)
- Hot/cold player tracking (future enhancement)
- Current day live game support (future enhancement)


## Architecture

### High-Level Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Box Scores Page │         │   Stats Page     │         │
│  │   (Route: /)     │         │ (Route: /stats)  │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Box Score        │         │  Leaderboard     │         │
│  │ Generator        │         │  Generator       │         │
│  └──────────────────┘         └──────────────────┘         │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Standings        │         │  Custom Stats    │         │
│  │ Generator        │         │  Calculator      │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   API Client     │         │  Cache Manager   │         │
│  │  (MLB StatsAPI)  │         │  (File-based)    │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ Configuration    │  │     Logger       │  │   Error   │ │
│  │    Manager       │  │                  │  │  Handler  │ │
│  └──────────────────┘  └──────────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
flask_baseball_app/
├── app.py                      # Flask application entry point
├── config/
│   ├── __init__.py
│   ├── config_manager.py       # Configuration loading and access
│   └── settings.yaml           # Configuration file
├── routes/
│   ├── __init__.py
│   ├── box_scores.py           # Box scores page route handler
│   └── stats.py                # Stats page route handler
├── services/
│   ├── __init__.py
│   ├── box_score_generator.py  # Box score generation logic
│   ├── leaderboard_generator.py # Leaderboard generation logic
│   ├── standings_generator.py  # Standings generation logic
│   └── stats_calculator.py     # Custom statistics calculations
├── data/
│   ├── __init__.py
│   ├── api_client.py           # MLB StatsAPI client
│   ├── cache_manager.py        # File-based caching
│   └── serializer.py           # JSON serialization/deserialization
├── models/
│   ├── __init__.py
│   ├── player_stats.py         # Player statistics data models
│   ├── game.py                 # Game and box score data models
│   └── stat_definition.py      # Stat metadata definitions
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Structured logging setup
│   └── exceptions.py           # Custom exception classes
├── static/
│   ├── css/
│   │   ├── base.css            # Base styles
│   │   ├── newspaper.css       # Newspaper theme
│   │   └── responsive.css      # Media queries
│   └── js/
│       └── date_selector.js    # Date selection functionality
├── templates/
│   ├── base.html               # Base template
│   ├── box_scores.html         # Box scores page template
│   └── stats.html              # Stats page template
└── tests/
    ├── unit/
    │   ├── test_cache_manager.py
    │   ├── test_serializer.py
    │   ├── test_config_manager.py
    │   └── test_stats_calculator.py
    └── integration/
        ├── test_box_scores_route.py
        └── test_stats_route.py
```


## Components and Interfaces

### Configuration Manager

**Responsibility:** Load and provide access to application configuration settings.

**Interface:**
```python
class ConfigurationManager:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Load configuration from YAML file."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default."""
        
    def get_cache_dir(self) -> str:
        """Get cache directory path."""
        
    def get_cache_ttl(self, cache_type: str) -> int:
        """Get cache TTL in seconds for specific cache type."""
        
    def get_api_timeout(self) -> int:
        """Get API request timeout in seconds."""
        
    def get_api_base_url(self) -> str:
        """Get MLB StatsAPI base URL."""
        
    def get_theme_settings(self) -> dict:
        """Get theme and styling configuration."""
```

**Configuration File Structure (settings.yaml):**
```yaml
cache:
  directory: "./cache"
  ttl:
    player_stats: 3600      # 1 hour
    box_scores: 86400       # 24 hours
    standings: 3600         # 1 hour
    leaderboards: 3600      # 1 hour

api:
  base_url: "https://statsapi.mlb.com/api/v1"
  timeout: 10
  retry_attempts: 3
  retry_backoff_base: 2

logging:
  level: "INFO"
  file: "./logs/app.log"
  max_bytes: 10485760       # 10MB
  backup_count: 5

theme:
  name: "newspaper"
  font_family: "Georgia, serif"
  base_font_size: "16px"
  primary_color: "#000000"
  background_color: "#f5f5f0"

teams:
  mets_team_id: 121

leaderboards:
  qualification_threshold: 3.1  # Plate appearances per team game
```

### Logger

**Responsibility:** Provide structured logging throughout the application.

**Interface:**
```python
class Logger:
    @staticmethod
    def setup(config: ConfigurationManager) -> logging.Logger:
        """Configure and return application logger."""
        
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance for specific module."""
```

**Usage Pattern:**
```python
logger = Logger.get_logger(__name__)
logger.info("Generating leaderboard", extra={
    "stat_type": "offensive",
    "season": 2024,
    "player_count": 150
})
```

### Data Serializer

**Responsibility:** Safely serialize and deserialize cached data using JSON.

**Interface:**
```python
class DataSerializer:
    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to JSON string."""
        
    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Deserialize JSON string to Python object."""
        
    @staticmethod
    def validate_structure(data: Any, expected_type: type) -> bool:
        """Validate deserialized data matches expected structure."""
```

**Implementation Notes:**
- Uses `json.dumps()` and `json.loads()` exclusively
- Handles datetime objects with custom encoder
- Validates data structure after deserialization
- Returns empty dict/list on deserialization failure
- Logs all serialization errors


### Cache Manager

**Responsibility:** Manage file-based caching with expiration and validation.

**Interface:**
```python
class CacheManager:
    def __init__(self, config: ConfigurationManager, serializer: DataSerializer):
        """Initialize cache manager with configuration and serializer."""
        
    def get(self, key: str, cache_type: str) -> Optional[Any]:
        """Retrieve cached data if valid and not expired."""
        
    def set(self, key: str, data: Any, cache_type: str) -> bool:
        """Store data in cache with metadata."""
        
    def invalidate(self, key: str) -> bool:
        """Remove specific cache entry."""
        
    def clear_expired(self) -> int:
        """Remove all expired cache entries, return count removed."""
        
    def _get_cache_path(self, key: str) -> str:
        """Generate file path for cache key."""
        
    def _is_expired(self, metadata: dict, cache_type: str) -> bool:
        """Check if cache entry has expired based on TTL."""
```

**Cache Entry Structure:**
```json
{
  "metadata": {
    "created_at": "2024-01-15T10:30:00Z",
    "cache_type": "player_stats",
    "key": "player_stats_2024_offensive"
  },
  "data": {
    // Actual cached data
  }
}
```

**Implementation Notes:**
- Creates cache directory if it doesn't exist
- Uses SHA256 hash of key for filename to avoid path issues
- Stores metadata alongside data for expiration checking
- Treats read errors as cache misses
- Thread-safe for concurrent access

### API Client

**Responsibility:** Encapsulate all MLB StatsAPI interactions with retry logic.

**Interface:**
```python
class MLBStatsAPIClient:
    def __init__(self, config: ConfigurationManager, cache: CacheManager):
        """Initialize API client with configuration and cache."""
        
    def get_games_by_date(self, date: str) -> List[Game]:
        """Retrieve all games for a specific date."""
        
    def get_box_score(self, game_id: int) -> BoxScore:
        """Retrieve detailed box score for a game."""
        
    def get_standings(self, date: str) -> Standings:
        """Retrieve standings as of a specific date."""
        
    def get_player_stats(self, player_id: int, season: int, 
                        stat_group: str) -> PlayerStats:
        """Retrieve statistics for a specific player."""
        
    def get_season_stats_batch(self, player_ids: List[int], 
                               season: int, stat_group: str) -> Dict[int, PlayerStats]:
        """Batch retrieve statistics for multiple players."""
        
    def get_qualified_players(self, season: int, 
                             stat_group: str) -> List[int]:
        """Retrieve list of qualified player IDs for leaderboards."""
        
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make HTTP request with retry logic and error handling."""
        
    def _retry_with_backoff(self, func: Callable, max_attempts: int) -> Any:
        """Execute function with exponential backoff retry."""
```

**Implementation Notes:**
- All API calls go through `_make_request()` for consistent error handling
- Implements exponential backoff: wait = base^attempt seconds
- Logs all requests with parameters and response times
- Returns normalized data structures (not raw API responses)
- Checks cache before making API calls
- Designed with interface pattern for future multi-source support


### Box Score Generator

**Responsibility:** Generate box scores with Mets prioritization logic.

**Interface:**
```python
class BoxScoreGenerator:
    def __init__(self, api_client: MLBStatsAPIClient, config: ConfigurationManager):
        """Initialize with API client and configuration."""
        
    def generate_for_date(self, date: str) -> List[BoxScore]:
        """Generate box scores for all games on a date, Mets first."""
        
    def _prioritize_mets(self, games: List[Game]) -> List[Game]:
        """Reorder games list to place Mets game first if present."""
        
    def _format_box_score(self, box_score: BoxScore) -> dict:
        """Format box score data for template rendering."""
```

### Standings Generator

**Responsibility:** Generate standings data organized by division.

**Interface:**
```python
class StandingsGenerator:
    def __init__(self, api_client: MLBStatsAPIClient):
        """Initialize with API client."""
        
    def generate_for_date(self, date: str) -> dict:
        """Generate standings organized by division."""
        
    def _format_standings(self, standings: Standings) -> dict:
        """Format standings data for template rendering."""
        
    def _highlight_team(self, standings: dict, team_id: int) -> dict:
        """Add highlighting metadata for specific team (e.g., Mets)."""
```

### Leaderboard Generator

**Responsibility:** Generate statistical leaderboards with optimization for minimal API calls.

**Interface:**
```python
class LeaderboardGenerator:
    def __init__(self, api_client: MLBStatsAPIClient, 
                 stats_calculator: StatsCalculator,
                 config: ConfigurationManager):
        """Initialize with API client, calculator, and configuration."""
        
    def generate(self, stat_definitions: List[StatDefinition], 
                season: int) -> dict:
        """Generate leaderboards for specified statistics."""
        
    def _get_qualified_players(self, season: int, 
                              stat_group: str) -> List[int]:
        """Get list of qualified player IDs based on threshold."""
        
    def _batch_fetch_stats(self, player_ids: List[int], 
                          season: int, stat_group: str) -> Dict[int, PlayerStats]:
        """Fetch statistics for multiple players in batches."""
        
    def _apply_qualification(self, players: List[PlayerStats], 
                           stat_def: StatDefinition) -> List[PlayerStats]:
        """Filter players based on qualification threshold."""
        
    def _sort_by_stat(self, players: List[PlayerStats], 
                     stat_name: str, descending: bool = True) -> List[PlayerStats]:
        """Sort players by specified statistic."""
```

**Performance Optimization Strategy:**
1. Fetch qualified player list once (1 API call)
2. Batch fetch player stats in groups of 50 (3-4 API calls for ~150 players)
3. Cache all player stats for 1 hour
4. Calculate custom stats (TBR, TBR+) from cached data
5. Generate all leaderboards from single cached dataset

**Target:** <100 API calls total, <30 seconds generation time


### Stats Calculator

**Responsibility:** Calculate custom statistics like TBR and TBR+.

**Interface:**
```python
class StatsCalculator:
    def calculate_tbr(self, total_bases: int, runs: int) -> float:
        """Calculate Total Bases per Run (TBR)."""
        
    def calculate_tbr_plus(self, player_tbr: float, league_avg_tbr: float) -> int:
        """Calculate TBR+ normalized to league average (100 = average)."""
        
    def get_league_average_tbr(self, season: int, 
                              player_stats: List[PlayerStats]) -> float:
        """Calculate league average TBR from player statistics."""
        
    def calculate_total_bases(self, stats: PlayerStats) -> int:
        """Calculate total bases from hits breakdown."""
```

**Calculation Formulas:**
- TBR = Total Bases / Runs (handle division by zero)
- Total Bases = (1B × 1) + (2B × 2) + (3B × 3) + (HR × 4)
- TBR+ = (Player TBR / League Average TBR) × 100

### Error Handler

**Responsibility:** Handle and format errors for user display.

**Interface:**
```python
class ErrorHandler:
    @staticmethod
    def handle_api_error(error: Exception, context: dict) -> dict:
        """Handle API-related errors and return user-friendly message."""
        
    @staticmethod
    def handle_cache_error(error: Exception, context: dict) -> dict:
        """Handle cache-related errors."""
        
    @staticmethod
    def handle_validation_error(error: Exception, context: dict) -> dict:
        """Handle input validation errors."""
        
    @staticmethod
    def format_error_response(error_type: str, message: str, 
                            details: dict = None) -> dict:
        """Format error for template rendering."""
```

### Custom Exceptions

```python
class BaseballAppException(Exception):
    """Base exception for application-specific errors."""
    pass

class APIClientException(BaseballAppException):
    """Raised when API client encounters an error."""
    pass

class CacheException(BaseballAppException):
    """Raised when cache operations fail."""
    pass

class ValidationException(BaseballAppException):
    """Raised when input validation fails."""
    pass

class ConfigurationException(BaseballAppException):
    """Raised when configuration is invalid or missing."""
    pass
```


## Data Models

### Game

```python
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
class Team:
    """Represents a baseball team."""
    team_id: int
    name: str
    abbreviation: str
```

### BoxScore

```python
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
```

### PlayerStats

```python
@dataclass
class PlayerStats:
    """Season statistics for a player."""
    player_id: int
    player_name: str
    team: str
    season: int
    stat_group: str  # "hitting", "pitching", "fielding"
    
    # Offensive stats
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
    
    # Custom calculated stats
    total_bases: int = 0
    tbr: float = 0.0
    tbr_plus: int = 0
    
    def is_qualified(self, threshold: float, team_games: int) -> bool:
        """Check if player meets qualification threshold."""
        required_pa = threshold * team_games
        return self.plate_appearances >= required_pa
```


### Standings

```python
@dataclass
class Standings:
    """Team standings organized by division."""
    date: str
    divisions: Dict[str, List[TeamRecord]]
    
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
```

### StatDefinition

```python
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
        """Format statistic value for display."""
        return f"{value:{self.format_string}}"
```

**Example StatDefinition Instances:**

```python
STAT_DEFINITIONS = {
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
    "tbr": StatDefinition(
        name="tbr",
        display_name="TBR",
        stat_group="hitting",
        calculation_method="calculated",
        sort_descending=True,
        qualification_threshold=3.1,
        format_string=".2f",
        description="Total Bases per Run"
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
    )
}
```


## API Interaction Patterns

### Request Flow

1. **Route Handler** receives HTTP request
2. **Business Logic** (Generator) processes request
3. **Cache Manager** checks for cached data
4. If cache miss: **API Client** makes request to MLB StatsAPI
5. **API Client** normalizes response to internal data models
6. **Cache Manager** stores normalized data
7. **Business Logic** processes/calculates additional metrics
8. **Route Handler** renders template with data

### Caching Strategy

**Cache Keys:**
- Box scores: `box_score_{game_id}`
- Standings: `standings_{date}`
- Player stats: `player_stats_{player_id}_{season}_{stat_group}`
- Qualified players: `qualified_players_{season}_{stat_group}`
- Leaderboard data: `leaderboard_data_{season}_{stat_group}`

**Cache TTL by Type:**
- Player stats: 1 hour (3600 seconds)
- Box scores: 24 hours (86400 seconds) - historical data doesn't change
- Standings: 1 hour (3600 seconds)
- Leaderboards: 1 hour (3600 seconds)

**Cache Invalidation:**
- Manual invalidation via admin endpoint (future enhancement)
- Automatic expiration based on TTL
- Periodic cleanup of expired entries

### Batch Request Optimization

**Problem:** Original implementation made 1200+ individual API calls for leaderboards.

**Solution:** Batch fetching strategy

1. **Single qualified players call:** Get list of ~150 qualified player IDs (1 API call)
2. **Batch player stats:** Fetch stats in batches of 50 players (3-4 API calls)
3. **Cache all results:** Store each player's stats individually for reuse
4. **Calculate custom metrics:** Compute TBR, TBR+ from cached data (0 API calls)
5. **Generate all leaderboards:** Use cached data for all stat types (0 API calls)

**Result:** ~5 API calls total vs 1200+, <30 second generation time

### Error Handling and Retry Logic

**Retry Strategy:**
```python
def _retry_with_backoff(self, func, max_attempts=3):
    """Exponential backoff: wait = 2^attempt seconds"""
    for attempt in range(max_attempts):
        try:
            return func()
        except requests.RequestException as e:
            if attempt == max_attempts - 1:
                raise APIClientException(f"Failed after {max_attempts} attempts") from e
            wait_time = 2 ** attempt
            logger.warning(f"API call failed, retrying in {wait_time}s", 
                         extra={"attempt": attempt + 1, "error": str(e)})
            time.sleep(wait_time)
```

**Error Propagation:**
- API errors → APIClientException → logged and returned to caller
- Cache errors → CacheException → logged, treated as cache miss
- Validation errors → ValidationException → user-friendly error page
- Configuration errors → ConfigurationException → application fails to start


## Frontend Architecture

### Page Structure

#### Box Scores Page (/)

**Layout:**
```
┌─────────────────────────────────────────────┐
│              Header / Navigation             │
│         "Baseball Box Scores for Herb"       │
├─────────────────────────────────────────────┤
│  Date Selector: [◀ Previous] [Date] [Next ▶]│
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Mets Game (if played on this date)  │  │
│  │  Away Team  vs  Home Team            │  │
│  │  Score: X - Y                         │  │
│  │  [Box Score Details Table]            │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Other Games                          │  │
│  │  [Box Score Details Tables]           │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Standings                            │  │
│  │  [Division Tables]                    │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  Link to Stats Page →                       │
└─────────────────────────────────────────────┘
```

#### Stats Page (/stats-for-kevin)

**Layout:**
```
┌─────────────────────────────────────────────┐
│              Header / Navigation             │
│         "Statistics for Kevin"               │
├─────────────────────────────────────────────┤
│  ← Back to Box Scores                        │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Batting Average Leaders              │  │
│  │  [Leaderboard Table]                  │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  TBR Leaders                          │  │
│  │  [Leaderboard Table]                  │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  TBR+ Leaders                         │  │
│  │  [Leaderboard Table]                  │  │
│  └──────────────────────────────────────┘  │
│                                              │
└─────────────────────────────────────────────┘
```

### Responsive Design Strategy

**Breakpoints:**
- Desktop: ≥1024px - Multi-column layout, full tables
- Tablet: 768px-1023px - Single column, scrollable tables
- Mobile: <768px - Stacked layout, simplified tables

**Mobile Optimizations:**
- Hide less important columns on small screens
- Use horizontal scroll for wide tables with sticky first column
- Increase touch target sizes for date navigation
- Simplify box score display to essential information

### CSS Architecture

**base.css:**
- Typography (Georgia serif, 16px base)
- Color palette (black text, off-white background)
- Layout utilities (flexbox, grid)
- Spacing system

**newspaper.css:**
- Newspaper-style theme
- Border styles (thin black lines)
- Table styling (alternating rows)
- Header typography (bold, larger)

**responsive.css:**
- Media queries for breakpoints
- Mobile-specific overrides
- Touch-friendly sizing


### Template Structure

**base.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Baseball Stats{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/newspaper.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/responsive.css') }}">
</head>
<body>
    <header>
        <h1>{% block header %}Baseball Statistics{% endblock %}</h1>
        <nav>{% block navigation %}{% endblock %}</nav>
    </header>
    
    <main>
        {% if error %}
        <div class="error-message">{{ error.message }}</div>
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>Data provided by MLB StatsAPI</p>
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

**box_scores.html:**
```html
{% extends "base.html" %}

{% block title %}Box Scores for Herb{% endblock %}
{% block header %}Baseball Box Scores for Herb{% endblock %}

{% block navigation %}
<a href="{{ url_for('stats.stats_page') }}">View Statistics →</a>
{% endblock %}

{% block content %}
<div class="date-selector">
    <a href="?date={{ previous_date }}" class="nav-button">◀ Previous</a>
    <span class="current-date">{{ selected_date }}</span>
    <a href="?date={{ next_date }}" class="nav-button">Next ▶</a>
</div>

{% for box_score in box_scores %}
<section class="box-score {% if box_score.is_mets %}mets-game{% endif %}">
    <h2>{{ box_score.away_team }} @ {{ box_score.home_team }}</h2>
    <div class="score">{{ box_score.away_score }} - {{ box_score.home_score }}</div>
    
    <table class="batting-stats">
        <!-- Batting statistics table -->
    </table>
    
    <table class="pitching-stats">
        <!-- Pitching statistics table -->
    </table>
</section>
{% endfor %}

<section class="standings">
    <h2>Standings</h2>
    {% for division, teams in standings.items() %}
    <h3>{{ division }}</h3>
    <table class="standings-table">
        <!-- Standings table -->
    </table>
    {% endfor %}
</section>
{% endblock %}
```

**stats.html:**
```html
{% extends "base.html" %}

{% block title %}Statistics for Kevin{% endblock %}
{% block header %}Statistics for Kevin{% endblock %}

{% block navigation %}
<a href="{{ url_for('box_scores.box_scores_page') }}">← Back to Box Scores</a>
{% endblock %}

{% block content %}
{% for leaderboard in leaderboards %}
<section class="leaderboard">
    <h2>{{ leaderboard.title }}</h2>
    <table class="leaderboard-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Team</th>
                {% for stat in leaderboard.columns %}
                <th>{{ stat.display_name }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for player in leaderboard.players %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ player.name }}</td>
                <td>{{ player.team }}</td>
                {% for stat in leaderboard.columns %}
                <td>{{ player.stats[stat.name] }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% endfor %}
{% endblock %}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following testable properties and performed redundancy elimination:

**Redundancies Identified:**
- Requirements 17.2, 18.1, 18.2, 18.3, 19.1, 20.3, 20.4, 20.5 are duplicates of earlier requirements
- Requirements 6.1-6.5, 10.1-10.6 are about code organization and test coverage, not functional behavior
- Requirements 9.1-9.4, 13.1-13.7 are about UI/UX design, not programmatically testable
- Requirements 14.1-14.5 are about architecture design for future extensibility
- Requirements 21.1-23.4 are future enhancements, not current behavior

**Properties Consolidated:**
- Cache metadata properties (7.1, 4.5) can be combined into one comprehensive property
- Date selection properties (15.8, 18.2, 18.3) are redundant, consolidated into one
- TBR calculation properties (16.6, 20.1, 20.2) consolidated into calculation correctness

### Property 1: Serialization Round Trip

*For any* valid Python data structure (dict, list, primitives), serializing to JSON and then deserializing should produce an equivalent data structure.

**Validates: Requirements 1.1**

### Property 2: Data Structure Validation

*For any* deserialized data, if the data structure is invalid for the expected type, the deserializer should reject it and return an empty result of the appropriate type.

**Validates: Requirements 1.3**

### Property 3: Environment Configuration Override

*For any* configuration key that has both a file value and an environment variable set, the environment variable value should take precedence.

**Validates: Requirements 2.5**

### Property 4: Log Entry Metadata

*For any* log entry created by the logger, the entry should contain a timestamp and context information (module name, log level).

**Validates: Requirements 3.3**

### Property 5: Cache Metadata Completeness

*For any* cache entry stored by the cache manager, the entry should include metadata with creation timestamp, cache type, and expiration time.

**Validates: Requirements 7.1, 4.5**

### Property 6: Cache Expiration Validation

*For any* cache entry retrieval, if the entry's age exceeds the configured TTL for its cache type, the cache manager should treat it as a cache miss and return None.

**Validates: Requirements 7.2, 7.3**

### Property 7: Cached Data Reuse

*For any* data request that has been cached and not expired, subsequent identical requests should return the cached data without making additional API calls.

**Validates: Requirements 4.4**

### Property 8: Invalid Input Error Messages

*For any* invalid user input (malformed dates, invalid parameters), the error handler should return a user-friendly error message without exposing internal details.

**Validates: Requirements 5.4**

### Property 9: API Response Normalization

*For any* API response from MLB StatsAPI, the API client should return data in the application's internal data model format, not the raw API response structure.

**Validates: Requirements 8.5**

### Property 10: API Request Logging

*For any* API request made by the API client, a log entry should be created containing the endpoint, parameters, and response time.

**Validates: Requirements 8.4**

### Property 11: Stat Definition Metadata

*For any* stat definition in the system, it should contain all required fields: name, display_name, stat_group, calculation_method, sort_descending, qualification_threshold, and format_string.

**Validates: Requirements 11.5**

### Property 12: Leaderboard Stat Flexibility

*For any* valid stat definition, the leaderboard generator should be able to generate a leaderboard sorted by that statistic.

**Validates: Requirements 12.1, 12.3**

### Property 13: Qualification Threshold Application

*For any* leaderboard generation with a qualification threshold, only players meeting or exceeding the threshold (plate appearances ≥ threshold × team games) should appear in the results.

**Validates: Requirements 12.4**

### Property 14: Mets Game Prioritization

*For any* date where the Mets played, the Mets box score should appear first in the list of box scores returned by the box score generator.

**Validates: Requirements 15.3**

### Property 15: Date Selection Data Consistency

*For any* valid historical date selected, the box scores and standings displayed should correspond to that specific date, not the current date.

**Validates: Requirements 15.8**

### Property 16: Future Date Rejection

*For any* date in the future, the application should reject it as invalid and return an error rather than attempting to fetch data.

**Validates: Requirements 18.4**

### Property 17: Historical Box Score Caching

*For any* historical date's box scores that have been fetched once, subsequent requests for the same date should use cached data.

**Validates: Requirements 18.5**

### Property 18: Non-Mets Game Ordering Consistency

*For any* set of non-Mets games on a given date, the ordering of those games should be consistent across multiple requests (deterministic ordering).

**Validates: Requirements 17.3**

### Property 19: Standings Data Completeness

*For any* team in the standings, the data should include team name, wins, losses, winning percentage, and games back.

**Validates: Requirements 19.2**

### Property 20: TBR Calculation Correctness

*For any* player with valid statistics, TBR should be calculated as Total Bases divided by Runs, where Total Bases = (1B × 1) + (2B × 2) + (3B × 3) + (HR × 4), and division by zero should be handled gracefully.

**Validates: Requirements 20.1, 16.6**

### Property 21: TBR+ Calculation Correctness

*For any* player TBR and league average TBR, TBR+ should be calculated as (Player TBR / League Average TBR) × 100, rounded to the nearest integer.

**Validates: Requirements 20.2**


## Error Handling

### Error Categories

**API Errors:**
- Network timeouts
- HTTP error responses (4xx, 5xx)
- Malformed API responses
- Rate limiting

**Cache Errors:**
- File system permission issues
- Corrupted cache files
- Disk space exhaustion
- Invalid JSON in cache

**Validation Errors:**
- Invalid date formats
- Future dates
- Missing required parameters
- Invalid stat types

**Configuration Errors:**
- Missing configuration file
- Invalid YAML syntax
- Missing required configuration keys
- Invalid configuration values

### Error Handling Strategy

**Retry Logic:**
```python
# Exponential backoff for transient failures
attempt = 0
while attempt < max_attempts:
    try:
        return make_api_call()
    except TransientError as e:
        wait_time = backoff_base ** attempt
        logger.warning(f"Retry {attempt + 1}/{max_attempts} after {wait_time}s")
        time.sleep(wait_time)
        attempt += 1
raise APIClientException("Max retries exceeded")
```

**Graceful Degradation:**
- Cache read failure → Treat as cache miss, fetch from API
- API failure after retries → Return error page with helpful message
- Partial data failure → Display available data with warning
- Configuration missing → Use sensible defaults where possible

**Error Logging:**
- All errors logged with full context (stack trace, request parameters)
- User-facing errors logged at WARNING level
- System errors logged at ERROR level
- Critical failures (config errors) logged at CRITICAL level

**User-Facing Error Messages:**
- "Unable to load box scores. Please try again later."
- "Invalid date selected. Please choose a date in the past."
- "Statistics temporarily unavailable. Please try again in a few minutes."
- "The Mets didn't play on this date."

### Error Recovery

**Automatic Recovery:**
- Retry transient API failures with exponential backoff
- Recreate cache directory if missing
- Fall back to API if cache is corrupted

**Manual Recovery:**
- Clear cache endpoint for administrators
- Configuration reload without restart
- Health check endpoint for monitoring


## Testing Strategy

### Dual Testing Approach

The application requires both unit tests and property-based tests for comprehensive coverage. These testing approaches are complementary:

**Unit Tests** verify:
- Specific examples and edge cases
- Integration points between components
- Error conditions and exception handling
- Flask route responses and status codes

**Property-Based Tests** verify:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Invariants and mathematical relationships
- Round-trip properties (serialization, caching)

### Property-Based Testing Configuration

**Library Selection:**
- Python: Use `hypothesis` library for property-based testing
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property

**Test Tagging Format:**
```python
@given(st.dictionaries(st.text(), st.integers()))
def test_serialization_round_trip(data):
    """
    Feature: flask-app-refactoring-optimization
    Property 1: For any valid Python data structure, serializing to JSON 
    and then deserializing should produce an equivalent data structure.
    """
    serialized = DataSerializer.serialize(data)
    deserialized = DataSerializer.deserialize(serialized)
    assert deserialized == data
```

### Unit Test Coverage

**Cache Manager Tests:**
- Test cache hit/miss scenarios
- Test expiration logic with various TTL values
- Test directory creation
- Test cache invalidation
- Test corrupted cache file handling

**Data Serializer Tests:**
- Test JSON serialization of various data types
- Test deserialization failure handling
- Test datetime object handling
- Test validation of deserialized structures

**Configuration Manager Tests:**
- Test loading valid configuration file
- Test environment variable overrides
- Test missing configuration keys with defaults
- Test invalid YAML handling

**Stats Calculator Tests:**
- Test TBR calculation with various inputs
- Test TBR+ calculation with various league averages
- Test division by zero handling
- Test total bases calculation

**API Client Tests (with mocking):**
- Test retry logic with simulated failures
- Test timeout handling
- Test response normalization
- Test cache integration

**Flask Route Tests:**
- Test box scores page returns 200 status
- Test stats page returns 200 status
- Test date parameter handling
- Test error page rendering
- Test navigation links present

### Property-Based Test Coverage

**Property 1: Serialization Round Trip**
```python
@given(st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children)
))
def test_serialization_round_trip(data):
    # Test implementation
```

**Property 3: Environment Configuration Override**
```python
@given(st.text(min_size=1), st.text(), st.text())
def test_env_override(key, file_value, env_value):
    # Test implementation
```

**Property 6: Cache Expiration Validation**
```python
@given(st.integers(min_value=1, max_value=3600), 
       st.integers(min_value=0, max_value=7200))
def test_cache_expiration(ttl, age):
    # Test implementation
```

**Property 13: Qualification Threshold Application**
```python
@given(st.lists(player_stats_strategy(), min_size=10),
       st.floats(min_value=2.0, max_value=4.0))
def test_qualification_threshold(players, threshold):
    # Test implementation
```

**Property 20: TBR Calculation Correctness**
```python
@given(st.integers(min_value=0, max_value=200),  # singles
       st.integers(min_value=0, max_value=100),  # doubles
       st.integers(min_value=0, max_value=50),   # triples
       st.integers(min_value=0, max_value=100),  # home runs
       st.integers(min_value=0, max_value=200))  # runs
def test_tbr_calculation(singles, doubles, triples, hrs, runs):
    # Test implementation
```

### Test Organization

```
tests/
├── unit/
│   ├── test_cache_manager.py
│   ├── test_serializer.py
│   ├── test_config_manager.py
│   ├── test_stats_calculator.py
│   ├── test_api_client.py
│   ├── test_box_score_generator.py
│   ├── test_leaderboard_generator.py
│   └── test_standings_generator.py
├── integration/
│   ├── test_box_scores_route.py
│   ├── test_stats_route.py
│   └── test_error_handling.py
├── property/
│   ├── test_serialization_properties.py
│   ├── test_cache_properties.py
│   ├── test_calculation_properties.py
│   └── test_leaderboard_properties.py
└── conftest.py  # Shared fixtures and strategies
```

### Coverage Goals

- Overall code coverage: 70%+ for core business logic
- Cache Manager: 90%+ coverage
- Data Serializer: 90%+ coverage
- Stats Calculator: 95%+ coverage
- API Client: 80%+ coverage (excluding external API calls)
- Route Handlers: 70%+ coverage

### Testing Best Practices

1. Use fixtures for common test data (sample games, players, stats)
2. Mock external API calls in unit tests
3. Use hypothesis strategies for generating valid test data
4. Test edge cases explicitly (empty lists, zero values, None)
5. Test error paths as thoroughly as happy paths
6. Keep tests fast (<5 seconds for full suite)
7. Run property tests with high iteration counts in CI (1000+)

