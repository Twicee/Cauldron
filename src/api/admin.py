from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    # TODO: resest potion capacity and ml_capacity and carts
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_green_ml = 0, total_blue_ml = 0, total_red_ml = 0, total_dark_ml = 0, gold = 100, potion_capacity = 50, ml_capacity = 10000"))
        connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = 0"))
        connection.execute(sqlalchemy.text("DELETE FROM carts"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
    return "OK"

