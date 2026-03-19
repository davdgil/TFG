from pathlib import Path
import pandas as pd
from pymongo import MongoClient
import sys

# Añadir el path para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config.settings import settings

# Conexión síncrona a MongoDB
client = MongoClient(settings.db_uri)
db = client[settings.db_name]


def getProducts():
    products = list(db["products"].find({}, {"_id": 0}))
    return pd.DataFrame(products)


df = pd.read_csv(Path(__file__).resolve().parent.parent.parent / "dataset" / "olist_order_items_dataset.csv")
print(df.head())

def clean_order_items(csv):

    df_final = csv[["order_id", "product_id", "price", "freight_value"]]
    print(df_final.head())

    return df_final

df_cleaned = clean_order_items(df)

products = getProducts()
print("datos recogidos", len(products))

def mergeProducts():
    df_merged = df_cleaned.merge(products, on="product_id", how="left")
    return df_merged

print(mergeProducts().head())


def insertOrderItems():
    order_items = db["order_items"]
    data = mergeProducts().to_dict(orient="records")
    try:
        order_items.insert_many(data)
        print(f"Datos insertados: {len(data)} registros")
    except Exception as e:
        print(f"Error insertando datos: {e}")

insertOrderItems()

def deleteOrderItems():
    db["order_items"].delete_many({})