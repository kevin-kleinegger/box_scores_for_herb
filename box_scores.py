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
    for inning in innings:
        try:
            home_string += " " + str(inning['home']['runs']) + " "
        except KeyError:
            home_string += " - "
        away_string += " " + str(inning['away']['runs']) + " "
    home_string += "  -  " + str(total['home']['runs']) + ' ' + str(total['home']['hits']) + ' ' + str(total['home']['errors'])
    away_string += "  -  " + str(total['away']['runs']) + ' ' + str(total['away']['hits']) + ' ' + str(total['away']['errors'])
    return home_string + '\n' + away_string + '\n'


def generate_data(d=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')):
    games = statsapi.schedule(date=d)
    teams = {t['teamName']:t['id'] for t in statsapi.get('teams', {'sportIds':1})['teams']}
    if len(games)==0:
        d = get_last_day_of_baseball(teams)
        games = statsapi.schedule(date=d)
    box_scores = []
    for g in games:
        full_score = create_linescore_string(g) + statsapi.boxscore(g['game_id'])
        box_scores.append(full_score)
    return box_scores, d

@app.route('/')
def index():
    box_scores, dd = generate_data()
    return render_template('index.html', box_scores=box_scores, default_date=dd)

@app.route('/<date>')
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
    app.run(debug=True)