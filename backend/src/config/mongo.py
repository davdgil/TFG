from motor.motor_asyncio import AsyncIOMotorClient
from src.config.settings import settings

client = AsyncIOMotorClient(settings.db_uri)
db = client[settings.db_name]

async def connect_db():
    try: 
        await client.admin.command("ping")
        print(f"Conectado a MongoDB: {db}")
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        raise

async def close_db() -> None:
    client.close()
    print("Conexion a Mongo terminada")
