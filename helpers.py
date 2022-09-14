import os
import mysql.connector
import csv
import datetime as dt
import random
from datetime import datetime
from datetime import timedelta
from flask import redirect, render_template, session
from functools import wraps
from pytz import timezone
from email.message import EmailMessage
import smtplib

# Configure business working hours (workshop business hours: 09:00=>21:00)
open_hours = dt.time(0, 1, 0, 0)         # 09:00:00
close_hours = dt.time(23, 59, 0, 0)       # 21:00:00

# Configure Email Address & Password for sending Emails
EMAIL_ADDRESS = os.environ.get('Gmail_smtp_username')
EMAIL_PSSWRD = os.environ.get('Gmail_smtp_psswrd')


# Udjust app's server timezone for GMT+3 (Israel)
def time_UTC_to_IL():
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    now_IL = datetime.now(timezone('Israel'))
    now_IL_str = now_IL.strftime('%Y-%m-%d %H:%M:%S.%f')
    now_IL_dt = datetime.strptime(now_IL_str, fmt)
    
    return now_IL_dt


# Configure MySql connection to DataBase For app Manager
db = mysql.connector.connect(
    host = "eu-cdbr-west-03.cleardb.net",
    user = os.environ.get("Heroku_user"),
    passwd = os.environ.get("Heroku_psswrd"),
    database = "heroku_666bfee5e0eaef3"
)


# Create required tables as program starts if not exist
def create_tables():
        # Check if TABLES exist in DB
        crsr = db.cursor()
        crsr.execute("SHOW TABLES")

        tables = crsr.fetchall()
        all_bikes = 0
        bikes = 0
        users = 0
        orders_history = 0
        service_order = 0
        services = 0
        for table in tables:
            if ("all_bikes" in table):
                all_bikes += 1
            if ("bikes" in table):
                bikes += 1
            if ("orders_history" in table):
                orders_history += 1
            if ("users" in table):
                users += 1
            if ("service_order" in table):
                service_order += 1
            if ("services" in table):
                services += 1
                
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
            CSV_Count = 0
            with open('Bikes.csv', 'r') as csv_file:
                reader = csv.reader(csv_file)
                for line in reader:
                    CSV_Count += 1
                csv_file.close()
                print('Check all_bikes LEN: CSV vs DB', CSV_Count, DB_Count)
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
            
        if (orders_history == 0):
            crsr.execute("CREATE TABLE orders_history (Service_ID int unsigned NOT NULL unique, Service_batch int unsigned, User_ID int unsigned NOT NULL, Bike_ID int unsigned NOT NULL, Service_procedure int unsigned NOT NULL, Service_notes varchar(511), Service_price float(10, 2) NOT NULL, Procedure_time int unsigned NOT NULL, Registration_datetime datetime, Start_datetime datetime, End_datetime datetime, completed_datetime datetime, Service_status varchar(15) DEFAULT 'queued', PRIMARY KEY (Service_ID))")
            print("Table orders_history Created")
        
        if (service_order == 0):
            crsr.execute("CREATE TABLE service_order (Service_ID int unsigned NOT NULL unique AUTO_INCREMENT, User_ID int unsigned NOT NULL, Bike_ID int unsigned NOT NULL, Service_procedure int unsigned NOT NULL, Service_notes varchar(511), Service_price float(10, 2) NOT NULL, Procedure_time int unsigned NOT NULL, Registration_datetime datetime, Start_datetime datetime, End_datetime datetime, Completed_datetime datetime, Service_status varchar(15) DEFAULT 'queued', Emailed tinyint DEFAULT 0, PRIMARY KEY (Service_ID))")
            print("Table service_order Created")
        
        if (services == 0):
            crsr.execute("CREATE TABLE services (ID int unsigned NOT NULL AUTO_INCREMENT, Service_ID int NOT NULL unique, Service_description varchar(65) NOT NULL, Service_price float(10, 2) NOT NULL, Service_time int NOT NULL, PRIMARY KEY (ID))")
            print("Table services Created")
            # Populate TABLE services when created
            populate_services_table(crsr)
        else:
            # Validate TABLE services with CSV file
            validate_services_table(crsr, db)
            
        if (users == 0):
            crsr.execute("CREATE TABLE users (ID int unsigned NOT NULL AUTO_INCREMENT, Fname varchar(55) NOT NULL, Lname varchar(55) NOT NULL, Email varchar(55) NOT NULL, Psswd varchar(128) NOT NULL, Phone int NOT NULL, City varchar(55) NOT NULL, Address varchar(128) NOT NULL, Verified INT NOT NULL, Registered datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (ID))")
            print("Table users Created")


# Polulate "All_Bikes" table from CSV Bikes file
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


# Polulate "services" table from CSV Service file
def populate_services_table(crsr):
    
    print("Populating table services. Please wait...")
    
    with open('Services.csv', 'r') as services_file:
        reader = csv.DictReader(services_file)
        for line in reader:
            # print(line['Service_ID'], line['Service_description'], line['Service_price'], line['Service_time'])
            service = [line['Service_ID'], line['Service_description'], line['Service_price'], line['Service_time']]
            crsr.execute("INSERT INTO services (Service_ID, Service_description, Service_price, Service_time) values(%s, %s, %s, %s)", service)
            db.commit()
        services_file.close()
        print("Table services up to date")


# Validate "services" table with CSV Service file
def validate_services_table(crsr, db):
    service_DB = []
    service_CSV = []
    SERVICES = load_services()
    crsr.execute("SELECT * FROM services order by Service_ID")
    
    for service in SERVICES:
        S1 = int(service['Service_ID']), service['Service_description'], float(service['Service_price']), int(service['Service_time'])
        service_CSV.append(S1)
    #print(service_DB)
    for line in crsr:
        S2 = line[1], line[2], line[3], line[4]
        service_DB.append(S2)
    #print(service_CSV)
    print('Check services LEN: CSV vs DB', len(service_CSV), len(service_DB))
    
    # Checks if CSV file were modified  
    if len(service_CSV) != len(service_DB):
        crsr.execute("DROP TABLE services")
        crsr.execute("CREATE TABLE services (ID int unsigned NOT NULL AUTO_INCREMENT, Service_ID int NOT NULL unique, Service_description varchar(65) NOT NULL, Service_price float(10, 2) NOT NULL, Service_time int NOT NULL, PRIMARY KEY (ID))")
        populate_services_table(crsr)
    # Checks if all parameters of CSV file and DB table are accurate    
    else:
        for i in range(len(service_CSV)):
            #print(service_DB[i][0], service_DB[i][1], service_DB[i][2])
            #print(service_CSV[i][0], service_CSV[i][1], service_CSV[i][2])
            if (service_DB[i][0], service_DB[i][1], service_DB[i][2], service_DB[i][3]) != (service_CSV[i][0], service_CSV[i][1], service_CSV[i][2], service_CSV[i][3]):
                Service_ID = [service_CSV[i][1], service_CSV[i][2], service_CSV[i][3], service_CSV[i][0]]
                print("Service_ID", i + 1, "Modified: ", Service_ID)
                crsr.execute("UPDATE services SET Service_description = %s, Service_price = %s, Service_time = %s WHERE Service_ID = %s", Service_ID)
                db.commit()
        print("Table services up to date")
    return None


# Load "services" from CSV file
def load_services():
    SERVICES = []
    with open('Services.csv', 'r') as services_file:
        reader = csv.DictReader(services_file)
        for line in reader:
            SERVICES.append(line)
    services_file.close()
    return SERVICES


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
    add_bike_to_DB(ID, MODEL, YEAR)
    
    # Update CSV file
    with open('Bikes.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow([BIKE])
        csv_file.close()
        print("CSV file updated")
    return


# Insert user bike into bikes table
def add_bike_to_DB(id, MODEL, YEAR):
    BIKE_MODEL = [session["user_id"], id, MODEL, YEAR]
    crsr = db.cursor()
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


# Update "service_order" table with customer's order/s
def service_order(SERVICES):
    for service in SERVICES:
        if service['bike_services']:
            for service_procedure in service['bike_services']:                
                ID = [service_procedure]
                queue = 'SELECT Service_price, Service_time FROM services WHERE Service_ID = %s'
                crsr = db.cursor()
                crsr.execute(queue, ID)
                for i in crsr:
                    parameters = []
                    parameters.append(service['user_ID'])
                    parameters.append(service['bike_ID'])
                    parameters.append(service_procedure)
                    parameters.append(service['bike_service_notes'])
                    parameters.append(i[0])
                    parameters.append(i[1])
                    
                    # Calculate service start/end datetime considering business working hours
                    start_end_service_time = time_management(i[1])
                    
                    parameters.append(start_end_service_time[0])
                    parameters.append(start_end_service_time[1])
                    parameters.append(start_end_service_time[2])
                    db.reconnect()
                    crsr.execute("INSERT INTO service_order (User_ID, Bike_ID, Service_procedure, Service_notes, Service_price, Procedure_time, Registration_datetime, Start_datetime, End_datetime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", parameters)
                    db.commit()
                    print("Bike:" + str(service['bike_ID']) + " Procedure:" + str(service_procedure) + " added to service_order table queue")
    return True


# BikeServices time management system function
def time_management(Procedure_time):
    # Determine business operation hours

    timenow = time_UTC_to_IL().time()
    datetimenow = time_UTC_to_IL()
    
    # if service ordered in business operation hours
    if timenow >= open_hours and timenow < close_hours:
        crsr = db.cursor()
        crsr.execute("SELECT End_datetime FROM service_order order by Service_ID desc limit 1")
        
        # If prior service exist in "service_order" table
        for service in crsr:
            # If service queue is empty & no service running
            if datetimenow >= service[0]:
                check_end_time = end_service_time(datetimenow, datetimenow, Procedure_time, open_hours, close_hours)
                return check_end_time
            # If service in queue and running
            else:
                check_end_time = end_service_time(datetimenow, service[0], Procedure_time, open_hours, close_hours)
                return check_end_time
        
        # if no service in "service_order" queue table (blank table)
        check_end_time = end_service_time(datetimenow, datetimenow, Procedure_time, open_hours, close_hours)
        return check_end_time
        
    # if service ordered outside business operation hours
    else:
        crsr = db.cursor()
        crsr.execute("SELECT End_datetime FROM service_order order by Service_ID desc limit 1")
        
        # if prior service exist in "service_order" table queue
        for service in crsr:
            if service[0] > datetimenow:
                check_end_time = end_service_time(datetimenow, service[0], Procedure_time, open_hours, close_hours)
                return check_end_time
            
        
        # if no service in "service_order" queue table (blank table)
        hours_now = int(timenow.strftime('%H'))
        minutes_now = int(timenow.strftime('%M'))
        
        hours_open = int(open_hours.strftime('%H'))
        minutes_open = int(open_hours.strftime('%M'))

        hours_close = int(close_hours.strftime('%H'))
        
        # If service booked after close hours & after midnight
        if hours_now < hours_open:
            hours_to_open = hours_open - hours_now - 1
            minutes_to_open = 60 - minutes_now
            start_service_time = datetimenow + timedelta(hours = hours_to_open, minutes = minutes_to_open)
            check_end_time = end_service_time(datetimenow, start_service_time, Procedure_time, open_hours, close_hours)
            return check_end_time
        
        # If service booked after close hours & before midnight
        elif hours_now >= hours_close and hours_now <= 23:
            open_hours_left = 23 - hours_now + hours_open
            open_minutes_left = 60 - minutes_now + minutes_open
            start_service_time = datetimenow + timedelta(hours = open_hours_left, minutes = open_minutes_left)
            check_end_time = end_service_time(datetimenow, start_service_time, Procedure_time, open_hours, close_hours)
            return check_end_time
        

# Determine service end time
def end_service_time(datetimenow, starttime, Procedure_time, open, close):
    
    # If service endtime before close time
    end_service_time = starttime + timedelta(minutes=Procedure_time)
    if end_service_time.time() < close:
        end_time = [datetimenow, starttime, end_service_time]
        return end_time
    
    # If service endtime after close time
    elif end_service_time.time() >= close:        
        hours_open = int(open.strftime('%H'))
        minutes_open = int(open.strftime('%M'))

        hours_close = int(close.strftime('%H'))
        minutes_close = int(close.strftime('%M'))

        HOURS = 23 - hours_close + hours_open
        MINUTES = 60 - minutes_close + minutes_open

        end_time = starttime + timedelta(hours=HOURS, minutes=MINUTES + Procedure_time)
        end_service_time = [datetimenow, starttime, end_time]

    return end_service_time


# Maintain "Service_status" in "service_order" table
def maintain_Service_status(Service_ID):
    db.reconnect()
    crsr = db.cursor()
    service_len = len(Service_ID)

    # Service_ID[0]=Service_ID, Service_ID[1]=Service_status, Service_ID[2]=End_datetime
    for i in range(service_len):
        
        # If Order ready
        if Service_ID[i][2] <= time_UTC_to_IL():
            ID = [Service_ID[i][0]]
            crsr.execute("UPDATE service_order SET Service_status = 'ready' WHERE Service_ID=%s", ID)
            db.commit()
         
        # If Order in progress
        elif time_UTC_to_IL() > Service_ID[i - 1][2] and time_UTC_to_IL() <= Service_ID[i][2]:
            ID = [Service_ID[i][0]]
            crsr.execute("UPDATE service_order SET Service_status = 'in service' WHERE Service_ID=%s", ID)
            db.commit()
            
        # If very first order in table
        elif Service_ID[i][4] == Service_ID[i][3]:
            ID = [Service_ID[i][0]]
            crsr.execute("UPDATE service_order SET Service_status = 'in service' WHERE Service_ID=%s", ID)
            db.commit()
            
        # If Order in waitlist
        else:
            ID = [Service_ID[i][0]]
            crsr.execute("UPDATE service_order SET Service_status = 'in queue' WHERE Service_ID=%s", ID)
            db.commit()
    return True


# Reordering required info from "service_order" table to be ready for display
def display_services():
    
    # Update status of bikes in service Queue
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT Service_ID, Service_status, End_datetime, Start_datetime, Registration_datetime FROM service_order order by End_datetime")
    sort_service = []
    for bike in crsr:
        if bike[1] != "completed":
            sort_service.append(bike)
    maintain_Service_status(sort_service)
    
    # Get info for SERVICE_RUNNING
    SERVICE_RUNNING = []
    db.reconnect()
    crsr = db.cursor()
    crsr.execute("SELECT service_order.Service_ID, all_bikes.brand, bikes.model, services.Service_description, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Service_status = 'in service' order by End_datetime, Service_ID")
    for line in crsr:
        # Convert datetime display method
        line_list = list(line)
        line_list[4] = line_list[4].strftime("%A, %d-%b-%Y %H:%M %p")
        SERVICE_RUNNING.append(line_list)

    # Get info for SERVICE_READY
    SERVICE_READY_REV = []
    SERVICE_READY = []
    count = 0
    counter = 0
    crsr = db.cursor()
    crsr.execute("SELECT service_order.Service_ID, all_bikes.brand, bikes.model, services.Service_description, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Service_status = 'ready' order by End_datetime DESC limit 3")
    for line2 in crsr:
        # Convert datetime display method
        line_list2 = list(line2)
        line_list2[4] = line_list2[4].strftime("%A, %d-%b-%Y %H:%M %p")
        SERVICE_READY_REV.append(line_list2)
        count += 1
    # Reverse SERVICE_READY display order in main.html
    counter = count
    for i in range (counter):
        SERVICE_READY.append(SERVICE_READY_REV[counter - 1 - i])
    
    
    # Get info for SERVICE_IN_Q
    SERVICE_IN_Q = []
    crsr = db.cursor()
    crsr.execute("SELECT service_order.Service_ID, all_bikes.brand, bikes.model, services.Service_description, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Service_status = 'in queue' order by End_datetime limit 3")
    for line3 in crsr:
        # Convert datetime display method
        line3_list = list(line3)
        line3_list[4] = line3_list[4].strftime("%A, %d-%b-%Y %H:%M %p")
        SERVICE_IN_Q.append(line3_list)

    # Convert datetime display method & send to display in main.html
    open_hours_str = open_hours.strftime("%H:%M %p")
    close_hours_str = close_hours.strftime("%H:%M %p")
    WORKING_HOURS = [open_hours_str, close_hours_str]
    
    return SERVICE_RUNNING, SERVICE_READY, SERVICE_IN_Q, WORKING_HOURS


# gathering required info from "service_order" table to be ready for display in pick_up.html
def display_user_service_status(USER_ID):
    db.reconnect()
    BIKES = []
    BIKES_READY = []
    BIKES_INSERVICE = []
    
    
    # Find all distinct bikes per user in service_order
    crsr = db.cursor()
    crsr2 = db.cursor()
    crsr_bike = db.cursor()
    crsr.execute("SELECT distinct Bike_ID FROM service_order WHERE User_ID = %s", USER_ID)
    for Bike in crsr:
        BIKES.append(Bike)
    
    # Sort fully ready serviced bikes
    for i in range(len(BIKES)):
        counter = 0
        crsr.execute("SELECT Bike_ID, count(Service_status), Service_status FROM service_order WHERE Bike_ID = %s", BIKES[i])
        for line in crsr:
            crsr2.execute("SELECT service_order.Service_ID, all_bikes.brand, bikes.model, services.Service_description, service_order.End_datetime, service_order.Service_status FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s order by End_datetime", BIKES[i])
            for line2 in crsr2:
                if line2[5] == line[2] and line[2] == 'ready':
                    counter += 1
        if counter == line[1]:
            BIKES_READY.append(BIKES[i])
                        
            # Send Email update to client with list of ready for pick up bikes
            send_email_ready_update = validate_ready_for_email()
            
        else:
            BIKES_INSERVICE.append(BIKES[i])
    crsr2.close()
    
    # Gather summarized info for every ready for pick-up bike from "service_order" table     
    for i in range(len(BIKES_READY)):
        BIKES_READY_DICT = {}
        crsr.execute("SELECT bikes.ID, all_bikes.brand, bikes.model, sum(service_order.Service_price) FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s", BIKES_READY[i])
        for line in crsr:
            BIKES_READY_DICT["BIKE_ID"] = line[0]
            BIKES_READY_DICT["BIKE_NAME"] = line[1] + " " + line[2]
            BIKES_READY_DICT["TOTAL_PRICE"] = line[3]
            BIKES_READY_DICT["SERVICES"] = []
        
        crsr.execute("SELECT service_order.Service_ID, services.Service_description, service_order.Service_price, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s order by End_datetime", BIKES_READY[i])
        for line in crsr:
            BIKES_READY_DICT["SERVICES"].append(line)
        BIKES_READY[i] = BIKES_READY_DICT
    
    
    # Gather summarized info for every unready bike from "service_order" table 
    for i in range(len(BIKES_INSERVICE)):
        BIKES_INSERVICE_DICT = {}
        crsr.execute("SELECT bikes.ID, all_bikes.brand, bikes.model, sum(service_order.Service_price) FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s", BIKES_INSERVICE[i])
        for line in crsr:
            BIKES_INSERVICE_DICT["BIKE_ID"] = line[0]
            BIKES_INSERVICE_DICT["BIKE_NAME"] = line[1] + " " + line[2]
            BIKES_INSERVICE_DICT["TOTAL_PRICE"] = line[3]
            BIKES_INSERVICE_DICT["SERVICES"] = []
        
        crsr.execute("SELECT service_order.Service_ID, services.Service_description, service_order.Service_price, service_order.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN service_order ON bikes.ID = service_order.Bike_ID JOIN services ON services.Service_ID = service_order.Service_procedure WHERE Bike_ID=%s order by End_datetime", BIKES_INSERVICE[i])
        for line in crsr:
            if line[3] < time_UTC_to_IL():
                line_tmp = list(line)
                line_tmp[3] = 0
                line = (line_tmp)
            BIKES_INSERVICE_DICT["SERVICES"].append(line)
        BIKES_INSERVICE[i] = BIKES_INSERVICE_DICT
    
    # Gather summarized info for every completed order batch from "orders_history" table
    # Find amount of (Batches) per user
    BATCHES = 0
    
    # Find all service dates (Batches) per user
    SERVICE_HISTORY = {}
    batches = []
    crsr.execute("SELECT DISTINCT Service_batch FROM orders_history WHERE User_ID = %s", USER_ID)
    for batch in crsr:
        batches.append(batch)
        SERVICE_HISTORY[batch[0]] = []
        BATCHES += 1    
        
    
    
    # Find all bikes in each batch for every Batch
    for bike_ID in batches:
        crsr.execute("SELECT COUNT(DISTINCT Bike_ID) FROM orders_history WHERE Service_batch = %s", bike_ID)
        count_bikes = crsr.fetchone()
           
    # Insert bike info into SERVICE_HISTORY dict
        data_tmp = []
        crsr.execute("SELECT DISTINCT Bike_ID, Service_batch FROM orders_history WHERE Service_batch = %s", bike_ID)
        for batch_bike in crsr:
            # Insert bike info into SERVICE_HISTORY dict
            data_tmp.append(batch_bike[0])
            SERVICE_HISTORY[batch_bike[1]] = data_tmp
                
    # Create and fill BIKES_COMPLETED array to store and display data @ pick_up.html
    BIKES_COMPLETED = []
    
    for i in SERVICE_HISTORY:
        tmparray = []
        for y in range(len(SERVICE_HISTORY[i])):
            BIKES_COMPLETED_DICT = {}

            BIKE_ID = [SERVICE_HISTORY[i][y], i]
            crsr.execute("SELECT bikes.ID, all_bikes.brand, bikes.model, sum(orders_history.Service_price) FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN orders_history ON bikes.ID = orders_history.Bike_ID JOIN services ON services.Service_ID = orders_history.Service_procedure WHERE Bike_ID=%s AND Service_batch = %s", BIKE_ID)
            line = crsr.fetchone()
            
            BIKES_COMPLETED_DICT["BIKE_ID"] = line[0]
            BIKES_COMPLETED_DICT["BIKE_NAME"] = line[1] + " " + line[2]
            BIKES_COMPLETED_DICT["TOTAL_PRICE"] = line[3]
            BIKES_COMPLETED_DICT["SERVICES"] = []
            
            crsr.execute("SELECT max(End_datetime), min(Start_datetime), Registration_datetime, Completed_datetime FROM orders_history WHERE Bike_ID=%s AND Service_batch = %s", BIKE_ID)
            time = crsr.fetchone()
            time_spent = time[0] - time[1]
            BIKES_COMPLETED_DICT["TOTAL_TIME"] = time_spent
            BIKES_COMPLETED_DICT["IN_OUT_TIME"] = [time[2], time[3]]
            
            
            crsr.execute("SELECT orders_history.Service_ID, services.Service_description, orders_history.Service_price, orders_history.End_datetime FROM all_bikes JOIN bikes ON all_bikes.ID = bikes.brand JOIN orders_history ON bikes.ID = orders_history.Bike_ID JOIN services ON services.Service_ID = orders_history.Service_procedure WHERE Bike_ID=%s AND Service_batch = %s order by End_datetime", BIKE_ID)
            for line in crsr:
                BIKES_COMPLETED_DICT["SERVICES"].append(line)
                
            crsr.execute("SELECT sum(Service_price) FROM orders_history WHERE Service_batch = %s", [BIKE_ID[1]])
            sum_price = crsr.fetchone()
            BIKES_COMPLETED_DICT["GRAND_TOTAL_PRICE"] = sum_price
            BIKES_COMPLETED_DICT["LOOP_INDEX"] = random.randint(100, 1000)
            
            tmparray.append(BIKES_COMPLETED_DICT)
        BIKES_COMPLETED.append(tmparray)
 
    #print(BIKES_COMPLETED)
    return BIKES_READY, BIKES_INSERVICE, BIKES_COMPLETED


# Update service status to "Completed" for paied service and move them to "orders_history" (history) table
def update_completed(BIKE_ID):
    
    DT_LOCAL = time_UTC_to_IL()
    INFO = []
    try:  
        crsr = db.cursor()
    except:
        db.reconnect()
        crsr = db.cursor()
        print("LINE 638 - Except Block:")
    finally:
        
        crsr_service_order = db.cursor()
        crsr_orders_history = db.cursor()
        
        # Chech "Service_batch" position in "orders_history" Table
        crsr_orders_history.execute("Select MAX(Service_batch) FROM orders_history")
        read_batch = crsr_orders_history.fetchone()
        if read_batch[0] == None:
            BATCH_ID = 1
        else:
            BATCH_ID = read_batch[0] + 1
        crsr_orders_history.close()
        
        # Read and update data from "service_order" & delete completed service from "service_order" table
        for i in BIKE_ID:
            BIKE_ID = [i]
            crsr_service_order.execute("Select * FROM service_order WHERE Bike_ID=%s AND Service_status = 'ready' ORDER BY Bike_ID", BIKE_ID)
            for service in crsr_service_order:
                service_list = list(service)
                service_list.pop()
                service_list.insert(1, BATCH_ID)
                service_list[11] = DT_LOCAL
                service_list[12] = 'completed'
                INFO.append(service_list)            
            crsr_service_order.execute("DELETE FROM service_order WHERE Bike_ID = %s", BIKE_ID)
            db.commit()

        # Insert updated data into "orders_history"
        crsr = db.cursor()
        for i in range(len(INFO)):
            crsr.execute("INSERT INTO orders_history (Service_ID, Service_batch, User_ID, Bike_ID, Service_procedure, Service_notes, Service_price, Procedure_time, Registration_datetime, Start_datetime, End_datetime, Completed_datetime, Service_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", INFO[i])
            db.commit()  
        return


# Validate bike service is fully ready and forward to Send_Status_update()
def validate_ready_for_email():
    
    # Send Email notification for customers with fully "ready" state bikes
    db.reconnect()
    crsr = db.cursor()
    SERVICED_BIKES = []
    # Find all unemailed ready services
    crsr.execute("SELECT DISTINCT Bike_ID FROM service_order WHERE Service_status = 'ready' AND Emailed = 0")
    for Bike_ID in crsr:
        SERVICED_BIKES.append(Bike_ID)
    
    # Verify service is fully "ready"
    for i in SERVICED_BIKES:
        
        crsr.execute("SELECT COUNT(Service_status) FROM service_order WHERE Bike_ID = %s", i)
        count_procedures = crsr.fetchone()
        
        crsr.execute("SELECT COUNT(Service_status) FROM service_order WHERE Bike_ID = %s AND Service_status = 'ready'", i)
        count_ready = crsr.fetchone()
        
        # If service is fully ready, send notification
        if count_procedures == count_ready:
            print("Send_Status_update")
            Send_Status_update(Bike_ID)
            
    return


# Send Email update to client with list of ready for pick up bikes
def Send_Status_update(BIKES_READY):
    
    # Find customer's Email address and send "Ready" notification
    CUSTOMERS_BIKE_ID = BIKES_READY[0]
    
    crsr = db.cursor()
    crsr.execute("SELECT users.Email, bikes.model FROM users JOIN bikes ON bikes.cust_id = users.ID JOIN service_order ON bikes.cust_id = service_order.User_ID WHERE bikes.ID = %s AND service_order.Emailed = 0 LIMIT 1", [CUSTOMERS_BIKE_ID])
    for line in crsr:
        CUSTOMERS_EAMIL = line[0]
        CUSTOMERS_BIKE = line[1]
        #print(CUSTOMERS_EAMIL, CUSTOMERS_BIKE, BIKES_READY[0])
    
        # Send update Email to user
        msg = EmailMessage()
        msg['Subject'] = 'This is a service status update From G-bikes'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = CUSTOMERS_EAMIL
        msg.set_content('Your service status just updated to ready!')
        txt = "We are happy to inform you that your service just finished and your bike <strong>" + str(CUSTOMERS_BIKE) + "</strong> is ready for pick up! <br><br> You can pay upfront by clicking the link: https://final-project-dany.herokuapp.com/pick_up"
        msg.add_alternative(txt, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PSSWRD)
            smtp.send_message(msg)
        
        # Update service Email status to send to prevent double email sending
        crsr.execute("UPDATE service_order SET Emailed = 1 WHERE Bike_ID = %s", [CUSTOMERS_BIKE_ID])
        db.commit()
        print("Email update to:", CUSTOMERS_EAMIL, "Sent!")
        return
    
    
    return