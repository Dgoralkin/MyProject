import os
import datetime
import mysql.connector
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import fullName, login_required, error, create_tables, add_bike_to_DB, update_all_bikes_table, load_services, service_order, maintain_Service_status
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
        database = "heroku_666bfee5e0eaef3"
    )
    if (db):
        print("Connection with server established")
        create_tables()
except:
    print("Connection Error")


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
                # Log user in if registered and verified 
                if check_password_hash(user[4], PSSWD)==True and user[8]==1:
                    session["user_id"] = user[0]
                    crsr.close()
                    return redirect("/")
                # Redirect user to reverification if registered and not verified 
                elif check_password_hash(user[4], PSSWD)==True and user[8]!=1:
                    USER.clear()
                    USER = user
                    return render_template("verification.html", user=USER)
            
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
        return render_template("verification.html", user=USER, RESPONSE="* Your Verification code is incorrect! please try again")
    
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
    
    FULLNAME = fullName()
    ID = [session["user_id"]]
    
    # User arrived from cart by confirming service/s
    if request.method == "POST":
        
        # Change user's service state from "queued" to current
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("SELECT Service_ID, Service_status, End_datetime FROM service_order WHERE User_ID=%s order by End_datetime", ID)
        to_service = []
        for bike in crsr:
            to_service.append(bike)
        
        # Send services to sort service state
        SERVICE_STATUS = maintain_Service_status(to_service)
        
        render_template("main.html", FULLNAME=FULLNAME)
    
    # if request.method == "GET":
    
    # Update "Service_status" in "service_order" table
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT Service_ID, Service_status, End_datetime FROM service_order WHERE User_ID=%s order by End_datetime", ID)
    sort_service = []
    for bike in crsr:
        sort_service.append(bike)
    SERVICE_STATUS = maintain_Service_status(sort_service)
        
    # Sends service info to main page
    SERVICES = []
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT service_order.Service_ID, all_bikes.brand, bikes.model, services.Service_description, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE User_ID=%s and Service_status = 'in service' order by End_datetime, Service_ID;", ID)
    for line in crsr:
        SERVICES.append(line)

    # Sends user to main page
    return render_template("main.html", FULLNAME=FULLNAME, SERVICES=SERVICES)


#--------------------------------------------------------------------------------- Service Page
@app.route("/service", methods=["GET", "POST"])
@login_required
def service():
    
    FULLNAME = fullName()    
    ID = [session["user_id"]]
    
    # Load list of services from CSV file ------------------------------------------------------------!!!!!!!!!!!!!!!!!!!!!!!
    SERVICES = load_services()
    
    # Check if user added his bike to DB
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT brand FROM bikes WHERE cust_id=%s", ID)
    bikes = []
    for x in crsr:
        if len(x) > 0:
            bikes.append(x[0])
    if len(bikes) == 0:
        return redirect("/add_bike")
    
    # Get all user's bikes
    USER_BIKES = []
    crsr.execute("SELECT bikes.ID, all_bikes.brand, bikes.model, bikes.model_year FROM bikes INNER JOIN all_bikes ON bikes.brand=all_bikes.ID WHERE cust_id=%s", ID)
    for bike in crsr:
        USER_BIKES.append(bike)

    # Redirect user to service page
    return render_template("service.html", FULLNAME=FULLNAME, USER_BIKES=USER_BIKES, SERVICES=SERVICES)


#--------------------------------------------------------------------------------- Add_bike
@app.route("/add_bike", methods=["GET", "POST"])
@login_required
def add_bike():
    
    FULLNAME = fullName()
    YEARS = []
    yearnow = datetime.datetime.now()
    for year in range(yearnow.year, yearnow.year - 23, -1):
        YEARS.append(year)
    
    # Receive data from page via "POST"
    if request.method == "POST":
        BIKE = request.form.get("BIKE").lower().capitalize()
        bike = [BIKE]
        MODEL = request.form.get("MODEL").lower().capitalize()
        YEAR = request.form.get("YEAR")
        
        # Check if user choosed bike from DB and update bike table
        bike_exist = False
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("SELECT ID FROM all_bikes WHERE brand = %s ", bike)
        for id in crsr:
            if len(id) > 0:
                bike_exist = add_bike_to_DB(id[0], MODEL, YEAR)
                
        # if bike not from DB, update bike table and CSV file
        if not bike_exist:
            print("Updating all_bikes table and CSV file")
            update_all_bikes_table(db, crsr, BIKE, MODEL, YEAR)
        return redirect("/service")

    # Redirect user to add_bike page
    return render_template("add_bike.html", FULLNAME=FULLNAME, YEARS=YEARS)


#--------------------------------------------------------------------------------- Remove_bike_from_user
@app.route("/remove_bike", methods=["GET"])
@login_required
def Remove_bike():
    
    # Delete bike from bikes table
    Q = [request.args.get("q")]
    query = 'DELETE FROM bikes WHERE ID=%s'
    db.reconnect()
    crsr = db.cursor()
    crsr.execute(query, Q)
    db.commit()
    print("Bike", Q[0], "removed from Table bikes")
    return render_template("service.html")


#--------------------------------------------------------------------------------- Search bikes in DB
@app.route("/search")
def search():
    
    # Find a bike brand from a DB
    try:
        q = request.args.get("q")
        if q:
            Q = ["%" + q + "%"]
            db.reconnect()
            crsr = db.cursor()
            crsr.execute("SELECT brand FROM all_bikes WHERE brand LIKE %s LIMIT 10", Q)
            bikes = []
            for x in crsr:
                if len(x) > 0:
                    bikes.append(x[0])
        return jsonify(bikes)
    except UnboundLocalError:
        print("local variable 'bikes' referenced before assignment")
    except TypeError:
        print("Error in search")



#--------------------------------------------------------------------------------- Pick_up Page
@app.route("/pick_up", methods=["GET", "POST"])
@login_required
def pick():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to pick up page
    return render_template("pick_up.html",  FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Account
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    
    # Show connected User Full Name
    FULLNAME = fullName()

    # Redirect user to account page
    return render_template("account.html",  FULLNAME=FULLNAME)


#--------------------------------------------------------------------------------- Cart
@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    FULLNAME = fullName()
    USER_ID = [session["user_id"]]
    SERVICES = []
    SERVICES2 = []

    if request.method == "POST":
        # Check what services user ordered for each bike
        SERVICES = []
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("SELECT ID FROM bikes WHERE cust_id=%s", USER_ID)
        counter = 0
        ServiceNotes = request.form.getlist("ServiceNotes")
        for x in crsr:
            SERVICE = {}
            SERVICE_ID = request.form.getlist("bike_" + str(x[0]))
            SERVICE["user_ID"] = USER_ID[0]
            SERVICE["bike_ID"] = x[0]
            SERVICE["bike_services"] = SERVICE_ID
            SERVICE["bike_service_notes"] = ServiceNotes[counter]
            SERVICES.append(SERVICE)
            counter += 1
            
        # Populate "service_order" table with user's request
        insert = service_order(SERVICES)
        if insert:
            return redirect("/cart")
    
    # Get path: Collects data from DB and display customer's cart
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT all_bikes.brand, services.Service_description, services.Service_price, service_order.Service_notes, service_order.Service_ID FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE User_ID=%s and Service_status='queued' order by brand, Service_ID", USER_ID)
    for line in crsr:
        SERVICES.append(line)

    crsr.execute("SELECT COUNT(DISTINCT Bike_ID) as total_bikes, COUNT(Service_procedure) as total_procedures, SUM(Service_price) as total_price FROM service_order WHERE User_ID=%s and Service_status='queued'", USER_ID)

    for line2 in crsr:
        if line2[2] == None:
            list_tmp = list(line2)
            list_tmp[2] = 0
            line2 = tuple(list_tmp)
        SERVICES2.append(line2)
        
    crsr.execute("SELECT End_datetime FROM service_order WHERE User_ID = %s and Service_status='queued' order by End_datetime desc limit 1", USER_ID)
    for line3 in crsr:
        datetime_STR = line3[0].strftime("%Y-%m-%d %H:%M:%S")
        SERVICES2.append(datetime_STR)
    # Redirect user to cart page
    return render_template("cart.html", FULLNAME=FULLNAME, SERVICES=SERVICES, SERVICES2=SERVICES2)


#--------------------------------------------------------------------------------- Remove_bike_from_Cart
@app.route("/remove_bike_cart", methods=["GET"])
@login_required
def remove_bike_cart():
    
    # Delete service for selected bike from "service_order" table
    Q = [request.args.get("q")]
    Q2 = [request.args.get("q2")]

    db.reconnect()
    crsr = db.cursor()
    crsr.execute("DELETE FROM service_order WHERE Service_ID=%s", Q2)
    db.commit()
    print("Service for", Q[0], "removed from Table service_order")
    return True