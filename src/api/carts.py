from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
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
            connection.execute(sqlalchemy.text("INSERT INTO customers (name, class, level) VALUES (:name, :class, :level)"), 
                               {"name": customer.customer_name, "class": customer.character_class, "level": customer.level})

    return "OK"

#   Assigns a cart_id value of 1 to any new customer
#   TODO: update this value dynamically for every new customer who wants a cart
@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        customer_id = connection.execute(sqlalchemy.text("SELECT customer_id FROM customers WHERE name = :name AND class = :class AND level = :level"),
                                         {"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}).scalar_one()
        connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:value)"), {"value": customer_id})
        cart_id = connection.execute(sqlalchemy.text("SELECT cart_id FROM carts")).scalar_one()
    return {"cart_id": cart_id}

#   Cart Item Schema
class CartItem(BaseModel):
    quantity: int

#   Updates the quantity of a specific item in the cart
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        potion_id = connection.execute(sqlalchemy.text("SELECT potion_id FROM potion_inventory WHERE sku = :sku"), {"sku": item_sku})
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, potion_id, quantity) VALUES (:cartid, :potionid, :quantity)"),
                           {"cartid": cart_id, "potionid": potion_id, "quantity": cart_item.quantity})
    return "OK"

#   CartChecout Schema 
class CartCheckout(BaseModel):
    payment: str

#   Think of it like a reciept
#   TODO: update inventory and gold dynamically
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # select the quantities and product price 
    return {"total_potions_bought": 1, "total_gold_paid": 50}
