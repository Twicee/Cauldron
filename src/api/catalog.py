from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        products = connection.execute(sqlalchemy.text("""
                                                    SELECT pi.sku, pi.name, SUM(pl.change) AS quantity, pi.price,
                                                      ARRAY[pi.num_red_ml, pi.num_green_ml, pi.num_blue_ml, pi.num_dark_ml] AS potion_type
                                                      FROM potion_inventory pi
                                                      JOIN potion_ledger pl ON pi.potion_id = pl.potion_id
                                                      GROUP BY pi.sku, pi.name, pi.price, pi.num_red_ml, pi.num_green_ml, pi.num_blue_ml, pi.num_dark_ml
                                                      HAVING SUM(pl.change) > 0
                                                      ORDER BY quantity DESC
                                                      LIMIT 6
                                                      """)).fetchall()
    for row in products:
        catalog_entry = {
            "sku": row.sku,
            "name": row.name,
            "quantity": row.quantity,
            "price": row.price,
            "potion_type": row.potion_type
        }
        catalog.append(catalog_entry)
    print(catalog)
    return catalog