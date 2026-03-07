---
inclusion: auto
---

# Baseball-Specific Testing Guidelines

When testing baseball statistics features, always consider these distinct time periods in the MLB calendar:

## MLB Calendar Periods

1. **Spring Training** (Late February - Late March)
   - Games are played but don't count toward regular season stats
   - Box scores page: SHOULD show spring training games
   - Stats/leaderboards page: Should NOT include spring training stats (use regular season only)
   - Regular season stat leaders will be empty or from previous season

2. **Regular Season** (Late March - Late September)
   - Primary season with 162 games per team
   - Stats accumulate throughout the season
   - All features should work normally

3. **All-Star Break** (Mid-July, typically 3-4 days)
   - No games scheduled
   - Stats are still available (season-to-date)
   - Should NOT fall back to previous season

4. **Postseason** (October)
   - Playoff games only (not all teams playing)
   - Regular season stats are final
   - Standings API may return empty for postseason dates

5. **Offseason** (November - February)
   - No games scheduled
   - Should fall back to most recent completed season
   - Previous season's final stats available

## Testing Checklist

When implementing or testing date-dependent features:

- [ ] Test with a regular season date (e.g., July 1, 2024)
- [ ] Test with All-Star break date (e.g., July 15, 2024)
- [ ] Test with postseason date (e.g., October 15, 2024)
- [ ] Test with offseason date (e.g., December 1, 2024)
- [ ] Test with spring training date (e.g., March 1, 2024)
- [ ] Test with current date (whatever today is)

## Common Pitfalls

- **Don't use "no games today" to detect offseason** - All-Star break would incorrectly trigger fallback
- **Don't assume current calendar year = current season** - In January-March, previous year is active season
- **Box scores vs Stats pages handle spring training differently** - Box scores show spring games, stats/leaderboards ignore them
- **Check for empty API responses** - Postseason dates may return no standings/games

## Example Test Dates (2024 Season)

- Regular season: `2024-07-01` (games available, stats accumulating)
- All-Star break: `2024-07-15` (no games, but 2024 stats exist)
- Postseason: `2024-10-15` (playoff games only)
- Offseason: `2024-12-01` (no games, fall back to 2024 final stats)
- Spring training: `2024-03-15` (spring games, but no regular season stats yet)
