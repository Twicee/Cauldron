from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        products = connection.execute(sqlalchemy.text("SELECT sku, name, quantity, price, ARRAY[num_red_ml, num_green_ml, num_blue_ml, num_dark_ml] AS potion_type FROM potion_inventory WHERE quantity > 0")).fetchall()
    for row in products:
        catalog_entry = {
            "sku": row.sku,
            "name": row.name,
            "quantity": row.quantity,
            "price": row.price,
            "potion_type": row.potion_type
        }
        catalog.append(catalog_entry)
    print(catalog)
    return catalog