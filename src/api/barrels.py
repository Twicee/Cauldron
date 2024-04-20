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

    #upon successful purchase update num_green_ml for each potion type
    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_GREEN_BARREL":
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :new_ml"), 
                                   {"new_ml": barrel.ml_per_barrel})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost"), {"cost": barrel.price})
        if barrel.sku == "MINI_BLUE_BARREL":
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + :new_ml"), 
                                   {"new_ml": barrel.ml_per_barrel})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost"), {"cost": barrel.price})
        if barrel.sku == "MINI_RED_BARREL":
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + :new_ml"), 
                                   {"new_ml": barrel.ml_per_barrel})
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost"), {"cost": barrel.price})

    return "OK"

# You should think of list[Barrel] as a list of Barrel Objects. Each containing the attributes specified by the schema
# FastAPI automatically converts the incoming JSON data into a list of python objects of that schema 
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)    #displays whats for sale
    #Inital Logic for when and what to buy:
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text("SELECT total_potion_num FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
    
    # When to buy Green Barrels
    if total_potions < 10 and gold >= 100:
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    
    if total_potions >= 10 and gold >= 100:
        return[
            {
                "sku": "MINI_BLUE_BARREL",
                "quantity": 1,
            }
        ]

