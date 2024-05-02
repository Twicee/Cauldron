from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    for potions in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = quantity + :quantity WHERE num_red_ml = :red AND num_green_ml = :green AND num_blue_ml = :blue AND num_dark_ml = :dark"),
                                                 {"quantity": potions.quantity, "red": potions.potion_type[0], 
                                                  "green": potions.potion_type[1],
                                                  "blue": potions.potion_type[2],
                                                  "dark": potions.potion_type[3]})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_red_ml = total_red_ml - :red"), {"red": potions.potion_type[0] * potions.quantity})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_green_ml = total_green_ml - :green"), {"green": potions.potion_type[1] * potions.quantity})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_blue_ml = total_blue_ml - :blue"), {"blue": potions.potion_type[2] * potions.quantity}) 
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_dark_ml = total_dark_ml - :dark"), {"dark": potions.potion_type[3] * potions.quantity})           
            
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # TODO: add better logic for determing the priority of potions to be made first 

    with db.engine.begin() as connection:
        total_red_ml, total_green_ml, total_blue_ml, total_dark_ml = connection.execute(sqlalchemy.text("SELECT total_red_ml, total_green_ml, total_blue_ml, total_dark_ml FROM global_inventory")).fetchone()
        potions = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM potion_inventory ORDER BY random()")).fetchall()
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_inventory")).scalar_one()
        potion_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM global_inventory")).scalar_one()
    
    plan = []

    for potion in potions:
        # if I have enough ml of each type to make the potion and spare capacity in potion inventory, make potions
        # calculate max_possible_num_potions
        # potion = (r, g, b, d, q)
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = potion
        max_possible_red = max_possible_green = max_possible_blue = max_possible_dark = 1000
        if num_red_ml != 0:
            max_possible_red = total_red_ml // num_red_ml
        if num_green_ml != 0:
            max_possible_green = total_green_ml // num_green_ml
        if num_blue_ml != 0:
            max_possible_blue = total_blue_ml // num_blue_ml
        if num_dark_ml != 0:
            max_possible_dark = total_dark_ml // num_dark_ml
        
        max = [max_possible_red, max_possible_green, max_possible_blue, max_possible_dark]
        max_possible_num_potions = min(max)
        
        total_red_ml = total_red_ml - (max_possible_num_potions * num_red_ml)
        total_green_ml = total_green_ml - (max_possible_num_potions * num_green_ml)
        total_blue_ml= total_blue_ml - (max_possible_num_potions * num_blue_ml)
        total_dark_ml= total_dark_ml - (max_possible_num_potions * num_dark_ml)

        if max_possible_num_potions and (total_potions + max_possible_num_potions) <= potion_capacity:
            plan.append({
                        "potion_type": [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml],
                        "quantity": max_possible_num_potions
                    })
    print(plan)
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())