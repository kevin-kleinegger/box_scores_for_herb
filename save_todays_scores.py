from box_scores import generate_data
from stats import generate_leaderboards
from datetime import datetime, timedelta, date
import os

def write_box_scores():
    d=(datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')
    box_scores, _ = generate_data(d)
    filename = d + "_data.txt"
    with open(filename, "a") as f:
        f.write(str(box_scores))

def write_leaderboards():
    d=(datetime.now() - timedelta(hours=4)).strftime('%Y-%m-%d')
    leaderboards = generate_leaderboards()
    filename = d + "_leaderboards.txt"
    with open(filename, "a") as f:
        f.write(str(leaderboards))

def delete_old_files():
    d1=(datetime.now() - timedelta(hours=52)).strftime('%Y-%m-%d')
    d2=(datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')
    os.remove(d1 + "_data.txt")
    os.remove(d2 + "_leaderboards.txt")
    return

def main():
    delete_old_files()
    write_box_scores()
    write_leaderboards()


if __name__ == "__main__":
    main()