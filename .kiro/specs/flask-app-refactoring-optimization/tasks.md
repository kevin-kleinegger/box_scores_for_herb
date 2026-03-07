# Implementation Plan: Flask Baseball Statistics Application Refactoring

## Overview

This implementation plan refactors an existing Flask baseball statistics application to improve security, performance, maintainability, and user experience. The refactoring addresses technical debt including unsafe serialization, hardcoded configuration, performance bottlenecks (1200+ API calls), and poor separation of concerns. The target is <100 API calls and <30 second leaderboard generation with 70%+ test coverage.

## Completed Tasks

- [x] 1-10. Infrastructure and data layer (all completed in previous sessions)
  - Configuration management, logging, serialization, caching, data models, API client, statistics calculator
  - All unit and integration tests passing

- [x] 11. Implement box score generator
  - [x] 11.1 BoxScoreGenerator service with Mets prioritization, offseason fallback, linescore generation
  - [x] 11.2 Integration tests (all passing)

- [x] 12. Implement standings generator  
  - [x] 12.1 StandingsGenerator service with AL/NL side-by-side display, caching
  - [x] 12.2 Integration tests (all passing)

- [x] 13. Implement leaderboard generator
  - [x] 13.1 LeaderboardGenerator service with 18 stats (10 hitting, 6 pitching, 2 custom TBR/TBR+)
  - [x] 13.2 Integration tests (all passing)
  - Performance: ~113 API calls, 19s first run, 0.26s cached (73x speedup)

- [x] 14. Create cache warming script
  - [x] 14.1 warm_cache.py for daily scheduled cache refresh (~16s runtime)

- [x] 15. Implement Flask routes
  - [x] 15.1 Box scores routes (/, /date/<date>, /submit_date)
  - [x] 15.2 Stats route (/stats-for-kevin)

- [x] 16. Create Flask application
  - [x] 16.1 flask_site_new.py with all services initialized

- [x] 17. Implement minimal frontend templates
  - [x] 17.1 index_new.html (box scores with linescore, standings)
  - [x] 17.2 stats_new.html (leaderboards)
  - [x] 17.3 error.html

- [x] 18. Recent improvements
  - [x] 18.1 Added linescore (inning-by-inning scoring) display
  - [x] 18.2 Centered all content (standings, linescores, box scores)
  - [x] 18.3 Removed redundant headers and final score lines
  - [x] 18.4 Hide standings during spring training/offseason
  - [x] 18.5 Side-by-side AL/NL standings layout

## Remaining Tasks

### High Priority

- [ ] 19. Polish and improve templates
  - [ ] 19.1 Improve visual styling (currently minimal)
  - [ ] 19.2 Add responsive CSS for mobile/tablet
  - [ ] 19.3 Consider newspaper theme styling
  - [ ] 19.4 Add date navigation (previous/next buttons)

- [ ] 20. Testing and validation
  - [ ] 20.1 Add route integration tests
  - [ ] 20.2 Manual testing across all baseball time periods
  - [ ] 20.3 Performance validation (<100 API calls, <30s)

- [ ] 21. Cleanup and migration
  - [ ] 21.1 Remove old implementation files (box_scores.py, stats.py, flask_site.py, utils.py)
  - [ ] 21.2 Rename flask_site_new.py → flask_site.py
  - [ ] 21.3 Rename templates (index_new.html → index.html, stats_new.html → stats.html)
  - [ ] 21.4 Update any remaining references

- [ ] 22. Deployment preparation
  - [ ] 22.1 Update PythonAnywhere configuration
  - [ ] 22.2 Set up cache warming scheduled task
  - [ ] 22.3 Test in production environment
  - [ ] 22.4 Update README with new architecture

### Optional (Property-Based Tests)

- [ ]* Property tests for serialization, caching, API client, statistics, routes
  - These provide additional validation but are not required for MVP

## Notes

- All core functionality is working and tested
- Performance targets met: ~113 API calls, <1s with caching
- Focus now on polish, cleanup, and deployment
- Property tests marked with `*` are optional enhancements
