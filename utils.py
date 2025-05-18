NAME_TO_ACRYONYM = {
                    "Arizona Diamondbacks":"ARI",
                    "Baltimore Orioles":"BAL",
                    "Boston Red Sox":"BOS",
                    "Chicago White Sox":"CWS",
                    "Cleveland Guardians":"CLE",
                    "Colorado Rockies":"COL",
                    "Detroit Tigers":"DET",
                    "Athletics":"ATH",
                    "Houston Astros":"HOU",
                    "Kansas City Royals":"KCR",
                    "Los Angeles Angels":"LAA",
                    "Los Angeles Dodgers":"LAD",
                    "Milwaukee Brewers":"MIL",
                    "Minnesota Twins":"MIN",
                    "New York Yankees":"NYY",
                    "Pittsburgh Pirates":"PIT",
                    "San Diego Padres":"SDP",
                    "San Francisco Giants":"SFG",
                    "Seattle Mariners":"SEA",
                    "Tampa Bay Rays":"TBR",
                    "Texas Rangers":"TEX",
                    "Toronto Blue Jays":"TOR",
                    "New York Mets":"NYM",
                    "Philadelphia Phillies":"PHI",
                    "Atlanta Braves":"ATL",
                    "Washington Nationals":"WSH",
                    "Miami Marlins":"MIA",
                    "Chicago Cubs":"CHC",
                    "St. Louis Cardinals":"STL",
                    "Cincinnati Reds":"CIN",
                    }
    

def map_team_name_to_acronym(team_name):
    return NAME_TO_ACRYONYM[team_name]

#given two strings, equalize the length of strings by adding whitespace in front of the smaller string
#returns tuple of strings in same order as passed in
def normalize_strings(s1, s2):
    if len(s1) > len(s2):
        for i in range(len(s1) - len(s2)):
            s2 = ' ' + s2
    elif len(s2) > len(s1):
        for i in range(len(s2) - len(s1)):
            s1 = ' ' + s1
    return s1, s2
