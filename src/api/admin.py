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
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = 50, ml_capacity = 10000"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
        connection.execute(sqlalchemy.text("DELETE FROM carts"))
        connection.execute(sqlalchemy.text("DELETE FROM gold_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM transactions"))
        connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description)"), {"description": "PotionsHub has a starting balance of 100 gold"})
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (change) VALUES (:change)"), {"change": 100})
    return "OK"

