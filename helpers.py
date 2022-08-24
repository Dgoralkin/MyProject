import os
import mysql.connector
import csv
import datetime as dt
from datetime import datetime
from datetime import timedelta
from flask import redirect, render_template, request, session
from functools import wraps

# Configure business working hours (workshop business hours: 09:00=>21:00)
open_hours = dt.time(9, 00, 0, 0)         # 09:00:00
close_hours = dt.time(21, 00, 0, 0)       # 21:00:00

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
        service_order = 0
        services = 0
        for table in tables:
            if ("all_bikes" in table):
                all_bikes += 1
            if ("bikes" in table):
                bikes += 1
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
        
        if (service_order == 0):
            crsr.execute("CREATE TABLE service_order (Service_ID int unsigned NOT NULL unique AUTO_INCREMENT, User_ID int unsigned NOT NULL, Bike_ID int unsigned NOT NULL, Service_procedure int unsigned NOT NULL, Service_notes varchar(511), Service_price float(10, 2) NOT NULL, Procedure_time int unsigned NOT NULL, Registration_datetime datetime, Start_datetime datetime, End_datetime datetime, Service_status varchar(15) DEFAULT 'queued',PRIMARY KEY (Service_ID))")
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

    timenow = datetime.now().time()
    datetimenow = datetime.now()
    
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
        if Service_ID[i][2] <= datetime.now():
            ID = [Service_ID[i][0]]
            crsr.execute("UPDATE service_order SET Service_status = 'ready' WHERE Service_ID=%s", ID)
            db.commit()
         
        # If Order in progress
        elif datetime.now() > Service_ID[i - 1][2] and datetime.now() <= Service_ID[i][2]:
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