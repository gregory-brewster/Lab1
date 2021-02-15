import os

from flask import Flask, session
from flask import Flask, render_template, request
import requests
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import jsonify

from tables import *    #means import everything (*) from the file models

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


#The main Page
@app.route("/")
def index():


    if 'username' in session:
        username = session['username']
        return render_template("main1.html", message1=f"Logged in as {username}", message2 = "Click here to log out.", message3="Click here to search for books.")

    else:
        return render_template("login.html")


@app.route("/login", methods=['GET','POST'])
def login():
    """Log into Account."""

    if 'username' in session:
        username = session['username']
        return render_template("main1.html", message1=f"Logged in as {username}", message2 = "Click here to log out.", message3="Click here to search for books.")

    else:
        username = request.form.get("username")
        password = request.form.get("password")

        session['username'] = username
        user = db.execute("SELECT * FROM username_passwords WHERE username = :username AND password = :password",
                    {"username": username, "password": password}).fetchone()


        if user == None:
            session.pop('username', None)
            return render_template("create.html", message="Username does not exist. Please create an account.")
        else:
            return render_template("main1.html", message1=f"Logged in as {username}", message2 = "Click here to log out.", message3="Click here to search for books.")



#Creates the Accounts
@app.route("/create", methods=['GET','POST'])
def create():
    """Create Account."""

    if 'username' in session:
        username = session['username']
        return render_template("main1.html", message1=f"Logged in as {username}", message2 = "Click here to log out.", message3="Click here to search for books.")

    else:

        if request.method == "GET":
            return render_template("create.html")

        #Get form information.
        username = request.form.get("username")
        password = request.form.get("password")

        #Check to see if there is a username that is the same as the inputted username
        user = db.execute("SELECT username FROM username_passwords WHERE username = :username",
                        {"username": username}).fetchone()

        if user != None:
            session.pop('username', None)
            return render_template("create.html", message="Username already exists.")
        else:
            db.execute("INSERT INTO username_passwords (username, password) VALUES (:username, :password)",
                    {"username": username, "password": password})
            db.commit()
            return render_template("login.html", message="Please log into your new account.")


@app.route('/logout', methods=['GET','POST'])
def logout():

   # remove the username from the session if it is there
   session.pop('username', None)
   return render_template("login.html", message = "You've been successfully logged out.")



@app.route("/books", methods=['GET','POST'])
def books():
    """Users can search for books"""

    #entered if form button is pressed
    if 'username' in session:
        username = session['username']

        #Get form information.
        input = request.form.get("input")
        book_id = request.form.get("book_id")

        results = None

        results = db.execute(f"SELECT * FROM books WHERE isbn LIKE '%{input}%' OR title LIKE '%{input}%' OR author LIKE '%{input}%' OR year LIKE '%{input}%'").fetchall()
        if results == None:
            return render_template("books.html", results=results, message2="Sorry, no books were found.", message=f"Logged in as {username}")


        if book_id != None:
            book = db.execute(f"SELECT * FROM books WHERE id LIKE '%{book_id}%'").fetchone()
            session['book'] = book

            #will create a new session for the book if one has not been created
            if session.get(f"{book.id}_reviews") is None:
                session[f"{book.id}_reviews"] = [] #users' particular sessions
                session[f"{book.id}_rating"] = []

            #Grab API data about book
            res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{book.isbn}"})
            data = res.json()
            session['data'] = data

            #Returns the average and amount of ratings for the user inputted book
            try:
                avg_rating = data["items"][0]["volumeInfo"]["averageRating"]
                rating_count = data["items"][0]["volumeInfo"]["ratingsCount"]
                error = ""

            except KeyError:
                error = "Sorry, book rating data not availabe."
                avg_rating = "Not available"
                rating_count = "Not available"

            #session[f"{book_id}_reviews"] = [] #users' particular sessions
            #session[f"{book_id}_rating"] = []

            #return render_template("error.html", username=rating_count, usernames=avg_rating)

            return render_template("book.html", book=book, message=f"Hello, {username}", reviews=session[f"{book_id}_reviews"], avg_rating=avg_rating, rating_count=rating_count, error=error)

        return render_template("books.html", results=results, message=f"Logged in as {username}")
        book = None

    else:
        return render_template("login.html", message = "You must log in to select books.")


#This is where users see book info and write reviews
@app.route("/book", methods=['POST'])
def book():
    """Users can Write Book Review"""

    #entered if user is logged in
    if 'username' in session:
        username = session['username']

        book = session['book']
        book_id = book.id
        review_username = None

#API DATA
        #Grab API data about book
        data = session['data']

        #Returns the average and amount of ratings for the user inputted book
        try:
            avg_rating = data["items"][0]["volumeInfo"]["averageRating"]
            rating_count = data["items"][0]["volumeInfo"]["ratingsCount"]
            error = ""

        except KeyError:
            error = "Sorry, book rating data not availabe."
            avg_rating = "Not available"
            rating_count = "Not available"


        #Allows books to have their own set of reviews
        if session.get(f"{book.id}_reviews") is None:
            session[f"{book.id}_reviews"] = [] #users' particular sessions
            session[f"{book.id}_rating"] = []


        #will return the username of a user who is logged in and has already written a review
        review_username = db.execute(f"SELECT INITCAP(username) FROM reviews WHERE username = :username",
                                {"username": username}).fetchone()

        #This makes both usernames into strings so that they look like ('_',)
        username_str = str(f"('{username}',)")
        review_username_str = str(review_username)

        #This if statements is only entered if the user has not already written a review for the inputted book
        if username_str != review_username_str:

            review = request.form.get("review")
            rating = request.form.get("rating")

            db.execute("INSERT INTO reviews (book_id, username, review, rating) VALUES (:book_id, :username, :review, :rating)",
                    {"book_id": book_id, "username": username, "review": review, "rating": rating})
            db.commit()

            combination = db.execute(f"SELECT CONCAT(username, ': ', review, '  - ', rating, ' stars') FROM reviews WHERE username = :username",
                                    {"username": username}).fetchone()

            session[f"{book.id}_reviews"].append(combination[0])


            return render_template("book.html", book=book, message=f"Hello, {username}", reviews=session[f"{book.id}_reviews"], avg_rating=avg_rating, rating_count=rating_count, error=error)

        else:
            message2 = "You have already written a review."
            return render_template("book.html", book=book, message=f"Hello, {username}", message2=message2, reviews=session[f"{book.id}_reviews"], avg_rating=avg_rating, rating_count=rating_count, error=error)

    else:
        return render_template("login.html", message = "You must log in to view a book.")

@app.route("/api/<isbn>")
def isbn_api(isbn):
    """Return details about a book"""

    book_isbn = db.execute(f"SELECT isbn FROM books WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchone()

    if book_isbn is None:
        return jsonify({"error 404": "ISBN is not in the database"}), 404

    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
    data = res.json()

    try:
        title = data["items"][0]["volumeInfo"]["title"]
    except KeyError:
        title = "Null"

    try:
        author = data["items"][0]["volumeInfo"]["authors"]
    except KeyError:
        author = "Null"
    try:
        publish_date= data["items"][0]["volumeInfo"]["publishedDate"]
    except KeyError:
        publish_date = "Null"
    try:
        ISBN_10 = data["items"][0]["volumeInfo"]["industryIdentifiers"][0]["identifier"]
    except KeyError:
        ISBN_10 = "Null"
    try:
        ISBN_13 = data["items"][0]["volumeInfo"]["industryIdentifiers"][1]["identifier"]
    except KeyError:
        ISBN_13 = "Null"
    try:
        avg_rating = data["items"][0]["volumeInfo"]["averageRating"]
    except KeyError:
        avg_rating = "Null"
    try:
        rating_count = data["items"][0]["volumeInfo"]["ratingsCount"]
    except KeyError:
        rating_count = "Null"

    return jsonify({
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "ISBN_10": ISBN_10,
            "ISBN_13": ISBN_13,
            "rating_count": rating_count,
            "avg_rating": avg_rating
            })
