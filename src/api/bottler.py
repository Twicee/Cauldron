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
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    # [r, g, b, d]
    color_mapping = {
        0: "red",
        1: "green",
        2: "blue",
        3: "dark"
    }
    for potions in potions_delivered:
        with db.engine.begin() as connection:
            # returns a list of indexes where value is not 0
            potions_to_use = [idx for idx, val in enumerate(potions.potion_type) if val != 0]
            potion_name, potion_id = connection.execute(sqlalchemy.text("SELECT name, potion_id FROM potion_inventory WHERE num_red_ml = :red AND num_green_ml= :green AND num_blue_ml = :blue AND num_dark_ml = :dark"),
                                   {"red": potions.potion_type[0], "green": potions.potion_type[1], "blue": potions.potion_type[2], "dark": potions.potion_type[3]}).fetchone()
            # potion of a single color
            if len(potions_to_use) == 1:
                description = f"PotionsHub used {potions.quantity * potions.potion_type[potions_to_use[0]]} {color_mapping[potions_to_use[0]]} ml to make {potions.quantity} {potion_name} {'potion' if potions.quantity == 1 else 'potions'}"
            
            # potion of two colors
            if len(potions_to_use) == 2:        
                description = f"PotionsHub used {potions.quantity * potions.potion_type[potions_to_use[0]]} {color_mapping[potions_to_use[0]]} ml and {potions.quantity * potions.potion_type[potions_to_use[1]]} {color_mapping[potions_to_use[1]]} ml to make {potions.quantity} {potion_name} {'potion' if potions.quantity == 1 else 'potions'}"

            # transactions entry
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"),{"description": description}).scalar_one()
            
            # potion_ledger entry
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (transaction_id, potion_id, change) VALUES (:transaction, :potionid, :change)"),
                               {"transaction": transaction_id, "potionid": potion_id, "change": potions.quantity})

            #ml_ledger entry
            if len(potions_to_use) == 1:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, color, change) VALUES (:transaction, :color, :change)"), 
                                                {"transaction": transaction_id, "color": color_mapping[potions_to_use[0]], "change": -(potions.quantity * potions.potion_type[potions_to_use[0]]) })
            if len(potions_to_use) == 2:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, color, change) VALUES (:transaction, :color, :change)"), 
                                                {"transaction": transaction_id, "color": color_mapping[potions_to_use[0]], "change": -(potions.quantity * potions.potion_type[potions_to_use[0]]) })
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, color, change) VALUES (:transaction, :color, :change)"), 
                                                {"transaction": transaction_id, "color": color_mapping[potions_to_use[1]], "change": -(potions.quantity * potions.potion_type[potions_to_use[1]]) })            
    
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
        total_red_ml = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE color = 'red'")).scalar_one()
        total_green_ml = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE color = 'green'")).scalar_one()
        total_blue_ml = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE color = 'blue'")).scalar_one()
        total_dark_ml = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE color = 'dark'")).scalar_one()
        potions = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM potion_inventory ORDER BY random()")).fetchall()
        total_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).scalar_one() 
        potion_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM global_inventory")).scalar_one()
    
    plan = []
    print(potions)
    for potion in potions:
        # if I have enough ml of each type to make the potion and spare capacity in potion inventory, make potions
        # calculate max_possible_num_potions
        # potion = (r, g, b, d, q)
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = potion
        max_possible_red = max_possible_green = max_possible_blue = max_possible_dark = 10000
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
            total_potions = total_potions + max_possible_num_potions
            plan.append({
                        "potion_type": [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml],
                        "quantity": max_possible_num_potions
                    })
        else:
            if max_possible_num_potions == 0:
                continue
            max_possible_num_potions = potion_capacity - total_potions
            if max_possible_num_potions == 0:
                continue
            total_potions = total_potions + max_possible_num_potions
            plan.append(
                {
                    "potion_type": [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml],
                    "quantity": max_possible_num_potions
                }
            )
    print(plan)
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())