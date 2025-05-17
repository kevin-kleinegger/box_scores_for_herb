import statsapi
import requests

stats_to_check_qualifying = ["tbr", "avg", "obp", "slg", "ops", "babip"]

def calculate_tbr(player_stats):
    try:
        # Extract necessary statistics
        h = int(player_stats.get('hits', 0))
        doubles = int(player_stats.get('doubles', 0))
        triples = int(player_stats.get('triples', 0))
        hr = int(player_stats.get('homeRuns', 0))
        bb = int(player_stats.get('baseOnBalls', 0))
        hbp = int(player_stats.get('hitByPitch', 0))
        sb = int(player_stats.get('stolenBases', 0))
        cs = int(player_stats.get('caughtStealing', 0))
        sf = int(player_stats.get('sacFlies', 0))
        sh = int(player_stats.get('sacBunts', 0))
        gidp = int(player_stats.get('groundIntoDoublePlay', 0))
        pa = int(player_stats.get('plateAppearances', 0))
        
        # Calculate singles
        singles = h - doubles - triples - hr
        
        # Calculate numerator and denominator
        numerator = singles + 2*doubles + 3*triples + 4*hr + bb + hbp + 0.5*sb + 0.5*sf + 0.5*sh - 0.5*gidp - 0.5*cs
        
        # Avoid division by zero
        if pa == 0:
            return 0.0
        
        tbr = numerator / pa
        return round(tbr, 3)
    except Exception as e:
        print(f"Error calculating TBR: {e}")
        return 0.0

def get_player_ids():
    # Retrieve list of active players
    teams = statsapi.get('teams', {'sportIds': 1})['teams']
    player_ids = set()
    for team in teams:
        roster = statsapi.get('team_roster', {'teamId': team['id'], 'rosterType': 'active'})
        for player in roster['roster']:
            player_ids.add(player['person']['id'])
    return list(player_ids)

def get_player_stats(data):
    stats_list = data.get('stats', [])
    
    if stats_list:
        # Use the first season (most recent)
        return stats_list[0]['stats']
    return {}

def get_team_games_played(team_id, season=2025):
    url = f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats'
    params = {
        'season': season,
        'group': 'hitting',
        'stats': 'season'
    }
    r = requests.get(url, params=params).json()
    return r['stats'][0]['splits'][0]['stat']['gamesPlayed']

def get_all_player_stats():
    players = get_player_ids()
    all_players_stats = []
    for p in players:
        data=statsapi.player_stat_data(p, group='hitting', type='season')
        stats = get_player_stats(data)
        tbr = calculate_tbr(stats)
        stats["tbr"] = tbr
        stats["firstName"] = data["first_name"]
        stats["lastName"] = data["last_name"]
        stats["currentTeam"] = data["current_team"]
        all_players_stats.append(stats)
    return all_players_stats

def make_leaderboard_string(stats, stat_to_make):
    new_stats = []
    games_played_so_far = get_team_games_played(121)
    for stat in stats:
        if(stat_to_make in stats_to_check_qualifying):
            if(int(stat.get('plateAppearances', 0)) > games_played_so_far*3.1):
                new_stats.append(stat)
        else:
            if(int(stat.get('plateAppearances', 0)) > 0):
                new_stats.append(stat)
    stats = new_stats

    stats.sort(key=lambda x:x[stat_to_make], reverse=True)
    top_one_hundred = stats[:100]
    display_string = ""
    for d in top_one_hundred:
        display_string += d['firstName'] + " " + d['lastName'] + " " + d["currentTeam"] + "\t" + str(d[stat_to_make]) + "\n"
    return display_string 


def generate_leaderboards():
    all_stats = get_all_player_stats()
    stats_to_display = ["tbr", "avg", "obp", "slg", "ops", "homeRuns", "doubles", "triples", "stolenBases"]
    leaderboards = []
    for stat in stats_to_display:
        leaderboards.append(make_leaderboard_string(all_stats, stat))
    return leaderboards

def main():
    lbs = generate_leaderboards()
    for lb in lbs:
        print(lb)

if __name__ == "__main__":
    main()
