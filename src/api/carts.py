from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import sqlalchemy.exc
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }

#   Customer schema 
class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

#   Just returns a list of customers according to the visit_id
@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    for customer in customers:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("INSERT INTO customers (name, class, level) VALUES (:name, :class, :level) ON CONFLICT ON CONSTRAINT unique_customer DO NOTHING"), 
                                    {"name": customer.customer_name, "class": customer.character_class, "level": customer.level})
    return "OK"

#   Assigns a cart_id value of 1 to any new customer
@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        customer_id = connection.execute(sqlalchemy.text("SELECT customer_id FROM customers WHERE name = :name AND class = :class AND level = :level"),
                                         {"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}).scalar_one()
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:value) RETURNING cart_id") , {"value": customer_id}).scalar_one()
    return {"cart_id": cart_id}

#   Cart Item Schema
class CartItem(BaseModel):
    quantity: int

#   Updates the quantity of a specific item in the cart
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        potion_id = connection.execute(sqlalchemy.text("SELECT potion_id FROM potion_inventory WHERE sku = :sku"), {"sku": item_sku}).scalar_one()
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, potion_id, quantity) VALUES (:cartid, :potionid, :quantity)"),
                           {"cartid": cart_id, "potionid": potion_id, "quantity": cart_item.quantity})
    return "OK"

#   CartChecout Schema 
class CartCheckout(BaseModel):
    payment: str

#   Think of it like a reciept
#   Since multiple checkout calls may be done at a single time we may have the case where one instance is working on a 
#    older value that has not updated for that instance. the solution? atomic operations - transactions 
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # select the quantities and product price
    with db.engine.begin() as connection:
        items = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_items WHERE cart_id = :cartid"), {"cartid": cart_id}).fetchall()
    
    total_sum = 0
    total_potions = 0
    for item in items:
        with db.engine.begin() as connection:
            customer_name = connection.execute(sqlalchemy.text("SELECT c.name FROM carts AS ct JOIN customers AS c ON ct.customer_id = c.customer_id WHERE ct.cart_id = :cartid"),
                                               {"cartid": cart_id}).scalar_one()
            customer_id = connection.execute(sqlalchemy.text("SELECT customer_id FROM carts WHERE cart_id = :cartid"), {"cartid": cart_id}).scalar_one()
            price = connection.execute(sqlalchemy.text("SELECT price FROM potion_inventory WHERE potion_id = :potionid"), {"potionid": item[0]}).scalar_one()
            potion_name = connection.execute(sqlalchemy.text("SELECT name FROM potion_inventory WHERE potion_id = :potionid"), {"potionid": item[0]}).scalar_one()
    
        total_sum = total_sum + (price * item[1])
        total_potions = total_potions + item[1]
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"),
                                        {"description": f"{customer_name} paid {price * item.quantity} gold for {item.quantity} {potion_name} {'potion' if item.quantity == 1 else 'potions'}"}).scalar_one() 
        connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (transaction_id, customer_id, potion_id, change) VALUES (:transaction, :customerid, :potionid, :change)"),
                           {"transaction": transaction_id, "customerid": customer_id, "potionid": item.potion_id, "change": -(item.quantity)})
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, customer_id, change) VALUES (:transaction, :customerid, :change)", 
                                           {"transaction": transaction_id, "customerid": customer_id, "change": (price * item[1])}))
        
    return {"total_potions_bought": total_potions, "total_gold_paid": total_sum}
