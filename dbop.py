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
    `fname` TEXT,
    `lname` TEXT,
    `address` TEXT,
    `phone_number` INTEGER NOT NULL,
    `email` TEXT,
    `tax_id` INTEGER NOT NULL,
    `delivery_address` TEXT,
    `company_name` TEXT,
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
DROP TABLE IF EXISTS `STATION_PRODUCT_INFO`;
CREATE TABLE `STATION_PRODUCT_INFO` (
    `prod_id` integer primary key NOT NULL UNIQUE,
    `price` REAL NOT NULL,
    `stock` INTEGER,
    `for_station_id` INTEGER NOT NULL,
    `for_prod_id` INTEGER NOT NULL,
    FOREIGN KEY(`for_station_id`) REFERENCES `STATION`(`station_id`) ON DELETE CASCADE,
    FOREIGN KEY(`for_prod_id`) REFERENCES `PRODUCT`(`product_id`) ON DELETE CASCADE
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
    `name` TEXT NOT NULL,
    `points` INTEGER NOT NULL,
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
    `switch_id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `for_transaction_id` integer NOT NULL,
    `for_point_system_id` integer NOT NULL,
    `date` DATETIME NOT NULL,
    `points_added` INTEGER DEFAULT 0,
    `points_deducted` INTEGER DEFAULT 0,
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


def _digits_or_none_only(s):
    '''Extract digits from a string and return as integer. If no digits, return 0.'''
    if s is None:
        return 0
    digits = re.sub(r"\D", "", str(s)) # remove non-digit characters, replace \D (non digit) characters with ""
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


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
        cur.execute("DELETE FROM `STATION_PRODUCT_INFO`;")
        cur.execute("DELETE FROM `STATION_PRODUCT`;")
        cur.execute("DELETE FROM `PRODUCT`;")
        cur.execute("DELETE FROM `STATION`;")
        cur.execute("DELETE FROM `POINT_SYSTEM`;")
        cur.execute("DELETE FROM `INCLUSION`;")
        cur.execute("DELETE FROM `SWITCH`;")

        # Re-enable foreign key constraints
        cur.execute("PRAGMA foreign_keys = ON;")

        # FUELS 
        # Insert fuel products and fuel data
        fuel_dict = generate_fuels_dict() # {'Fuel Type': (price_per_liter, points_per_liter), ...}
        fuel_id_list = [] # to keep track of fuel product IDs
        
        for pid, (fuel_type, (price_per_liter, points_per_liter)) in enumerate(fuel_dict.items(), start=1):
            fuel_id_list.append(pid)
            # Insert into PRODUCT
            cur.execute("INSERT INTO PRODUCT(product_id, prod_type) VALUES (?, ?)", (pid, "fuel"))
            # Insert into FUEL
            cur.execute("INSERT INTO FUEL(prod_id, fuel_type, points_per_liter, for_prod_id) VALUES (?, ?, ?, ?)",(pid, fuel_type, points_per_liter, pid))

        # STORE ITEMS
        # Build store catalog and insert PRODUCT and STATION_PRODUCT entries
        store_catalog = generate_store_products_dict() # {category: {product_name: {price, points, stock}}}
        store_product_map = {}  # key: (category, name) -> {product_id, points}
        
        fuel_count = len(fuel_id_list)
        product_id = fuel_count  # Start store item IDs after fuels
        
        for category, products in store_catalog.items():
            for product_name, product_data in products.items():
                product_id += 1
                points = product_data['points']
                store_product_map[(category, product_name)] = {"product_id": product_id, "points": points} # store_product_map = {(category, name): {product_id, points}, ...}
                # Insert into PRODUCT
                cur.execute("INSERT INTO PRODUCT(product_id, prod_type) VALUES (?, ?)", (product_id, "store_items"))
                # Insert into STATION_PRODUCT
                cur.execute("INSERT INTO STATION_PRODUCT(prod_id, prod_type, name, points, for_prod_id) VALUES (?, ?, ?, ?, ?)",(product_id, category, product_name, points, product_id))

        # STATIONS
        for sid in range(1, seed_stations + 1):
            name = fake.company()
            email = fake.company_email()
            phone = _digits_or_none_only(fake.phone_number())
            location = fake.address().replace("\n", ", ")
            automated = True if random.random() < 0.3 else False # 30% chance to be automated
            has_store = True if (not automated) and (random.random() < 0.8) else False # non-automated stations have 80% chance to have store
            cur.execute(
                "INSERT INTO STATION(station_id, location, name, phone, email, automated, has_store) VALUES (?, ?, ?, ?, ?, ?, ?)",(sid, location, name, phone, email, automated, has_store),)

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

        for_station = 0
        for_prod_id = 0

        #fuel_count = len(fuel_types) #number of fuel types
        tank_id = 0
        pump_id = 0
        station_product_info_id = 0

        for _ in range(seed_stations):  #max 7 tanks per station
            tanks_dict = generate_tanks_dict() # {'Fuel Type': (count, (price_per_liter, points_per_liter)), ...}, count: number of tanks for that fuel type
            tan_num = sum(v[0] for v in tanks_dict.values())  #total number of tanks for the station
            for_station += 1
            tank_id_list_station = [i for i in range(tank_id_holder + 1, tank_id_holder + tan_num + 1)] #per station

            for_fuel_id_list = [] # list of fuel_ids corresponding to each tank, use for_prod_id in TANK insert
            capacity_holder = [] # list of capacities corresponding to each tank
            tank_id_holder += tan_num
            
            # Get tank counts
            autogas_count = tanks_dict["Autogas"][0]
            u95_count = tanks_dict["FuelSave Unleaded 95"][0]
            u98_count = tanks_dict["V-Power 98"][0]
            u100_count = tanks_dict["V-Power Racing"][0] 
            diesel_count = tanks_dict["FuelSave Diesel"][0]
            diesel_vp_count = tanks_dict["V-Power Diesel"][0]
            heating_oil_count = tanks_dict["Heating Oil"][0]
            
            # Extract prices and points for each fuel type
            u95_price = tanks_dict["FuelSave Unleaded 95"][1][0]
            u95_points = tanks_dict["FuelSave Unleaded 95"][1][1]
            u98_price = tanks_dict["V-Power 98"][1][0]
            u98_points = tanks_dict["V-Power 98"][1][1]
            u100_price = tanks_dict["V-Power Racing"][1][0]
            u100_points = tanks_dict["V-Power Racing"][1][1]
            diesel_price = tanks_dict["FuelSave Diesel"][1][0]
            diesel_points = tanks_dict["FuelSave Diesel"][1][1]
            diesel_vp_price = tanks_dict["V-Power Diesel"][1][0]
            diesel_vp_points = tanks_dict["V-Power Diesel"][1][1]
            heating_oil_price = tanks_dict["Heating Oil"][1][0]
            heating_oil_points = tanks_dict["Heating Oil"][1][1]
            autogas_price = tanks_dict["Autogas"][1][0]
            autogas_points = tanks_dict["Autogas"][1][1]
            
            # Build fuel prices dict for this station (fuel_id -> price)
            fuel_prices_for_station = {
                1: u95_price,
                2: u98_price,
                3: u100_price,
                4: diesel_price,
                5: diesel_vp_price,
                6: heating_oil_price,
                7: autogas_price
            }

            # Build tank lists
            for i in range(u95_count):
                capacity_holder.append(u95_capacity) # 
                for_fuel_id_list.append(1)


            # Always 1 tank of u98
            capacity_holder.append(u98_capacity)
            for_fuel_id_list.append(2)


            for i in range(u100_count):
                capacity_holder.append(u100_capacity)
                for_fuel_id_list.append(3)


            for i in range(diesel_count):
                capacity_holder.append(diesel_capacity)
                for_fuel_id_list.append(4)
 

            for i in range(diesel_vp_count):
                capacity_holder.append(diesel_vp_capacity)
                for_fuel_id_list.append(5)


            for i in range(heating_oil_count):
                capacity_holder.append(heating_oil_capacity)
                for_fuel_id_list.append(6)
   

            for i in range(autogas_count):
                capacity_holder.append(autogas_capacity)
                for_fuel_id_list.append(7)

            # LAST FILL UP DATE - random date within last year               

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
                # Sample minimum operational fuel level ~ N(200, 30^2), bounded to [0, capacity], as integer
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

            #------------------- INSERT STATION_PRODUCT_INFO entries for this station's fuels (stock = NULL for fuels)
            for fuel_id, price in fuel_prices_for_station.items(): # fuel_prices_for_station = {fuel_id -> price}
                station_product_info_id += 1
                cur.execute("INSERT INTO STATION_PRODUCT_INFO(prod_id, price, stock, for_station_id, for_prod_id) VALUES (?, ?, NULL, ?, ?)",(station_product_info_id, price, for_station, fuel_id),)

            #------------------- INSERT STATION_PRODUCT_INFO entries for this station's store products (if has_store)
            # Check if this station has a store
            cur.execute("SELECT has_store FROM STATION WHERE station_id = ?", (for_station,))
            row_has_store = cur.fetchone()
            has_store = row_has_store[0] if row_has_store else False
            
            if has_store:
                # Generate store products for this station
                store_products = generate_store_products_dict() # {category: {product_name: {price, points, stock}}}, i want different prices and stock per station and that's the reason for re-calling the function
                
                # Insert each product into STATION_PRODUCT_INFO with stock
                for category, products in store_products.items():
                    for product_name, product_data in products.items():
                        station_product_info_id += 1 # continues from fuel station_product_info_id
                        price = product_data['price']
                        stock = product_data['stock']
                        product_info = store_product_map.get((category, product_name)) # get product_id from store_product_map to use as for_prod_id

                        cur.execute(
                            "INSERT INTO STATION_PRODUCT_INFO(prod_id, price, stock, for_station_id, for_prod_id) VALUES (?, ?, ?, ?, ?)",(station_product_info_id, price, stock, for_station, product_info["product_id"]),
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
                ssn = _digits_or_none_only(fake.ssn()) or fake.random_int(min=100000000, max=999999999) # afm 9 digits
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


def generate_store_products_dict():
    '''Generate store products dict '''
    
    #product id, product type, cost, points total(based on cost), number of items in stock
    min_items_snacks = 5
    max_items_snacks = 20

    min_items_beverages = 5
    max_items_beverages = 20    

    min_items_car_care = 3
    max_items_car_care = 15

    min_items_vaping = 2
    max_items_vaping = 10

    min_items_personal_care = 2
    max_items_personal_care = 10

    min_items_convenience = 5
    max_items_convenience = 20        

    fake = Faker(locale="el_GR")

    #store_items = {product_category: {product_name: [cost_low, cost_high, points_total, min_items, max_items]}}
    store_items = {
        "Snacks": {
            "Κριτσίνια": [2.5, 3.5, 20, min_items_snacks, max_items_snacks],
            "Πατατάκια": [2.8, 3.8, 20, min_items_snacks, max_items_snacks],
            "Κρακεράκια": [2.2, 3.2, 20, min_items_snacks, max_items_snacks],
            "Καλαμάκια": [1.8, 2.8, 20, min_items_snacks, max_items_snacks],
            "Ξηροί Καρποί": [3.5, 4.9, 20, min_items_snacks, max_items_snacks],
            "Σοκολάτα": [1.2, 2.0, 20, min_items_snacks, max_items_snacks],
            "Καραμέλες": [2.0, 3.0, 20, min_items_snacks, max_items_snacks],
            "Μπάρα Δημητριακών": [1.8, 2.5, 20, min_items_snacks, max_items_snacks],
            "Σοκολατάκια": [1.5, 2.3, 20, min_items_snacks, max_items_snacks]
        },
        "Beverages": {
            "Νερό Εμφιαλωμένο": [0.5, 0.5, 20, min_items_beverages, max_items_beverages],
            "Αναψυκτικό": [1.8, 2.8, 20, min_items_beverages, max_items_beverages],
            "Ενεργειακό Ποτό": [2.5, 3.5, 20, min_items_beverages, max_items_beverages],
            "Λεμονάδα": [1.0, 1.8, 20, min_items_beverages, max_items_beverages],
            "Τσάι ": [1.5, 2.5, 20, min_items_beverages, max_items_beverages],
            "Χυμός Φυσικός": [1.2, 2.0, 20, min_items_beverages, max_items_beverages],
            "Καφές": [2.0, 3.0, 20, min_items_beverages, max_items_beverages],
            "Αναψυκτικό Χωρίς Ζάχαρη": [1.5, 2.5, 20, min_items_beverages, max_items_beverages],
            "Γάλα": [2.2, 3.2, 20, min_items_beverages, max_items_beverages]
            
        },
        "Car Care": {
            "Λάδι Κινητήρα": [12.0, 18.0, 0, min_items_car_care, max_items_car_care],
            "Υγρό Υαλοκαθαριστήρων": [3.5, 5.5, 0, min_items_car_care, max_items_car_care],
            "Τρόμπα": [15.0, 22.0, 0, min_items_car_care, max_items_car_care],
            "Αρωματικό Αυτοκινήτου": [2.5, 4.0, 0, min_items_car_care, max_items_car_care],
            "Πανί Καθαρισμού": [3.0, 5.0, 0, min_items_car_care, max_items_car_care],
            "Λάστιχα Υαλοκαθαριστήρων": [12.0, 18.0, 0, min_items_car_care, max_items_car_care],
            "Ξύστρα Πάγου": [4.0, 6.5, 0, min_items_car_care, max_items_car_care],
            "Βάση Κινητού": [4.0, 12.0, 0, min_items_car_care, max_items_car_care],
            "Φορτιστής USB": [6.0, 10.0, 0, min_items_car_care, max_items_car_care],
            "Καλώδια Μπαταρίας": [15.0, 30.0, 0, min_items_car_care, max_items_car_care]
        },
        "Vaping": {
            "Τσιγάρα": [2.5, 8.0, 0, min_items_vaping, max_items_vaping],
            "Πούρο": [4.0, 7.0, 0, min_items_vaping, max_items_vaping],
            "Αναπτήρας": [1.0, 3.0, 0, min_items_vaping, max_items_vaping],
            "Καπνός": [7.0, 22.0, 0, min_items_vaping, max_items_vaping],
            "Χαρτάκια": [1.5, 2.5, 0, min_items_vaping, max_items_vaping]
        },
        "Personal Care": {
            "Αντισηπτικό Χεριών": [2.0, 3.5, 0, min_items_personal_care, max_items_personal_care],
            "Υγρά Μαντηλάκια": [2.5, 4.0, 0, min_items_personal_care, max_items_personal_care],
            "Παυσίπονο": [3.0, 5.0, 0, min_items_personal_care, max_items_personal_care],
            "Γυαλιά Ηλίου": [20.0, 40.0, 0, min_items_personal_care, max_items_personal_care]
        },
        "Convenience Items": {
            "Καλώδιο Φόρτισης": [7.0, 12.0, 0, min_items_convenience, max_items_convenience],
            "Ακουστικά": [10.0, 16.0, 0, min_items_convenience, max_items_convenience],
            "Ομπρέλα": [6.0, 10.0, 0, min_items_convenience, max_items_convenience],
            "Φακός": [8.0, 13.0, 0, min_items_convenience, max_items_convenience],
            "Μπαταρίες ΑΑ": [4.0, 6.5, 0, min_items_convenience, max_items_convenience],
            "Θερμό": [7.0, 15.0, 0, min_items_convenience, max_items_convenience],
            "Αντιηλιακό": [6.0, 10.0, 0, min_items_convenience, max_items_convenience],
            "Κιτ Πρώτων Βοηθειών": [12.0, 20.0, 0, min_items_convenience, max_items_convenience]
        },
        "LPG Fuel Cylinders": {
            "Φιάλη Υγραερίου 5kg": [25.0, 35.0, 0, 2, 10],
            "Φιάλη Υγραερίου 10kg": [35.0, 60.0, 0, 2, 10],
            "Φιάλη Υγραερίου 12kg": [50.0, 65.0, 0, 2, 10],
            "Φιάλη Υγραερίου 24kg": [90.0, 120.0, 0, 1, 5]
        }
    }
    
    store_products_dict = {} # {category: {product_name: {price, points, stock}, ...}}
    for category, products in store_items.items():
        store_products_dict[category] = {}
        for product_name, (low, high, points, min_stock, max_stock) in products.items():
            price = round(fake.random.uniform(low, high), 2)
            stock = random.randint(min_stock, max_stock)
            store_products_dict[category][product_name] = {"price": price, "points": points, "stock": stock}
    
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
                    JOIN STATION_PRODUCT_INFO as pp ON pp.for_prod_id = f.prod_id AND pp.for_station_id = ?
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


def get_store_products_for_station(station_id):
    '''Return store products for a station grouped by category.'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sp.prod_type, sp.name, sp.points, spi.price, spi.stock, spi.prod_id
            FROM STATION_PRODUCT_INFO AS spi
            JOIN PRODUCT AS p ON p.product_id = spi.for_prod_id
            JOIN STATION_PRODUCT AS sp ON sp.for_prod_id = p.product_id
            WHERE spi.for_station_id = ? AND p.prod_type = 'store_items'
            ORDER BY sp.prod_type, sp.name
            """,
            (station_id,),
        )
        rows = cursor.fetchall()

    products = {}
    for category, name, points, price, stock, prod_id in rows:
        products.setdefault(category, {})[name] = {
            "price": price,
            "points": points,
            "stock": stock,
            "prod_id": prod_id,
        }
    return products
    
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
        # left join for customer to include anonymous transactions
        cursor.execute(
            "SELECT t.trans_id, t.trans_date, t.amount_of_money, t.total_points, t.for_cust_id, t.payment_method, t.for_station_id, s.name, c.fname, c.lname "
            "FROM `TRANSACTION` t "
            "JOIN `STATION` s ON t.for_station_id = s.station_id "
            "LEFT JOIN `CUSTOMER` c ON t.for_cust_id = c.customer_id "
            "ORDER BY t.trans_date DESC"
        )
        rows = cursor.fetchall()
        return rows

def insert_customer(fname=None, lname=None, address=None, phone_number=None, email=None, tax_id=None, delivery_address=None, company_name=None, card_number=None):
    '''Insert a new customer and create a corresponding points record with card number'''
    # phone, tax_id are NOT NULL INTEGER fields, provide defaults if needed
    with _connect() as conn:
        cursor = conn.cursor()
        try:

            # Phone number: extract digits and convert to int, default to 0
            phone_int = _digits_or_none_only(phone_number) if phone_number else 0
            
            # Tax ID: extract digits and convert to int, default to 0
            tax_id_int = _digits_or_none_only(tax_id) if tax_id else 0
              
            # Insert customer with converted fields
            cursor.execute("INSERT INTO `CUSTOMER` (fname, lname, address, phone_number, email, tax_id, delivery_address, company_name, for_system_points_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (fname, lname, address, phone_int, email, tax_id_int, delivery_address, company_name))
            customer_id = cursor.lastrowid # fetches the auto-generated customer_id
            
            # Create corresponding points record with card number
            cursor.execute("INSERT INTO `POINT_SYSTEM` (customer_id, points, card_number) VALUES (?, ?, ?)",(customer_id, 0, card_number))
            
            # Update customer's for_system_points_id
            cursor.execute("UPDATE `CUSTOMER` SET for_system_points_id = ? WHERE customer_id = ?",(customer_id, customer_id))
            
            conn.commit()
            return customer_id
        except Exception as e:
            print(f"Error inserting customer: {e}")
            return None

def record_transaction_points(customer_id, points_to_add, points_to_redeem, trans_id, trans_date):
    '''Record points transaction in SWITCH entity - one entry per transaction with both added and redeemed points'''
    if customer_id is None:
        return True  # No customer, no points to track
    
    with _connect() as conn:
        cursor = conn.cursor()
        try:
            # Insert single record into SWITCH table with both points_added and points_deducted
            cursor.execute(
                "INSERT INTO `SWITCH` (for_transaction_id, for_point_system_id, date, points_added, points_deducted) "
                "VALUES (?, ?, ?, ?, ?)",
                (trans_id, customer_id, trans_date, points_to_add, points_to_redeem)
            )
            
            # Update POINT_SYSTEM: add earned points and subtract redeemed points
            net_points_change = points_to_add - points_to_redeem
            cursor.execute(
                "UPDATE `POINT_SYSTEM` SET points = points + ? WHERE customer_id = ?",
                (net_points_change, customer_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error recording transaction points: {e}")
            return False

def get_customer_by_id(customer_id):
    '''Get customer information by customer_id'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_id, fname, lname, address, phone_number, email, tax_id, delivery_address, company_name FROM `CUSTOMER` WHERE customer_id = ?",
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
                'delivery_address': row[7],
                'company_name': row[8]
            }
        return None

def get_customer_name(customer_id):
    '''Get customer full name by customer_id'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT fname, lname FROM `CUSTOMER` WHERE customer_id = ?",(customer_id,))
        row = cursor.fetchone()
        if row:
            fname = row[0] if row[0] else ""
            lname = row[1] if row[1] else ""
            return f"{fname} {lname}".strip()
        return "Unknown"

def get_all_customers_with_points():
    '''Get all customers with their points and card numbers from POINT_SYSTEM'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ps.customer_id, c.fname, c.lname, ps.points, ps.card_number " 
            "FROM `POINT_SYSTEM` ps JOIN `CUSTOMER` c ON ps.customer_id = c.customer_id "
            "ORDER BY ps.customer_id"
        )
        rows = cursor.fetchall()
        return rows

def get_customer_by_card_number(card_number):
    '''Get customer by their card number from POINT_SYSTEM'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ps.customer_id, c.fname, c.lname, ps.points, ps.card_number "
            "FROM `POINT_SYSTEM` ps "
            "JOIN `CUSTOMER` c ON ps.customer_id = c.customer_id "
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


def deduct_store_product_stock_by_id(prod_id, quantity_purchased):
    '''Deduct stock of a store product using prod_id (STATION_PRODUCT_INFO primary key)'''
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Get current stock from STATION_PRODUCT_INFO using primary key
        cursor.execute("SELECT stock FROM STATION_PRODUCT_INFO WHERE prod_id = ?;", (prod_id,))
        row = cursor.fetchone()
        if not row:
            return False
        current_stock = row[0] or 0

        # Ensure enough stock is available
        if current_stock < quantity_purchased:
            return False

        new_stock = current_stock - quantity_purchased
        cursor.execute("UPDATE STATION_PRODUCT_INFO SET stock = ? WHERE prod_id = ?;", (new_stock, prod_id))
        conn.commit()
        return True

def get_store_product_info_by_id(prod_id):
    '''Get store product information using STATION_PRODUCT_INFO.prod_id (primary key)
    Returns: {name, price, stock} or None if not found'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sp.name, spi.price, spi.stock
            FROM STATION_PRODUCT_INFO AS spi
            JOIN PRODUCT AS p ON p.product_id = spi.for_prod_id
            JOIN STATION_PRODUCT AS sp ON sp.for_prod_id = p.product_id
            WHERE spi.prod_id = ? AND p.prod_type = 'store_items'
            """,
            (prod_id,)
        )
        row = cursor.fetchone()
        if row:
            return {'name': row[0],'price': row[1],'stock': row[2]}
        return None

def get_customer_details(customer_id):
    '''Get detailed customer information including points data'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT c.customer_id, c.fname, c.lname, c.address, c.phone_number, c.email, "
            "c.tax_id, c.delivery_address, c.company_name, "
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
                'delivery_address': row[7],
                'company_name': row[8],
                'points': row[9],
                'card_number': row[10]
            }
        return None

def get_customer_point_history(customer_id):
    '''Get all point transactions for a customer from SWITCH table'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.switch_id, s.date, s.points_added, s.points_deducted, s.for_transaction_id "
            "FROM `SWITCH` s "
            "WHERE s.for_point_system_id = ? "
            "ORDER BY s.date DESC",
            (customer_id,)
        )
        rows = cursor.fetchall()
        return rows

def get_switch_entries_by_transaction(trans_id):
    '''Get SWITCH entry for a specific transaction showing points added and deducted (one entry per transaction)'''
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT switch_id, for_point_system_id, date, points_added, points_deducted "
            "FROM `SWITCH` "
            "WHERE for_transaction_id = ?",
            (trans_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'switch_id': row[0],
                'customer_id': row[1],
                'date': row[2],
                'points_added': row[3] if row[3] else 0,
                'points_deducted': row[4] if row[4] else 0
            }
        else:
            # No SWITCH entry (anonymous customer)
            return {
                'switch_id': None,
                'customer_id': None,
                'date': None,
                'points_added': 0,
                'points_deducted': 0
            }

if __name__ == '__main__':
    create_schema()
    db_init(seed_stations=10)
    #print_counts()