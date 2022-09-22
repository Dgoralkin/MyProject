import os
import datetime
from re import I
import mysql.connector
from flask import Flask, jsonify, redirect, render_template, request, session, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import fullName, login_required, error, create_tables, add_bike_to_DB, update_all_bikes_table, load_services, service_order, time_UTC_to_IL, display_services, display_user_service_status, update_completed, Send_Status_update, validate_ready_for_email, send_email
import smtplib
import random
from email.message import EmailMessage
import secrets
import string



# Heroku app location: https://final-project-dany.herokuapp.com/

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure Email Address & Password for sending Emails
EMAIL_ADDRESS = os.environ.get('Gmail_smtp_username')
EMAIL_PSSWRD = os.environ.get('Gmail_smtp_psswrd')

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
    print("ERROR! - Something went wrong!")
    error("Something went wrong!", 400)
    
    
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
        EMAIL = request.form.get("email").lower().strip()
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
            flash('* Username OR Password is incorrect.')
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
        FNAME = request.form.get("Fname").strip().capitalize()
        LNAME = request.form.get("Lname").strip().capitalize()
        EMAIL = request.form.get("email").lower().strip()
        PSSWD = request.form.get("password")
        PSSWD2 = request.form.get("password2")
        PHONE = request.form.get("phone")
        CITY = request.form.get("city").strip().capitalize()
        ADDRESS = request.form.get("address").strip().capitalize()
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
                if EMAIL.lower().strip() == x[0].lower().strip():
                    print("USER EXIST IN DB")
                    return render_template("register.html", response2="User already registered. Try to recover your password or enter other credentials.", recover="Recover password")
            crsr.close()
        except NameError:
            return error("Cannot Connect to Database Server !!!", 500)
        
        # Generate 2-step Psswd for Email verification
        TWOSTEPCODE = random.randint(1000,9999)
        
        # Send verification Email to user
        SUBJECT = 'This is a verification Email From G-bikes'
        SETCONTENT = 'Your 2-Step verification code just arrived'
        TXT = "Your code is: " + str(TWOSTEPCODE)
        send_status = send_email(EMAIL, SUBJECT, SETCONTENT, TXT)
            
        # Add username and Hashed password into db.
        user_info = (FNAME, LNAME, EMAIL, generate_password_hash(PSSWD), PHONE, CITY, ADDRESS, TWOSTEPCODE)
        db.reconnect()
        crsr = db.cursor()
        crsr.execute("INSERT INTO users (Fname, Lname, Email, Psswd, Phone, City, Address, Verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", user_info)
        db.commit()
        crsr.close()

        print("New User Inserted into DB")
        
        # Inform owner about new customer registration
        SUBJECT = 'New user just signed in to G-bikes Service'
        SETCONTENT = 'This is an update Email From G-bikes'
        TXT = 'User details: ' + str(USER[1]) + ' ' + str(USER[2]) + ' Email: ' + str(USER[3])
        send_status = send_email(EMAIL_ADDRESS, SUBJECT, SETCONTENT, TXT)

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
            flash("Wellcome to G-bikes. You may now login with your details.")
            return redirect("/login")
        flash('* Your Verification code is incorrect! please try again')
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
    if request.method == "POST":
        flash('We on it! You will get notified by Email as your bike will be ready! Meanwhile, you can check your service status at - "Pick up & Status" page')
        return redirect("/main")
    
    # Send data to display_services function in helpers for sorting for display
    display_service_queue = display_services()
    
    send_email_ready_update = validate_ready_for_email()
        
    # Sends user to main page
    return render_template("main.html", FULLNAME=FULLNAME, SERVICE_RUNNING=display_service_queue[0], SERVICE_READY=display_service_queue[1], SERVICE_IN_Q=display_service_queue[2], WORKING_HOURS=display_service_queue[3])


#--------------------------------------------------------------------------------- iframe for login page
@app.route("/iframe", methods=["GET"])
def iframe():
    # Send data to display_services function in helpers for sorting for display
    display_service_queue = display_services()
    
    # Send info to iframe page to display data of services
    return render_template("iframe.html", SERVICE_RUNNING=display_service_queue[0], SERVICE_READY=display_service_queue[1], SERVICE_IN_Q=display_service_queue[2], WORKING_HOURS=display_service_queue[3])


#--------------------------------------------------------------------------------- Service Page
@app.route("/service", methods=["GET", "POST"])
@login_required
def service():
    
    FULLNAME = fullName()    
    ID = [session["user_id"]]
    
    # Load list of services from CSV file
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
    yearnow = time_UTC_to_IL()
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
        crsr.execute("SELECT ID FROM all_bikes WHERE brand = %s", bike)
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
    
    USER_ID = session["user_id"]
    BIKE_ID = request.args.get("q")
    PARAMETERS = [USER_ID, BIKE_ID]
    
    db.reconnect()
    crsr = db.cursor()
    # Delete bike from table oredrs_history
    crsr.execute("DELETE FROM orders_history WHERE User_ID = %s AND Bike_ID = %s", PARAMETERS)
    db.commit()
    
    # Delete bike from table service_order
    crsr.execute("DELETE FROM service_order WHERE User_ID = %s AND Bike_ID = %s", PARAMETERS)
    db.commit()
    
    # Delete bike from bikes table
    query = 'DELETE FROM bikes WHERE ID=%s'
    crsr.execute(query, [BIKE_ID])
    db.commit()
    print("Bike", BIKE_ID, "removed from Tables: orders_history, service_order, bikes")
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


# Container for ready for payment bikes passed to @app.route("/paid") if Payment Succeeded.
Paid_bike_ids = []
PAY_FOR_SERVICES = []
PAY_FOR_SERVICES_ADDONS = [0, 0]
CUSTOMER_DETAILS = []


#--------------------------------------------------------------------------------- Pick_up Page
@app.route("/pick_up", methods=["GET", "POST"])
@login_required
def pick():
    
    # Show connected User Full Name
    FULLNAME = fullName()
    USER_ID = [session["user_id"]]

    # Refresh page date
    REFRESH = display_services()
    
    # Send data to display_services function in helpers for sorting for display
    SERVICES = display_user_service_status(USER_ID)
        
    # Sends user to main page
    return render_template("pick_up.html", FULLNAME=FULLNAME, SERVICES=SERVICES)


#--------------------------------------------------------------------------------- Payment Page
@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    
    # Show connected User Full Name
    FULLNAME = fullName()
    Paid_bike_ids.clear()
    
    if request.method == "POST":
        try:
            crsr = db.cursor()
            print("Try Block:")
        except:
            db.reconnect()
            crsr = db.cursor()
            print("Except Block:")
        finally:
            
            PAY_FOR_SERVICES.clear()
            PAY_FOR_SERVICES_ADDONS[0] = 0
            PAY_FOR_SERVICES_ADDONS[1] = 0
            
            pay_bike_id = request.form.getlist("pay_bike_id")
            for id in pay_bike_id:
                print("3- ", id)
                
                # Get bike's name
                crsr.execute("SELECT all_bikes.brand, bikes.model FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s limit 1", [id])
                bike_name = crsr.fetchmany()
                tmp_array = [id, bike_name[0][0] + " " + bike_name[0][1]]

                # Get bike's service price
                crsr.execute("SELECT SUM(Service_price) FROM service_order WHERE Bike_ID=%s", [id])
                total_price = crsr.fetchone()
                tmp_array.append(total_price[0])
                print("tmp_array", tmp_array)
                PAY_FOR_SERVICES.append(tmp_array)
                PAY_FOR_SERVICES_ADDONS[1] += total_price[0]
                
                # Add bike ID to global container for storing
                Paid_bike_ids.append(id)
                print("4- ", Paid_bike_ids)

            PAY_FOR_SERVICES_ADDONS[0] = (len(pay_bike_id))
            
            # Get customer's details
            crsr.execute("SELECT CONCAT(users.Fname, ' ', users.Lname) AS fullname, users.Email, users.Address, users.City FROM users JOIN service_order ON users.ID = service_order.User_ID WHERE Bike_ID=%s LIMIT 1", [id])
            customers_details = crsr.fetchall()
            CUSTOMER_DETAILS.append(customers_details[0])
                        
            return render_template("payment.html", FULLNAME=FULLNAME, PAY_FOR_SERVICES=PAY_FOR_SERVICES, PAY_FOR_SERVICES_ADDONS=PAY_FOR_SERVICES_ADDONS, CUSTOMER_DETAILS=CUSTOMER_DETAILS)

    return redirect("/pick_up")


#--------------------------------------------------------------------------------- paid
@app.route("/paid", methods=["GET", "POST"])
@login_required
def paid():
        
    if request.method == "POST":
        # Send list of "Paid services" to status update
        CARDNUMBER = request.form.get("cardnumber")
        cardlen = len(CARDNUMBER)
        EXPMONTH = request.form.get("expmonth")
        EXPYEAR = request.form.get("expyear")
        CVV = request.form.get("cvv")
        
        # Validate card number
        if cardlen >= 13 and cardlen <= 16:
            regular = 0
            double = 0
            x = cardlen - 1
            while (x >= 0):
                regular += int(CARDNUMBER[x])
                x -= 1
                if x >= 0:
                    double_digit = int(CARDNUMBER[x]) * 2
                    double += int(double_digit // 10)
                    double += int(double_digit % 10)
                    x -= 1
                    
            if (regular + double)%10 == 0:
                print("Payment Succeeded")
                # Card Valid
                COMPLETED = update_completed(Paid_bike_ids)
                if COMPLETED == 1:
                    #flash('Payment Succeeded! You may pick your bike/s. Thank you!')
                    #return redirect("/pick_up")
                    return redirect("/payment_accepted")
                    
            else:
                print("Payment Rejected")
                ERROR_RES = [0]
                return render_template("payment.html", PAY_FOR_SERVICES=PAY_FOR_SERVICES, PAY_FOR_SERVICES_ADDONS=PAY_FOR_SERVICES_ADDONS, CUSTOMER_DETAILS=CUSTOMER_DETAILS, ERROR_RES=ERROR_RES)
        else:
            # return to payment.html page with "Payment Rejected" alert
            print("Invalid credit card number")
            ERROR_RES = [0]
            return render_template("payment.html", PAY_FOR_SERVICES=PAY_FOR_SERVICES, PAY_FOR_SERVICES_ADDONS=PAY_FOR_SERVICES_ADDONS, CUSTOMER_DETAILS=CUSTOMER_DETAILS, ERROR_RES=ERROR_RES)
    return redirect("/pick_up")


#--------------------------------------------------------------------------------- payment_accepted
@app.route("/payment_accepted", methods=["GET", "POST"])
@login_required
def payment_accepted():
    FULLNAME = fullName()
    
    # Reroute after payment approved
    if request.method == "POST":
        return redirect("/pick_up")
    
    # Send to payment_accepted.html to show dummy payment show
    flash("Please wait while our credit card is being checked")
    return render_template("payment_accepted.html", FULLNAME = FULLNAME)


#--------------------------------------------------------------------------------- Account
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    
    ID = [session["user_id"]]

    if request.method == "POST":
        FNAME = request.form.get("Fname").strip().capitalize()
        LNAME = request.form.get("Lname").strip().capitalize()
        PHONE = request.form.get("Phone")
        PSSWD = request.form.get("Password1").strip()
        CITY = request.form.get("City").strip().capitalize()
        ADDRESS = request.form.get("Address").strip().capitalize()
        USER = [FNAME, LNAME, PSSWD, PHONE, CITY, ADDRESS, ID[0]]
        try:
            crsr = db.cursor()
        except:
            db.reconnect()
            crsr = db.cursor()
        finally:
            # Set easch User's detail if updated
            if FNAME:
                SET = [FNAME, ID[0]]
                crsr.execute("UPDATE users SET Fname = %s WHERE ID = %s", SET)
                db.commit()
            if LNAME:
                SET = [LNAME, ID[0]]
                crsr.execute("UPDATE users SET Lname = %s WHERE ID = %s", SET)
                db.commit()
            if PHONE:
                SET = [PHONE, ID[0]]
                crsr.execute("UPDATE users SET Phone = %s WHERE ID = %s", SET)
                db.commit()
            if PSSWD:
                HASHED_PSWRD = generate_password_hash(PSSWD)
                SET = [HASHED_PSWRD, ID[0]]
                crsr.execute("UPDATE users SET Psswd = %s WHERE ID = %s", SET)
                db.commit()
            if CITY:
                SET = [CITY, ID[0]]
                crsr.execute("UPDATE users SET City = %s WHERE ID = %s", SET)
                db.commit()
            if ADDRESS:
                SET = [ADDRESS, ID[0]]
                crsr.execute("UPDATE users SET Address = %s WHERE ID = %s", SET)
                db.commit()
            
            # If some details updated:
            if FNAME or LNAME or PHONE or PSSWD or CITY or ADDRESS:
                print("User's profile updated!")
                flash("Your details were updated !")
    
    # Get fresh record of User's details        
    try:
        crsr = db.cursor()
    except:
        db.reconnect()
        crsr = db.cursor()
    finally:
        crsr.execute("SELECT Fname, Lname, Email, Phone, Psswd, City, Address FROM users WHERE ID = %s", ID)
        USER_INFO = crsr.fetchmany()

    # Show connected User Full Name
    FULLNAME = fullName()
    
    # Redirect user to account page
    return render_template("account.html", FULLNAME=FULLNAME, USER = USER_INFO[0])


#--------------------------------------------------------------------------------- Recover account
@app.route("/recover", methods=["GET", "POST"])
def Recover():
    
    if request.method == "POST":
        if request.form.get("empty_input") == 'None':
                       
            # Get required info from user @ login page VIA recover form
            PHONE = request.form.get("Recover_Email").lower().strip()
            EMAIL = request.form.get("Recover_Pswrd").lower().strip()
            VERIFICATION = request.form.get("Ver_Code")
            
            TMPARRAY = [EMAIL, PHONE, VERIFICATION]
            
            # Check if user is registered
            try:
                crsr = db.cursor()
            except:
                db.reconnect()
                crsr = db.cursor()
            finally:
                crsr.execute("SELECT Email FROM users WHERE Email = %s", [EMAIL])
                USERS_EMAIL = crsr.fetchone()
                
                # If user exist, find him by Email
                if USERS_EMAIL != None:                        
                    # Generate 2-step Psswd for Email verification
                    TWOSTEPCODE = random.randint(1000,9999)
                    TMPARRAY.append(TWOSTEPCODE)
                    # Send verification Email to user
                    EMAIL_CONTENT = ['This is a verification Email From G-bikes', 'Your verification code just arrived', "Your code is: " + str(TWOSTEPCODE)]
                    send_status = send_email(EMAIL, EMAIL_CONTENT[0], EMAIL_CONTENT[1], EMAIL_CONTENT[2])
                    return render_template("recover.html", TMPARRAY=TMPARRAY)
                else:
                    # Find User's Email by Phone number
                    crsr.execute("SELECT Email FROM users WHERE Phone = %s limit 1", [PHONE])
                    USERS_EMAIL_BY_PHONE = crsr.fetchone()
                    
                    # If User's Phone number exist
                    if USERS_EMAIL_BY_PHONE != None:                        
                        TWOSTEPCODE = random.randint(1000,9999)
                        TMPARRAY.append(TWOSTEPCODE)
                        TXT = "Your code is: " + str(TWOSTEPCODE)
                        EMAIL_CONTENT = ['This is a verification Email From G-bikes', 'Your verification code just arrived', TXT]
                        send_status = send_email(USERS_EMAIL_BY_PHONE[0], EMAIL_CONTENT[0], EMAIL_CONTENT[1], TXT)
                        TMPARRAY[0] = USERS_EMAIL_BY_PHONE[0]
                        return render_template("recover.html", TMPARRAY=TMPARRAY)
                    else:
                        # If user or Phone does not exist.
                        TMPARRAY.append(None)
                        return render_template("recover.html", TMPARRAY=TMPARRAY)
        else:
            EMAIL = request.form.get("EMAIL")
            # Generate new temporary password
            RAND_PSWRD = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
              for i in range(10))
                       
            # Send the new temporary password to user
            EMAIL_CONTENT = ['Grab your new password From G-bikes', 'Your temporary password just arrived', "Your temporary password is: <strong>" + str(RAND_PSWRD) + "</strong><br> After login with the temporary password we strongly recommend to change the password on you account page."]
            send_status = send_email(EMAIL, EMAIL_CONTENT[0], EMAIL_CONTENT[1], EMAIL_CONTENT[2])
            
            # Send new password for hashing
            HASHED_PSWRD = generate_password_hash(RAND_PSWRD)
            parameters = [HASHED_PSWRD, EMAIL]
            
            # Update the password in user's profile
            try:
                crsr = db.cursor()
            except:
                db.reconnect()
                crsr = db.cursor()
            finally:
                crsr.execute("UPDATE users SET Psswd = %s WHERE Email = %s", parameters)
                db.commit()
    flash("We sent an Email with a verification code to your Mailbox")
    return redirect("/login")


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
        datetime_STR = line3[0].strftime("%A, %d-%b-%Y %H:%M %p")
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