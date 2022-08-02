import os
import mysql.connector
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

# Configure MySql connection to DataBase For app Manager
db = mysql.connector.connect(
    host = "eu-cdbr-west-03.cleardb.net",
    user = os.environ.get("Heroku_user"),
    passwd = os.environ.get("Heroku_psswrd"),
    # user="b62d0c2852c752",
    # passwd="047bddc0",
    database = "heroku_666bfee5e0eaef3"
)

def create_tables():
        # Check if TABLES exist in DB
        crsr = db.cursor()
        crsr.execute("SHOW TABLES")

        tables = crsr.fetchall()
        all_bikes = 0
        bikes = 0
        users = 0
        for table in tables:
            if ("all_bikes" in table):
                all_bikes += 1
            if ("bikes" in table):
                bikes += 1
            if ("users" in table):
                users += 1
                
        # Create required tables if doesn't exist in DB
        if (all_bikes == 0):
            crsr.execute("CREATE TABLE all_bikes (ID int unsigned NOT NULL AUTO_INCREMENT, brand varchar(30) NOT NULL unique, model varchar(30), model_year int, PRIMARY KEY (ID))")
            print("Table all_bikes Created")
        if (bikes == 0):
            crsr.execute("CREATE TABLE bikes (ID int unsigned NOT NULL AUTO_INCREMENT, cust_id int NOT NULL, brand varchar(55) NOT NULL, model varchar(55) NOT NULL, model_year int NOT NULL, PRIMARY KEY (ID))")
            print("Table bikes Created")
        if (users == 0):
            crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(55) NOT NULL, Lname varchar(55) NOT NULL, Email varchar(55) NOT NULL, Psswd varchar(128) NOT NULL, Phone int NOT NULL, City varchar(55) NOT NULL, Address varchar(128) NOT NULL, Verified INT NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID))")
            print("Table users Created")






def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Display Error page if Exception occurs
def error(message, code=400):
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", top=code, bottom=escape(message))


# Render user's fullname
def fullName():
    ID = [session["user_id"]]
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT Fname, Lname FROM users WHERE ID=%s", ID)
    for x in crsr:
        FULLNAME = x[0] + " " + x[1]
    return FULLNAME


'''
def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "symbol": quote["symbol"],
            "name": quote["companyName"],
            "price": float(quote["latestPrice"])
        }
    except (KeyError, TypeError, ValueError):
        return None
'''


