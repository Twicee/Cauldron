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
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar_one()
        total_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger")).scalar_one()
        total_gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar_one()
        
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": total_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar_one()
        total_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger")).scalar_one()
        total_gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar_one()
    
    # TODO: add some better logic once your shop grows big and update capacities in db 
    if total_potions >= 5 and total_gold >= 1000:
        total_gold = total_gold - 1000
        if total_potions >= 2 and total_gold >= 1000:
            print("Shop is big now! buying more inventory space for potions and ml")
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = potion_capacity + 50"))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET ml_capacity = ml_capacity + 10000"))
            return {
            "potion_capacity": 1,
            "ml_capacity": 1
            }
        print("Shop is big now! buying more inventory space for potions") #delete - debug purposes
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = potion_capacity + 50"))
        return {
            "potion_capacity": 1,
            "ml_capacity": 0
        }
    else:
        print("Shop still too small to expand") #delete - debug purposes 
        return{
            "potion_capacity" : 0,
            "ml_capacity": 0,
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
    with db.engine.begin() as connection:
        if capacity_purchase.potion_capacity:
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"),
                                                {"description": f"PotionsHub spent {capacity_purchase.potion_capacity * 1000} gold upgrading their potion capacity"}).scalar_one()
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, change) VALUES (:transaction, :change)"), 
                               {"transaction": transaction_id, "change": -(capacity_purchase.potion_capacity * 1000)})
        if capacity_purchase.ml_capacity:
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"),
                                                {"description": f"PotionsHub spent {capacity_purchase.ml_capacity * 1000} gold upgrading their ml capacity"}).scalar_one()
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, change) VALUES (:transaction, :change)"), 
                               {"transaction": transaction_id, "change": -(capacity_purchase.ml_capacity * 1000)})

    print(f"You spent gold on upgrading your inventory")
    return "OK"
