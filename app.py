import os
import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import fullName, login_required, error
import smtplib
import random
from email.message import EmailMessage


# Heroku app location: https://final-project-dany.herokuapp.com/

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


try:
    # Try to Configure MySql connection to DataBase For app Manager
    db = mysql.connector.connect(
        host = "eu-cdbr-west-03.cleardb.net",
        user = os.environ.get("Heroku_user"),
        passwd = os.environ.get("Heroku_psswrd"),
        # user="b62d0c2852c752",
        # passwd="047bddc0",
        database = "heroku_666bfee5e0eaef3"
    )
    if (db):
        print("Connection")
        
        # Check if TABLES exist in DB
        crsr = db.cursor()
        crsr.execute("SHOW TABLES")

        tables = crsr.fetchall()
        bikes = 0
        user_bike = 0
        users = 0
        for table in tables:
            if ("bikes" in table):
                bikes += 1
            if ("user_bike" in table):
                user_bike += 1
            if ("users" in table):
                users += 1
        # Create required tables if doesn't exist in DB
        if (bikes == 0):
            crsr.execute("CREATE TABLE bikes (ID int unsigned NOT NULL AUTO_INCREMENT, brand varchar(55) NOT NULL, model varchar(55) NOT NULL, model_year int NOT NULL, PRIMARY KEY (ID))")
            print("Table bikes Created")
        if (user_bike == 0):
            crsr.execute("CREATE TABLE user_bike (ID int unsigned NOT NULL AUTO_INCREMENT, cust_id int NOT NULL, bike_id int NOT NULL unique,  PRIMARY KEY (ID))")
            print("Table user_bike Created")
        if (users == 0):
            crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(55) NOT NULL, Lname varchar(55) NOT NULL, Email varchar(55) NOT NULL, Psswd varchar(128) NOT NULL, Phone int NOT NULL, City varchar(55) NOT NULL, Address varchar(128) NOT NULL, Verified INT NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID))")
            print("Table users Created")
            
except Exception:
    print("No DataBase Connection !!!")


#--------------------------------------------------------------------------------- /
@app.route("/")
@login_required
def index():
    # Filter wheter user loged in
    return redirect("/main")


#--------------------------------------------------------------------------------- LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    
    #Log user in & Forget last user_id
    session.clear()

    # If User reached route via POST
    if request.method == "POST":
        
        # Check if user is registered and verified
        EMAIL = request.form.get("email").lower()
        PSSWD = request.form.get("password")
        USER = [EMAIL]
        
        # Check if DataBase connected
        try:
            db.reconnect()
            crsr = db.cursor()
            crsr.execute("SELECT * FROM users WHERE Email=%s", USER)
            for user in crsr:
                if check_password_hash(user[4], PSSWD)==True and user[8]==1:
                    session["user_id"] = user[0]
                    crsr.close()
                    return redirect("/")
            
            return render_template("login.html", loginError="* Username OR Password is incorrect.")
        except NameError:
            return error("Cannot Connect to Database Server !!!", 500)
            
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


#--------------------------------------------------------------------------------- /register
@app.route("/register", methods=["GET", "POST"])
def register():
    
    # Register user
    if request.method == "POST":
        ID = 0
        FNAME = request.form.get("Fname")
        LNAME = request.form.get("Lname")
        EMAIL = request.form.get("email").lower()
        PSSWD = request.form.get("password")
        PSSWD2 = request.form.get("password2")
        PHONE = request.form.get("phone")
        CITY = request.form.get("city")
        ADDRESS = request.form.get("address")
        VERIFIED = 0
        USER = [ID, FNAME, LNAME, EMAIL, PSSWD, PHONE, CITY, ADDRESS, VERIFIED]
        
        # Check if forms filled.
        if (PSSWD != PSSWD2):
            response = "Please re-enter passwords correctly"
            return render_template("register.html", response=response)
        

        # Check if username exists in db and db is connected.
        try:            
            db.reconnect()
            crsr = db.cursor()
            crsr.execute("SELECT Email FROM users")
            for x in crsr:
                # print(x[0])
                if EMAIL.lower() == x[0].lower():
                    print("USER EXIST IN DB")
                    return render_template("register.html", response2="User already registered. Try to recover your password or enter other credentials.", recover="Recover password")
            crsr.close()
        except NameError:
            return error("Cannot Connect to Database Server !!!", 500)
        
        # Generate 2-step Psswd for Email verification
        TWOSTEPCODE = random.randint(1000,9999)
        
        # Send verification Email to user
        
        EMAIL_ADDRESS = os.environ.get('Gmail_smtp_username')
        EMAIL_PSSWRD = os.environ.get('Gmail_smtp_psswrd')
        # EMAIL_ADDRESS = 'gbikes.customer.service@gmail.com'
        # EMAIL_PSSWRD = 'llbqckvmfvshbonk'
        
        msg = EmailMessage()
        msg['Subject'] = 'This is a verification Email From G-bikes'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL
        msg.set_content('Your 2-Step verification code just arrived')
        txt = "Your code is: " + str(TWOSTEPCODE)
        msg.add_alternative(txt, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PSSWRD)
            smtp.send_message(msg)
            
        # Add username and Hashed password into db.
        user_info = (FNAME, LNAME, EMAIL, generate_password_hash(PSSWD), PHONE, CITY, ADDRESS, TWOSTEPCODE)
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("INSERT INTO users (Fname, Lname, Email, Psswd, Phone, City, Address, Verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", user_info)
        db.commit()
        crsr.close()

        print("New User Inserted into DB")

        return render_template("verification.html", user=USER, EMAIL=EMAIL)
    return render_template("register.html")


#--------------------------------------------------------------------------------- /verification
@app.route("/verification", methods=["GET", "POST"])
def verifify():

    # Register user
    if request.method == "POST":
        
        # Receive data from page
        VERPSSWD = request.form.get("verPasswd")
        EMAIL = request.form.get("EMAIL")
        email = [EMAIL]
        
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("SELECT * FROM users WHERE Email=%s", email)
    
        for x in crsr:
            USER = x

        if (VERPSSWD == str(USER[8])):
            print("User Verified")
            
            # Update user to be verified in DB
            email = [EMAIL]
            crsr.execute("UPDATE users SET Verified = 1 WHERE Email=%s", email)
            db.commit()
            crsr.close()
            return redirect("/")
        return render_template("verification.html", user=USER, RESPONSE="Your Verification code is incorrect!, please try again")
    
    # return from GET response
    return redirect("/")


#--------------------------------------------------------------------------------- Logout
@app.route("/logout")
def logout():
    # Log user out & Forget signed in user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


#--------------------------------------------------------------------------------- Main Page
@app.route("/main", methods=["GET", "POST"])
@login_required
def main():
    
    # Show connected User Full Name
    FULLNAME = fullName()
        
    # Redirect user to login form
    return render_template("main.html", FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Service Page
@app.route("/service", methods=["GET", "POST"])
@login_required
def service():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to login form
    return render_template("service.html",  FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Pick_up Page
@app.route("/pick_up", methods=["GET", "POST"])
@login_required
def pick():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to login form
    return render_template("pick_up.html",  FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Account
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to login form
    return render_template("account.html",  FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Cart
@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to login form
    return render_template("cart.html",  FULLNAME=FULLNAME)

