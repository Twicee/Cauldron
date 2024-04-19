from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory", #this is just a shortcut way of prefixing each route with the value
    tags=["inventory"], #this is how we group our routes in /docs i.e. see them together nicely 
    dependencies=[Depends(auth.get_api_key)],
)

#pull from your database the following values i.e. so its not hardcoded
@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text("SELECT total_potion_num FROM global_inventory")).scalar_one()
        total_ml_in_barrels = connection.execute(sqlalchemy.text("SELECT total_ml_in_barrels FROM global_inventory")).scalar_one()
        total_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml_in_barrels, "gold": total_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 1,
        "ml_capacity": 1
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
