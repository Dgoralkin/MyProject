import os
import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
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

def checConnection():
    connection = mysql.connector.connect(
        host="eu-cdbr-west-03.cleardb.net",
        user='b9886f5b189f60',
        passwd='0190bc04',
        database="heroku_3003039de5cde26"
    )
    if (connection):
        print("Connection Established")
    else:
        print("NO Connection")
        db.close()
        checConnection()

# Configure MySql connection to DataBase For app Manager
db = mysql.connector.connect(
    host="eu-cdbr-west-03.cleardb.net",
    user='b9886f5b189f60',
    passwd='0190bc04',
    database="heroku_3003039de5cde26"
)

if (db):
    print("Connection")
else:
    print("No connection")
crsr = db.cursor()


# Create table "users" if doesn't exist in DB

checConnection()
crsr.execute("SHOW TABLES")
read = crsr.fetchall()
exist = 0
for x in read:
    if ("users" == x[0]):
        exist += 1
if (exist == 0):
    crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(45) NOT NULL, Lname varchar(45) NOT NULL, Email varchar(45) NOT NULL, Psswd varchar(255) NOT NULL, Phone int NOT NULL, City varchar(45) NOT NULL, Address varchar(45) NOT NULL, Verified TINYINT NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID), UNIQUE KEY INDEXID_UNIQUE (ID))")
    print("Table Created")



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
    
    

    return render_template("login.html")



#--------------------------------------------------------------------------------- LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    

    #Log user in

    # Forget any user_id
    # session.clear()

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
        # crsr = db.cursor()
        FNAME = request.form.get("Fname")
        LNAME = request.form.get("Lname")
        EMAIL = request.form.get("email")
        PSSWD = request.form.get("password")
        PSSWD2 = request.form.get("password2")
        PHONE = request.form.get("phone")
        CITY = request.form.get("city")
        ADDRESS = request.form.get("address")
        VERIFIED = 0
        USER = [{"FNAME":FNAME}, {"LNAME":LNAME}, {"EMAIL":EMAIL}, {"PSSWD":PSSWD}, {"PHONE":PHONE}, {"CITY":CITY}, {"ADDRESS":ADDRESS}, {"VERIFIED":VERIFIED}]
        print(USER)
        
        # Check if forms filled.
        if (PSSWD != PSSWD2):
            response = "Please re-enter passwords correctly"
            return render_template("register.html", response=response)
        

        # Check if username exists in db.
        db.close()
        checConnection()

        crsr.execute("SELECT Email FROM users")
        for x in crsr:
            # print(x[0])
            if EMAIL.lower() == x[0].lower():
                print("USER EXIST IN DB")
                return render_template("register.html", response2="User already registered. Try to recover your password or enter other credentials.", recover="Recover password")
            
        
        # Generate 2-step Psswd for Email verification
        TWOSTEPCODE = random.randint(1000,9999)
        
        # Send verification Email to user
        
        # EMAIL_ADDRESS = os.environ.get('Gmail_smtp_username')
        # EMAIL_PSSWRD = os.environ.get('Gmail_smtp_psswrd')
        EMAIL_ADDRESS = 'gbikes.customer.service@gmail.com'
        EMAIL_PSSWRD = 'llbqckvmfvshbonk'
        
        msg = EmailMessage()
        msg['Subject'] = 'This is a verification Email From G-bikes'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL
        msg.set_content('Your 2-Step verification code just arrived')
        txt = "Your code is: " + str(TWOSTEPCODE)
        
        print("Your code is: ", str(TWOSTEPCODE))
        

        msg.add_alternative(txt, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PSSWRD)
            smtp.send_message(msg)
            
        # Add username and Hashed password into db.
        user_info = (FNAME, LNAME, EMAIL.lower(), generate_password_hash(PSSWD), PHONE, CITY, ADDRESS, VERIFIED)
        db.close()
        checConnection()
        crsr.execute("INSERT INTO users (Fname, Lname, Email, Psswd, Phone, City, Address, Verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", user_info)
        db.commit()

        print("New User Inserted into DB")
        
        
        return render_template("verification.html", user=USER, EMAIL=EMAIL.lower(), TwoStepCode=TWOSTEPCODE)
    return render_template("register.html")


#--------------------------------------------------------------------------------- /verification
@app.route("/verification", methods=["GET", "POST"])
def verifify():

    # Register user
    if request.method == "POST":
        VERPSSWD1 = request.form.get("verPasswd1")
        VERPSSWD2 = request.form.get("verPasswd2")
        EMAIL = request.form.get("EMAIL")
        print('WE ARE HERE', VERPSSWD1, VERPSSWD2, EMAIL)
        if (VERPSSWD1 == VERPSSWD2):
            print("YESSSSSSSSS")
            
            # Update user to be verified
            email = [EMAIL]
            db.close()
            checConnection()
            crsr.execute("UPDATE users SET Verified = 1 WHERE Email=%s", email)
            db.commit()

            return redirect("/")


    return render_template("verification.html")



#--------------------------------------------------------------------------------- LOGout
@app.route("/logout")
def logout():
    # Log user out

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")











