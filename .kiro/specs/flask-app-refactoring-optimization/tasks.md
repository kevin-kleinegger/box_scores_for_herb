# Implementation Plan: Flask Baseball Statistics Application Refactoring

## Overview

This implementation plan refactors an existing Flask baseball statistics application to improve security, performance, maintainability, and user experience. The refactoring addresses technical debt including unsafe serialization, hardcoded configuration, performance bottlenecks (1200+ API calls), and poor separation of concerns. The target is <100 API calls and <30 second leaderboard generation with 70%+ test coverage.

## Tasks

- [x] 1. Set up project structure and infrastructure layer
  - Create directory structure for modules (config/, utils/, data/, services/, routes/, models/, static/, templates/, tests/)
  - Set up Python package structure with __init__.py files
  - Create requirements.txt with dependencies (Flask, PyYAML, requests, hypothesis, pytest, pytest-cov)
  - _Requirements: 6.1, 6.2_

- [x] 2. Implement configuration management
  - [x] 2.1 Create configuration file structure
    - Create config/settings.yaml with cache, API, logging, theme, and leaderboard settings
    - Define configuration schema for all application settings
    - _Requirements: 2.1, 2.3, 2.4, 2.6, 2.7_
  
  - [x] 2.2 Implement ConfigurationManager class
    - Write config/config_manager.py with YAML loading and access methods
    - Implement get(), get_cache_dir(), get_cache_ttl(), get_api_timeout(), get_api_base_url(), get_theme_settings()
    - Add environment variable override support
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [x]* 2.3 Write unit tests for ConfigurationManager
    - Test loading valid configuration file
    - Test environment variable overrides
    - Test missing configuration keys with defaults
    - Test invalid YAML handling
    - _Requirements: 10.3_
  
  - [ ]* 2.4 Write property test for configuration
    - **Property 3: Environment Configuration Override**
    - **Validates: Requirements 2.5**

- [x] 3. Implement structured logging
  - [x] 3.1 Create Logger utility class
    - Write utils/logger.py with setup() and get_logger() methods
    - Configure log levels, file output, and rotation based on configuration
    - Add structured logging with context information
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 3.2 Define custom exception classes
    - Write utils/exceptions.py with BaseballAppException, APIClientException, CacheException, ValidationException, ConfigurationException
    - _Requirements: 5.5_

- [x] 4. Implement data serialization
  - [x] 4.1 Create DataSerializer class
    - Write data/serializer.py with serialize(), deserialize(), validate_structure() methods
    - Use json.dumps() and json.loads() exclusively
    - Add datetime handling with custom encoder
    - Add validation and error logging
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x]* 4.2 Write unit tests for DataSerializer
    - Test JSON serialization of various data types
    - Test deserialization failure handling
    - Test datetime object handling
    - Test validation of deserialized structures
    - _Requirements: 10.2_
  
  - [ ]* 4.3 Write property test for serialization round trip
    - **Property 1: Serialization Round Trip**
    - **Validates: Requirements 1.1**
  
  - [ ]* 4.4 Write property test for data structure validation
    - **Property 2: Data Structure Validation**
    - **Validates: Requirements 1.3**

- [x] 5. Implement cache management
  - [x] 5.1 Create CacheManager class
    - Write data/cache_manager.py with get(), set(), invalidate(), clear_expired() methods
    - Implement cache entry structure with metadata (timestamp, cache_type, key)
    - Add expiration validation based on TTL configuration
    - Create cache directory if it doesn't exist
    - Use SHA256 hash of key for filenames
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 4.4, 4.5_
  
  - [x]* 5.2 Write unit tests for CacheManager
    - Test cache hit/miss scenarios
    - Test expiration logic with various TTL values
    - Test directory creation
    - Test cache invalidation
    - Test corrupted cache file handling
    - _Requirements: 10.1_
  
  - [ ]* 5.3 Write property test for cache metadata
    - **Property 5: Cache Metadata Completeness**
    - **Validates: Requirements 7.1, 4.5**
  
  - [ ]* 5.4 Write property test for cache expiration
    - **Property 6: Cache Expiration Validation**
    - **Validates: Requirements 7.2, 7.3**
  
  - [ ]* 5.5 Write property test for cached data reuse
    - **Property 7: Cached Data Reuse**
    - **Validates: Requirements 4.4**

- [x] 6. Checkpoint - Ensure infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement data models
  - [x] 7.1 Create game and team data models
    - Write models/game.py with Game, Team, BoxScore, BatterStats, PitcherStats, InningScore dataclasses
    - _Requirements: 11.1_
  
  - [x] 7.2 Create player statistics data models
    - Write models/player_stats.py with PlayerStats dataclass including offensive stats and custom calculated stats
    - Add is_qualified() method for qualification threshold checking
    - _Requirements: 11.1, 11.2, 11.6_
  
  - [x] 7.3 Create standings data models
    - Write models/game.py (append) with Standings and TeamRecord dataclasses
    - _Requirements: 11.1_
  
  - [x] 7.4 Create stat definition model
    - Write models/stat_definition.py with StatDefinition dataclass and format_value() method
    - Define STAT_DEFINITIONS dictionary with batting_average, tbr, tbr_plus configurations
    - _Requirements: 11.5, 12.1_

- [x] 8. Implement API client with retry logic
  - [x] 8.1 Create MLBStatsAPIClient class structure
    - Write data/api_client.py with __init__(), _make_request(), _retry_with_backoff() methods
    - Implement exponential backoff retry logic (3 attempts, base 2)
    - Add request logging with parameters and response times
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 5.1, 5.2_
  
  - [x] 8.2 Implement game and box score API methods
    - Add get_games_by_date() and get_box_score() methods
    - Normalize API responses to internal Game and BoxScore models
    - Integrate with CacheManager for caching
    - _Requirements: 8.5, 8.6_
  
  - [x] 8.3 Implement standings API methods
    - Add get_standings() method
    - Normalize API responses to internal Standings model
    - Integrate with CacheManager for caching
    - _Requirements: 8.5, 8.6, 19.4, 19.5_
  
  - [x] 8.4 Implement player statistics API methods
    - Add get_player_stats(), get_season_stats_batch(), get_qualified_players() methods
    - Implement batch fetching strategy (50 players per batch)
    - Normalize API responses to internal PlayerStats model
    - Integrate with CacheManager for caching
    - _Requirements: 8.5, 8.6, 4.1, 4.2_
  
  - [ ]* 8.5 Write unit tests for API client (with mocking)
    - Test retry logic with simulated failures
    - Test timeout handling
    - Test response normalization
    - Test cache integration
  
  - [ ]* 8.6 Write property test for API response normalization
    - **Property 9: API Response Normalization**
    - **Validates: Requirements 8.5**
  
  - [ ]* 8.7 Write property test for API request logging
    - **Property 10: API Request Logging**
    - **Validates: Requirements 8.4**

- [x] 9. Implement statistics calculator
  - [x] 9.1 Create StatsCalculator class
    - Write services/stats_calculator.py with calculate_tbr(), calculate_tbr_plus(), get_league_average_tbr(), calculate_total_bases() methods
    - Implement TBR formula: Total Bases / Runs (handle division by zero)
    - Implement TBR+ formula: (Player TBR / League Average TBR) × 100
    - Implement Total Bases formula: (1B × 1) + (2B × 2) + (3B × 3) + (HR × 4)
    - _Requirements: 20.1, 20.2, 16.6_
  
  - [ ]* 9.2 Write unit tests for StatsCalculator
    - Test TBR calculation with various inputs
    - Test TBR+ calculation with various league averages
    - Test division by zero handling
    - Test total bases calculation
    - _Requirements: 10.4_
  
  - [ ]* 9.3 Write property test for TBR calculation
    - **Property 20: TBR Calculation Correctness**
    - **Validates: Requirements 20.1, 16.6**
  
  - [ ]* 9.4 Write property test for TBR+ calculation
    - **Property 21: TBR+ Calculation Correctness**
    - **Validates: Requirements 20.2**

- [x] 10. Checkpoint - Ensure data layer tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement box score generator
  - [ ] 11.1 Create BoxScoreGenerator class
    - Write services/box_score_generator.py with generate_for_date(), _prioritize_mets(), _format_box_score() methods
    - Implement Mets prioritization logic (Mets game first if present)
    - Handle offseason dates: if no games found for requested date, find and display most recent game date
    - _Requirements: 17.1, 17.2, 17.3, 15.3_
  
  - [ ]* 11.2 Write property test for Mets prioritization
    - **Property 14: Mets Game Prioritization**
    - **Validates: Requirements 15.3**
  
  - [ ]* 11.3 Write property test for non-Mets game ordering
    - **Property 18: Non-Mets Game Ordering Consistency**
    - **Validates: Requirements 17.3**

- [ ] 12. Implement standings generator
  - [ ] 12.1 Create StandingsGenerator class
    - Write services/standings_generator.py with generate_for_date(), _format_standings(), _highlight_team() methods
    - Organize standings by division
    - Add Mets highlighting metadata
    - _Requirements: 17.4, 19.1, 19.3_
  
  - [ ]* 12.2 Write property test for standings data completeness
    - **Property 19: Standings Data Completeness**
    - **Validates: Requirements 19.2**

- [ ] 13. Implement leaderboard generator with optimization
  - [ ] 13.1 Create LeaderboardGenerator class
    - Write services/leaderboard_generator.py with generate(), _get_qualified_players(), _batch_fetch_stats(), _apply_qualification(), _sort_by_stat() methods
    - For standard stats (AVG, HR, RBI, OBP, SLG, OPS, ERA, W, K, SV, IP, WHIP): use `/stats/leaders` endpoint (1 API call per stat)
    - For custom stats (TBR, TBR+): fetch OPS leaders as base (top 100 players), then calculate TBR/TBR+ using StatsCalculator
    - Cache all player stats for 1 hour reuse
    - Generate all leaderboards from single cached dataset
    - _Requirements: 4.1, 4.2, 4.3, 12.1, 12.2, 12.3, 12.4_
  
  - [ ]* 13.2 Write property test for stat definition metadata
    - **Property 11: Stat Definition Metadata**
    - **Validates: Requirements 11.5**
  
  - [ ]* 13.3 Write property test for leaderboard stat flexibility
    - **Property 12: Leaderboard Stat Flexibility**
    - **Validates: Requirements 12.1, 12.3**
  
  - [ ]* 13.4 Write property test for qualification threshold
    - **Property 13: Qualification Threshold Application**
    - **Validates: Requirements 12.4**

- [ ] 14. Implement error handler
  - [ ] 14.1 Create ErrorHandler class
    - Write utils/exceptions.py (append) with ErrorHandler class
    - Implement handle_api_error(), handle_cache_error(), handle_validation_error(), format_error_response() methods
    - Add user-friendly error message formatting
    - _Requirements: 5.4_
  
  - [ ]* 14.2 Write property test for error messages
    - **Property 8: Invalid Input Error Messages**
    - **Validates: Requirements 5.4**

- [ ] 15. Checkpoint - Ensure business logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement Flask routes
  - [ ] 16.1 Create box scores route handler
    - Write routes/box_scores.py with box_scores_page() route handler for "/"
    - Implement date selection logic (default to previous day)
    - Integrate BoxScoreGenerator and StandingsGenerator
    - Add date validation (reject future dates)
    - Add error handling with ErrorHandler
    - _Requirements: 15.1, 15.2, 15.7, 15.8, 18.1, 18.2, 18.3, 18.4_
  
  - [ ] 16.2 Create stats route handler
    - Write routes/stats.py with stats_page() route handler for "/stats-for-kevin"
    - Integrate LeaderboardGenerator with TBR and TBR+ stat definitions
    - Add error handling with ErrorHandler
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 20.3_
  
  - [ ]* 16.3 Write integration tests for box scores route
    - Test box scores page returns 200 status
    - Test date parameter handling
    - Test error page rendering
    - Test Mets prioritization in response
    - _Requirements: 10.5_
  
  - [ ]* 16.4 Write integration tests for stats route
    - Test stats page returns 200 status
    - Test leaderboard data in response
    - Test error page rendering
    - _Requirements: 10.5_
  
  - [ ]* 16.5 Write property test for date selection consistency
    - **Property 15: Date Selection Data Consistency**
    - **Validates: Requirements 15.8**
  
  - [ ]* 16.6 Write property test for future date rejection
    - **Property 16: Future Date Rejection**
    - **Validates: Requirements 18.4**
  
  - [ ]* 16.7 Write property test for historical box score caching
    - **Property 17: Historical Box Score Caching**
    - **Validates: Requirements 18.5**

- [ ] 17. Create Flask application entry point
  - [ ] 17.1 Create app.py with Flask application setup
    - Initialize Flask app
    - Register blueprints for box_scores and stats routes
    - Configure logging with Logger
    - Load configuration with ConfigurationManager
    - Add error handlers for 404, 500 errors
    - _Requirements: 6.1_

- [ ] 18. Implement responsive frontend templates
  - [ ] 18.1 Create base template
    - Write templates/base.html with header, navigation, main content block, footer
    - Include CSS links for base.css, newspaper.css, responsive.css
    - Add error message display block
    - _Requirements: 13.1, 9.1_
  
  - [ ] 18.2 Create box scores template
    - Write templates/box_scores.html extending base.html
    - Add date selector with previous/next navigation
    - Display box scores with Mets game highlighted
    - Display batting and pitching statistics tables
    - Display standings organized by division
    - Add link to stats page
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.7, 9.1_
  
  - [ ] 18.3 Create stats template
    - Write templates/stats.html extending base.html
    - Display leaderboard tables for batting average, TBR, TBR+
    - Add link back to box scores page
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 9.1_

- [ ] 19. Implement responsive CSS styling
  - [ ] 19.1 Create base CSS
    - Write static/css/base.css with typography (Georgia serif, 16px base), color palette, layout utilities, spacing system
    - _Requirements: 13.1, 13.3, 13.7_
  
  - [ ] 19.2 Create newspaper theme CSS
    - Write static/css/newspaper.css with newspaper-style theme, border styles, table styling, header typography
    - _Requirements: 13.2, 13.3, 13.4_
  
  - [ ] 19.3 Create responsive CSS
    - Write static/css/responsive.css with media queries for desktop (≥1024px), tablet (768px-1023px), mobile (<768px)
    - Implement mobile optimizations: hide less important columns, horizontal scroll for tables, larger touch targets
    - _Requirements: 9.2, 9.3, 9.4, 13.6_

- [ ] 20. Checkpoint - Ensure frontend renders correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 21. Replace unsafe serialization in existing code
  - [ ] 21.1 Identify all uses of ast.literal_eval() in existing codebase
    - Search for ast.literal_eval() calls
    - Document each usage location and context
    - _Requirements: 1.2_
  
  - [ ] 21.2 Replace ast.literal_eval() with DataSerializer
    - Replace all ast.literal_eval() calls with DataSerializer.deserialize()
    - Update cache reading code to use new serialization
    - _Requirements: 1.1, 1.2_
  
  - [ ] 21.3 Replace print statements with Logger calls
    - Search for all print() statements
    - Replace with appropriate Logger calls (info, warning, error)
    - Add context information to log calls
    - _Requirements: 3.1_

- [ ] 22. Migrate existing functionality to new architecture
  - [ ] 22.1 Migrate existing box score logic
    - Extract existing box score generation code
    - Refactor to use BoxScoreGenerator and MLBStatsAPIClient
    - Remove hardcoded file paths and configuration
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [ ] 22.2 Migrate existing leaderboard logic
    - Extract existing leaderboard generation code
    - Refactor to use LeaderboardGenerator, StatsCalculator, and MLBStatsAPIClient
    - Implement batch fetching optimization
    - Remove hardcoded file paths and configuration
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [ ] 22.3 Migrate existing cache logic
    - Extract existing cache code
    - Refactor to use CacheManager and DataSerializer
    - Update cache keys and metadata structure
    - _Requirements: 6.3, 7.5_

- [ ] 23. Performance validation
  - [ ] 23.1 Measure leaderboard generation performance
    - Run leaderboard generation and count API calls
    - Measure total generation time
    - Verify <100 API calls and <30 seconds
    - _Requirements: 4.1, 4.3_
  
  - [ ] 23.2 Verify caching effectiveness
    - Test cache hit rates for repeated requests
    - Verify cache expiration behavior
    - Test batch fetching reduces API calls
    - _Requirements: 4.4, 7.2, 7.3_

- [ ] 24. Final integration testing
  - [ ]* 24.1 Run full test suite
    - Execute all unit tests, integration tests, and property tests
    - Verify 70%+ code coverage for core business logic
    - _Requirements: 10.6_
  
  - [ ] 24.2 Manual testing of user workflows
    - Test box scores page with date selection
    - Test stats page with leaderboards
    - Test error handling scenarios
    - Test responsive design on different screen sizes
    - _Requirements: 9.3, 9.4, 13.6_
  
  - [ ] 24.3 Verify all requirements met
    - Review requirements document
    - Confirm all acceptance criteria satisfied
    - Document any deviations or future enhancements

- [ ] 25. Final checkpoint - Deployment readiness
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The refactoring maintains existing functionality while improving code quality
- Performance optimization focuses on batch API fetching and caching
- Frontend refactoring replaces `<pre>` tags with responsive HTML tables
- All configuration is externalized to settings.yaml
- All logging uses structured Logger instead of print statements
