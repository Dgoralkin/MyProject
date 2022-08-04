import os
import mysql.connector
import urllib.parse
import csv

from flask import redirect, render_template, request, session
from functools import wraps

# Configure MySql connection to DataBase For app Manager
db = mysql.connector.connect(
    host = "eu-cdbr-west-03.cleardb.net",
    user = os.environ.get("Heroku_user"),
    passwd = os.environ.get("Heroku_psswrd"),
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
            crsr.execute("CREATE TABLE all_bikes (ID int unsigned NOT NULL AUTO_INCREMENT, brand varchar(30) NOT NULL unique, PRIMARY KEY (ID))")
            print("Table all_bikes Created")
            # Populate TABLE all_bikes when created
            populate_all_bikes_table(crsr)
        else:
            # Check if "CSV Bike_list File" were updated by moderator and update if required
            crsr.execute("SELECT COUNT(brand) as count_bikes FROM all_bikes")
            for x in crsr:
                DB_Count = x[0]
                print('DB_Count:', DB_Count)
            CSV_Count = 0
            with open('Bikes.csv', 'r') as csv_file:
                reader = csv.reader(csv_file)
                for line in reader:
                    CSV_Count += 1
                print('CSV_count:', CSV_Count)
                if DB_Count == CSV_Count:
                    print("Table all_bikes up to date")
                else:
                    crsr.execute("DROP TABLE all_bikes")
                    db.commit()
                    print("Table all_bikes Deleted")
                    crsr.execute("CREATE TABLE all_bikes (ID int unsigned NOT NULL AUTO_INCREMENT, brand varchar(30) NOT NULL unique, PRIMARY KEY (ID))")
                    populate_all_bikes_table(crsr)
                    
        if (bikes == 0):
            crsr.execute("CREATE TABLE bikes (ID int unsigned NOT NULL AUTO_INCREMENT, cust_id int NOT NULL, brand int NOT NULL, model varchar(55) NOT NULL, model_year int NOT NULL, PRIMARY KEY (ID))")
            print("Table bikes Created")
        if (users == 0):
            crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(55) NOT NULL, Lname varchar(55) NOT NULL, Email varchar(55) NOT NULL, Psswd varchar(128) NOT NULL, Phone int NOT NULL, City varchar(55) NOT NULL, Address varchar(128) NOT NULL, Verified INT NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID))")
            print("Table users Created")


def populate_all_bikes_table(crsr):
    print("Populating table all_bikes. Please wait...")
    db.reconnect()
    with open('Bikes.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        for line in reader:
                bike = [line[0].lower().capitalize()]
                crsr.execute("INSERT INTO all_bikes (brand) VALUES (%s)", bike)
                db.commit()
        csv_file.close()
        print("Table all_bikes updated")


# Update all_bike table and CSV file with new bike
def update_all_bikes_table(db, crsr, BIKE, MODEL, YEAR):
    bike = [BIKE]
    crsr.execute("INSERT INTO all_bikes (brand) VALUES (%s)", bike)
    db.commit()
    # find MAX (ID) FROM all_bikes and update table bikes
    crsr.execute("SELECT MAX(ID) FROM all_bikes")
    for maxID in crsr:
        print('maxID:', maxID)
        ID = maxID[0]
    add_bike_to_DB(db, crsr, ID, MODEL, YEAR)
    
    # Update CSV file
    with open('Bikes.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow([BIKE])
        csv_file.close()
        print("CSV file updated")
    return


# Insert user bike into bikes table
def add_bike_to_DB(db, crsr, id, MODEL, YEAR):
    BIKE_MODEL = [session["user_id"], id, MODEL, YEAR]
    crsr.execute("INSERT INTO bikes (cust_id, brand, model, model_year) VALUES (%s, %s, %s, %s)", BIKE_MODEL)
    db.commit()
    print("Bike " + str(id) + " from DB added to Table bikes")
    bike_exist = True
    return bike_exist


def login_required(f):
    # Decorate routes to require login.
    """
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
        
        # Escape special characters.
        """
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



