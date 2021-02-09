from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Username_Passwords(db.Model):
    __tablename__ = "username_passwords"   #corresponds to the name of the table we want to create in the database
    #columns inside the table
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)


class Book(db.Model):
    __tablename__ = "Books"
    #columns inside the table
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
