import pandas as pd
from pathlib import Path
import pathlib
from pymongo import MongoClient
import sys

# Añadir el path para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config.settings import settings

# Conexión síncrona a MongoDB
client = MongoClient(settings.db_uri)
db = client[settings.db_name]

ruta = pathlib.Path(__file__).resolve().parent.parent.parent
print(f"Ruta actual: {ruta}")

df = pd.read_csv(Path(ruta)  / "dataset" / "olist_products_dataset.csv")
df_translate = pd.read_csv(Path(ruta)  / "dataset" / "product_category_name_translation.csv")
print(df.head(200))


def cleanProducts(csv, csv_translate):
    ## nos quedamos solo con estos campos, el resto son irrelevantes
    
    df = csv[["product_id", "product_category_name"]]
    ## on, el dataset sobre el que hacemos el merge, left, si hay match se sustituye, si no, se queda el valor original
    df_merged = df.merge(csv_translate, on="product_category_name", how="left")
    df_final = df_merged.drop(columns=["product_category_name"])
    ## rellenamos los valores nulos con "uncategorized"
    df_final["product_category_name_english"] = df_final["product_category_name_english"].fillna("uncategorized")
    
    
    print(df_final.head(200))
    
    return df_final

cleanProducts(df, df_translate)


def insertProducts():
    products = db["products"]
    data = cleanProducts(df, df_translate).to_dict(orient="records")
    try:
        products.insert_many(data)
        print(f"Datos insertados: {len(data)} registros")
    except Exception as e:
        print(f"Error insertando datos: {e}")

insertProducts()

def deleteProducts():
    db["products"].delete_many({})
