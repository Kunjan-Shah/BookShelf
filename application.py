import os
import requests

from flask import Flask, session, flash, jsonify, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    name = db.execute("SELECT name FROM users WHERE username = :username", {"username" : session["user_id"]}).fetchall()
    if request.method == "POST" and request.form.get("booksearch") != "":
        booksearch = "%" + request.form.get("booksearch") + "%"
        search_results = db.execute("SELECT * FROM books WHERE isbn LIKE :booksearch OR LOWER(title) LIKE LOWER(:booksearch) OR LOWER(author) LIKE LOWER(:booksearch)", {"booksearch": booksearch}).fetchall()
        return render_template("index.html", name = name[0].name, query = request.form.get("booksearch"), search_results = search_results, trending_books = None)
    else:
        trending_books = db.execute("SELECT * FROM books ORDER BY rating_by_goodreads DESC LIMIT 10").fetchall()
        return render_template("index.html", name=name[0].name, trending_books = trending_books)

@app.route("/book/<string:isbn>")
@login_required
def book(isbn):
    name = db.execute("SELECT name FROM users WHERE username = :username", {"username" : session["user_id"]}).fetchall()
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn" : isbn}).fetchone()
    goodreads_info = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "9OeQ6eUg9YOcgNtdaDtTrA", "isbns": isbn}).json()["books"][0]

    user_id = db.execute("SELECT id FROM users WHERE username = :username",{"username": session["user_id"]}).fetchone().id
    review_submitted_by_this_user = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_isbn = :isbn",{"user_id": user_id, "isbn": isbn}).fetchone()
    review_submitted_for_this_book = db.execute("SELECT username, review, rating, tos FROM users JOIN reviews ON reviews.user_id = users.id WHERE book_isbn = :isbn AND NOT user_id = :user_id ORDER BY tos DESC",{"isbn": isbn, "user_id": user_id}).fetchall()

    return render_template("book.html", book = book, name=name[0].name, goodreads_info = goodreads_info, review_submitted_by_this_user = review_submitted_by_this_user, review_submitted_for_this_book = review_submitted_for_this_book)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    error = None

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error = "must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error = "must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username" : request.form.get("username")}).fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].password, request.form.get("password")):
            return render_template("login.html", error = "invalid username/password")
        # Remember which user has logged in
        session["user_id"] = rows[0].username

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    error = None

    if request.method == "GET":
        return render_template("register.html")

    # Ensure username was submitted
    if not request.form.get("username"):
        return render_template("register.html", error = "must provide username")

    # Ensure password was submitted
    elif not request.form.get("password"):
        return render_template("register.html", error = "must provide password")
    # Ensure confirm_password was submitted
    elif not request.form.get("confirm_password"):
        return render_template("register.html", error = "must provide confirm password")

    # Check if password and confirm_password are same
    if request.form.get("password") != request.form.get("confirm_password"):
        return render_template("register.html", error = "password does not match with confirm password")

    # Check if username is already exists
    user_list = db.execute("SELECT username from users where username = :username", {"username": request.form.get("username")}).fetchall()
    if user_list:
        return render_template("register.html", error = "username already exists")

    # Insert new user's data
    db.execute("INSERT INTO users (name, username, password) VALUES (:name, :username, :password)", {"name": request.form.get("name"), "username": request.form.get("username"), "password": generate_password_hash(request.form.get("password"))})
    db.commit()

    # Login user
    session["user_id"] = request.form.get("username")

    # Redirect user to home page
    return redirect("/")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change Password"""
    error = None
    name = db.execute("SELECT name FROM users WHERE username = :username", {"username" : session["user_id"]}).fetchall()

    if request.method == "GET":
        return render_template("change_password.html", name=name[0].name)

    # Ensure old_password was submitted
    if not request.form.get("old_password"):
        return render_template("change_password.html", error = "Must provide old password", name=name[0].name)
    # Ensure new_password was submitted
    elif not request.form.get("new_password"):
        return render_template("change_password.html", error = "Must provide new password", name=name[0].name)
    # Ensure confirm_new_password was submitted
    elif not request.form.get("confirm_new_password"):
        return render_template("change_password.html", error = "Must rewrite new password", name=name[0].name)
    #Check if old password is correct
    if not check_password_hash(db.execute("SELECT password from users WHERE username=:username",{"username": session["user_id"]}).fetchone().password, request.form.get("old_password")):
        return render_template("change_password.html", error = "Incorrect old password! Try again", name=name[0].name)
    # Check if new_password and confirm_new_password are same
    if request.form.get("new_password") != request.form.get("confirm_new_password"):
        return render_template("change_password.html", error = "New password does not match with rewritten password! Try again", name=name[0].name)

    # Update user's data
    db.execute("UPDATE users SET password=:password WHERE username=:username",{"password": generate_password_hash(request.form.get("new_password")), "username": session["user_id"]})
    db.commit()
    return redirect("/")

@app.route("/submit_reviews", methods=["POST"])
@login_required
def submit_reviews():
    """Insert user's reviews into table"""
    if request.method == "POST":
        user_id = db.execute("SELECT id FROM users WHERE username = :username",{"username": session["user_id"]}).fetchone().id
        db.execute("INSERT INTO reviews (user_id, book_isbn, review, rating) VALUES (:user_id, :book_isbn, :review, :rating)", {"user_id": user_id, "book_isbn": request.form.get("isbn"), "review": request.form.get("review"), "rating": request.form.get("rating")})
        db.commit()
        return redirect("/book/" + request.form.get("isbn"))

@app.route("/profile")
@login_required
def profile():
    """User's reviewed books"""
    name = db.execute("SELECT name FROM users WHERE username = :username", {"username" : session["user_id"]}).fetchall()
    user_id = db.execute("SELECT id FROM users WHERE username = :username",{"username": session["user_id"]}).fetchone().id
    reviewed_books = db.execute("SELECT isbn, title, author, year, review, rating, tos FROM books JOIN reviews ON reviews.book_isbn=books.isbn WHERE user_id=:user_id",{"user_id": user_id}).fetchall()
    return render_template("profile.html", name = name[0].name, reviewed_books = reviewed_books)

@app.route("/contact", methods=["GET","POST"])
@login_required
def contact():
    """Contact page"""
    if request.method == "GET":
        name = db.execute("SELECT name FROM users WHERE username = :username", {"username" : session["user_id"]}).fetchall()
        return render_template("contact.html", name=name[0].name)
    else:
        user_id = db.execute("SELECT id FROM users WHERE username = :username",{"username": session["user_id"]}).fetchone().id
        db.execute("INSERT INTO contact (user_id, name, email, message) VALUES (:user_id, :name, :email, :message)", {"user_id": user_id, "name": request.form.get("contact_name"), "email": request.form.get("contact_email"), "message": request.form.get("contact_message")})
        db.commit()
        return redirect("/")

@app.route("/api/<string:isbn>")
@login_required
def api(isbn):
    """Generate API"""
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_isbn=:isbn",{"isbn":isbn}).fetchone()[0]
    average_score = db.execute("SELECT AVG(rating) FROM reviews WHERE book_isbn=:isbn",{"isbn":isbn}).fetchone()[0]
    if average_score is None:
        average_score = 0

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": str(round(average_score, 2))
    })