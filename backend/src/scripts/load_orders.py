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

base_dir = Path(__file__).resolve().parent
csv_path = base_dir.parent.parent / "dataset" / "olist_orders_dataset.csv"

print(f"Cargando desde: {csv_path}")

df = pd.read_csv(csv_path)
print(df.head())



def cleanOrders(csv):
    ## nos quedamos solo con estos campos, el resto son irrelevantes
    
    df = csv[["order_id", "customer_id", "order_purchase_timestamp"]]
    df_final = df.rename(columns={"order_purchase_timestamp" : "order_date"})
    
    print(df_final.head())
    
    return df_final

 
def insertOrders():
    
    orders = db["orders"]
    ## convertimos el dataset a diccionario
    data = cleanOrders(df).to_dict(orient = "records")
    try:
        orders.insert_many(data)
        print(f"Datos insertados: {len(data)} registros")
    except Exception as e:
        print(f"Error insertando datos: {e}")
    
#insertOrders()

def deleteOrders():
    db["orders"].delete_many({})

## deleteOrders()