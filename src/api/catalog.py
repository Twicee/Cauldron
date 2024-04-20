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
        blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
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
    if blue_potions > 0:
        return[
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": blue_potions,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        ]

    if red_potions > 0:
        return[
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0]
            }
        ]
    
    return []
