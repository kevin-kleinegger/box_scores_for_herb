# Baseball Box Scores for Herb

A Flask web application that displays baseball box scores and statistics leaderboards, featuring custom metrics like TBR (Total Bases per Run).

## Features

- **Box Scores Page**: Daily baseball box scores with Mets games prioritized
- **Stats Page**: Player leaderboards with custom statistics (TBR, TBR+)
- **Responsive Design**: Newspaper-style aesthetic optimized for all devices
- **Smart Caching**: Reduces API calls and improves performance

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

### Configuration

Configuration is managed in `config/settings.yaml`. Key settings:

- **Cache TTL**: How long to cache data (default: 1 hour for stats, 24 hours for box scores)
- **API Settings**: Timeout and retry configuration for MLB StatsAPI
- **Logging**: Log level and file location
- **Theme**: Visual styling preferences

To override settings, you can use environment variables (prefixed with `BASEBALL_`).

### Directory Structure

```
box_scores_for_herb/
├── config/           # Configuration management
├── data/             # API client, caching, serialization
├── services/         # Business logic (generators, calculators)
├── routes/           # Flask route handlers
├── models/           # Data models
├── utils/            # Logging and error handling
├── static/           # CSS and JavaScript
├── templates/        # HTML templates
├── tests/            # Unit and integration tests
├── cache/            # Cached data (auto-created, not in git)
└── logs/             # Application logs (auto-created, not in git)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only property-based tests
pytest tests/property/
```

### Development Workflow

1. Make changes to code
2. Test changes: `pytest` or run the app locally
3. Commit when tests pass: `git commit -m "description"`
4. Push at major checkpoints

### Deployment (PythonAnywhere)

1. Pull the latest code: `git pull`
2. Install/update dependencies: `pip install -r requirements.txt`
3. Reload the web app from PythonAnywhere dashboard

The `cache/` and `logs/` directories will be created automatically on first run.

## Pages

- **`/`** - Box Scores for Herb (default landing page)
- **`/stats-for-kevin`** - Statistics leaderboards

## Custom Statistics

- **TBR (Total Bases per Run)**: Measures offensive efficiency
- **TBR+**: TBR normalized to league average (100 = average)

## License

Personal project for displaying baseball statistics.
