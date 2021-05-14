import csv
import requests
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn,title,author,year in reader:
        book_info = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "9OeQ6eUg9YOcgNtdaDtTrA", "isbns": isbn})
        json_book = book_info.json()
        db.execute("INSERT INTO books (isbn, title, author, year, rating_by_goodreads) VALUES (:isbn, :title, :author, :year, :rating_by_goodreads)",{"isbn": isbn, "title": title, "author": author, "year": year, "rating_by_goodreads": json_book["books"][0]["average_rating"]})
        db.commit()
if __name__ == "__main__":
    main()