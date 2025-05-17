from box_scores import generate_data
from datetime import datetime, timedelta, date

def main():
    d=(datetime.now() - timedelta(hours=28)).strftime('%Y-%m-%d')
    box_scores, _ = generate_data(d)
    filename = d + "_data.txt"
    with open(filename, "a") as f:
        f.write(str(box_scores))

if __name__ == "__main__":
    main()