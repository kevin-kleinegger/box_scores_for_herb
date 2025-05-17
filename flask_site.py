from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, redirect, url_for
import os
from box_scores import generate_data
import ast

app = Flask(__name__)

#homepage flask, call generate_datea, pass the results to the HTML and display!
@app.route('/')
def index():
    d = (datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')
    if(os.path.exists(d + "_data.txt")):
        box_scores, dd = read_data_from_file(d)
    else:
        box_scores, dd = generate_data(d)
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
    #TODO: use flash to validate input, without having to throw a 400
    try:
        parsed_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD", 400  # Bad Request

    if parsed_date >= date.today():
        return "Date must be in the past (not today or future)", 400
    # Redirect to the route with the specified date
    return redirect(url_for('display_box_scores', date=input_date))

def read_data_from_file(d):
    filename = d + "_data.txt"
    with open(filename, 'r') as file:
        content = file.read()
        return ast.literal_eval(content), d
    
if __name__ == '__main__':
    app.run()