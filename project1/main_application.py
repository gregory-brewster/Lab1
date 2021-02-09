import os

from flask import Flask, session
from flask import Flask, render_template, request
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
    return render_template("Main.html")




@app.route("/login", methods=['POST'])
def login():
    """Log into Account."""

    #entered if form button is pressed
    if request.method == 'POST':
        #Get form information.
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.execute("SELECT * FROM username_passwords WHERE username = :username AND password = :password",
                    {"username": username, "password": password}).fetchone()

        if user == None:
            return render_template("Main.html", message="Username does not exist. PLease create an account.")
        else:
            return render_template("books.html")

    else:
        return render_template("error.html", message="Please log in to view this page.")




#Creates the Accounts
@app.route("/create", methods=['POST'])
def create():
    """Create Account."""

    #entered if form button is pressed
    if request.method == 'POST':

        #Get form information.
        username = request.form.get("username")
        password = request.form.get("password")

        #Check to see if there is a username that is the same as the inputted username
        user = db.execute("SELECT username FROM username_passwords WHERE username = :username",
                        {"username": username}).fetchone()

        if user != None:
            return render_template("Main.html", message="Username already exists.")
        else:
            db.execute("INSERT INTO username_passwords (username, password) VALUES (:username, :password)",
                    {"username": username, "password": password})
            db.commit()
            return render_template("Main.html", message="Please log into your new account.")
    else:
        return render_template("error.html", message="Please log in to view this page.")



@app.route("/books", methods=['POST'])
def books():
    """Users can search for books"""

    #entered if form button is pressed
    if request.method == 'POST':

        #Get form information.
        input = request.form.get("input")

        results = db.execute(f"SELECT * FROM Books WHERE isbn LIKE '%{input}%'").fetchall()
        #results = db.execute(f"SELECT * FROM username_passwords WHERE username LIKE '%{inputs}%'").fetchall()

        return render_template("books.html", result=results)





def main():

        inputs = (input("\ninputs: "))

        results = db.execute(f"SELECT * FROM username_passwords WHERE username LIKE '%{inputs}%'").fetchall()

        print(results)

if __name__ == "__main__":
    main()
