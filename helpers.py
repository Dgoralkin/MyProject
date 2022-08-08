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


# Create required tables as program starts if not exist
def create_tables():
        # Check if TABLES exist in DB
        crsr = db.cursor()
        crsr.execute("SHOW TABLES")

        tables = crsr.fetchall()
        all_bikes = 0
        bikes = 0
        users = 0
        services = 0
        for table in tables:
            if ("all_bikes" in table):
                all_bikes += 1
            if ("bikes" in table):
                bikes += 1
            if ("users" in table):
                users += 1
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
                print('DB_Count:', DB_Count)
            CSV_Count = 0
            with open('Bikes.csv', 'r') as csv_file:
                reader = csv.reader(csv_file)
                for line in reader:
                    CSV_Count += 1
                csv_file.close()
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
            
        if (services == 0):
            crsr.execute("CREATE TABLE services (ID int unsigned NOT NULL AUTO_INCREMENT, Service_ID int NOT NULL unique, Service_description varchar(65) NOT NULL, Service_price float(10, 2) NOT NULL, PRIMARY KEY (ID))")
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
            # print(line['Service_ID'], line['Service_description'], line['Service_price'])
            service = [line['Service_ID'], line['Service_description'], line['Service_price']]
            crsr.execute("INSERT INTO services (Service_ID, Service_description, Service_Price) values(%s, %s, %s)", service)
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
        S1 = int(service['Service_ID']), service['Service_description'], float(service['Service_price'])
        service_CSV.append(S1)
    #print(service_DB)
    for line in crsr:
        S2 = line[1], line[2], line[3]
        service_DB.append(S2)
    #print(service_CSV)
    print('Check services LEN: CSV vs DB', len(service_CSV), len(service_DB))
    
    # Checks if CSV file were modified  
    if len(service_CSV) != len(service_DB):
        crsr.execute("DROP TABLE services")
        crsr.execute("CREATE TABLE services (ID int unsigned NOT NULL AUTO_INCREMENT, Service_ID int NOT NULL unique, Service_description varchar(65) NOT NULL, Service_price float(10, 2) NOT NULL, PRIMARY KEY (ID))")
        populate_services_table(crsr)
    # Checks if all parameters of CSV file and DB table are accurate    
    else:
        for i in range(len(service_CSV)):
            #print(service_DB[i][0], service_DB[i][1], service_DB[i][2])
            #print(service_CSV[i][0], service_CSV[i][1], service_CSV[i][2])
            if (service_DB[i][0], service_DB[i][1], service_DB[i][2]) != (service_CSV[i][0], service_CSV[i][1], service_CSV[i][2]):
                Service_ID = [service_CSV[i][1], service_CSV[i][2], service_CSV[i][0]]
                print("Service_ID", i + 1, "Modified: ", Service_ID)
                crsr.execute("UPDATE services SET Service_description = %s, Service_Price = %s WHERE Service_ID = %s", Service_ID)
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



