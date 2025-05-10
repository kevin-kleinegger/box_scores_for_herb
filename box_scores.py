import statsapi
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)

def create_linescore_string(game):
    linescore = statsapi.get('game_linescore', {'gamePk':game['game_id']})
    innings = linescore['innings']
    total = linescore['teams']
    home_string = ""
    away_string = ""
    header_string = ""
    for index, inning in enumerate(innings):
        try:
            i_away_string, i_home_string = normalize_strings(str(inning['away']['runs']), str(inning['home']['runs']))
        except KeyError:
            i_away_string, i_home_string = normalize_strings(str(inning['away']['runs']), "X")
        home_string += i_home_string + ' '
        away_string += i_away_string + ' '
        header_string += normalize_strings(str(index+1), i_away_string)[0] + ' '
    away_runs, home_runs = normalize_strings(str(total['away']['runs']), str(total['home']['runs']))
    away_hits, home_hits = normalize_strings(str(total['away']['hits']), str(total['home']['hits']))
    away_errors, home_errors = normalize_strings(str(total['away']['errors']), str(total['home']['errors']))
    away_name, home_name = normalize_strings(game['away_name'], game['home_name'])

    home_string += " -  " + home_runs + ' ' + home_hits + ' ' + home_errors
    away_string += " -  " + away_runs + ' ' + away_hits + ' ' + away_errors
    header_string = normalize_strings("", away_name)[0] + '\t' + header_string + " -  " + normalize_strings("R", away_runs)[0] + ' ' + normalize_strings("H", away_hits)[0] + ' ' + normalize_strings("E", away_errors)[0]
    return header_string + '\n' + away_name + '\t' + away_string + '\n' + home_name + '\t' +  home_string + '\n'

def normalize_strings(s1, s2):
    if len(s1) > len(s2):
        for i in range(len(s1) - len(s2)):
            s2 = ' ' + s2
    elif len(s2) > len(s1):
        for i in range(len(s2) - len(s1)):
            s1 = ' ' + s1
    return s1, s2



def generate_data(d=(datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')):
    games = statsapi.schedule(date=d)
    if len(games)==0:
        teams = {t['teamName']:t['id'] for t in statsapi.get('teams', {'sportIds':1})['teams']}
        d = get_last_day_of_baseball(teams)
        games = statsapi.schedule(date=d)
    box_scores = []
    for g in games:
        full_score = create_linescore_string(g) + statsapi.boxscore(g['game_id'])
        if g['away_name'] == "New York Mets" or g['home_name'] == "New York Mets":
            box_scores = [full_score] + box_scores
        else:
            box_scores.append(full_score)
    
    return box_scores, d

@app.route('/')
def index():
    box_scores, dd = generate_data()
    return render_template('index.html', box_scores=box_scores, default_date=dd)

@app.route('/date/<date>')
def display_box_scores(date):
    box_scores, date = generate_data(date)
    return render_template('index.html', box_scores=box_scores, default_date=date)

@app.route('/submit_date', methods=['POST'])
def submit_date():
    # Get the input date from the form
    input_date = request.form['input_date']

    # Redirect to the route with the specified date
    return redirect(url_for('display_box_scores', date=input_date))

def get_last_day_of_baseball(teams):
    most_recent_day = 0
    output = ''
    for team in teams:
        gameId = statsapi.last_game(teams[team])
        timestamp = statsapi.get("game", {'gamePk':gameId})['metaData']['timeStamp'].split('_')
        if(int(timestamp[0]) > most_recent_day):
            most_recent_day = int(timestamp[0])
    for i, c in enumerate(str(most_recent_day)):
        output += c
        if(i == 3 or i == 5):
            output += '-'
    return output

if __name__ == '__main__':
    app.run()