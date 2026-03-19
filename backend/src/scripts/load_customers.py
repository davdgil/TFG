from pathlib import Path
import pandas as pd
from pymongo import MongoClient
import sys

# Añadir el path para importar settings
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config.settings import settings


client = MongoClient(settings.db_uri)
db = client[settings.db_name]


customers = pd.read_csv(Path(__file__).resolve().parent.parent.parent / "dataset" / "olist_customers_dataset.csv")
customers_data = customers.to_dict(orient="records")

def insertCustomers():
    customers_collection = db["customers"]
    try:
        customers_collection.insert_many(customers_data)
        print(f"Datos insertados: {len(customers_data)} registros")
    except Exception as e:
        print(f"Error insertando datos: {e}")
        
insertCustomers()

def deleteCustomers():
    db["customers"].delete_many({})
    
## deleteCustomers()