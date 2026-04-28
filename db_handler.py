from MARIADB_CREDS import DB_CONFIG
from mariadb import connect
from models.RentalHistory import RentalHistory
from models.Waitlist import Waitlist
from models.Item import Item
from models.Rental import Rental
from models.Customer import Customer
from datetime import date, timedelta


conn = connect(user=DB_CONFIG["username"], password=DB_CONFIG["password"], host=DB_CONFIG["host"],
               database=DB_CONFIG["database"], port=DB_CONFIG["port"])


cur = conn.cursor()


def add_item(new_item: Item = None):
    """
    new_item - An Item object containing a new item to be inserted into the DB in the item table.
        new_item and its attributes will never be None.
    """

    # Get new date for rec_start_date
    new_date = f"{new_item.start_year}-01-01"

    # Get the max i_item_sk and add 1 to get the new i_item_sk
    cur.execute("SELECT COALESCE(MAX(i_item_sk), 0) FROM item")
    new_sk = cur.fetchone()[0] + 1
    cur.execute("INSERT INTO item (i_item_sk, i_item_id, i_rec_start_date, i_product_name, i_brand, i_class, i_category, i_manufact, i_current_price, i_num_owned) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_sk, new_item.item_id, new_date, new_item.product_name, new_item.brand, new_item.item_class, new_item.category, new_item.manufact, new_item.current_price, new_item.num_owned))


def add_customer(new_customer: Customer = None):

    """
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    cur.execute("SELECT COALESCE(MAX(c_customer_sk), 0) FROM customer")
    new_sk = cur.fetchone()[0] + 1

    cur.execute("SELECT COALESCE(MAX(ca_address_sk), 0) FROM customer_address")
    new_addr_sk = cur.fetchone()[0] + 1
    # split new_customer.name to get first and last name
    first_name, last_name = new_customer.name.split(" ", 1)

    # Parse address
    street, city, state_zip = [
        part.strip() for part in new_customer.address.split(",")
    ]

    street_number, street_name = street.split(" ", 1)
    state, zip_code = state_zip.split(" ", 1)

    cur.execute("INSERT INTO customer_address (ca_address_sk, ca_street_number, ca_street_name, ca_city, ca_state, ca_zip) VALUES (?, ?, ?, ?, ?, ?)",
                (new_addr_sk, street_number, street_name, city, state, zip_code))


    cur.execute("INSERT INTO customer (c_customer_sk, c_customer_id, c_first_name, c_last_name, c_email_address, c_current_addr_sk) VALUES (?, ?, ?, ?, ?, ?)",
                (new_sk, new_customer.customer_id, first_name, last_name, new_customer.email, new_addr_sk))


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    if new_customer.name is not None:
        first_name, last_name = new_customer.name.split(" ", 1)

        cur.execute("UPDATE customer SET c_first_name = ?, c_last_name = ? WHERE c_customer_id = ?",
                    (first_name, last_name, original_customer_id))

    if new_customer.email is not None:
        cur.execute("UPDATE customer SET c_email_address = ? WHERE c_customer_id = ?",
                    (new_customer.email, original_customer_id))
    if new_customer.address is not None:
        street, city, state_zip = [
            part.strip() for part in new_customer.address.split(",")
    ]
        street_number, street_name = street.split(" ", 1)
        state, zip_code = state_zip.split(" ", 1)

        cur.execute("UPDATE customer_address SET ca_street_number = ?, ca_street_name = ?, ca_city = ?, ca_state = ?, ca_zip = ? WHERE ca_address_sk = (SELECT c_current_addr_sk FROM customer WHERE c_customer_id = ?)",
                (street_number, street_name, city, state, zip_code, original_customer_id))
    
    if new_customer.customer_id is not None:
        cur.execute("UPDATE customer SET c_customer_id = ? WHERE c_customer_id = ?",
                    (new_customer.customer_id, original_customer_id))


def rent_item(item_id: str = None, customer_id: str = None):
    """
    item_id - A string containing the Item ID for the item being rented.
    customer_id - A string containing the customer id of the customer renting the item.
    """
    # todays date
    today = date.today().isoformat()

    # due date is 14 days from today
    due_date = (date.today() + timedelta(days=14)).isoformat()

    # Inserts a row into rental with rental_date = today and due_date = today + 14 days
    cur.execute("INSERT INTO rental (rental_date, due_date, item_id, customer_id) VALUES (?, ?, ?, ?)",
                 (today, due_date, item_id, customer_id))


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    # Inserts a new row with place_in_line = line_length + 1. Returns the new place_in_line.
    place_in_line = line_length(item_id) + 1
    cur.execute("INSERT INTO waitlist (item_id, customer_id, place_in_line) VALUES (?, ?, ?)", (item_id, customer_id, place_in_line))
    # return the new place in line
    return place_in_line

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    # Remove the person at position 1
    cur.execute("DELETE FROM waitlist WHERE item_id = ? AND place_in_line = 1", (item_id,))

    # Shift everyone else down by 1
    cur.execute("UPDATE waitlist SET place_in_line = place_in_line - 1 WHERE item_id = ? AND place_in_line > 1", (item_id,))



def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """

    # set return_date to today’s date.
    return_date = date.today().isoformat()
    
    # Move the rental record from rental to rental_history
    cur.execute("INSERT INTO rental_history (rental_date, due_date, return_date, item_id, customer_id) SELECT rental_date, due_date, ?, item_id, customer_id FROM rental WHERE item_id = ? AND customer_id = ?",
                (return_date, item_id, customer_id))
    cur.execute("DELETE FROM rental WHERE item_id = ? AND customer_id = ?", (item_id, customer_id))


def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
  # Get the current due date for rental
    cur.execute("SELECT due_date FROM rental WHERE item_id = ? AND customer_id = ?", (item_id, customer_id))

    row = cur.fetchone()
    current_due_date = date.fromisoformat(str(row[0]))

    # Add 14 days to the current due date
    new_due_date = (current_due_date + timedelta(days=14)).isoformat()

    # Update the rental record with the new due date
    cur.execute("UPDATE rental SET due_date = ? WHERE item_id = ? AND customer_id = ?", (new_due_date, item_id, customer_id))


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    query = "SELECT i_item_id, i_product_name, i_brand, i_class, i_category, i_manufact, i_current_price, YEAR(i_rec_start_date), i_num_owned FROM item"

    conditions = []
    params = []

    # Add attribute filters
    if filter_attributes is not None:
        op = "LIKE" if use_patterns else "="
        def x(s):
            return f"%{s}%" if use_patterns else s
        if filter_attributes.item_id is not None:
            conditions.append(f"i_item_id {op} ?")
            params.append(x(filter_attributes.item_id))

        if filter_attributes.product_name is not None:
            conditions.append(f"i_product_name {op} ?")
            params.append(x(filter_attributes.product_name))
            
        if filter_attributes.brand is not None:
            conditions.append(f"i_brand {op} ?")
            params.append(x(filter_attributes.brand))

        if filter_attributes.item_class is not None:
            conditions.append(f"i_class {op} ?")
            params.append(x(filter_attributes.item_class))

        if filter_attributes.category is not None:
            conditions.append(f"i_category {op} ?")
            params.append(x(filter_attributes.category))
            
        if filter_attributes.manufact is not None:
            conditions.append(f"i_manufact {op} ?")
            params.append(x(filter_attributes.manufact))

        if filter_attributes.current_price not in (None, -1):
            conditions.append("i_current_price = ?")
            params.append(filter_attributes.current_price)

        if filter_attributes.start_year not in (None, -1):
            conditions.append("YEAR(i_rec_start_date) = ?")
            params.append(filter_attributes.start_year)

        if filter_attributes.num_owned not in (None, -1):
            conditions.append("i_num_owned = ?")
            params.append(filter_attributes.num_owned)

    # Add price range conditions
    if min_price != -1:
        conditions.append("i_current_price >= ?")
        params.append(min_price)
    if max_price != -1:
        conditions.append("i_current_price <= ?")
        params.append(max_price)

    # Add start year range conditions
    if min_start_year != -1:
        conditions.append("YEAR(i_rec_start_date) >= ?")
        params.append(min_start_year)
    if max_start_year != -1:
        conditions.append("YEAR(i_rec_start_date) <= ?")
        params.append(max_start_year)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur.execute(query, params)
    rows = cur.fetchall()
   
    return [
        Item(
            item_id=row[0].strip() if row[0] is not None else None, 
            product_name=row[1].strip() if row[1] is not None else None, 
            brand=row[2].strip() if row[2] is not None else None, 
            item_class=row[3].strip() if row[3] is not None else None, 
            category=row[4].strip() if row[4] is not None else None, 
            manufact=row[5].strip() if row[5] is not None else None, 
            current_price=row[6], start_year=row[7], num_owned=row[8]
            ) 
        for row in rows
    ]

def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    query = "SELECT c_customer_id, CONCAT(c_first_name, ' ', c_last_name) AS name, c_email_address, CONCAT(ca_street_number, ' ', ca_street_name, ', ', ca_city, ', ', ca_state, ' ', ca_zip) AS address FROM customer JOIN customer_address ON c_current_addr_sk = ca_address_sk"
    
    conditions = []
    params = []

    # Add attribute filters 
    if filter_attributes is not None:
        op = "LIKE" if use_patterns else "="
        def x(s):
            return f"%{s}%" if use_patterns else s
        if filter_attributes.customer_id is not None:
            conditions.append(f"c_customer_id {op} ?")
            params.append(x(filter_attributes.customer_id))

        if filter_attributes.name is not None:
            conditions.append(f"CONCAT(c_first_name, ' ', c_last_name) {op} ?")
            params.append(x(filter_attributes.name))

        if filter_attributes.email is not None:
            conditions.append(f"c_email_address {op} ?")
            params.append(x(filter_attributes.email))

        if filter_attributes.address is not None:
            conditions.append(f"CONCAT(ca_street_number, ' ', ca_street_name, ', ', ca_city, ', ', ca_state, ' ', ca_zip) {op} ?")
            params.append(x(filter_attributes.address))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur.execute(query, params)
    rows = cur.fetchall()

    return [
        Customer(
            customer_id=row[0].strip() if row[0] is not None else None,
            name=row[1].strip() if row[1] is not None else None,
            email=row[2].strip() if row[2] is not None else None,
            address=row[3].strip() if row[3] is not None else None
        )
        for row in rows
    ]

def get_filtered_rentals(filter_attributes: Rental = None,
                         min_rental_date: str = None,
                         max_rental_date: str = None,
                         min_due_date: str = None,
                         max_due_date: str = None) -> list[Rental]:
    """
    Returns a list of Rental objects matching the filters.
    """
    query = "SELECT rental_date, due_date, item_id, customer_id FROM rental"

    conditions = []
    params = []

    # Add attribute filters
    if filter_attributes is not None:
        if filter_attributes.rental_date is not None:
            conditions.append("rental_date = ?")
            params.append(filter_attributes.rental_date)

        if filter_attributes.due_date is not None:
            conditions.append("due_date = ?")
            params.append(filter_attributes.due_date)

        if filter_attributes.item_id is not None:
            conditions.append("item_id = ?")
            params.append(filter_attributes.item_id)

        if filter_attributes.customer_id is not None:
            conditions.append("customer_id = ?")
            params.append(filter_attributes.customer_id)
    
    # Add date range conditions
    if min_rental_date is not None:
        conditions.append("rental_date >= ?")
        params.append(min_rental_date)
    if max_rental_date is not None:
        conditions.append("rental_date <= ?")
        params.append(max_rental_date)
    if min_due_date is not None:
        conditions.append("due_date >= ?")
        params.append(min_due_date)
    if max_due_date is not None:
        conditions.append("due_date <= ?")
        params.append(max_due_date)             

    if conditions:
        query += " WHERE " + " AND ".join(conditions)  

    cur.execute(query, params)
    rows = cur.fetchall()

    return [
        Rental(
            rental_date=row[0].isoformat() if row[0] is not None else None,
            due_date=row[1].isoformat() if row[1] is not None else None,
            item_id=row[2].strip() if row[2] is not None else None,
            customer_id=row[3].strip() if row[3] is not None else None
        )
        for row in rows
    ]    
    

def get_filtered_rental_histories(filter_attributes: RentalHistory = None,
                                  min_rental_date: str = None,
                                  max_rental_date: str = None,
                                  min_due_date: str = None,
                                  max_due_date: str = None,
                                  min_return_date: str = None,
                                  max_return_date: str = None) -> list[RentalHistory]:
    """
    Returns a list of RentalHistory objects matching the filters.
    """
    query = "SELECT rental_date, due_date, return_date, item_id, customer_id FROM rental_history"

    conditions = []
    params = []

    # Add attribute filters
    if filter_attributes is not None:
        if filter_attributes.rental_date is not None:
            conditions.append("rental_date = ?")
            params.append(filter_attributes.rental_date)

        if filter_attributes.due_date is not None:
            conditions.append("due_date = ?")
            params.append(filter_attributes.due_date)

        if filter_attributes.return_date is not None:
            conditions.append("return_date = ?")
            params.append(filter_attributes.return_date)

        if filter_attributes.item_id is not None:
            conditions.append("item_id = ?")
            params.append(filter_attributes.item_id)

        if filter_attributes.customer_id is not None:
            conditions.append("customer_id = ?")
            params.append(filter_attributes.customer_id)

    # Add date range conditions
    if min_rental_date is not None:
        conditions.append("rental_date >= ?")
        params.append(min_rental_date)
    if max_rental_date is not None:
        conditions.append("rental_date <= ?")
        params.append(max_rental_date)
    if min_due_date is not None:
        conditions.append("due_date >= ?")
        params.append(min_due_date)
    if max_due_date is not None:
        conditions.append("due_date <= ?")
        params.append(max_due_date)
    if min_return_date is not None:
        conditions.append("return_date >= ?")
        params.append(min_return_date)
    if max_return_date is not None:
        conditions.append("return_date <= ?")
        params.append(max_return_date)  

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cur.execute(query, params)
    rows = cur.fetchall()       
    return [
        RentalHistory(
            rental_date=row[0].isoformat() if row[0] is not None else None,
            due_date=row[1].isoformat() if row[1] is not None else None,
            return_date=row[2].isoformat() if row[2] is not None else None,
            item_id=row[3].strip() if row[3] is not None else None,
            customer_id=row[4].strip() if row[4] is not None else None
        )
        for row in rows
    ]            


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    query = "SELECT item_id, customer_id, place_in_line FROM waitlist"

    conditions = []
    params = []

    # Add attribute filters
    if filter_attributes is not None:
        if filter_attributes.item_id is not None:
            conditions.append(f"item_id = ?")
            params.append(filter_attributes.item_id)

        if filter_attributes.customer_id is not None:
            conditions.append(f"customer_id = ?")
            params.append(filter_attributes.customer_id)

        if filter_attributes.place_in_line not in (None, -1):
            conditions.append("place_in_line = ?")
            params.append(filter_attributes.place_in_line)

    # Add place_in_line range conditions
    if min_place_in_line != -1:
        conditions.append("place_in_line >= ?")
        params.append(min_place_in_line)
    if max_place_in_line != -1:
        conditions.append("place_in_line <= ?")
        params.append(max_place_in_line)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cur.execute(query, params)
    rows = cur.fetchall()
    return [
        Waitlist(
            item_id=row[0].strip() if row[0] is not None else None,
            customer_id=row[1].strip() if row[1] is not None else None,
            place_in_line=row[2]
        )
        for row in rows
    ]


def number_in_stock(item_id: str = None) -> int:
    """
    Returns num_owned - active rentals. Returns -1 if item doesn't exist.
    """
    # check if item exists
    cur.execute("SELECT i_num_owned FROM item WHERE i_item_id = ?", (item_id,))
    result = cur.fetchone()
    if result is None:
        return -1
    # get num_owned
    num_owned = result[0]
    # get active rentals
    cur.execute("SELECT COUNT(*) FROM rental WHERE item_id = ?", (item_id,))
    active_rentals = cur.fetchone()[0]
    # return num_owned - active rentals
    return num_owned - active_rentals


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    cur.execute("SELECT place_in_line FROM waitlist WHERE item_id = ? AND customer_id = ?", (item_id, customer_id))
    result = cur.fetchone()
    if result is None:
        return -1
    return result[0]


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    cur.execute("SELECT COUNT(*) FROM waitlist WHERE item_id = ?", (item_id,))
    result = cur.fetchone()
    return result[0]

def save_changes():
    """
    Commits all changes made to the db.
    """
    conn.commit()


def close_connection():
    """
    Closes the cursor and connection.
    """
    cur.close()
    conn.close()

