import customtkinter as ctk
import dbop
import entities
from datetime import datetime
import random
from PIL import Image
from tkinter import messagebox
import numpy as np

APP_TITLE = "Fuel Gas Chain"
APP_GEOMETRY = "600x500"
MAIN_FRAME_WIDTH = 1200
MAIN_FRAME_HEIGHT = 800
MAIN_FRAME_COLOUR = ("white","#0F0F0F")

# Αρχικό GUI 
class AppGUI(ctk.CTk):
    # Initialize the database schema and seed with data if needed
    dbop.create_schema()
    dbop.init_db_if_needed()

    ctk.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"
    def __init__(self):
        super().__init__()
        self.geometry(APP_GEOMETRY)
        self.iconbitmap("images\\logo.ico")
        self.title(APP_TITLE)

        # Initialize points redemption variables
        self.redemption_approved = False
        self.points_redeemed = 0
        self.euros_discount = 0.0
        self.current_customer_points = 0
        self.customer_has_card = False
        self.customer_id_for_points = None

        # Initialize non-automated station mode
        self.non_auto_mode = 'liters'  # Default: 'liters' | 'euros' | 'fill'

        # Initialize station and fuel variables
        self.current_customer_station = None
        self.current_admin_station = None
        self.customer_tank_capacity = 0
        self.selected_fuel = None
        self.selected_pump_id = None
        self.selected_tank_id = None
        self.automated_amount_total = 0.0

        # Initialize fill mode variables
        self.customer_tank_capacity = 0.0
        self.fill_total_cost = 0.0
        self.fill_points = 0

        # Initialize entry widget references
        self.amount_entry = None
        self.qty_entry = None
        self.card_number_entry = None

        # Initialize label widget references
        self.total_amount_label = None
        self.points_earned_label = None
        self.derived_liters_label = None
        self.liters_label = None

        # Initialize store variables
        self.selected_store_items = {}
        self.store_total_cost = 0.0
        self.store_payment_method = None
        self.current_store_category = None

        # Initialize payment and transaction variables
        self.selected_payment_method = None
        self.category_buttons = {}

        # configure root grid so frames expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # create frames

        self.card_window = None  # Initialize card display window reference
        self.frames = []
        self.main_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.main_frame)

        self.admin_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.admin_frame)

        self.customer_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.customer_frame)

        self.admin_all_stations_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.admin_all_stations_frame)

        self.customer_all_stations_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.customer_all_stations_frame)

        self.admin_station_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.admin_station_frame)

        self.customer_station_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.customer_station_frame)

        self.fill_up_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.fill_up_frame)

        self.fuel_purchase_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.fuel_purchase_frame)

        self.non_auto_fill_options_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.non_auto_fill_options_frame)

        self.payment_method_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.payment_method_frame)

        self.add_points_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.add_points_frame)

        self.shell_go_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.shell_go_frame)

        self.store_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.store_frame)

        self.store_payment_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.store_payment_frame)

        self.transactions_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.transactions_frame)

        self.fill_summary_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.fill_summary_frame)

        self.shell_go_customers_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.shell_go_customers_frame)

        self.customer_details_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.customer_details_frame)



        # manual fill frame for non-automated stations
        self.manual_fill_frame = ctk.CTkFrame(master=self, fg_color=MAIN_FRAME_COLOUR)
        self.frames.append(self.manual_fill_frame)

        # place frames in same grid cell; we'll raise the active one;
        # set all the frames ready, to appear or hide them
        for f in self.frames:
            f.grid(row=0, column=0, sticky="nsew")

        # populate frames with widgets
        self._build_main_frame()
        self._build_admin_frame()
        self._build_customer_frame()
        self._build_admin_all_stations_frame()
        self._build_customer_all_stations_frame()
        self._build_manual_fill_frame()
        #self._build_admin_station_frame()
        # _build_customer_station_frame() is called when station is selected in go_to_station_func()

        # show main frame initially
        self.show_frame(self.main_frame)

    #MAIN FRAME
    def _build_main_frame(self):
        title = ctk.CTkLabel(self.main_frame, text=APP_TITLE, font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(20, 10)) #pady=(upper, lower) / padx=(left, right)

        # make columns expand evenly
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        #buttons
        btn1 = ctk.CTkButton(self.main_frame, text="Administrator", command=lambda: self.show_frame(self.admin_frame))
        btn1.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        btn2 = ctk.CTkButton(self.main_frame, text="Enter as Customer", command=lambda: self.show_frame(self.customer_frame))
        btn2.grid(row=1, column=1, padx=20, pady=20, sticky="ew")
    

    #ADMIN FRAME
    def _build_admin_frame(self): 
        '''First Administrator Frame'''
        # make rows and columns expand evenly
        self.admin_frame.grid_rowconfigure(0, weight=1)
        self.admin_frame.grid_rowconfigure(1, weight=1)
        self.admin_frame.grid_rowconfigure(2, weight=0)  # Back button row
        self.admin_frame.grid_columnconfigure(0, weight=1)
        self.admin_frame.grid_columnconfigure(1, weight=1)

        #buttons
        btn_show_stations = ctk.CTkButton(self.admin_frame, text="Show Stations", command=lambda: self.btn_show_stations_func(self.admin_all_stations_frame))
        btn_show_stations.grid(row=0, column=0, padx=20, pady=20, sticky="we")

        btn_show_transactions = ctk.CTkButton(self.admin_frame, text="Show all Transactions", command=lambda: self._build_transactions_frame() or self.show_frame(self.transactions_frame))
        btn_show_transactions.grid(row=0, column=1, padx=20, pady=20, sticky="we")

        btn_show_customers = ctk.CTkButton(self.admin_frame, text="Shell Go+ Customers", command=lambda: self._build_shell_go_customers_frame() or self.show_frame(self.shell_go_customers_frame))
        btn_show_customers.grid(row=1, column=0, padx=20, pady=20, sticky="we")

        btn_back = ctk.CTkButton(self.admin_frame, text="Back", command=lambda: self.btn_back_func(self.main_frame))
        btn_back.grid(row=2, column=1, padx=20, pady=20, sticky="se")


    #CUSTOMER FRAME
    def _build_customer_frame(self):
        '''First Customer Frame'''
        # make rows and columns expand evenly
        self.customer_frame.grid_rowconfigure(0, weight=1)
        self.customer_frame.grid_rowconfigure(1, weight=1)
        self.customer_frame.grid_columnconfigure(0, weight=1)
        self.customer_frame.grid_columnconfigure(1, weight=1)

        #buttons
        btn_back = ctk.CTkButton(self.customer_frame, text="Back", command=lambda: self.btn_back_func(self.main_frame))
        btn_back.grid(row=1, column=1, padx=20, pady=20, sticky="se")
        btn_gas = ctk.CTkButton(self.customer_frame, text="Select Station", command=lambda: self.btn_show_stations_func(self.customer_all_stations_frame))
        btn_gas.grid(row=0, column=0, padx=20, pady=20, sticky="we")


    #ALL STATIONS WHEN ADMIN ENTERS FRAME
    def _build_admin_all_stations_frame(self):
        '''Station option Frame'''
        self.admin_all_stations_frame.grid_rowconfigure(0, weight=1)
        self.admin_all_stations_frame.grid_columnconfigure(0, weight=1)       
        self.admin_all_stations_frame.grid_rowconfigure(1, weight=0)  # back button row should not expand

        self.scrollable_station_frame = ctk.CTkScrollableFrame(master=self.admin_all_stations_frame, fg_color=MAIN_FRAME_COLOUR)

        self.scrollable_station_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_station_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_station_frame.grid_rowconfigure(1, weight=1)
        self.scrollable_station_frame.grid_columnconfigure(1, weight=1)

        self.scrollable_station_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        stations_info = dbop.get_stations()
        #create buttons for each station
        for station in stations_info:
            is_automated = station[5]
            has_store = station[6]
            store_suffix = " - Has Store" if has_store else ""
            btn_text = f"{station[2]} - {station[1]} - {'Automated' if is_automated else 'Non-Automated'}{store_suffix}"
            btn = ctk.CTkButton(self.scrollable_station_frame, text=btn_text, command=lambda station=station: self.go_to_station_func(station[0], self.admin_station_frame)) 
            btn.pack(pady=5, fill="x")

        # Back button positioned at the bottom, outside the scrollable frame
        btn_back = ctk.CTkButton(self.admin_all_stations_frame, text="Back", command=lambda: self.btn_back_func(self.admin_frame))
        btn_back.grid(row=1, column=0, padx=20, pady=20, sticky="se")
    

    #ALL STATIONS WHEN CUSTOMER ENTERS FRAME
    def _build_customer_all_stations_frame(self):
        '''Station option Frame'''
        
        self.customer_all_stations_frame.grid_rowconfigure(0, weight=1) 
        self.customer_all_stations_frame.grid_columnconfigure(0, weight=1)       
        self.customer_all_stations_frame.grid_rowconfigure(1, weight=0)  # back button row should not expand

        self.scrollable_station_frame = ctk.CTkScrollableFrame(master=self.customer_all_stations_frame, fg_color=MAIN_FRAME_COLOUR)

        self.scrollable_station_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_station_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_station_frame.grid_rowconfigure(1, weight=1)
        self.scrollable_station_frame.grid_columnconfigure(1, weight=1)

        self.scrollable_station_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        stations_info = dbop.get_stations()
        
        for station in stations_info:
            station_id = station[0]
            is_automated = station[5]
            has_store = station[6]  
            
            store_suffix = " - Has Store" if has_store else "" 
            btn_text = f"{station[2]} - {station[1]}- {'Automated' if is_automated else 'Non-Automated'}{store_suffix}"
            btn = ctk.CTkButton(self.scrollable_station_frame, text=btn_text, command=lambda station=station: self.go_to_station_func(station[0], self.customer_station_frame))
            btn.pack(pady=5, fill="x")

        # Back button positioned at the bottom, outside the scrollable frame
        btn_back = ctk.CTkButton(self.customer_all_stations_frame, text="Back", command=lambda: self.btn_back_func(self.customer_frame))
        btn_back.grid(row=1, column=0, padx=20, pady=20, sticky="se")


    #SELECTED STATION WHEN ADMIN ENTERS
    def _build_admin_station_frame(self, station_id): 
        '''Station Frame'''
        # Clear previous widgets so that we don't have any leftovers when we enter a new station
        for widget in self.admin_station_frame.winfo_children():
            widget.destroy()
        
        # make rows and columns expand evenly
        self.admin_station_frame.grid_rowconfigure(0, weight=1)
        self.admin_station_frame.grid_columnconfigure(0, weight=1)
        self.admin_station_frame.grid_rowconfigure(1, weight=0)  # back button row

        self.scrollable_admin_station_frame = ctk.CTkScrollableFrame(master=self.admin_station_frame, fg_color=MAIN_FRAME_COLOUR)
        self.scrollable_admin_station_frame.grid(row=0, column=0, sticky="nsew")
        for i in range(5): # store title, tanks, pumps, fuels, employees 
            self.scrollable_admin_station_frame.grid_rowconfigure(i, weight=1) # make rows expand evenly
        self.scrollable_admin_station_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_admin_station_frame.grid_columnconfigure(1, weight=1)

        #frame 
        station_info = dbop.get_admin_station_info(station_id)
        station_label = ctk.CTkLabel(self.scrollable_admin_station_frame, text=f"Station id: {station_info['station_id']} \n Station name: {station_info['name']} \n Station location: {station_info['location']} \n Contact: {station_info['phone']} \n Email: {station_info['email']} \n {'Automated' if station_info['automated'] else 'Non-Automated'}", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
        station_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))

        # Tanks info
        tanks_text = "Tanks:\n" + "\n".join([
            f"ID: {t['tank_id']}, Capacity: {t['capacity']} L, Current: {t['current_quantity']} L, Min: {(f'{t['min_fuel_quantity']:.2f}' if t.get('min_fuel_quantity') is not None else 'N/A')} L, Fuel: {t['fuel_type']}"
            for t in station_info['tanks']
        ])
        tanks_label = ctk.CTkLabel(self.scrollable_admin_station_frame, text=tanks_text, font=ctk.CTkFont(size=14))
        tanks_label.grid(row=1, column=0, columnspan=2, pady=(10, 10))

        # Pumps info
        pumps_text = "Pumps:\n" + "\n".join([f"ID: {p['pump_id']}, Active: {p['is_active']}, Number: {p['pump_number']}, Tank ID: {p['for_tank_id']}" for p in station_info['pumps']])
        pumps_label = ctk.CTkLabel(self.scrollable_admin_station_frame, text=pumps_text, font=ctk.CTkFont(size=14))
        pumps_label.grid(row=2, column=0, columnspan=2, pady=(10, 10))

        # Fuels info
        fuels_text = "Fuels:\n" + "\n".join([
            f"ID: {f['prod_id']}, Type: {f['fuel_type']}, Price: {f['price_per_liter']:.2f}€/L, Points: {f['points_per_liter']}"
            for f in station_info['fuels']
        ])
        fuels_label = ctk.CTkLabel(self.scrollable_admin_station_frame, text=fuels_text, font=ctk.CTkFont(size=14))
        fuels_label.grid(row=3, column=0, columnspan=2, pady=(10, 10))

        # Employees info
        employees_text = "Employees:\n" + "\n".join([f"\nID: {e['emp_id']}, \nName: {e['fname']}, \nLast Name: {e['lname']}, \nAmka: {e['ssn']}, \nSalary: {e['salary']}, \nEmail: {e['email']}" for e in station_info['employees']])
        employees_label = ctk.CTkLabel(self.scrollable_admin_station_frame, text=employees_text, font=ctk.CTkFont(size=14))
        employees_label.grid(row=4, column=0, columnspan=2, pady=(10, 10))

        #back button outside scrollable frame
        btn_back = ctk.CTkButton(self.admin_station_frame, text="Back", command=lambda: self.btn_back_func(self.admin_all_stations_frame))
        btn_back.grid(row=1, column=0, padx=20, pady=20, sticky="se")


    #SELECTED STATION WHEN CUSTOMER ENTERS
    def _build_customer_station_frame(self): 
        '''Station Frame'''
        # Clear previous widgets 
        for widget in self.customer_station_frame.winfo_children():
            widget.destroy()
        
        self.customer_station_frame.grid_rowconfigure(0, weight=1)
        self.customer_station_frame.grid_columnconfigure(0, weight=1)

        # Buttons centered vertically, stacked

        # Passing by customer fill up button
        btn_fill_up = ctk.CTkButton(self.customer_station_frame, text="Fill-up", command=lambda: self.btn_fill_up_func())
        btn_fill_up.pack(pady=(50, 10), padx=20)

        # Check if station has store from database
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        has_store = station_info.get('has_store') 

        # Show "Go to Store" button only if station has store
        if has_store:
            btn_go_to_store = ctk.CTkButton(self.customer_station_frame, text="Go to Store", command=lambda: self.btn_go_to_store_func())
            btn_go_to_store.pack(pady=(10, 50), padx=20)
        else:
            # Add padding if store button is not shown
            ctk.CTkLabel(self.customer_station_frame, text="").pack(pady=(10, 50))

        # Back button 
        btn_back = ctk.CTkButton(self.customer_station_frame, text="Back", command=lambda: self.btn_back_func(self.customer_all_stations_frame))
        btn_back.pack(side="bottom", anchor="e", padx=20, pady=20)
    
    
    #FUEL PURCHASE FRAME FOR NON-AUTOMATED STATIONS
    def _build_fuel_purchase_frame(self):
        '''Fuel Purchase Frame for non automated stations only (supports liters/euros modes)'''
        for widget in self.fuel_purchase_frame.winfo_children():
            widget.destroy()

        station_info = dbop.get_admin_station_info(self.current_customer_station)
        mode = self.non_auto_mode  # 'liters' | 'euros' | 'fill' 
        
        # Layout
        self.fuel_purchase_frame.grid_rowconfigure(0, weight=0)  # Station name
        self.fuel_purchase_frame.grid_rowconfigure(1, weight=0)  # Title
        self.fuel_purchase_frame.grid_rowconfigure(2, weight=1)  # Content
        self.fuel_purchase_frame.grid_columnconfigure(0, weight=1)
        self.fuel_purchase_frame.grid_columnconfigure(1, weight=1)
        
        # Display station name at the top
        station_name = station_info.get('name') 
        station_label = ctk.CTkLabel(self.fuel_purchase_frame, text=station_name, font=ctk.CTkFont(size=16, weight="bold"))
        station_label.grid(row=0, column=0, columnspan=2, pady=(20, 5), sticky="n")

        # Title (Purchase Fuel)
        title_label = ctk.CTkLabel(self.fuel_purchase_frame, text=f"Purchase {self.selected_fuel['fuel_type']}", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=(5, 10))

        # Input label changes based on mode
        qty_label_text = "Quantity (liters):" if mode == 'liters' else "Euros (€):"
        qty_label = ctk.CTkLabel(self.fuel_purchase_frame, text=qty_label_text)
        qty_label.grid(row=2, column=0, padx=20, pady=10, sticky="e")

        current_row = 3

        # computed values for each case (liters,euros)
        # Total amount (show in liters mode, hide in euros mode)
        if mode == 'liters':
            total_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Total amount:")
            total_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

            self.total_amount_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0.00€", font=ctk.CTkFont(size=16, weight="bold"))
            self.total_amount_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")
            current_row += 1

        # For euros mode, show computed liters
        if mode == 'euros':
            liters_text_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Liters:")
            liters_text_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

            self.derived_liters_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0.00 L", font=ctk.CTkFont(size=14, weight="bold")) 
            self.derived_liters_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")
            current_row += 1

        # Points row 
        points_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Points to earn:")
        points_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

        self.points_earned_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0 points", font=ctk.CTkFont(size=14, weight="bold"))
        self.points_earned_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")
        
        points_row = current_row

        # Input widgets based on mode, placed in the middle of the frame
        if mode == 'liters':  # user types liters, we compute euros
            self.qty_entry = ctk.CTkEntry(self.fuel_purchase_frame)
            self.qty_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
            self.qty_entry.insert(0, "10")
            self.qty_entry.bind("<KeyRelease>", lambda e: self.update_from_liters_entry())
            self.update_from_liters_entry()
        elif mode == 'euros':  # user types euros, we compute liters
            self.amount_entry = ctk.CTkEntry(self.fuel_purchase_frame)
            self.amount_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
            self.amount_entry.insert(0, "20")
            self.amount_entry.bind("<KeyRelease>", lambda e: self.update_from_euros_entry())
            self.update_from_euros_entry()
        else:  # 'fill' mode same as 'liters' mode for protection reasons. It's defined in fill
            self.qty_entry = ctk.CTkEntry(self.fuel_purchase_frame)
            self.qty_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
            self.qty_entry.insert(0, "10")
            self.qty_entry.bind("<KeyRelease>", lambda e: self.update_from_liters_entry())
            self.update_from_liters_entry()

        # Buttons
        # continue to payment method frame with continue
        btn_continue = ctk.CTkButton(self.fuel_purchase_frame, text="Continue", command=lambda: [self._build_payment_method_frame(), self.show_frame(self.payment_method_frame)])
        btn_continue.grid(row=points_row + 1, column=0, padx=20, pady=20, sticky="w")

        btn_back = ctk.CTkButton(self.fuel_purchase_frame, text="Back", command=lambda: self.show_frame(self.fill_up_frame))
        btn_back.grid(row=points_row + 2, column=1, padx=20, pady=20, sticky="e")


    def _build_fill_up_frame(self):
        '''Fill-up Frame, shows fuel types to select from'''
        # Clear previous widgets if any
        for widget in self.fill_up_frame.winfo_children():
            widget.destroy()

        # Reset any previously selected pump/tank when entering fuel selection
        self.leave_selected_pump_and_tank()
        
        # Configure grid
        self.fill_up_frame.grid_rowconfigure(0, weight=1)
        self.fill_up_frame.grid_columnconfigure(0, weight=1)

        # Get station info (assumed to exist)
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        if not station_info:
            return

        # Display station name at the top
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.fill_up_frame, text=station_name,font=ctk.CTkFont(size=16, weight="bold"))
        station_label.pack(pady=(20, 5))

        # Select Fuel Type label
        label = ctk.CTkLabel(self.fill_up_frame, text="Select Fuel Type")
        label.pack(pady=(5, 10))

        # Fuel buttons, except Heating Oil and Household LPG - these are not for vehicles
        # Disable a fuel if no active pump has a tank with quantity above its min threshold
        for fuel in station_info['fuels']:
            if fuel['fuel_type'] != 'Heating Oil' and fuel['fuel_type'] != 'Household LPG':
                # Check if fuel is available (pump active + tank quantity above min threshold)
                available = self._is_fuel_available(fuel, station_info)

                label_text = f"{fuel['fuel_type']} - {fuel['price_per_liter']:.2f} €/L"
                if available:
                    btn = ctk.CTkButton(self.fill_up_frame, text=label_text, command=lambda f=fuel: self.select_fuel(f))
                else:
                    btn = ctk.CTkButton(self.fill_up_frame, text=f"{label_text} (Unavailable)", state="disabled")
                btn.pack(pady=5, padx=20)

        # Back button
        btn_back = ctk.CTkButton(self.fill_up_frame, text="Back", command=lambda: self.show_frame(self.non_auto_fill_options_frame))
        btn_back.pack(side="bottom", anchor="e", pady=20, padx=20)

    def find_pump_and_tank_for_fuel(self, fuel_type, station_info):
        """
        Find an active pump and its associated tank for the given fuel type at the station.
        Returns a tuple (pump_id, tank_id) if found, else (None, None).
        """
        for tank in station_info['tanks']:
            if tank['fuel_type'] != fuel_type: # if not the right fuel type
                continue

            # Check tank has sufficient quantity
            min_qty = tank.get('min_fuel_quantity', 0)
            if tank['current_quantity'] <= min_qty:
                continue

            # Pumps for this tank (one-to-one mapping expected)
            pumps_for_tank = [p for p in station_info['pumps'] if p['for_tank_id'] == tank['tank_id']]
            for pump in pumps_for_tank:
                if pump['is_active']:
                    return (pump['pump_id'], tank['tank_id'])

        return (None, None)

    def leave_selected_pump_and_tank(self):
        self.selected_tank_id = None
        self.selected_pump_id = None

    def _is_fuel_available(self, fuel, station_info):
        """
        Check if a fuel type is available at the station. A fuel is available if there's at least one tank with:
        - The correct fuel type
        - An active pump connected to it
        - Current quantity above minimum threshold
        """
        for tank in station_info['tanks']: # Iterate over tanks
            if tank['fuel_type'] != fuel['fuel_type']: # if not the right fuel type
                continue
            # Find if there is any active pump for this tank

            # Find pumps for this tank
            pumps_for_tank = [p for p in station_info['pumps'] if p['for_tank_id'] == tank['tank_id']] # [{'pump_id': 1, ...}, {'pump_id': 2, ...}]

            #check if any pump is active
            pump_active = any(p['is_active'] for p in pumps_for_tank) # True if any pump is active, False otherwise

            # Check if tank quantity is above min threshold
            min_qty = tank.get('min_fuel_quantity', 0) # checks what's the minimum quantity of the tank, default is 0 if not set
            qty_ok = tank['current_quantity'] > min_qty # True if current quantity is above min threshold

            #available if both pump is active and quantity is ok
            if pump_active and qty_ok:
                return True

        return False

    def _build_non_auto_fill_options_frame(self):
        '''Non-Automated Station Fill Options Frame (Liters/Euros/Fill)'''
        
        # Clear previous widgets
        for widget in self.non_auto_fill_options_frame.winfo_children():
            widget.destroy()

        # Layout
        self.non_auto_fill_options_frame.grid_rowconfigure(0, weight=1)
        self.non_auto_fill_options_frame.grid_columnconfigure(0, weight=1)

        # Display station name at the top 
        station_info = dbop.get_admin_station_info(self.current_customer_station) or {}
        station_name = station_info.get('name', 'Unknown Station')
        station_label = ctk.CTkLabel(self.non_auto_fill_options_frame, text=station_name, font=ctk.CTkFont(size=16, weight="bold"))
        station_label.pack(pady=(20, 5))

        # Title
        title = ctk.CTkLabel(self.non_auto_fill_options_frame, text="Choose Fill Mode", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(5, 10), padx=20)

        # Buttons
        btn_liters = ctk.CTkButton(self.non_auto_fill_options_frame, text="Liters", command=lambda: self._on_non_auto_option_selected('liters'))
        btn_liters.pack(pady=10, padx=20, fill="x")

        btn_euros = ctk.CTkButton(self.non_auto_fill_options_frame, text="Euros", command=lambda: self._on_non_auto_option_selected('euros'))
        btn_euros.pack(pady=10, padx=20, fill="x")

        btn_fill = ctk.CTkButton(self.non_auto_fill_options_frame, text="Fill", command=lambda: self._on_non_auto_option_selected('fill'))
        btn_fill.pack(pady=10, padx=20, fill="x")

        # Back
        btn_back = ctk.CTkButton(self.non_auto_fill_options_frame, text="Back", command=lambda: self.show_frame(self.customer_station_frame))
        btn_back.pack(side="bottom", anchor="e", pady=20, padx=20)

    def _build_payment_method_frame(self):
        '''Payment Method Frame for Non-Automated stations'''
        # Clear previous widgets
        for widget in self.payment_method_frame.winfo_children():
            widget.destroy()

        # Display station name at the top 
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.payment_method_frame, text=station_name, font=ctk.CTkFont(size=16, weight="bold"))
        station_label.pack(pady=(20, 5))

        # Centered vertical layout using pack
        title = ctk.CTkLabel(self.payment_method_frame, text="Payment Method", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(5, 10), padx=20)
        
        # Display final amount to pay 
        if self.non_auto_mode == 'euros':
            amount_text = self.amount_entry.get().strip() 
            try:
                amount = float(amount_text) if amount_text else 0.0
            except ValueError:
                amount = 0.0

            price = self.selected_fuel.get('price_per_liter', 1.0)
            max_euros = self.customer_tank_capacity * price # maximum euros based on tank capacity of the customer
            amount = min(amount, max_euros) # amount of euros the customer has to pay is decided from what he selected and what's his tank capacity

        elif self.non_auto_mode == 'fill':
            amount = self.fill_total_cost # in fill mode, amount is precomputed based on tank capacity, we have computed that self.fill_total_cost = self.customer_tank_capacity * price_per_liter

        else:  # liters mode
            qty_text = self.qty_entry.get().strip() 
            try:
                qty_liters = float(qty_text) if qty_text else 0.0
            except ValueError:
                qty_liters = 0.0
               
            qty_liters = min(qty_liters, self.customer_tank_capacity) # limit liters to tank capacity
            price_per_liter = self.selected_fuel.get('price_per_liter', 1.0) 
            amount = qty_liters * price_per_liter
        
        amount_label = ctk.CTkLabel(self.payment_method_frame, text=f"Amount to Pay: €{amount:.2f}",font=ctk.CTkFont(size=14, weight="bold"),text_color="green")
        amount_label.pack(pady=(0, 20), padx=20)

        btn_cash = ctk.CTkButton(self.payment_method_frame, text="Cash", command=lambda: self.confirm_non_auto_purchase("Cash", amount))
        btn_cash.pack(pady=8, padx=20)

        btn_card = ctk.CTkButton(self.payment_method_frame, text="Card", command=lambda: self.confirm_non_auto_purchase("Card", amount))
        btn_card.pack(pady=8, padx=20)

        btn_fuel_card = ctk.CTkButton(self.payment_method_frame, text="Fuel Card", command=lambda: self.confirm_non_auto_purchase("Fuel Card", amount))
        btn_fuel_card.pack(pady=8, padx=20)

        btn_add_points = ctk.CTkButton(self.payment_method_frame, text="Add Points", command=lambda: (self._build_add_points_frame(), self.show_frame(self.add_points_frame)))
        btn_add_points.pack(pady=(20, 8), padx=20)
        
        btn_register_shell = ctk.CTkButton(self.payment_method_frame, text="Register in Shell go+", command=lambda: (self._build_shell_go_registration_frame(), self.show_frame(self.shell_go_frame)))
        btn_register_shell.pack(pady=8, padx=20)
        
        # Back button
        btn_back = ctk.CTkButton(self.payment_method_frame, text="Back", command=lambda: self.show_frame(self.fill_up_frame))
        btn_back.pack(side="bottom", anchor="e", padx=20, pady=20)

    def _build_payment_method_frame_automated(self):
        '''Payment Method Frame for Automated stations'''

        # Clear previous widgets
        for widget in self.payment_method_frame.winfo_children():
            widget.destroy()

        # Display station name at the top
        
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.payment_method_frame, text=station_name, font=ctk.CTkFont(size=16, weight="bold"))
        station_label.pack(pady=(20, 5))

        # Centered vertical layout using pack
        title = ctk.CTkLabel(self.payment_method_frame, text="Select Payment Method", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(5, 20), padx=20)

        btn_cash = ctk.CTkButton(self.payment_method_frame, text="Cash", command=lambda: self.select_payment_method("Cash"))
        btn_cash.pack(pady=8, padx=20)

        btn_card = ctk.CTkButton(self.payment_method_frame, text="Card", command=lambda: self.select_payment_method("Card"))
        btn_card.pack(pady=8, padx=20)

        btn_fuel_card = ctk.CTkButton(self.payment_method_frame, text="Fuel Card", command=lambda: self.select_payment_method("Fuel Card"))
        btn_fuel_card.pack(pady=8, padx=20)

        btn_add_points = ctk.CTkButton(self.payment_method_frame, text="Add Points", command = lambda: (self._build_add_points_frame(), self.show_frame(self.add_points_frame)))
        btn_add_points.pack(pady=(20, 8), padx=20)

        # Back button
        btn_back = ctk.CTkButton(self.payment_method_frame, text="Back", command=lambda: self.show_frame(self.fill_up_frame))
        btn_back.pack(side="bottom", anchor="e", padx=20, pady=20)

    def select_payment_method(self, payment_method):
        '''only for automated stations'''
        
        self.selected_payment_method = payment_method
        self._build_auto_euro_amount_selection_frame()
        self.show_frame(self.fuel_purchase_frame)

    def _build_fill_summary_frame(self):
        '''Frame showing fill summary with liters and cost for fill mode'''
        for widget in self.fill_summary_frame.winfo_children():
            widget.destroy()

        # Layout
        self.fill_summary_frame.grid_rowconfigure(0, weight=0)  # Station name
        self.fill_summary_frame.grid_rowconfigure(1, weight=0)  # Title
        self.fill_summary_frame.grid_rowconfigure(2, weight=1)  # Content
        self.fill_summary_frame.grid_rowconfigure(3, weight=0)  # Buttons
        self.fill_summary_frame.grid_columnconfigure(0, weight=1)

        # Display station name at the top
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.fill_summary_frame, text=station_name,font=ctk.CTkFont(size=16, weight="bold"))
        station_label.grid(row=0, column=0, pady=(20, 5))

        # Title (Purchase Fuel)
        title_label = ctk.CTkLabel(self.fill_summary_frame, text=f"Purchase {self.selected_fuel['fuel_type']}", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=1, column=0, pady=(5, 20))

        # building 2 transparent frames to setup the fill_summary_frame layout properly

        # Content frame for centered information
        content_frame = ctk.CTkFrame(self.fill_summary_frame, fg_color="transparent") # fg transparent to blend with parent
        content_frame.grid(row=2, column=0, padx=40, pady=20)
        
        # Liters filled
        liters_info = ctk.CTkLabel(content_frame,text=f"Liters filled: {self.customer_tank_capacity:.2f} L", font=ctk.CTkFont(size=16, weight="bold"))
        liters_info.pack(pady=10)

        # Total cost
        cost_info = ctk.CTkLabel(content_frame, text=f"Total cost: {self.fill_total_cost:.2f} €",font=ctk.CTkFont(size=16, weight="bold"),text_color="green")
        cost_info.pack(pady=10)

        # Points to earn
        points_info = ctk.CTkLabel(content_frame,text=f"Points to earn: {self.fill_points} points",font=ctk.CTkFont(size=14))
        points_info.pack(pady=10)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.fill_summary_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        btn_back = ctk.CTkButton(buttons_frame, text="Back", command=lambda: self.show_frame(self.fill_up_frame))
        btn_back.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        btn_continue = ctk.CTkButton(buttons_frame, text="Continue", command= lambda: (self._build_payment_method_frame(), self.show_frame(self.payment_method_frame))) # continue to payment method 
        btn_continue.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def _build_auto_euro_amount_selection_frame(self):
        '''Fuel Purchase Frame for automated stations only (euros selection with fixed buttons)'''
        # Clear previous widgets
        for widget in self.fuel_purchase_frame.winfo_children():
            widget.destroy()

        # Layout
        self.fuel_purchase_frame.grid_rowconfigure(0, weight=0)  # Station name
        self.fuel_purchase_frame.grid_rowconfigure(1, weight=0)  # Title
        self.fuel_purchase_frame.grid_rowconfigure(2, weight=1)  # Content
        self.fuel_purchase_frame.grid_columnconfigure(0, weight=1)
        self.fuel_purchase_frame.grid_columnconfigure(1, weight=1)

        # Display station name at the top
    
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.fuel_purchase_frame, text=station_name, font=ctk.CTkFont(size=16, weight="bold"))
        station_label.grid(row=0, column=0, columnspan=2, pady=(20, 5), sticky="n")

        # Title (Purchase Fuel)
        title_label = ctk.CTkLabel(self.fuel_purchase_frame, text=f"Purchase {self.selected_fuel['fuel_type']}", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=(5, 10))

        # Payment method display
        payment_label = ctk.CTkLabel(self.fuel_purchase_frame, text=f"Payment: {self.selected_payment_method}")
        payment_label.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

        # Euro amount selection using fixed buttons that can be combined
        self.automated_amount_total = 0.0

        amount_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Select Amount (€):")
        amount_label.grid(row=3, column=0, padx=20, pady=10, sticky="e")

        btn_10 = ctk.CTkButton(self.fuel_purchase_frame, text="10 €", command=lambda: self.add_amount_automated(10))
        btn_10.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        btn_20 = ctk.CTkButton(self.fuel_purchase_frame, text="20 €", command=lambda: self.add_amount_automated(20))
        btn_20.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        btn_50 = ctk.CTkButton(self.fuel_purchase_frame, text="50 €", command=lambda: self.add_amount_automated(50))
        btn_50.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        btn_100 = ctk.CTkButton(self.fuel_purchase_frame, text="100 €", command=lambda: self.add_amount_automated(100))
        btn_100.grid(row=6, column=1, padx=10, pady=5, sticky="w")

        current_row = 7

        # Total amount selected
        total_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Total selected:")
        total_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

        self.total_amount_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0.00€", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_amount_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")
        current_row += 1

        # Liters display
        liters_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Liters:")
        liters_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

        self.liters_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0.00 L", font=ctk.CTkFont(size=16, weight="bold"))
        self.liters_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")
        current_row += 1

        # Points display
        points_label = ctk.CTkLabel(self.fuel_purchase_frame, text="Points to earn:")
        points_label.grid(row=current_row, column=0, padx=20, pady=10, sticky="e")

        self.points_earned_label = ctk.CTkLabel(self.fuel_purchase_frame, text="0 points", font=ctk.CTkFont(size=14, weight="bold"))
        self.points_earned_label.grid(row=current_row, column=1, padx=20, pady=10, sticky="w")

        # Calculate initial values
        self.update_total_automated()

        # Buttons
        btn_confirm = ctk.CTkButton(self.fuel_purchase_frame, text="Confirm", width=140, command=self.confirm_automated_purchase)
        btn_confirm.grid(row=current_row + 1, column=0, padx=20, pady=20, sticky="w")

        btn_back = ctk.CTkButton(self.fuel_purchase_frame, text="Back", command=lambda: self._build_payment_method_frame_automated() or self.show_frame(self.payment_method_frame))
        btn_back.grid(row=current_row + 1, column=1, padx=20, pady=20, sticky="e")

        # Cancel button under Confirm
        btn_cancel = ctk.CTkButton(self.fuel_purchase_frame, text="Cancel", width=140, fg_color="gray", command=self.cancel_automated_purchase)
        btn_cancel.grid(row=current_row + 2, column=0, padx=20, pady=(0,20), sticky="w")

    def add_amount_automated(self, amount):
        self.automated_amount_total += float(amount)
        self.update_total_automated()

    def update_total_automated(self):
        '''Update liters, points, and total for automated stations based on accumulated euro amount'''
        amount = self.automated_amount_total
         # Update total amount label
        self.total_amount_label.configure(text=f"{amount:.2f}€")
        price = self.selected_fuel['price_per_liter']
        liters = amount / price if price else 0.0
        self.liters_label.configure(text=f"{liters:.2f} L")

        # Calculate points
        points_per_liter = self.selected_fuel.get('points_per_liter', 0)
        points = int(liters * points_per_liter)
        self.points_earned_label.configure(text=f"{points} points")

    def cancel_automated_purchase(self):
        self.automated_amount_total = 0.0
        self.show_frame(self.customer_station_frame)

    def confirm_automated_purchase(self):
        '''Confirm fuel purchase and save transaction'''
        from datetime import datetime
        
        # Get payment method
        payment_method = getattr(self, 'selected_payment_method', 'Unknown')
        
        # Get transaction details
        trans_date = datetime.now().timestamp()
        requested_amount = getattr(self, 'automated_amount_total', 0.0)
        amount_of_money = requested_amount
        
        # Clamp to tank capacity on confirmation
        if hasattr(self, 'customer_tank_capacity') and hasattr(self, 'selected_fuel'):
            price = self.selected_fuel.get('price_per_liter', 1.0)
            max_euros = self.customer_tank_capacity * price
            amount_of_money = min(amount_of_money, max_euros)
        
        # Apply points discount if redeemed
        if hasattr(self, 'euros_discount') and self.euros_discount > 0:
            amount_of_money = max(0, amount_of_money - self.euros_discount)
        
        # Calculate change (money returned to customer)
        change = requested_amount - amount_of_money
        
        # Calculate points for FUEL: liters × points_per_liter (only if customer has provided card)
        if hasattr(self, 'customer_has_card') and self.customer_has_card:
            if amount_of_money > 0 and hasattr(self, 'selected_fuel'):
                price = self.selected_fuel.get('price_per_liter', 1.0)
                liters_purchased = amount_of_money / price if price else 0.0
                points_per_liter = self.selected_fuel.get('points_per_liter', 0)
                total_points = int(liters_purchased * points_per_liter)
            else:
                total_points = 0
        else:
            total_points = 0
        
        # Get station ID and customer ID if available
        for_station_id = self.current_customer_station
        for_cust_id = getattr(self, 'customer_id_for_points', None)
        
        # Insert transaction
        try:
            trans_id = dbop.insert_transaction(trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {e}")
            return
        
        # Update customer points if they provided card and earned points
        if total_points > 0 and hasattr(self, 'customer_id_for_points'):
            dbop.update_customer_points(self.customer_id_for_points, total_points)
        
        # Redeem points if applicable
        if hasattr(self, 'redemption_approved') and self.redemption_approved and hasattr(self, 'customer_id_for_points'):
            dbop.redeem_points(self.customer_id_for_points, self.points_redeemed)
        
        # Deduct fuel from the selected tank
        if hasattr(self, 'selected_fuel') and hasattr(self, 'selected_tank_id') and amount_of_money > 0:
            price = self.selected_fuel.get('price_per_liter', 1.0)
            liters_purchased = amount_of_money / price if price else 0.0
            dbop.deduct_fuel_from_tank(self.selected_tank_id, liters_purchased)
        
        # Show completion message with amount paid and change/discount received
        message = f"Thank you for your purchase!\n\nAmount Paid: €{amount_of_money:.2f}"
        if hasattr(self, 'euros_discount') and self.euros_discount > 0:
            message += f"\nPoints Discount: €{self.euros_discount:.2f}"
        if change > 0:
            message += f"\nChange Received: €{change:.2f}"
        messagebox.showinfo("Purchase Complete", message)
        
        # Reset all customer session data
        self._reset_customer_session()
        
        self.show_frame(self.customer_station_frame)

    def confirm_non_auto_purchase(self, payment_method, amount):
        '''Confirm non-automated fuel purchase and save transaction'''
        
        # Get transaction details
        trans_date = datetime.now().timestamp()
        amount_of_money = amount # amount already calculated and clamped to tank capacity in _build_payment_method_frame
        
        # Calculate liters purchased
        price = self.selected_fuel.get('price_per_liter', 1.0)
        liters_purchased = amount_of_money / price if price else 0.0
        
        # Calculate points for FUEL: liters × points_per_liter (only if customer has card)
        if self.customer_has_card:
            points_per_liter = self.selected_fuel.get('points_per_liter', 0)
            total_points = int(liters_purchased * points_per_liter)
        else:
            total_points = 0
        
        # Apply points discount if redeemed
        if self.euros_discount > 0:
            amount_of_money = max(0, amount_of_money - self.euros_discount)
        
        # Get station ID and customer ID if available
        for_station_id = self.current_customer_station
        for_cust_id = self.customer_id_for_points # may be None if no card provided
        
        # Insert transaction
        try:
            trans_id = dbop.insert_transaction(trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {e}")
            return
        
        # Update customer points if they provided card and earned points
        if total_points > 0 and for_cust_id is not None:
            dbop.update_customer_points(for_cust_id, total_points)
        
        # Redeem points if applicable
        if self.redemption_approved and for_cust_id is not None:
            dbop.redeem_points(for_cust_id, self.points_redeemed)
        
        # Deduct fuel from tank
        dbop.deduct_fuel_from_tank(self.selected_tank_id, liters_purchased)
        
        # Show completion message with amount paid and discount info
        message = f"Thank you for your purchase!\n\nAmount Paid: €{amount_of_money:.2f}"
        if self.euros_discount > 0:
            message += f"\nPoints Discount: €{self.euros_discount:.2f}"
        messagebox.showinfo("Purchase Complete", message)
        
        # Reset all customer session data
        self._reset_customer_session()
        
        self.show_frame(self.customer_station_frame)

    def _build_manual_fill_frame(self):
        # Clear previous widgets
        for widget in self.manual_fill_frame.winfo_children():
            widget.destroy()

        # Basic layout
        self.manual_fill_frame.grid_rowconfigure(0, weight=1)
        self.manual_fill_frame.grid_columnconfigure(0, weight=1)

        # Get station info
        station_info = {}
        try:
            station_info = dbop.get_admin_station_info(self.current_customer_station) or {}
        except Exception:
            station_info = {}

        name = station_info.get('name', 'Unknown station')
        automated_text = "Automated" if station_info.get('automated') else "Non-Automated"
        title_text = f"Station: {name}\nStatus: {automated_text}"
        label = ctk.CTkLabel(self.manual_fill_frame, text=title_text, font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=(20, 10))

        msg = "This station is not automated. Please go to the attendant to request a fill-up."
        msg_label = ctk.CTkLabel(self.manual_fill_frame, text=msg)
        msg_label.pack(pady=(10, 20), padx=20)

        # Optionally list employees/attendants
        employees = station_info.get('employees') or []
        if employees:
            emp_text = "Attendants:\n" + "\n".join([f"{e['fname']} {e['lname']} (ID:{e['emp_id']})" for e in employees])
            emp_label = ctk.CTkLabel(self.manual_fill_frame, text=emp_text)
            emp_label.pack(pady=(10, 20), padx=20)

        # Back button
        btn_back = ctk.CTkButton(self.manual_fill_frame, text="Back", command=lambda: self.show_frame(self.customer_station_frame))
        btn_back.pack(side="bottom", anchor="e", padx=20, pady=20)
    
    def _build_shell_go_registration_frame(self):
        '''Build the Shell go+ registration frame'''

        # Clear previous widgets if any
        for widget in self.shell_go_frame.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.shell_go_frame, text="Shell go+ Registration", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(20, 10), padx=20)

        # Content frame for form fields, transparent to blend with parent
        content = ctk.CTkFrame(self.shell_go_frame, fg_color="transparent")
        content.pack(expand=True)
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)

        # (Label, Entry) pairs for registration
        fields = [("Name", "name"),("Lastname", "lastname"),("Address", "address"),("Phone number", "phone"),("Email", "email"),("AFM", "afm"),]

        # Store entry widgets in a dictionary
        self.shellgo_entries = {} # {'name': name_entry_widget, ...}
        for i, (label_text, key) in enumerate(fields):
            lbl = ctk.CTkLabel(content, text=label_text) 
            lbl.grid(row=i, column=0, padx=10, pady=8, sticky="e")
            entry = ctk.CTkEntry(content, placeholder_text=label_text)
            entry.grid(row=i, column=1, padx=10, pady=8, sticky="w")
            self.shellgo_entries[key] = entry

        btn_submit = ctk.CTkButton(self.shell_go_frame, text="Submit", command=self._submit_shell_go_registration)
        btn_submit.pack(pady=10, padx=20)

        # Back button 
        btn_back = ctk.CTkButton(self.shell_go_frame, text="Back", command=lambda: self.show_frame(self.store_payment_frame))
        btn_back.pack(side="bottom", anchor="e", pady=20, padx=20)

    def _submit_shell_go_registration(self):
        '''Handle Shell go+ registration submission when button is clicked'''

        keys_to_be_included = ["name", "lastname", "address", "phone", "email", "afm"]
        if all(self.shellgo_entries[k].get().strip() for k in keys_to_be_included): # checks if all fields are filled from user
            
            # Generate a random 7-digit Shell Go+ card number
            card_number = self.generate_card_number()
            
            try:
                # Create customer in database
                customer_id = dbop.insert_customer(
                    fname=self.shellgo_entries['name'].get().strip(),
                    lname=self.shellgo_entries['lastname'].get().strip(),
                    address=self.shellgo_entries['address'].get().strip(),
                    phone_number=self.shellgo_entries['phone'].get().strip(),
                    email=self.shellgo_entries['email'].get().strip(),
                    tax_id=self.shellgo_entries['afm'].get().strip(),
                    payment_type="Shell Go+",
                    delivery_address=None,
                    fuel_card=None,
                    company_name=None,
                    card_number=card_number
                )
                
                if customer_id: # if insertion was successful
                    # Store customer info for current session
                    self.customer_id_for_points = customer_id
                    self.customer_has_card = True
                    self.customer_card_number = card_number
                    
                    # Get customer name for display
                    customer_name = dbop.get_customer_name(customer_id)
                    
                    # Display the card window
                    self.show_card_window(card_number, customer_name)
                    
                    messagebox.showinfo("Shell go+", f"Registration successful!\n\nYour Shell Go+ card number is: {card_number}\n\nUse this card number when adding points at fuel stations or stores.\nThe card number is also displayed in a separate window.")
                else:
                    messagebox.showerror("Shell go+", "Registration failed. Could not create customer record.")
            except Exception as e:
                print(f"Registration error: {e}")
            
            # Return to the appropriate frame based on context
            back_frame = self.store_payment_frame if self.store_total_cost > 0 else self.payment_method_frame
            self.show_frame(back_frame)
        else:
            messagebox.showwarning("Shell go+", "Please fill in all fields.")

    def _build_add_points_frame(self):
        for widget in self.add_points_frame.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.add_points_frame, text="Enter card number", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(30, 10), padx=20)

        self.card_number_entry = ctk.CTkEntry(self.add_points_frame, placeholder_text="Card number")
        self.card_number_entry.pack(pady=8, padx=20)

        btn_submit = ctk.CTkButton(self.add_points_frame, text="Submit", command=self._submit_add_points)
        btn_submit.pack(pady=8, padx=20)

        # Determine where to go back to based on context
        back_frame = self.store_payment_frame if hasattr(self, 'store_total_cost') and self.store_total_cost > 0 else self.payment_method_frame
        btn_back = ctk.CTkButton(self.add_points_frame, text="Back", command=lambda: self.show_frame(back_frame))
        btn_back.pack(side="bottom", anchor="e", padx=20, pady=20)

    def _submit_add_points(self):
        number = self.card_number_entry.get().strip() if hasattr(self, "card_number_entry") else ""
        if number:
            # Look up customer by card number
            customer = dbop.get_customer_by_card_number(number)
            
            if customer:
                # Store the card number and customer info
                self.customer_card_number = number
                self.customer_has_card = True
                self.customer_id_for_points = customer['customer_id']
                self.current_customer_points = customer['points']
                
                # Calculate points to be earned from current purchase
                points_to_earn = 0
                if hasattr(self, 'selected_fuel'):
                    # Determine the amount based on context
                    if hasattr(self, 'automated_amount_total'):
                        # Automated station
                        amount = self.automated_amount_total
                    elif hasattr(self, 'non_auto_mode'):
                        # Non-automated station
                        if self.non_auto_mode == 'euros':
                            amount_text = self.amount_entry.get().strip() if hasattr(self, 'amount_entry') else "0"
                            amount = float(amount_text) if amount_text else 0.0
                        elif self.non_auto_mode == 'fill':
                            amount = self.fill_total_cost if hasattr(self, 'fill_total_cost') else 0.0
                        else:  # liters
                            qty_text = self.qty_entry.get().strip() if hasattr(self, 'qty_entry') else "0"
                            qty_liters = float(qty_text) if qty_text else 0.0
                            price_per_liter = self.selected_fuel.get('price_per_liter', 1.0)
                            amount = qty_liters * price_per_liter
                    else:
                        amount = 0.0
                    
                    # Clamp to tank capacity if applicable
                    if hasattr(self, 'customer_tank_capacity'):
                        price = self.selected_fuel.get('price_per_liter', 1.0)
                        max_euros = self.customer_tank_capacity * price
                        amount = min(amount, max_euros)
                    
                    # Calculate points for FUEL: liters × points_per_liter
                    if amount > 0:
                        price = self.selected_fuel.get('price_per_liter', 1.0)
                        liters = amount / price if price else 0.0
                        points_per_liter = self.selected_fuel.get('points_per_liter', 0)
                        points_to_earn = int(liters * points_per_liter)
                    else:
                        points_to_earn = 0
                
                customer_name = f"{customer['fname']} {customer['lname']}".strip()
                
                # Check if customer has at least 250 points for redemption
                if self.current_customer_points >= 250:
                    # Show redemption dialog
                    self._show_points_redemption_dialog(customer_name, self.current_customer_points, points_to_earn)
                else:
                    # Just show welcome message with points to earn
                    messagebox.showinfo("Add Points", f"Card number found!\nWelcome back, {customer_name}!\nPoints to earn: {points_to_earn}")
                
                # Return to the appropriate frame based on context
                if hasattr(self, 'store_total_cost') and self.store_total_cost > 0:
                    # Coming from store - rebuild and show store payment frame
                    self._build_store_payment_frame()
                    self.show_frame(self.store_payment_frame)
                else:
                    # Coming from fuel purchase - show payment method frame
                    self.show_frame(self.payment_method_frame)
            else:
                messagebox.showerror("Add Points", f"Card number '{number}' not found.\nPlease register first through Shell Go+ Registration.")
                return
        else:
            messagebox.showwarning("Add Points", "Please enter a card number.")

    def _show_points_redemption_dialog(self, customer_name, customer_points, points_to_earn):
        '''Show dialog for points redemption if customer has at least 250 points'''
        # Calculate available euros from points (250 points = 1 euro)
        euros_available = customer_points / 250.0
        
        # Create a new window for redemption
        redemption_window = ctk.CTkToplevel(self)
        redemption_window.title("Points Redemption")
        redemption_window.geometry("400x300")
        redemption_window.transient(self)
        redemption_window.grab_set()  # Make window modal
        
        # Center the window
        redemption_window.update_idletasks()
        x = (redemption_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (redemption_window.winfo_screenheight() // 2) - (300 // 2)
        redemption_window.geometry(f"400x300+{x}+{y}")
        
        # Title
        title_label = ctk.CTkLabel(
            redemption_window,
            text="Points Redemption",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Welcome message
        welcome_label = ctk.CTkLabel(
            redemption_window,
            text=f"Welcome back, {customer_name}!",
            font=ctk.CTkFont(size=14)
        )
        welcome_label.pack(pady=5)
        
        # Points info
        points_label = ctk.CTkLabel(
            redemption_window,
            text=f"You have {customer_points} points",
            font=ctk.CTkFont(size=13)
        )
        points_label.pack(pady=5)
        
        earn_label = ctk.CTkLabel(
            redemption_window,
            text=f"You will earn {points_to_earn} points from this purchase",
            font=ctk.CTkFont(size=13)
        )
        earn_label.pack(pady=5)
        
        # Redemption offer
        redemption_label = ctk.CTkLabel(
            redemption_window,
            text=f"You can redeem {euros_available:.2f} euros discount",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="green"
        )
        redemption_label.pack(pady=15)
        
        # Question
        question_label = ctk.CTkLabel(
            redemption_window,
            text="Do you want to redeem for discount?",
            font=ctk.CTkFont(size=13)
        )
        question_label.pack(pady=10)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(redemption_window, fg_color="transparent")
        button_frame.pack(pady=20)
        
        def on_yes():
            self.points_redeemed = customer_points
            self.euros_discount = euros_available
            self.redemption_approved = True
            redemption_window.destroy()
        
        def on_no():
            self.redemption_approved = False
            self.points_redeemed = 0
            self.euros_discount = 0
            redemption_window.destroy()
        
        yes_button = ctk.CTkButton(
            button_frame,
            text="Yes, Redeem",
            command=on_yes,
            width=120,
            fg_color="green"
        )
        yes_button.pack(side="left", padx=10)
        
        no_button = ctk.CTkButton(
            button_frame,
            text="No, Thanks",
            command=on_no,
            width=120
        )
        no_button.pack(side="left", padx=10)
        
        # Wait for window to close
        self.wait_window(redemption_window)

    def _on_non_auto_option_selected(self, mode):
        # Set the selected mode
        self.non_auto_mode = mode
        
        if mode == 'fill':
            # For fill mode, go directly to fuel selection, then show fill summary
            self._build_fill_up_frame()
            self.show_frame(self.fill_up_frame)
        else:
            # Continue to fuel selection for liters/euros mode
            self._build_fill_up_frame()
            self.show_frame(self.fill_up_frame)

    def update_from_euros_entry(self):
        """When user types euros (non-automated + euros mode): compute liters and points."""
        try:
            amt_text = self.amount_entry.get().strip()
            euros = float(amt_text) if amt_text else 0.0
            price = self.selected_fuel['price_per_liter']
            liters = euros / price 

            # Show computed liters
            self.derived_liters_label.configure(text=f"{liters:.2f} L")

            # Points based on liters
            points_per_liter = self.selected_fuel.get('points_per_liter', 0)
            points = int(liters * points_per_liter)
            self.points_earned_label.configure(text=f"{points} points")
            
        except ValueError:
            self.derived_liters_label.configure(text="0.00 L")
            self.points_earned_label.configure(text="0 points")



    def update_from_liters_entry(self):
        """Update total amount and points from entry field for non-automated stations (liters mode)"""
        try:
            qty_text = self.qty_entry.get().strip()
            if not qty_text:
                qty = 0.0
            else:
                qty = float(qty_text)
            
            price = self.selected_fuel['price_per_liter']
            total = qty * price # Calculate total amount of money
            self.total_amount_label.configure(text=f"{total:.2f}€")
            
            #  Calculate points
            points_per_liter = self.selected_fuel.get('points_per_liter', 0)
            points = int(qty * points_per_liter) 
            self.points_earned_label.configure(text=f"{points} points")
        except ValueError:
            # Invalid number entered
            self.total_amount_label.configure(text="0.00€")

    def _submit_add_points(self):
        number = self.card_number_entry.get().strip() if hasattr(self, "card_number_entry") else ""
        if number:
            # Look up customer by card number
            customer = dbop.get_customer_by_card_number(number)
            
            if customer:
                # Store the card number and customer info
                self.customer_card_number = number
                self.customer_has_card = True
                self.customer_id_for_points = customer['customer_id']
                
                customer_name = f"{customer['fname']} {customer['lname']}".strip()
                messagebox.showinfo("Add Points", f"Card number found!\nWelcome back, {customer_name}!\nPoints: {customer['points']}")
            else:
                messagebox.showerror("Add Points", f"Card number '{number}' not found.\nPlease register first through Shell Go+ Registration.")
                return
            
            self.show_frame(self.payment_method_frame)
        else:
            messagebox.showwarning("Add Points", "Please enter a card number.")

    def show_frame(self, frame):
        """Raise the given frame to the top to make it visible."""
        frame.tkraise()

    def _reset_customer_session(self):
        """Reset all customer session variables after a transaction"""
        self.customer_tank_capacity = 0
        self.redemption_approved = False
        self.points_redeemed = 0
        self.euros_discount = 0.0
        self.customer_has_card = False
        self.customer_id_for_points = None
        self.automated_amount_total = 0.0
        self.selected_pump_id = None
        self.selected_tank_id = None
        self.selected_store_items = {}
        self.store_total_cost = 0.0

    def generate_card_number(self):
        """Generate a random 7-digit card number"""
        return str(random.randint(0, 9999999)).zfill(7) # Ensure it's 7 digits by padding leading zeros if needed

    def show_card_window(self, card_number, customer_name):
        """Create and display a card window showing card number and customer name. Only closes when application closes."""

        # Create new card window
        self.card_window = ctk.CTkToplevel(self)
        self.card_window.title("Shell Go+ Card Number")
        self.card_window.geometry("400x200")
        
        # Remove close button by overriding protocol
        self.card_window.protocol("WM_DELETE_WINDOW", lambda: None) # Disable close button
        
        # Title
        title = ctk.CTkLabel(self.card_window,text="Your Shell Go+ Card Number", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(20, 10))
        
        # Customer name
        name_label = ctk.CTkLabel(self.card_window, text=f"Customer: {customer_name}", font=ctk.CTkFont(size=12))
        name_label.pack(pady=5)
        
        # Card number in large font, with green color 
        card_display = ctk.CTkLabel(self.card_window,text=card_number, font=ctk.CTkFont(size=24, weight="bold"),text_color="#00AA00")
        card_display.pack(pady=20)
        
        # Information text
        info_label = ctk.CTkLabel(self.card_window,text="This window will close when you close the application",font=ctk.CTkFont(size=10),text_color="gray")
        info_label.pack(pady=10)

    #BUTTON FUNCTIONS

    #BACK
    def btn_back_func(self, frame):
        self.show_frame(frame)
    
    #SHOW ALL STATIONS 
    def btn_show_stations_func(self, frame):
        self.show_frame(frame)
        #dbop.print_stations()


    #SHOW TRANSACTION HISTORY
    def btn_show_transaction_history_func(self, frame):
        self.show_frame(frame)
        pass
    

    #GO TO SELECTED STATION FOR ADMIN OR CUSTOMER
    def go_to_station_func(self, station, frame):
        if frame == self.admin_station_frame:
            self.current_admin_station = station
            self._build_admin_station_frame(station)
        elif frame == self.customer_station_frame:
            self.current_customer_station = station
            # Generate the remaining fuel tank capacity available for refueling using Gaussian distribution (mean=25, std=10, min=10, max=80)
            self.customer_tank_capacity = max(10, min(80, np.random.normal(25, 10)))
            # Initialize customer_has_card flag to False when entering a station
            self.customer_has_card = False
            self._build_customer_station_frame()
        self.show_frame(frame)

    def btn_fill_up_func(self):
        '''Decide next frame based on station automation status'''
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        is_automated = station_info.get('automated', True) # check whether the station is automated

        if not is_automated:
            # Non-automated: go to non-automated stations fill options frame like liters/euros/fill 
            self._build_non_auto_fill_options_frame()
            self.show_frame(self.non_auto_fill_options_frame)
        else:
            # Automated: proceed with existing fuel selection
            self._build_fill_up_frame()
            self.show_frame(self.fill_up_frame)

    def btn_go_to_store_func(self):
        '''Go to store frame from customer station frame'''
        self.selected_store_items = {}  # Track selected items: {product_name: {'price': price, 'quantity': count}}
        self._build_store_frame()
        self.show_frame(self.store_frame)

    def select_fuel(self, fuel):
        '''Handle fuel selection and navigate to next frame based on station type and mode'''
        # in automated stations the next frame is payment method selection
        # in non-automated stations the next frame is either fuel purchase (liters/euros) or fill summary (fill mode)

        self.selected_fuel = fuel # Store selected fuel for later use

        # Get station info and find which pump is being used
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        
        # Find the pump_id for this fuel selection using fuel_type from station_info
        fuel_type = fuel.get('fuel_type', '')
        self.selected_pump_id, self.selected_tank_id = self.find_pump_and_tank_for_fuel(fuel_type, station_info)
        
        # Check if station is automated
        is_automated = station_info.get('automated', False)
        
        if is_automated:
            # For automated: go to payment method selection
            self._build_payment_method_frame_automated()
            self.show_frame(self.payment_method_frame)
        else:
            # For non-automated: check if it's fill mode
            if self.non_auto_mode == 'fill':
                # Calculate fill amount using tank capacity
                price_per_liter = fuel.get('price_per_liter', 0)

                # cost = liters to fill × price_per_liter
                self.fill_total_cost = self.customer_tank_capacity * price_per_liter

                # Calculate points for FUEL: liters × points_per_liter
                points_per_liter = fuel.get('points_per_liter', 0)
                self.fill_points = int(self.customer_tank_capacity * points_per_liter)
                
                # Show fill summary frame
                self._build_fill_summary_frame()
                self.show_frame(self.fill_summary_frame)
            else:
                # For liters/euros mode: go to fuel purchase frame
                self._build_fuel_purchase_frame()
                self.show_frame(self.fuel_purchase_frame)


    def _build_store_frame(self):
        '''Store frame with category buttons and product selection'''
        for widget in self.store_frame.winfo_children():
            widget.destroy()

        # configure frame layout

        self.store_frame.grid_rowconfigure(0, weight=0)  # Station name
        self.store_frame.grid_rowconfigure(1, weight=0)  # Title row
        self.store_frame.grid_rowconfigure(2, weight=0)  # Category buttons row
        self.store_frame.grid_rowconfigure(3, weight=1)  # Products scrollable frame
        self.store_frame.grid_rowconfigure(4, weight=0)  # Back/Continue buttons row
        self.store_frame.grid_columnconfigure(0, weight=1)

        # Display station name at the top 
      
        station_info = dbop.get_admin_station_info(self.current_customer_station)
        station_name = station_info.get('name', 'Unknown Station') 
        station_label = ctk.CTkLabel(self.store_frame, text=station_name,font=ctk.CTkFont(size=16, weight="bold"))
        station_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        # Title "Store"
        title = ctk.CTkLabel(self.store_frame, text="Store", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=1, column=0, padx=20, pady=(5, 10))

        # Category buttons frame
        category_frame = ctk.CTkFrame(self.store_frame, fg_color="transparent")
        category_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        category_frame.grid_columnconfigure(0, weight=1)

        # Fetch store products for this station from DB
        self.store_products_by_category = dbop.get_store_products_for_station(self.current_customer_station)
        categories = list(self.store_products_by_category.keys())
        self.category_buttons = {}

        for i, category in enumerate(categories): # create a button for each category and place them next to each other
            # when button gets clicked it shows all the corresponding products in the scrollable frame below
            btn = ctk.CTkButton(category_frame, text=category, command=lambda c=category: self._show_store_products(c), height=30) 
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            category_frame.grid_columnconfigure(i, weight=1) # make all buttons expand equally
            self.category_buttons[category] = btn # {category_name: button_widget}

        # Products scrollable frame
        self.store_products_frame = ctk.CTkScrollableFrame(self.store_frame, fg_color=MAIN_FRAME_COLOUR,label_text="Products")
        self.store_products_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.store_products_frame.grid_columnconfigure(0, weight=1)

        # Bottom buttons frame (for back and continue)
        bottom_frame = ctk.CTkFrame(self.store_frame, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        btn_back = ctk.CTkButton(bottom_frame, text="Back", command=lambda: self.show_frame(self.customer_station_frame))
        btn_back.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        btn_continue = ctk.CTkButton(bottom_frame, text="Continue", command=self._continue_store_purchase)
        btn_continue.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # Show first category by default
        self._show_store_products(categories[0])


    def _show_store_products(self, category):
        '''Display products for the selected category in the scrollable frame'''
        # Store current category for refresh
        self.current_store_category = category
        
        # Clear previous products
        for widget in self.store_products_frame.winfo_children():
            widget.destroy()


        # Get products for this category
        category_products = self.store_products_by_category.get(category, {}) # {product_name: {price: , points: , stock: }}

        if not category_products:
            empty_label = ctk.CTkLabel(self.store_products_frame, text="No products available", font=ctk.CTkFont(size=12))
            empty_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return

        for idx, (product_name, product_data) in enumerate(category_products.items()):
            price = product_data['price']
            points = product_data['points']
            stock = product_data['stock']
            
            # Get selected quantity if any
            # selected_store_items is filled in _add_product_quantity function and holds the selected products and their quantities

            quantity = self.selected_store_items.get(product_name, {}).get('quantity', 0) # selected_store_items = {product_name: {'price': price, 'quantity': count}}

            # Product row frame, transparent to blend with parent frame
            product_row = ctk.CTkFrame(self.store_products_frame, fg_color="transparent")
            product_row.grid(row=idx, column=0, sticky="ew", padx=10, pady=5)
            product_row.grid_columnconfigure(0, weight=1)
            product_row.grid_columnconfigure(1, weight=0)
            product_row.grid_columnconfigure(2, weight=0)

            # Product info (name, price, and stock)
            product_info = f"{product_name} - {price:.2f} € (Stock: {stock})"
            product_label = ctk.CTkLabel(product_row, text=product_info, font=ctk.CTkFont(size=12))
            product_label.grid(row=0, column=0, sticky="w")

            # Quantity display/button - only show if quantity > 0
            if quantity > 0:
                qty_label = ctk.CTkLabel(product_row, text=f"({quantity})", font=ctk.CTkFont(size=12, weight="bold"),text_color="green") # shows the quantity of each product, if selected
                qty_label.grid(row=0, column=1, padx=(10, 0))

            # Select button
            select_btn = ctk.CTkButton(product_row, text="+", width=40, command=lambda pn=product_name, p=price: self._add_product_quantity(pn, p)) # + button to add one more of this product
            select_btn.grid(row=0, column=2, padx=(10, 0))

    def _add_product_quantity(self, product_name, price):
        '''Add one to the product quantity'''

        if product_name in self.selected_store_items: # check if item already exists in selected items, so that we can increment quantity
            # Item already exists, increment quantity
            self.selected_store_items[product_name]['quantity'] += 1
        else:
            # if it doesn't exist already, it's a new item, so we initialize quantity to 1
            self.selected_store_items[product_name] = {'price': price, 'quantity': 1}

        # Return to the same category view to refresh quantities in _show_store_products function
        self._show_store_products(self.current_store_category)


    def _continue_store_purchase(self):
        '''Go to store payment frame with selected items'''
        if not self.selected_store_items:
            messagebox.showwarning("No Items", "Please select at least one item.")
            return

        # Calculate total cost based on price * quantity for each item
        self.store_total_cost = sum(item['price'] * item['quantity'] for item in self.selected_store_items.values())
        self._build_store_payment_frame()
        self.show_frame(self.store_payment_frame)

    def _build_store_payment_frame(self):
        '''Store payment frame showing total, payment method, and points options'''
        for widget in self.store_payment_frame.winfo_children():
            widget.destroy()

        self.store_payment_frame.grid_rowconfigure(0, weight=0)  # Station name
        self.store_payment_frame.grid_rowconfigure(1, weight=0)  # Title
        self.store_payment_frame.grid_rowconfigure(2, weight=0)  # Total amount
        self.store_payment_frame.grid_rowconfigure(3, weight=0)  # Payment method
        self.store_payment_frame.grid_rowconfigure(4, weight=0)  # Points buttons
        self.store_payment_frame.grid_rowconfigure(5, weight=1)  # Spacer
        self.store_payment_frame.grid_rowconfigure(6, weight=0)  # Bottom buttons
        self.store_payment_frame.grid_columnconfigure(0, weight=1)

        # Display station name at the top (if station is selected)
        if hasattr(self, 'current_customer_station'):
            station_info = dbop.get_admin_station_info(self.current_customer_station)
            station_name = station_info.get('name', 'Unknown Station') if station_info else 'Unknown Station'
            station_label = ctk.CTkLabel(
                self.store_payment_frame, 
                text=station_name,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            station_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        # Title
        title = ctk.CTkLabel(self.store_payment_frame, text="Store Payment", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=1, column=0, padx=20, pady=(5, 10))

        # Total amount section
        total_frame = ctk.CTkFrame(self.store_payment_frame, fg_color="transparent")
        total_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        total_frame.grid_columnconfigure(0, weight=0)
        total_frame.grid_columnconfigure(1, weight=1)

        total_label = ctk.CTkLabel(total_frame, text="Total Amount:", font=ctk.CTkFont(size=14))
        total_label.grid(row=0, column=0, padx=(0, 20), sticky="e")

        total_amount_label = ctk.CTkLabel(
            total_frame,
            text=f"€{self.store_total_cost:.2f}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="green"
        )
        total_amount_label.grid(row=0, column=1, sticky="w")

        # Payment method section
        payment_frame = ctk.CTkFrame(self.store_payment_frame, fg_color="transparent")
        payment_frame.grid(row=3, column=0, padx=20, pady=15, sticky="ew")
        payment_frame.grid_columnconfigure(0, weight=0)
        payment_frame.grid_columnconfigure(1, weight=1)

        payment_label = ctk.CTkLabel(payment_frame, text="Payment Method:", font=ctk.CTkFont(size=14))
        payment_label.grid(row=0, column=0, padx=(0, 20), sticky="e")

        self.store_payment_method = ctk.CTkComboBox(
            payment_frame,
            values=["Credit Card", "Debit Card", "Cash", "Mobile Payment"],
            state="readonly"
        )
        self.store_payment_method.set("Credit Card")
        self.store_payment_method.grid(row=0, column=1, sticky="w", padx=(0, 20))

        # Points options section
        points_frame = ctk.CTkFrame(self.store_payment_frame, fg_color="transparent")
        points_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        points_frame.grid_columnconfigure(0, weight=1)
        points_frame.grid_columnconfigure(1, weight=1)

        btn_add_points = ctk.CTkButton(
            points_frame,
            text="Add Points",
            command=lambda: (self._build_add_points_frame(self.store_payment_frame), self.show_frame(self.add_points_frame))
        )
        btn_add_points.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        btn_shell_go = ctk.CTkButton(
            points_frame,
            text="Register in Shell Go+",
            command=lambda: (self._build_shell_go_registration_frame(), self.show_frame(self.shell_go_frame))
        )
        btn_shell_go.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self.store_payment_frame, fg_color="transparent")
        bottom_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        btn_back = ctk.CTkButton(
            bottom_frame,
            text="Back",
            command=lambda: self.show_frame(self.store_frame)
        )
        btn_back.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        btn_confirm = ctk.CTkButton(
            bottom_frame,
            text="Confirm Purchase",
            command=self._confirm_store_purchase
        )
        btn_confirm.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def _confirm_store_purchase(self):
        '''Confirm store purchase and complete transaction'''
        from datetime import datetime
        
        payment_method = self.store_payment_method.get()
        
        # Save transaction to database
        trans_date = datetime.now().timestamp()
        amount_of_money = self.store_total_cost
        
        # Apply points discount if redeemed
        if hasattr(self, 'euros_discount') and self.euros_discount > 0:
            amount_of_money = max(0, amount_of_money - self.euros_discount)
        
        # Calculate points: 1 point per euro + 2 bonus points (only if customer has provided card)
        if hasattr(self, 'customer_has_card') and self.customer_has_card:
            if amount_of_money > 0:
                total_points = int(amount_of_money) + 2
            else:
                total_points = 0
            for_cust_id = getattr(self, 'customer_id_for_points', None)
        else:
            total_points = 0
            for_cust_id = None  # Anonymous customer
        
        for_station_id = self.current_customer_station
        
        try:
            trans_id = dbop.insert_transaction(trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {e}")
            return
        
        # Update customer points if they provided card and earned points
        if total_points > 0 and hasattr(self, 'customer_id_for_points'):
            dbop.update_customer_points(self.customer_id_for_points, total_points)
        
        # Redeem points if applicable
        if hasattr(self, 'redemption_approved') and self.redemption_approved and hasattr(self, 'customer_id_for_points'):
            dbop.redeem_points(self.customer_id_for_points, self.points_redeemed)
        
        # Show success message with amount and discount info
        message = f"Payment is successful!\n\nItems Purchased:"
        
        # Debug: verify items dictionary structure
        total_items_count = 0
        for item_name, item_data in self.selected_store_items.items():
            quantity = item_data.get('quantity', 1)
            price = item_data.get('price', 0)
            total_item_cost = quantity * price
            total_items_count += quantity
            message += f"\n  {item_name} (x{quantity}) = €{total_item_cost:.2f}"
        
        message += f"\n\nSubtotal (original): €{self.store_total_cost:.2f}"
        message += f"\nTotal items selected: {total_items_count}"
        message += f"\n\nTotal Amount Paid: €{amount_of_money:.2f}"
        if hasattr(self, 'euros_discount') and self.euros_discount > 0:
            message += f"\nPoints Discount: €{self.euros_discount:.2f}"
        messagebox.showinfo("Payment Successful!", message)
        
        # Reset all customer session data
        self._reset_customer_session()
        
        # Return to customer station frame
        self.show_frame(self.customer_station_frame)

    def _build_transactions_frame(self):
        '''Display all transactions from the database'''
        from datetime import datetime
        
        for widget in self.transactions_frame.winfo_children():
            widget.destroy()

        self.transactions_frame.grid_rowconfigure(0, weight=0)  # Title
        self.transactions_frame.grid_rowconfigure(1, weight=1)  # Transactions scrollable
        self.transactions_frame.grid_rowconfigure(2, weight=0)  # Back button
        self.transactions_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(self.transactions_frame, text="All Transactions", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Get all transactions
        transactions = dbop.get_all_transactions()

        # Scrollable frame for transactions
        scrollable_trans_frame = ctk.CTkScrollableFrame(
            self.transactions_frame,
            fg_color=MAIN_FRAME_COLOUR
        )
        scrollable_trans_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        scrollable_trans_frame.grid_columnconfigure(0, weight=1)

        if transactions:
            for i, trans in enumerate(transactions):
                trans_id, trans_date, amount_of_money, total_points, for_cust_id, payment_method, for_station_id, station_name, fname, lname = trans
                
                # Convert timestamp to readable date
                trans_datetime = datetime.fromtimestamp(trans_date).strftime("%Y-%m-%d %H:%M:%S") if trans_date else "N/A"
                
                # Build customer info with name if available
                if for_cust_id and fname and lname:
                    cust_info = f"Customer: {fname} {lname} (ID: {for_cust_id})"
                elif for_cust_id:
                    cust_info = f"Customer ID: {for_cust_id}"
                else:
                    cust_info = "Anonymous"
                
                station_info = f"Station: {station_name} (ID: {for_station_id})" if station_name else f"Station ID: {for_station_id}"
                trans_info = (
                    f"ID: {trans_id} | Date: {trans_datetime} | Amount: €{amount_of_money:.2f} | "
                    f"Points: {total_points} | {cust_info} | {station_info} | Payment: {payment_method}"
                )
                
                trans_label = ctk.CTkLabel(
                    scrollable_trans_frame,
                    text=trans_info,
                    font=ctk.CTkFont(size=11),
                    justify="left"
                )
                trans_label.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
        else:
            no_trans_label = ctk.CTkLabel(
                scrollable_trans_frame,
                text="No transactions found.",
                font=ctk.CTkFont(size=12)
            )
            no_trans_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Back button
        btn_back = ctk.CTkButton(self.transactions_frame, text="Back", command=lambda: self.show_frame(self.admin_frame))
        btn_back.grid(row=2, column=0, padx=20, pady=20, sticky="se")

    def _build_shell_go_customers_frame(self):
        '''Display all Shell Go+ customers with their points'''
        for widget in self.shell_go_customers_frame.winfo_children():
            widget.destroy()

        self.shell_go_customers_frame.grid_rowconfigure(0, weight=0)  # Title
        self.shell_go_customers_frame.grid_rowconfigure(1, weight=1)  # Customers scrollable
        self.shell_go_customers_frame.grid_rowconfigure(2, weight=0)  # Back button
        self.shell_go_customers_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(self.shell_go_customers_frame, text="Shell Go+ Customers", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Get all points customers
        customers = dbop.get_all_points_customers()

        # Scrollable frame for customers
        scrollable_cust_frame = ctk.CTkScrollableFrame(
            self.shell_go_customers_frame,
            fg_color=MAIN_FRAME_COLOUR
        )
        scrollable_cust_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        scrollable_cust_frame.grid_columnconfigure(0, weight=1)

        if customers:
            for i, customer in enumerate(customers):
                customer_id, fname, lname, points, card_number = customer
                
                # Build customer name
                full_name = f"{fname} {lname}".strip() if (fname or lname) else "Unknown"
                points = points if points else 0
                card_num_display = card_number if card_number else "N/A"
                
                # Build customer info button with card number
                cust_info = f"Card: {card_num_display} | Name: {full_name} | Points: {points}"
                
                cust_button = ctk.CTkButton(
                    scrollable_cust_frame,
                    text=cust_info,
                    font=ctk.CTkFont(size=12),
                    command=lambda cid=customer_id: self._show_customer_details(cid)
                )
                cust_button.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
        else:
            no_cust_label = ctk.CTkLabel(
                scrollable_cust_frame,
                text="No Shell Go+ customers found.",
                font=ctk.CTkFont(size=12)
            )
            no_cust_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Back button
        btn_back = ctk.CTkButton(self.shell_go_customers_frame, text="Back", command=lambda: self.show_frame(self.admin_frame))
        btn_back.grid(row=2, column=0, padx=20, pady=20, sticky="se")

    def _show_customer_details(self, customer_id):
        '''Display detailed customer information in a frame'''
        customer = dbop.get_customer_details(customer_id)
        
        if not customer:
            messagebox.showerror("Error", "Customer information not found.")
            return
        
        # Build the customer details frame
        for widget in self.customer_details_frame.winfo_children():
            widget.destroy()

        self.customer_details_frame.grid_rowconfigure(0, weight=0)  # Title
        self.customer_details_frame.grid_rowconfigure(1, weight=1)  # Details scrollable
        self.customer_details_frame.grid_rowconfigure(2, weight=0)  # Back button
        self.customer_details_frame.grid_columnconfigure(0, weight=1)

        # Title
        full_name = f"{customer.get('fname', '')} {customer.get('lname', '')}".strip()
        title = ctk.CTkLabel(
            self.customer_details_frame,
            text=f"Customer Details - {full_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Scrollable frame for details
        scrollable_details = ctk.CTkScrollableFrame(
            self.customer_details_frame,
            fg_color=MAIN_FRAME_COLOUR
        )
        scrollable_details.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        scrollable_details.grid_columnconfigure(0, weight=0)
        scrollable_details.grid_columnconfigure(1, weight=1)

        # Helper function to add detail rows
        def add_detail_row(row_num, label, value):
            label_widget = ctk.CTkLabel(
                scrollable_details,
                text=f"{label}:",
                font=ctk.CTkFont(size=12),
                justify="left",
                text_color="black"
            )
            label_widget.grid(row=row_num, column=0, sticky="w", padx=(10, 20), pady=5)

            value_str = str(value) if value is not None else "N/A"
            value_widget = ctk.CTkLabel(
                scrollable_details,
                text=value_str,
                font=ctk.CTkFont(size=12),
                justify="left",
                text_color="black"
            )
            value_widget.grid(row=row_num, column=1, sticky="w", padx=(20, 10), pady=5)

        # Add all customer details
        points = customer.get('points', 0) or 0
        
        add_detail_row(0, "Customer ID", customer.get('customer_id', 'N/A'))
        add_detail_row(1, "Name", full_name)
        add_detail_row(2, "Card Number", customer.get('card_number', 'N/A'))
        add_detail_row(3, "Points", points)
        add_detail_row(4, "Address", customer.get('address', 'N/A'))
        add_detail_row(5, "Delivery Address", customer.get('delivery_address', 'N/A'))
        add_detail_row(6, "Phone", customer.get('phone_number', 'N/A'))
        add_detail_row(7, "Email", customer.get('email', 'N/A'))
        add_detail_row(8, "Tax ID", customer.get('tax_id', 'N/A'))
        add_detail_row(9, "Payment Type", customer.get('payment_type', 'N/A'))
        add_detail_row(10, "Company Name", customer.get('company_name', 'N/A'))
        add_detail_row(11, "Fuel Card", customer.get('fuel_card', 'N/A'))
        add_detail_row(12, "Anonymous", customer.get('anonymous', 'N/A'))

        # Back button
        btn_back = ctk.CTkButton(
            self.customer_details_frame,
            text="Back",
            command=lambda: self.show_frame(self.shell_go_customers_frame)
        )
        btn_back.grid(row=2, column=0, padx=20, pady=20, sticky="se")

        # Show the frame
        self.show_frame(self.customer_details_frame)




if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()