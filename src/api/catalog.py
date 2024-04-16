from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
    #add logic so that your catalog only displays inventory > 0
    if green_potions > 0:
        return [
                {
                    "sku": "GREEN_POTION_0",    #SKU = unique indentifier assigned to each distinct product in a store or inventory
                    "name": "green potion",
                    "quantity": green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],  #amount of ml we have of each potion: red, green, blue, dark liquid 
                }
            ]
    else:
        return []
