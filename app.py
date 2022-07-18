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
    host="eu-cdbr-west-03.cleardb.net",
    user="ba430e02e4e6b8",
    passwd="1fbec195",
    database="heroku_c982995c47a34c9"
)

if (db):
    print("Connection")
else:
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
    crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(45) NOT NULL, Lname varchar(45) NOT NULL, Email varchar(45) NOT NULL, Psswd varchar(45) NOT NULL, Phone int NOT NULL, City varchar(45) NOT NULL, Address varchar(45) NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID), UNIQUE KEY INDEXID_UNIQUE (ID))")
    print("Table Created")

# Test INSERT INTO TABLE:
crsr.execute("INSERT INTO users (Fname, Lname, Email, Psswd, Phone, City, Address) VALUES ("Dany", "Goralkin", "Goralkin@Gmail.com", "123ABC", 972555, "Yoqneam", "Stam 1254");
")




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
        FNAME = request.form.get("Fname")
        LNAME = request.form.get("Lname")
        PSSWD = request.form.get("password")
        PSSWD2 = request.form.get("password2")
        PHONE = request.form.get("phone")
        CITY = request.form.get("city")
        ADDRESS = request.form.get("address")
        '''
        # Check if forms filled.
        if not username or not password or not confirmation:
            return apology("Please fill UserName and/or password", 401)

         # Check if passwords are identical.
        elif password != confirmation:
            return apology("Passwords doesn't match")

        
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











