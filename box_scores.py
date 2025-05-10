import statsapi
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

#homepage flask, call generate_datea, pass the results to the HTML and display!
@app.route('/')
def index():
    box_scores, dd = generate_data()
    return render_template('index.html', box_scores=box_scores, default_date=dd)

#display box scores for any other date
@app.route('/date/<date>')
def display_box_scores(date):
    box_scores, date = generate_data(date)
    return render_template('index.html', box_scores=box_scores, default_date=date)

#POST method that our HTML calls when a user requests box scores for a specific date
@app.route('/submit_date', methods=['POST'])
def submit_date():
    # Get the input date from the form
    input_date = request.form['input_date']

    # Redirect to the route with the specified date
    return redirect(url_for('display_box_scores', date=input_date))

#main function for getting games for given day and generating all line and box scores
#takes in date variable d (yyyy-mm-dd), if none given defaults to current date - 28 hours
#By default we want to see yesterday's box scores, 4 hours added to account for GMT timezone
#Returns an array of box_scores to display, as well as the date used (needs to return the date for the default case where one was not passed in)
#TODO: dynamically set GMT conversion
def generate_data(d=(datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')):
    games = statsapi.schedule(date=d)
    #if there were no games yesterday, find the last day that a game was played and display those
    if len(games)==0:
        teams = {t['teamName']:t['id'] for t in statsapi.get('teams', {'sportIds':1})['teams']}
        d = get_last_day_of_baseball(teams)
        games = statsapi.schedule(date=d)
    #for each game, generate a linescore to display with the boxscore
    box_scores = []
    for g in games:
        full_score = create_linescore_string(g) + statsapi.boxscore(g['game_id'])
        #As a Mets fan, of course their game has to always be at the top :)
        if g['away_name'] == "New York Mets" or g['home_name'] == "New York Mets":
            box_scores = [full_score] + box_scores
        else:
            box_scores.append(full_score)
    return box_scores, d

#creates a string displaying team names, runs per inning, and total runs, hits and errors for a given game
def create_linescore_string(game):
    #get linescore from API and split totals and each inning into own array
    linescore = statsapi.get('game_linescore', {'gamePk':game['game_id']})
    innings = linescore['innings']
    total = linescore['teams']

    #intialize empty strings
    home_string = ""
    away_string = ""
    header_string = ""
    #add runs for each inning to respective strings (whitespace for header)
    for index, inning in enumerate(innings):
        #trying to get home runs in bottom of 9th, may throw a Key Error
        #We catch that exception and pass in a X if that is the case
        #inning['away']['runs'] should theoretically always be populated, however could poentially throw a KeyError if it was null
        try:
            i_away_string, i_home_string = normalize_strings(str(inning['away']['runs']), str(inning['home']['runs']))
        except KeyError:
            i_away_string, i_home_string = normalize_strings(str(inning['away']['runs']), "X")
        home_string += i_home_string + ' '
        away_string += i_away_string + ' '
        #get inning number using index+1, normalize the whitespace in case double digit runs scored
        header_string += normalize_strings(str(index+1), i_away_string)[0] + ' '
    #call normalize_strings on all total values to make sure that home and away all of the same amount of characters for display reasons
    away_runs, home_runs = normalize_strings(str(total['away']['runs']), str(total['home']['runs']))
    away_hits, home_hits = normalize_strings(str(total['away']['hits']), str(total['home']['hits']))
    away_errors, home_errors = normalize_strings(str(total['away']['errors']), str(total['home']['errors']))
    away_name, home_name = normalize_strings(game['away_name'], game['home_name'])
    #add totals to respective strings
    home_string += " -  " + home_runs + ' ' + home_hits + ' ' + home_errors
    away_string += " -  " + away_runs + ' ' + away_hits + ' ' + away_errors
    #empty string in normalize strings to give leading whitespace based on longest team name, names were already normalized so it doesn't matter which one we use
    #rest of header string formatted using normalize_strings to account for any double digit totals, only need to return first element in tuple
    header_string = normalize_strings("", away_name)[0] + '\t' + header_string + " -  " + normalize_strings("R", away_runs)[0] + ' ' + normalize_strings("H", away_hits)[0] + ' ' + normalize_strings("E", away_errors)[0]
    #put it all in one big string with newlines and return for display
    return header_string + '\n' + away_name + '\t' + away_string + '\n' + home_name + '\t' +  home_string + '\n'

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

#returns the date when baseball was last played, takes in a list of evey team
#TODO: this is slow and proabably not necessary
def get_last_day_of_baseball(teams):
    most_recent_day = 0
    output = ''
    #for every team get their last game and check if that is the moist recent so far
    for team in teams:
        gameId = statsapi.last_game(teams[team])
        timestamp = statsapi.get("game", {'gamePk':gameId})['metaData']['timeStamp'].split('_')
        #timestamp[0] is date in yyyymmdd format, so we can just treat this as an integer and check it to most_recent_day
        if(int(timestamp[0]) > most_recent_day):
            most_recent_day = int(timestamp[0])
    #convert most_recent_day from yyyymmdd to yyyy-mm-dd
    for i, c in enumerate(str(most_recent_day)):
        output += c
        if(i == 3 or i == 5):
            output += '-'
    return output

if __name__ == '__main__':
    app.run()