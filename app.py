import os
import mysql.connector


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required


# Heroku app location: https://final-project-dany.herokuapp.com/

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure MySql connection to DataBase For app Manager
db = mysql.connector.connect(
    host="localhost",
    user="appuser",
    passwd="appuser123",
    database="my_project"
)
if (not db):
    print("No connection")

crsr = db.cursor()

# Create table "users" if doesn't exist in DB
crsr.execute("SHOW TABLES")
read = crsr.fetchall()
exist = 0
for x in read:
    if ("users" == x[0]):
        exist += 1
if (exist == 0):
    crsr.execute("CREATE TABLE users (ID INT UNSIGNED NOT NULL AUTO_INCREMENT, Fname VARCHAR(45) NOT NULL, Lname VARCHAR(45) NOT NULL, Email VARCHAR(45) NOT NULL, Phone INT NOT NULL, Registered DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID),UNIQUE INDEXID_UNIQUE(ID ASC) VISIBLE)")



  





@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#--------------------------------------------------------------------------------- /
@app.route("/")
@login_required
def index():
    

    return render_template("index.html")



#--------------------------------------------------------------------------------- LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    #Log user in

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        '''
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        '''

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


#--------------------------------------------------------------------------------- /register
@app.route("/register", methods=["GET", "POST"])
def register():

    # Register user
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if forms filled.
        if not username or not password or not confirmation:
            return apology("Please fill UserName and/or password", 401)

         # Check if passwords are identical.
        elif password != confirmation:
            return apology("Passwords doesn't match")

        '''
        # Check if username exists in db.
        users = db.execute("SELECT username FROM users")
        for user in users:
            #print(user["username"])
            if username == user["username"]:
                #print("confirmed")
                return apology("Username exists, choose other username.")

        # Add username and Hashed password into db.
        db.execute("INSERT INTO users (username, hash) values (?, ?)", username, generate_password_hash(password))

        return greet("You are a member now!")
        '''
    return render_template("register.html")


#--------------------------------------------------------------------------------- LOGout
@app.route("/logout")
def logout():
    # Log user out

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")











