from fastapi import APIRouter, Depends
from pydantic import BaseModel #Its own completely seperate library has nothing to do with FAST API
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

#This is how we specify how we want the user(client) to send data. It validates that it follows this class
#You are forcing the user to follow this "schema". i.e. I expect the data to look like this
#Just use BaseModel in the parameter for the class that defines your schema
class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int  #you may also assign default value 
    potion_type: list[int]
    price: int

    quantity: int

#{order_id} is saying that it expects the argument to be passed to it by the user(client) in the url. Known as a "path parameter"
#Since we're expecting the user(client) to give us data in the form of the schema, our parameters are of type the schema we defined 
#This function returns what barrels were delivered for a specific order_id
#look up parameter binding -i.e. preventing sequel injection attacks. %s (works but dont do) under the database under the hood do parameter binding instead
@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    # Upon successful purchase update num of ml for each potion type
    for barrel in barrels_delivered:
        color_type = barrel.sku.split('_')
        color = color_type[1].lower()
        print(color) #delete only for testing purposes 
        
        with db.engine.begin() as connection:
            # new transaction entry
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING transaction_id"), 
                               {"description": f"PotionsHub spent {barrel.price} gold on {barrel.quantity} {color} {'barrel' if barrel.quantity == 1 else 'barrels'}"}).scalar_one()
            # new ml_ledger entry
            connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, color, change) VALUES (:transaction, :color, :change)"), 
                               {"transaction": transaction_id, "color": color, "change": barrel.ml_per_barrel})
            
            # new gold ledger entry
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, change) VALUES (:transaction, :change)"), 
                                               {"transaction": transaction_id, "change": -(barrel.quantity * barrel.price)})

    return "OK"

# You should think of list[Barrel] as a list of Barrel Objects. Each containing the attributes specified by the schema
# FastAPI automatically converts the incoming JSON data into a list of python objects of that schema 
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)    #displays whats for sale
    plan = []   #Begin with empty plan
    # total_amount = 0

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM gold_ledger")).scalar_one()
        total_ml = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM ml_ledger")).scalar_one()
        ml_capacity = connection.execute(sqlalchemy.text("SELECT ml_capacity FROM global_inventory")).scalar_one()

    # TODO: Implement better logic  
    # 1. You can only buy barrels when you have gold
    # 2. Keep a running count of how much you're spending
    if gold <= 0:
        return plan
    
    #Purchase a small red barrel
    if gold >= 100 and (total_ml + 500) <= ml_capacity:
        if gold >= 250 and (total_ml + 2500) <= ml_capacity:
            plan.append(
                {
                    "sku": "MEDIUM_RED_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 250
            total_ml = total_ml + 2500
        else:
            plan.append(
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 100
            total_ml = total_ml + 500
    
    #Purchase a small blue barrel
    if gold >= 120 and (total_ml + 500) <= ml_capacity:
        if gold >= 300 and (total_ml + 2500) <= ml_capacity:
            plan.append(
                {
                    "sku": "MEDIUM_BLUE_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 300
            total_ml = total_ml + 2500
        else:
            plan.append(
                {
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 120
            total_ml = total_ml + 500

    #Purchase a large dark barrel
    if gold >= 750 and (total_ml + 10000) <= ml_capacity:
        plan.append(
            {
                "sku": "LARGE_DARK_BARREL",
                "quantity": 1,
            }
        )
        gold = gold - 750
        total_ml = total_ml + 10000
    
    #Purchase a small green barrel
    if gold >= 100 and (total_ml + 500) <= ml_capacity:
        if gold >= 250 and (total_ml + 2500) <= ml_capacity:
            plan.append(
                {
                    "sku": "MEDIUM_GREEN_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 250
            total_ml = total_ml + 2500
        else:
            plan.append(
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
            )
            gold = gold - 100
            total_ml = total_ml + 500
    
    print(plan) #delete - only for testing purposes 
    return plan

