import pandas as pd
from pathlib import Path
from pymongo import MongoClient
import sys


sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config.settings import settings

client = MongoClient(settings.db_uri)
db = client[settings.db_name]


orders_data = list(db["orders"].find({}, {"_id": 0}))
order_items_data = list(db["order_items"].find({}, {"_id": 0}))

df_orders = pd.DataFrame(orders_data)
df_items = pd.DataFrame(order_items_data)

print("Orders:")
print(df_orders.head())

print("Order items:")
print(df_items.head())


## preparamos los items que queremos para meterlo dentro de orders_final
def build_items(df_items):

    # Nos quedamos solo con lo importante para items[]
    df_items = df_items[[
        "order_id",
        "product_id",
        "price",
        "freight_value",
        "product_category_name_english"
    ]]

    return df_items

df_items_clean = build_items(df_items)

## agrupamos los items por el order_id y lo pasamos a diccionario listo para posteriormete subirlo al mongo
grouped_items = (
    df_items_clean
    .groupby("order_id")
    .apply(lambda x: x.to_dict(orient="records"), include_groups=False)
    .reset_index(name="items")
)

print("Grouped items:")
print(grouped_items.head())


df_orders_final = df_orders.merge(grouped_items, on="order_id", how="left")

# Si algun pedido no tiene items, ponemos lista vacia
df_orders_final["items"] = df_orders_final["items"].apply(
    lambda x: x if isinstance(x, list) else []
)

print("Orders final:")
print(df_orders_final.head())


def insert_orders_final(df):
    collection = db["orders_final"]
    data = df.to_dict(orient="records")

    collection.delete_many({})
    collection.insert_many(data)

    print(f"Orders final insertados: {len(data)}")

insert_orders_final(df_orders_final)