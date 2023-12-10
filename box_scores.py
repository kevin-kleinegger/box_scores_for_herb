import statsapi
from datetime import datetime, timedelta
from flask import Flask, render_template

app = Flask(__name__)

def generate_data():
    date_of_interest = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    games = statsapi.schedule(date=date_of_interest)
    teams = {t['teamName']:t['id'] for t in statsapi.get('teams', {'sportIds':1})['teams']}
    if len(games)==0:
        date_of_interest = get_last_day_of_baseball(teams)
        games = statsapi.schedule(date=date_of_interest)
    f = open("box_scores.txt", "w", encoding='utf-8')
    box_scores = []
    for g in games:
        box_scores.append(statsapi.boxscore(g['game_id']))
    return box_scores

@app.route('/')
def index():
    return render_template('index.html', box_scores=generate_data())
    

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