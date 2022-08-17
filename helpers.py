import os
import mysql.connector
import csv
import datetime
from datetime import datetime
import math

from flask import redirect, render_template, request, session
from functools import wraps

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
                # print('DB_Count:', DB_Count)
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
                    # Calculate service start/end datetime
                    start_end_service_time = start_end_time(service['user_ID'], i[1])
                    parameters.append(start_end_service_time[0])
                    parameters.append(start_end_service_time[1])
                    parameters.append(start_end_service_time[2])
                    db.reconnect()
                    crsr.execute("INSERT INTO service_order (User_ID, Bike_ID, Service_procedure, Service_notes, Service_price, Procedure_time, Registration_datetime, Start_datetime, End_datetime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", parameters)
                    db.commit()
                    print("Bike:" + str(service['bike_ID']) + " Procedure:" + str(service_procedure) + " added to service_order table queue")
    return True


# Service time management system FNK
def start_end_time(User_ID, Procedure_time_MIN):
    User_ID = [User_ID]
    
    # Determine workshop business hours
    open_time = ((9*60)+(0))  # DayTime to minute { Open @ 09:30am => H:(9*60) + M:(30) }
    close_time = ((21*60)+(0))   # DayTime to minute { Close @ 22:30pm => H:(22*60) + M:(30) }
    
    # Set "End service time" if table "service_order" populated
    crsr = db.cursor()
    crsr.execute('SELECT End_datetime FROM service_order WHERE User_ID=%s order by Service_ID desc', User_ID)
    for end_time in crsr:
        Registration_datetime = datetime.now()
        
        # If workshop's service queue is empty, start service immediately
        if math.trunc(datetime.timestamp(Registration_datetime)) >= math.trunc(datetime.timestamp(end_time[0])):
            
                # Check user registration time is inside/outside business hours
                Start_datetime = datetime.now()
                hour = int(Start_datetime.strftime("%H"))
                minute = int(Start_datetime.strftime("%M"))
                outside_business_hour_time = ((hour*60)+minute)
                over_time_delta = (outside_business_hour_time - close_time)*60
                
                # If service booked outside of business hours
                if over_time_delta >= 0:
                    udjusted_overtime_timestamp = math.trunc(datetime.timestamp(Start_datetime)) - over_time_delta
                    udjusted_overtime_timestamp_datetime = datetime.fromtimestamp(udjusted_overtime_timestamp)
                    
                    # Send service data to schedule service/s in service queue for the next business day
                    converted = workhours(Start_datetime, udjusted_overtime_timestamp_datetime, Procedure_time_MIN, open_time, close_time)
                    return converted
                else:
                    # Send service data to schedule service/s as long as they are in same business day time time window
                    converted = workhours(Start_datetime, Start_datetime, Procedure_time_MIN, open_time, close_time)
                    return converted
            
        # If workshop's service queue is busy, add service to queue
        converted = workhours(Registration_datetime, end_time[0], Procedure_time_MIN, open_time, close_time)
        return converted
        
    # Set "End service time" if table "service_order" empty or no services in service queue
    Start_datetime = datetime.now()
    converted = workhours(Start_datetime, Start_datetime, Procedure_time_MIN, open_time, close_time)
    return converted

# Determine service end time
def workhours(Registration_datetime, Start_datetime, Procedure_time_MIN, open_time, close_time):
   
    # Convert to datetime to timestamp
    input_time_timestamp = math.trunc(datetime.timestamp(Start_datetime))

    hour = int(Start_datetime.strftime("%H"))
    minute = int(Start_datetime.strftime("%M"))
    time_now_day_minutes = (hour*60) + minute
    
    # If service finishes before end of business day return "End service time"
    if (time_now_day_minutes + Procedure_time_MIN) <= close_time:
        input_time_timestamp = math.trunc(datetime.timestamp(Start_datetime))
        end_time = input_time_timestamp + (Procedure_time_MIN * 60)
        end_time_datetime = datetime.fromtimestamp(end_time)
        start_end = [Registration_datetime, Start_datetime, end_time_datetime]
        return start_end
    
    # If service finishes after end of business day return "End service time" on the next day
    else:
        time_to_day_end = ((1440-close_time+open_time)*60) + input_time_timestamp + (Procedure_time_MIN*60)
        end_time_datetime = datetime.fromtimestamp(time_to_day_end)
        start_end = [Registration_datetime, Start_datetime, end_time_datetime]
        return start_end
