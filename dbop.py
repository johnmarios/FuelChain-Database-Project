import sqlite3
import os
import re
from datetime import date
from faker import Faker
import random 

DB_PATH = "fuel_chain.db"

# Schema uses the exact table names from your SQL, including the Greek-named `ΤΑΝΚ` table
SCHEMA_SQL = '''
DROP TABLE IF EXISTS `SWITCH`;
DROP TABLE IF EXISTS `INCLUSION`;
DROP TABLE IF EXISTS `POINT_SYSTEM`;
DROP TABLE IF EXISTS `TRANSACTION`;
DROP TABLE IF EXISTS `STATION`;
DROP TABLE IF EXISTS `CUSTOMER`;
CREATE TABLE IF NOT EXISTS `STATION` (
    `station_id` integer primary key NOT NULL UNIQUE,
    `location` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `phone` INTEGER NOT NULL,
    `email` TEXT NOT NULL,
    `automated` BOOLEAN NOT NULL,
    `has_store` BOOLEAN NOT NULL
);
DROP TABLE IF EXISTS `PUMP`;
DROP TABLE IF EXISTS `TANK`;
CREATE TABLE `TANK` (
    `tank_id` integer primary key NOT NULL UNIQUE,
    `last_fill_up` REAL NOT NULL,
    `capacity` INTEGER NOT NULL,
    `current_quantity` REAL NOT NULL,
    `min_fuel_quantity` REAL NOT NULL,
    `for_station_id` INTEGER NOT NULL,
    `for_fuel_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_station_id`) REFERENCES `STATION`(`station_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_fuel_id`) REFERENCES `FUEL`(`prod_id`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `EMPLOYEE`;
CREATE TABLE `EMPLOYEE` (
    `emp_id` integer primary key NOT NULL UNIQUE,
    `fname` TEXT NOT NULL,
    `lname` TEXT NOT NULL,
    `ssn` INTEGER NOT NULL,
    `for_station_id` INTEGER NOT NULL,
    `salary` INTEGER NOT NULL,
    `email` TEXT NOT NULL,
    FOREIGN KEY(`for_station_id`) REFERENCES `STATION`(`station_id`) ON DELETE CASCADE
);
CREATE TABLE `PUMP` (
    `pump_id` integer primary key NOT NULL UNIQUE,
    `is_active` REAL NOT NULL,
    `pump_number` INTEGER NOT NULL,
    `for_tank_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_tank_id`) REFERENCES `ΤΑΝΚ`(`tank_id`) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS `CUSTOMER` (
    `customer_id` integer primary key NOT NULL UNIQUE,
    `fname` TEXT NOT NULL,
    `lname` TEXT NOT NULL,
    `address` TEXT NOT NULL,
    `phone_number` INTEGER NOT NULL,
    `email` TEXT NOT NULL,
    `tax_id` INTEGER NOT NULL,
    `payment_type` TEXT NOT NULL,
    `anonymous` REAL NOT NULL,
    `delivery_address` TEXT NOT NULL,
    `fuel_card` INTEGER NOT NULL,
    `company_name` TEXT NOT NULL,
    `for_system_points_id` INTEGER,
    FOREIGN KEY(`for_system_points_id`) REFERENCES `POINT_SYSTEM`(`customer_id`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `TRANSACTION`;
CREATE TABLE `TRANSACTION` (
    `trans_id` integer primary key NOT NULL UNIQUE,
    `trans_date` REAL NOT NULL,
    `amount_of_money` REAL NOT NULL,
    `total_points` INTEGER NOT NULL,
    `for_cust_id` INTEGER,
    `for_station_id` INTEGER,
    `payment_method` TEXT NOT NULL,
    FOREIGN KEY(`for_cust_id`) REFERENCES `CUSTOMER`(`customer_id`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `FUEL`;
CREATE TABLE `FUEL` (
    `prod_id` integer primary key UNIQUE,
    `fuel_type` TEXT NOT NULL,
    `points_per_liter` INTEGER NOT NULL,
    `for_prod_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_prod_id`) REFERENCES `PRODUCT`(`product_id`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `PRODUCT`;
CREATE TABLE `PRODUCT` (
    `product_id` integer primary key NOT NULL UNIQUE,
    `prod_type` TEXT NOT NULL
);
DROP TABLE IF EXISTS `PRODUCT_PRICE`;
CREATE TABLE `PRODUCT_PRICE` (
    `prod_id` integer primary key NOT NULL UNIQUE,
    `price` REAL NOT NULL,
    `for_station_id` INTEGER NOT NULL,
    `for_fuel_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_station_id`) REFERENCES `STATION`(`station_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_fuel_id`) REFERENCES `FUEL`(`prod_id`) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS `SUPPLY` (
    `for_pump_id` integer NOT NULL UNIQUE,
    `for_prod_id` integer NOT NULL UNIQUE,
    `quantity` REAL NOT NULL,
    `over_500_liters` REAL NOT NULL,
    FOREIGN KEY(`for_pump_id`) REFERENCES `PUMP`(`pump_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_prod_id`) REFERENCES `PRODUCT`(`product_id`) ON DELETE CASCADE
);
DROP TABLE IF EXISTS `STATION_PRODUCT`;
CREATE TABLE `STATION_PRODUCT` (
    `prod_id` integer primary key UNIQUE,
    `prod_type` TEXT NOT NULL,
    `for_prod_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_prod_id`) REFERENCES `PRODUCT`(`product_id`) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS `POINT_SYSTEM` (
    `customer_id` integer primary key NOT NULL UNIQUE,
    `points` INTEGER NOT NULL,
    `card_number` TEXT NOT NULL,
    FOREIGN KEY(`customer_id`) REFERENCES `CUSTOMER`(`customer_id`) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS `INCLUSION` (
    `for_prod_id` integer NOT NULL,
    `for_transaction_id` integer NOT NULL,
    FOREIGN KEY(`for_prod_id`) REFERENCES `PRODUCT`(`product_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_transaction_id`) REFERENCES `TRANSACTION`(`trans_id`) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS `SWITCH` (
    `for_transaction_id` integer NOT NULL,
    `for_point_system_id` integer NOT NULL,
    `date` DATETIME NOT NULL,
    `points_added` INTEGER,
    `points_deducted` INTEGER,
    FOREIGN KEY(`for_transaction_id`) REFERENCES `TRANSACTION`(`trans_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_point_system_id`) REFERENCES `POINT_SYSTEM`(`customer_id`) ON DELETE CASCADE
);
'''


def _connect():
    conn = sqlite3.connect(DB_PATH)
    # enable foreign key enforcement
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

#SCHEMA CREATION
def create_schema():
    ''' With foreign keys off, tables can reference each other regardless of creation order.'''
    with _connect() as conn:
        conn.execute('PRAGMA foreign_keys = OFF;')
        conn.executescript(SCHEMA_SQL)
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.commit()


def _digits_only(s: str) -> int:
    '''Extract digits from a string and return as integer. If no digits, return 0.'''
    if s is None:
        return 0
    digits = re.sub(r"\D", "", str(s)) # remove non-digit characters
    try:
        return int(digits) if digits else 0
    except ValueError:
        return 0


def init_db_if_needed(seed_stations: int = 10):
    """Initialize database schema and seed with data if empty"""
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Check if database has data (check if STATION table has any records)
        cursor.execute("SELECT COUNT(*) FROM `STATION`")
        station_count = cursor.fetchone()[0]
        
        if station_count == 0:
            # Database is empty, seed it with data
            print("Database is empty, seeding with initial data...")
            db_init(seed_stations)
        else:
            # Database has data, just ensure schema is up to date
            print(f"Database has {station_count} stations, schema is ready")


def db_init(seed_stations: int = 10):
    """Seed the database according to the provided schema with fake data."""
    fake = Faker(locale="el_GR")
    create_schema()

    with _connect() as conn:
        cur = conn.cursor()

        # Disable foreign key constraints temporarily to clear tables in any order
        cur.execute("PRAGMA foreign_keys = OFF;")   

        # clear existing rows (order respects foreign key dependencies)
        cur.execute("DELETE FROM `SUPPLY`;")
        cur.execute("DELETE FROM `TRANSACTION`;")
        cur.execute("DELETE FROM `PUMP`;")
        cur.execute("DELETE FROM `FUEL`;")
        cur.execute("DELETE FROM `TANK`;")
        cur.execute("DELETE FROM `EMPLOYEE`;")
        cur.execute("DELETE FROM `CUSTOMER`;")
        cur.execute("DELETE FROM `PRODUCT_PRICE`;")
        cur.execute("DELETE FROM `STATION_PRODUCT`;")
        cur.execute("DELETE FROM `PRODUCT`;")
        cur.execute("DELETE FROM `STATION`;")
        cur.execute("DELETE FROM `POINT_SYSTEM`;")
        cur.execute("DELETE FROM `INCLUSION`;")
        cur.execute("DELETE FROM `SWITCH`;")

        # Re-enable foreign key constraints
        cur.execute("PRAGMA foreign_keys = ON;")

        # PRODUCTS - 8 fuels + 50 store items
        fuel_id_list = []
        fuel_count = 8 
        store_items_count = 50
        for pid in range(fuel_count): #pid: product_id
            prod_type = "fuel"
            fuel_id_list.append(pid + 1)
            cur.execute(
                "INSERT INTO PRODUCT(product_id, prod_type) VALUES (?, ?)",
                (pid + 1, prod_type),
            )

        for pid in range(store_items_count): #pid: product_id
            prod_type = "store_items"
            cur.execute(
                "INSERT INTO PRODUCT(product_id, prod_type) VALUES (?, ?)",
                (pid + fuel_count + 1, prod_type),
            )

        # FUEL
        fuel_dict = generate_fuels_dict()
        fuel_points_per_liter = []
        for ft, (price_per_liter, points_per_liter) in fuel_dict.items():
            fuel_points_per_liter.append(points_per_liter)
        fuel_info = zip(fuel_id_list, fuel_dict.keys(), fuel_points_per_liter) #[(fuel_id, fuel_type, points_per_liter), ...]
        for fid, ft, points_per_liter in fuel_info:
            for_prod_id = fid
            cur.execute(
                "INSERT INTO FUEL(prod_id, fuel_type, points_per_liter, for_prod_id) VALUES (?, ?, ?, ?)",
                (fid, ft, points_per_liter, for_prod_id),
            )

        # STATIONS
        for sid in range(1, seed_stations + 1):
            name = fake.company()
            email = fake.company_email()
            phone = _digits_only(fake.phone_number())
            location = fake.address().replace("\n", ", ")
            automated = True if random.random() < 0.3 else False # 30% chance to be automated
            has_store = True if (not automated) and (random.random() < 0.8) else False # non-automated stations have 80% chance to have store
            cur.execute(
                "INSERT INTO STATION(station_id, location, name, phone, email, automated, has_store) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, location, name, phone, email, automated, has_store),
            )

        # TANKS (ΤΑΝΚ) : 4-7 tanks per station

        #FuelSave Unleaded 95: 1-2 25k liters / V-Power 98: 1 20k liters / V-Power Racing 100: 0-1 20k liters / FuelSave Diesel: 1-2 30k liters / VPower Diesel: 0-1 25k liters / Autogas: 0-1 10k liters / Heating Oil: 0-1 15k liters

        u95_capacity = 25000
        u98_capacity = 20000
        u100_capacity = 20000
        diesel_capacity = 30000
        diesel_vp_capacity = 25000
        heating_oil_capacity = 15000
        autogas_capacity = 10000

        tank_id_holder = 0 # saves tank id across stations (station 1 - > tank_num = 5, station 2 -> tank_num = 4, then tank_id for station 2 starts from 6, tank_id_holder = 6)
        pump_id_holder = 0
        fuel_id_holder = 0
        prod_id_holder = 0
        product_price_id = 0

        for_station = 0

        #fuel_count = len(fuel_types) #number of fuel types
        tank_id = 0
        pump_id = 0

        for _ in range(seed_stations):  #max 7 tanks per station
            tanks_dict = generate_tanks_dict()
            tan_num = sum(v[0] for v in tanks_dict.values())  #total number of tanks for the station
            for_station += 1
            tank_id_list_station = [i for i in range(tank_id_holder + 1, tank_id_holder + tan_num + 1)] #per station

            for_fuel_id_list = []
            capacity_holder = []
            price_per_liter_holder = []
            points_per_liter_holder = []
            fuel_prices_for_station = {}  # {key: fuel_id, value: price_per_liter}
            tank_id_holder += tan_num
            autogas_count = tanks_dict["Autogas"][0] # number of autogas tanks for the station
            u95_count = tanks_dict["FuelSave Unleaded 95"][0]
            u98_count = tanks_dict["V-Power 98"][0]   #always 1
            u100_count = tanks_dict["V-Power Racing"][0] 
            diesel_count = tanks_dict["FuelSave Diesel"][0]
            diesel_vp_count = tanks_dict["V-Power Diesel"][0] #always 1
            heating_oil_count = tanks_dict["Heating Oil"][0]

            for i in range(u95_count):
                capacity_holder.append(u95_capacity) # capacity for each tank with u95 fuel 
                for_fuel_id_list.append(1)  # fuel_id for Unleaded 95 is 1
                price = tanks_dict["FuelSave Unleaded 95"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["FuelSave Unleaded 95"][1][1])
                fuel_prices_for_station[1] = price  # Store price for this fuel_id

            # always 1 tank of u98
            capacity_holder.append(u98_capacity)
            for_fuel_id_list.append(2)  # fuel_id for V-Power 98 is 2
            price = tanks_dict["V-Power 98"][1][0]
            price_per_liter_holder.append(price)
            points_per_liter_holder.append(tanks_dict["V-Power 98"][1][1])
            fuel_prices_for_station[2] = price

            for i in range(u100_count):           
                capacity_holder.append(u100_capacity)
                for_fuel_id_list.append(3)  # fuel_id for V-Power Racing is 3
                price = tanks_dict["V-Power Racing"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["V-Power Racing"][1][1])
                fuel_prices_for_station[3] = price

            for i in range(diesel_count):
                capacity_holder.append(diesel_capacity)
                for_fuel_id_list.append(4)  # fuel_id for FuelSave Diesel is 4
                price = tanks_dict["FuelSave Diesel"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["FuelSave Diesel"][1][1])
                fuel_prices_for_station[4] = price

            for i in range(diesel_vp_count):
                capacity_holder.append(diesel_vp_capacity)
                for_fuel_id_list.append(5)  # fuel_id for V-Power Diesel is 5
                price = tanks_dict["V-Power Diesel"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["V-Power Diesel"][1][1])
                fuel_prices_for_station[5] = price

            for i in range(heating_oil_count):
                capacity_holder.append(heating_oil_capacity)
                for_fuel_id_list.append(6)  # fuel_id for Heating Oil is 6
                price = tanks_dict["Heating Oil"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["Heating Oil"][1][1])
                fuel_prices_for_station[6] = price

            for i in range(autogas_count):
                capacity_holder.append(autogas_capacity)
                for_fuel_id_list.append(7)  # fuel_id for Autogas is 7
                price = tanks_dict["Autogas"][1][0]
                price_per_liter_holder.append(price)
                points_per_liter_holder.append(tanks_dict["Autogas"][1][1])
                fuel_prices_for_station[7] = price                 

            last_fill_up = fake.date_between(start_date='-1y', end_date='today').isoformat()

        # PUMPS 
        # u95 1-2, u98 1, u100 0-1, diesel 1-2, vp_diesel: 1, autogas: 0-1, heating oil 0-1 -> total 4-9 pumps per station so it depends on the number of tanks of each station
            pump_id = 0
            for_tank_id = 0
            pump_id_list_station = [i for i in range(pump_id_holder + 1, pump_id_holder + tan_num + 1)] #per station
            pump_id_holder += tan_num
            pump_number_station = [i for i in range(1, tan_num + 1)]
            pump_active_station = [random.random() > 0.1 for i in range(tan_num)] # 90% chance to be active, random.random() > 0.1 -> True 90% of the time
            
            for i in range(tan_num):
                tank_id = tank_id_list_station[i]
                capacity = capacity_holder[i]
                for_fuel_id = for_fuel_id_list[i]
                current_quantity = fake.random_int(min=0, max=capacity)
                # Sample minimum operational fuel level ~ N(200, 30^2), clamped to [0, capacity], as integer
                min_fuel_quantity = random.gauss(200, 30)
                min_fuel_quantity = int(round(max(0.0, min(float(capacity), float(min_fuel_quantity)))))

                pump_id = pump_id_list_station[i]
                is_active = pump_active_station[i]
                pump_number = pump_number_station[i]
                for_tank_id = tank_id

        # -------------------INSERT TANKS AND PUMPS

                cur.execute(
                    "INSERT INTO `TANK`(tank_id, last_fill_up, capacity, current_quantity, min_fuel_quantity, for_station_id, for_fuel_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tank_id, last_fill_up, capacity, current_quantity, min_fuel_quantity, for_station, for_fuel_id),
                )
                cur.execute(
                    "INSERT INTO PUMP(pump_id, is_active, pump_number, for_tank_id) VALUES (?, ?, ?, ?)",
                    (pump_id, is_active, pump_number, for_tank_id),
                )

        #------------------- INSERT PRODUCT_PRICE entries for this station's fuels
            for fuel_id, price in fuel_prices_for_station.items():
                product_price_id += 1
                cur.execute(
                    "INSERT INTO PRODUCT_PRICE(prod_id, price, for_station_id, for_fuel_id) VALUES (?, ?, ?, ?)",
                    (product_price_id, price, for_station, fuel_id),
                )


        # EMPLOYEES : 1-2 per station if is non automated | 0 if is automated
        emp_id = 0
        for sid in range(1, seed_stations + 1): # for each station
            # read automated flag from the STATION row we previously inserted
            cur.execute("SELECT automated FROM STATION WHERE station_id = ?;", (sid,))
            row_automated = cur.fetchone()
            is_automated = row_automated[0] if row_automated else False
            emp_num = 0 if is_automated else random.choice([1, 2])
            for i in range(emp_num): # for each employee
                emp_id += 1
                fname = fake.first_name()
                lname = fake.last_name()
                ssn = _digits_only(fake.ssn()) or fake.random_int(min=100000000, max=999999999)
                salary = fake.random_int(min=9600, max=12000)
                email = fake.email()
                for_station_id = sid        
                cur.execute(
                    "INSERT INTO EMPLOYEE(emp_id, fname, lname, ssn, for_station_id, salary, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (emp_id, fname, lname, ssn, for_station_id, salary, email),
                )
        conn.commit()


def generate_fuels_dict():
        fake = Faker(locale="el_GR")
        #low,high for price per liter/ points per liter (low,high,points) -- points are independent from fuel price per liter
        fuel_types = ["V-Power Racing, FuelSave Unleaded 95","FuelSave Diesel","Autogas", "V-Power 98", "V-Power Diesel", "Heating Oil","Household LPG"]
        fuel_type_price_per_liter = {
            "FuelSave Unleaded 95": (1.60, 1.85, 1),
            "V-Power 98":  (1.75, 2.05, 2),
            "V-Power Racing":   (1.85, 2.25, 4),

            "FuelSave Diesel":     (1.45, 1.70, 1),
            "V-Power Diesel":      (1.55, 1.85, 2),

            "Autogas":             (0.85, 1.05, 1),
            "Heating Oil":         (1.20, 1.45, 0.5),
            "Household LPG":       (0.90, 1.15, 0.5) #πωλείται σε φιάλες / δεν μπαίνει σε αντλία 
        }
        fuels_dict = {}   
        for fid, (ft, (low, high, points)) in enumerate(fuel_type_price_per_liter.items(), start=1): #fid: fuel_id->1, 2, 3, ...
            price_per_liter = round(fake.random.uniform(low, high), 2) # 2 decimal places
            points_per_liter = points
            fuels_dict[ft] = [price_per_liter, points_per_liter]  #for each fuel category, needed for each station
        return fuels_dict

# Cache for store products to ensure consistent pricing
_store_products_cache = None

def generate_store_products_dict():
        '''Generate store products dict once and cache it'''
        global _store_products_cache
        
        # Return cached version if already generated
        if _store_products_cache is not None:
            return _store_products_cache
        
        #product id, product type, cost, points total(based on cost)

        fake = Faker(locale="el_GR")

        store_items = {
            # Snacks & Chips (10 items)
            "Κριτσίνια": [2.5, 3.5, 20],
            "Πατατάκια": [2.8, 3.8, 20],
            "Κρακεράκια": [2.2, 3.2, 20],
            "Καλαμάκια": [1.8, 2.8, 20],
            "Ξηροί Καρποί": [3.5, 4.9, 20],
            "Σοκολάτα": [1.2, 2.0, 20],
            "Καραμέλες": [2.0, 3.0, 20],
            "Ενεργειακή Μπάρα": [2.5, 3.5, 20],
            "Μπάρα Δημητριακών": [1.8, 2.5, 20],
            "Σοκολατάκια": [1.5, 2.3, 20],
            
            # Beverages (10 items)
            "Νερό Εμφιαλωμένο": [0.5, 0.5, 20],
            "Αναψυκτικό": [1.8, 2.8, 20],
            "Ενεργειακό Ποτό": [2.5, 3.5, 20],
            "Λεμονάδα": [1.0, 1.8, 20],
            "Τσάι ": [1.5, 2.5, 20],
            "Χυμός Φυσικός": [1.2, 2.0, 20],
            "Καφές": [2.0, 3.0, 20],
            "Αναψυκτικό Χωρίς Ζάχαρη": [1.5, 2.5, 20],
            "Γάλα": [2.2, 3.2, 20],
            "Ποτό Βιταμινών": [2.0, 3.0, 20],
            
            # Car Care (10 items)
            "Λάδι Κινητήρα": [12.0, 18.0, 0],
            "Υγρό Υαλοκαθαριστήρων": [3.5, 5.5, 0],
            "Αντλία Ελαστικού": [15.0, 22.0, 0],
            "Αρωματικό Αυτοκινήτου": [2.5, 4.0, 0],
            "Πανί Καθαρισμού": [3.0, 5.0, 0],
            "Λάστιχα Υαλοκαθαριστήρων": [12.0, 18.0, 0],
            "Ξύστρα Πάγου": [4.0, 6.5, 0],
            "Βάση Κινητού": [8.0, 12.0, 0],
            "Φορτιστής USB": [6.0, 10.0, 0],
            "Καλώδια Μπαταρίας": [15.0, 23.0, 0],
            
            # Tobacco & Vaping (5 items)
            "Τσιγάρα": [5.0, 8.0, 0],
            "Πούρο": [4.0, 7.0, 0],
            "Αναπτήρας": [1.0, 2.0, 0],
            "Υγρό Κάπνισμα": [8.0, 12.0, 0],
            "Χαρτάκια": [1.5, 2.5, 0],
            
            # Personal Care (5 items)
            "Αντισηπτικό Χεριών": [2.0, 3.5, 0],
            "Υγρά Μαντηλάκια": [2.5, 4.0, 0],
            "Παυσίπονο": [4.0, 6.5, 0],
            "Γυαλιά Ηλίου": [8.0, 14.0, 0],
            "Βάλσαμο Χειλιών": [1.5, 2.8, 0],
            
            # Convenience Items (10 items)
            "Καλώδιο Φόρτισης": [7.0, 12.0, 0],
            "Ακουστικά": [10.0, 16.0, 0],
            "Ομπρέλα": [6.0, 10.0, 0],
            "Φακός": [8.0, 13.0, 0],
            "Μπαταρίες ΑΑ": [4.0, 6.5, 0],
            "Θερμό": [7.0, 11.0, 0],
            "Αντιηλιακό": [6.0, 10.0, 0],
            "Κιτ Πρώτων Βοηθειών": [12.0, 18.0, 0],
            "Κολλητική Ταινία": [5.0, 8.0, 0],
            "Λάστιχα Ασφάλειας": [4.0, 7.0, 0]
        }
        store_products_dict = {}   
        for fid, (ft, (low, high, points)) in enumerate(store_items.items(), start=1): #fid: store_prod_id->1, 2, 3, ...
            price = round(fake.random.uniform(low, high), 2) # 2 decimal places
            store_products_dict[ft] = [price, points]  #for each fuel category, needed for each station
        
        # Cache the generated products
        _store_products_cache = store_products_dict
        return store_products_dict

def generate_tanks_dict():
    tanks = {
        "FuelSave Unleaded 95": 1, #mutable: 1 or 2
        "V-Power 98": 1,       
        "V-Power Racing": 0, #mutable: 0 or 1   
        "FuelSave Diesel": 1, #mutable: 1 or 2 
        "V-Power Diesel": 1,        
        "Heating Oil": 0,  #mutable: 0 or 1  
        "Autogas": 0 #mutable: 0 or 1
    }

    # Extra tank for U95 (0 or 1)
    tanks["FuelSave Unleaded 95"] += random.choice([0, 1])

    # Extra tank for Diesel (0 or 1)
    tanks["FuelSave Diesel"] += random.choice([0, 1])

    # V-Power Racing (100) tand (0 or 1)
    tanks["V-Power Racing"] += random.choice([0, 1])

    # Heating oil tank (0 or 1)
    tanks["Heating Oil"] = random.choice([0, 1])

    # Autogas tank (0 or 1)
    tanks["Autogas"] += random.choice([0, 1])

    #price per liter and points per liter 
    fuels_dict = generate_fuels_dict()
    tanks["FuelSave Unleaded 95"] = [tanks["FuelSave Unleaded 95"], fuels_dict["FuelSave Unleaded 95"]] #[number of tanks, [price per liter, points per liter]]
    tanks["V-Power 98"] = [tanks["V-Power 98"], fuels_dict["V-Power 98"]]
    tanks["V-Power Racing"] = [tanks["V-Power Racing"], fuels_dict["V-Power Racing"]]
    tanks["FuelSave Diesel"] = [tanks["FuelSave Diesel"], fuels_dict["FuelSave Diesel"]]
    tanks["V-Power Diesel"] = [tanks["V-Power Diesel"], fuels_dict["V-Power Diesel"]]
    tanks["Heating Oil"] = [tanks["Heating Oil"], fuels_dict["Heating Oil"]]
    tanks["Autogas"] = [tanks["Autogas"], fuels_dict["Autogas"]]

    return tanks

def get_stations():
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM STATION;")
        rows = cursor.fetchall()

        stations = []
        for row in rows:
            station_id = row[0]
            location = row[1]
            name = row[2]
            phone = row[3]
            email = row[4]
            automated = row[5]
            has_store = row[6]
            stations.append([station_id, location, name, phone, email, automated, has_store])

        return stations

def get_admin_station_info(station_id):
    with _connect() as conn:
        cursor = conn.cursor()
        #select station info based on station_id
        cursor.execute("SELECT * FROM STATION WHERE station_id = ?;", (station_id,))
        row = cursor.fetchone()

        if row:
            station_info = {
                "station_id": row[0],
                "location": row[1],
                "name": row[2],
                "phone": row[3],
                "email": row[4],
                "automated": row[5],
                "has_store": row[6]
            }
            
            # Get tanks for the station
            cursor.execute("SELECT * FROM TANK WHERE for_station_id = ?;", (station_id,))
            tanks = cursor.fetchall()
            # Column order in TANK: 0 tank_id, 1 last_fill_up, 2 capacity, 3 current_quantity, 4 min_fuel_quantity, 5 for_station_id, 6 for_fuel_id
            for_fuel_id_list = [t[6] for t in tanks]
            fuel_type_list = [get_fuel_name(f_id) for f_id in for_fuel_id_list]
            station_info["tanks"] = [
                {
                    "tank_id": t[0],
                    "last_fill_up": t[1],
                    "capacity": t[2],
                    "current_quantity": t[3],
                    "min_fuel_quantity": t[4],
                    "for_station_id": t[5],
                    "fuel_type": fuel_type_list[i],
                }
                for i, t in enumerate(tanks)
            ]
            
            # Get pumps for the tanks of the station
            tank_ids = [t[0] for t in tanks]
            if tank_ids:
                cursor.execute("SELECT * FROM PUMP WHERE for_tank_id IN ({})".format(','.join('?' * len(tank_ids))), tank_ids)
                pumps = cursor.fetchall()
                station_info["pumps"] = [{"pump_id": p[0], "is_active": p[1], "pump_number": p[2], "for_tank_id": p[3]} for p in pumps]
            else:
                station_info["pumps"] = []
            
            # Get fuels for the station
            fuel_ids = list(set(t[6] for t in tanks))
            if fuel_ids:
                placeholders = ','.join('?' * len(fuel_ids)) # "?, ?, ?..."
                sql = f"""
                    SELECT f.prod_id, f.fuel_type, f.points_per_liter, f.for_prod_id, pp.price
                    FROM FUEL as f
                    JOIN PRODUCT_PRICE as pp ON pp.for_fuel_id = f.prod_id AND pp.for_station_id = ?
                    WHERE f.prod_id IN ({placeholders})
                """
                params = [station_id] + fuel_ids # list concatenation
                cursor.execute(sql, params)
                fuels = cursor.fetchall()
                station_info["fuels"] = [{"prod_id": f[0], "fuel_type": f[1], "price_per_liter": f[4], "points_per_liter": f[2], "for_prod_id": f[3]} for f in fuels]
            else:
                station_info["fuels"] = []

            #Get employees for the station
            cursor.execute("SELECT * FROM EMPLOYEE WHERE for_station_id = ?;", (station_id,))
            employees = cursor.fetchall()
            station_info["employees"] = [{"emp_id": e[0], "fname": e[1], "lname": e[2], "ssn": e[3], "for_station_id": e[4], "salary": e[5], "email": e[6]} for e in employees]
            
            return station_info
        
        else:
            return None

def get_fuel_name(fuel_id):
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT fuel_type FROM FUEL WHERE prod_id = ?;", (fuel_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
def get_fuel_price(fuel_id):
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price_per_liter FROM FUEL WHERE prod_id = ?;", (fuel_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
def station_name(station_id):
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM STATION WHERE station_id = ?;", (station_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def insert_transaction(trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id):
    '''Insert a transaction into the database. for_cust_id can be None for anonymous purchases.
    for_station_id is required and links the transaction to the station.'''
    with _connect() as conn:
        cursor = conn.cursor()   
        cursor.execute("INSERT INTO `TRANSACTION` (trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id) VALUES (?, ?, ?, ?, ?, ?)",
            (trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id))
        conn.commit()
        return cursor.lastrowid # inserting transaction, return its id

def get_all_transactions():
    '''Retrieve all transactions from the database with station and customer information'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT t.trans_id, t.trans_date, t.amount_of_money, t.total_points, t.for_cust_id, t.payment_method, t.for_station_id, s.name, c.fname, c.lname "
            "FROM `TRANSACTION` t "
            "LEFT JOIN `STATION` s ON t.for_station_id = s.station_id "
            "LEFT JOIN `CUSTOMER` c ON t.for_cust_id = c.customer_id "
            "ORDER BY t.trans_date DESC"
        )
        rows = cursor.fetchall()
        return rows

def insert_customer(fname=None, lname=None, address=None, phone_number=None, email=None, tax_id=None, payment_type=None, delivery_address=None, fuel_card=None, company_name=None, card_number=None):
    '''Insert a new customer and create a corresponding points record with card number'''
    with _connect() as conn:
        cursor = conn.cursor()
        try:
            # Convert and provide defaults for NOT NULL fields
            # Phone number: extract digits and convert to int, default to 0
            phone_int = _digits_only(phone_number) if phone_number else 0
            
            # Tax ID: extract digits and convert to int, default to 0
            tax_id_int = _digits_only(tax_id) if tax_id else 0
            
            # Fuel card: convert to int, default to 0
            fuel_card_int = _digits_only(fuel_card) if fuel_card else 0
            
            # Provide defaults for TEXT NOT NULL fields
            fname = fname if fname else ""
            lname = lname if lname else ""
            address = address if address else ""
            email = email if email else ""
            payment_type = payment_type if payment_type else ""
            delivery_address = delivery_address if delivery_address else ""
            company_name = company_name if company_name else ""
            
            # Insert customer with converted fields
            cursor.execute(
                "INSERT INTO `CUSTOMER` (fname, lname, address, phone_number, email, tax_id, payment_type, anonymous, delivery_address, fuel_card, company_name, for_system_points_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (fname, lname, address, phone_int, email, tax_id_int, payment_type, 0, delivery_address, fuel_card_int, company_name)
            )
            customer_id = cursor.lastrowid
            
            # Create corresponding points record with card number
            cursor.execute(
                "INSERT INTO `POINT_SYSTEM` (customer_id, points, card_number) VALUES (?, ?, ?)",
                (customer_id, 0, card_number if card_number else "")
            )
            
            # Update customer's for_system_points_id
            cursor.execute(
                "UPDATE `CUSTOMER` SET for_system_points_id = ? WHERE customer_id = ?",
                (customer_id, customer_id)
            )
            
            conn.commit()
            return customer_id
        except Exception as e:
            import traceback
            print(f"Error inserting customer: {e}")
            traceback.print_exc()
            return None

def update_customer_points(customer_id, points_to_add):
    '''Update customer points when they complete a transaction with card'''
    with _connect() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE `POINT_SYSTEM` SET points = points + ? WHERE customer_id = ?",(points_to_add, customer_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating customer points: {e}")
            return False

def get_customer_by_id(customer_id):
    '''Get customer information by customer_id'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_id, fname, lname, address, phone_number, email, tax_id, payment_type, delivery_address, fuel_card, company_name FROM `CUSTOMER` WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'customer_id': row[0],
                'fname': row[1],
                'lname': row[2],
                'address': row[3],
                'phone_number': row[4],
                'email': row[5],
                'tax_id': row[6],
                'payment_type': row[7],
                'delivery_address': row[8],
                'fuel_card': row[9],
                'company_name': row[10]
            }
        return None

def get_customer_name(customer_id):
    '''Get customer full name by customer_id'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT fname, lname FROM `CUSTOMER` WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        if row:
            fname = row[0] if row[0] else ""
            lname = row[1] if row[1] else ""
            return f"{fname} {lname}".strip()
        return "Unknown"

def get_all_points_customers():
    '''Get all customers with their points and card numbers from POINT_SYSTEM'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ps.customer_id, c.fname, c.lname, ps.points, ps.card_number FROM `POINT_SYSTEM` ps "
            "LEFT JOIN `CUSTOMER` c ON ps.customer_id = c.customer_id "
            "ORDER BY ps.customer_id"
        )
        rows = cursor.fetchall()
        return rows

def get_customer_by_card_number(card_number):
    '''Get customer by their card number from POINT_SYSTEM'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ps.customer_id, c.fname, c.lname, ps.points, ps.card_number FROM `POINT_SYSTEM` ps "
            "LEFT JOIN `CUSTOMER` c ON ps.customer_id = c.customer_id "
            "WHERE ps.card_number = ?",
            (card_number,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'customer_id': row[0],
                'fname': row[1],
                'lname': row[2],
                'points': row[3],
                'card_number': row[4]
            }
        return None

def deduct_fuel_from_tank(tank_id, liters_purchased):
    '''Deduct purchased liters from the specified tank.'''
    if liters_purchased is None or liters_purchased < 0:
        return False

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT current_quantity, min_fuel_quantity FROM TANK WHERE tank_id = ?",(tank_id,))
        row = cursor.fetchone()
        if not row:
            return False

        current_qty, min_qty = row
        min_qty = min_qty or 0

        # Ensure there is enough fuel to stay above the minimum threshold
        if current_qty - liters_purchased < min_qty:
            return False

        new_quantity = round(current_qty - liters_purchased, 2)
        cursor.execute("UPDATE TANK SET current_quantity = ? WHERE tank_id = ?",(new_quantity, tank_id))
        conn.commit()
        return True

def get_customer_details(customer_id):
    '''Get detailed customer information including points data'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT c.customer_id, c.fname, c.lname, c.address, c.phone_number, c.email, "
            "c.tax_id, c.payment_type, c.anonymous, c.delivery_address, c.fuel_card, c.company_name, "
            "ps.points, ps.card_number "
            "FROM `CUSTOMER` c "
            "LEFT JOIN `POINT_SYSTEM` ps ON c.customer_id = ps.customer_id "
            "WHERE c.customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'customer_id': row[0],
                'fname': row[1],
                'lname': row[2],
                'address': row[3],
                'phone_number': row[4],
                'email': row[5],
                'tax_id': row[6],
                'payment_type': row[7],
                'anonymous': row[8],
                'delivery_address': row[9],
                'fuel_card': row[10],
                'company_name': row[11],
                'points': row[12],
                'card_number': row[13]
            }
        return None

def redeem_points(customer_id, points_to_redeem):
    '''Redeem points for a customer and return euros discount'''
    with _connect() as conn:
        cursor = conn.cursor()
        # Calculate euros from points (250 points = 1 euro)
        euros_discount = points_to_redeem // 250.0 # floored
        
        # Update POINT_SYSTEM to subtract redeemed points
        cursor.execute("UPDATE POINT_SYSTEM SET points = points - ? WHERE customer_id = ?",(points_to_redeem, customer_id))
        conn.commit()
        
        return euros_discount

if __name__ == '__main__':
    create_schema()
    db_init(seed_stations=10)
    #print_counts()