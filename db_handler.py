from uuid import MAX

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
    i_item_sk, i_item_id, i_rec_start_date, i_product_name, i_brand, i_class, i_category, i_manufact, i_current_price
    new_item - An Item object containing a new item to be inserted into the DB in the item table.
        new_item and its attributes will never be None.
    """

    # Get today's date for i_rec_start_date
    new_date = date.today().isoformat()

    # Get the max i_item_sk and add 1 to get the new i_item_sk
    cur.execute("SELECT MAX(i_item_sk) FROM item")
    new_sk = cur.fetchone()[0] + 1
    cur.execute("INSERT INTO item (i_item_sk, i_item_id, i_rec_start_date, i_product_name, i_brand, i_class, i_category, i_manufact, i_current_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_sk, new_item.i_item_id, new_date, new_item.i_product_name, new_item.i_brand, new_item.i_class, new_item.i_category, new_item.i_manufact, new_item.i_current_price))


def add_customer(new_customer: Customer = None):

    """
    c_customer_sk, c_customer_id, c_first_name, c_last_name, c_email_address, c_current_addr_sk
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    cur.execute("SELECT MAX(c_customer_sk) FROM customer")
    new_sk = cur.fetchone()[0] + 1

    # split new_customer.name to get first and last name
    name_split = new_customer.c_first_name.split(" ")
    new_first_name = name_split[0]
    new_last_name = name_split[1]

    # NOT DONE parse address to get c_current_addr_sk

    cur.execute("INSERT INTO customer (c_customer_sk, c_customer_id, c_first_name, c_last_name, c_email_address, c_current_addr_sk) VALUES (?, ?, ?, ?, ?, ?)",
                (new_sk, new_customer.c_customer_id, new_first_name, new_last_name, new_customer.c_email_address, new_customer.c_current_addr_sk))


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    if new_customer.name is not None:
        name_split = new_customer.c_first_name.split(" ")
        new_first_name = name_split[0]
        new_last_name = name_split[1]

        cur.execute("UPDATE customer SET c_first_name = ?, c_last_name = ? WHERE c_customer_id = ?",
                    (new_first_name, new_last_name, original_customer_id))

    if new_customer.c_email_address is not None:
        cur.execute("UPDATE customer SET c_email_address = ? WHERE c_customer_id = ?",
                    (new_customer.c_email_address, original_customer_id))
    if new_customer.c_current_addr_sk is not None:
          street_number, street_name, city, state, zip_code = [
            part.strip() for part in new_customer.c_current_addr_sk.split(",")
    ]

    cur.execute("UPDATE customer_address SET street_number = ?, street_name = ?, city = ?, state = ?, zip_code = ? WHERE c_customer_id = ?",
                (street_number, street_name, city, state, zip_code, original_customer_id))
    
    if new_customer.c_customer_id is not None:
        cur.execute("UPDATE customer SET c_customer_id = ? WHERE c_customer_id = ?",
                    (new_customer.c_customer_id, original_customer_id))


def rent_item(item_id: str = None, customer_id: str = None):
    """
    item_id - A string containing the Item ID for the item being rented.
    customer_id - A string containing the customer id of the customer renting the item.
    """
    # Inserts a row into rental with rental_date = today and due_date = today + 14 days
    curr.execute("INSERT INTO rental (rental_date, due_date) VALUES (DATE('now'), DATE('now', '+14 days'))")


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    raise NotImplementedError("you must implement this function")

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    raise NotImplementedError("you must implement this function")


def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """
    raise NotImplementedError("you must implement this function")


def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_rentals(filter_attributes: Rental = None,
                         min_rental_date: str = None,
                         max_rental_date: str = None,
                         min_due_date: str = None,
                         max_due_date: str = None) -> list[Rental]:
    """
    Returns a list of Rental objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


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
    raise NotImplementedError("you must implement this function")


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def number_in_stock(item_id: str = None) -> int:
    """
    Returns num_owned - active rentals. Returns -1 if item doesn't exist.
    """
    raise NotImplementedError("you must implement this function")


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    raise NotImplementedError("you must implement this function")


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    raise NotImplementedError("you must implement this function")


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

