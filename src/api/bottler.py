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
        # GREEN_POTION
        if potions.potion_type[1] == 100:
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + :quantity"),
                                   {"quantity": potions.quantity})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - :ml"),
                                   {"ml": potions.potion_type[1] * potions.quantity})
        #BLUE_POTION
        if potions.potion_type[2] == 100:
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions + :quantity"),
                                   {"quantity": potions.quantity})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - :ml"),
                                   {"ml": potions.potion_type[2] * potions.quantity})
        #RED_POTION
        if potions.potion_type[0] == 100:
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions + :quantity"),
                                   {"quantity": potions.quantity})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - :ml"),
                                   {"ml": potions.potion_type[0] * potions.quantity})
            
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # TODO: remove the hardcoding of potion ml values

    with db.engine.begin() as connection:
        total_green_ml = connection.execute(sqlalchemy.text("SELECT total_green_ml FROM global_inventory")).scalar_one()
        total_blue_ml = connection.execute(sqlalchemy.text("SELECT total_blue_ml FROM global_inventory")).scalar_one()
        total_red_ml = connection.execute(sqlalchemy.text("SELECT total_red_ml FROM global_inventory")).scalar_one()
        total_dark_ml = connection.execute(sqlalchemy.text("SELECT total_dark_ml FROM global_inventory")).scalar_one()
        total_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM global_inventory")).scalar_one()
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_inventory")).scalar_one()
        potions = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM potion_inventory")).fetchall()
        potions_quantity = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory")).fetchall()
    
    plan = []
    type_of_potion = [list(row) for row in potions] # r0, g1, b2, d3, p4, br5
    quantity_of_potions = [t[0] for t in potions_quantity] # r0, g1, b2, d3, p4, br5


    # starting case: we make all green potions
    if total_potions == 0 and total_green_ml:
        max_possible_num_potions = math.floor(total_green_ml / type_of_potion[1][1]) 
        plan.append(
            {
                "potion_type": type_of_potion[1],
                "quantity": max_possible_num_potions
            }
        )
    
    #Prioritze making purple potions first 
    if total_red_ml and total_blue_ml and quantity_of_potions[4] == 0:
        max_possible_num_potions1 = math.floor(total_red_ml / type_of_potion[4][0])
        max_possible_num_potions2 = math.floor(total_blue_ml / type_of_potion[4][2])
        plan.append(
            {
                "potion_type": type_of_potion[4],
                "quantity": min(max_possible_num_potions1, max_possible_num_potions2)
            }
        )

    #red potion
    if total_red_ml:
        max_possible_num_potions = math.floor(total_red_ml / type_of_potion[0][0])
        plan.append(
            {
                "potion_type": type_of_potion[0],
                "quantity": max_possible_num_potions
            }
        )

    #green potion
    if total_green_ml:
        max_possible_num_potions = math.floor(total_green_ml / type_of_potion[1][1])
        plan.append(
            {
                "potion_type": type_of_potion[1],
                "quantity": max_possible_num_potions
            }
        )

    #blue potion
    if total_blue_ml:
        max_possible_num_potions = math.floor(total_blue_ml / type_of_potion[2][2])
        plan.append(
            {
                "potion_type": type_of_potion[2],
                "quantity": max_possible_num_potions
            }
        )
    
    #dark potion
    if total_dark_ml:
        max_possible_num_potions = math.floor(total_dark_ml / type_of_potion[3][3])
        plan.append(
            {
                "potion_type": type_of_potion[3],
                "quantity": max_possible_num_potions
            }
        )
    
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())