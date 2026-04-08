
from ..config.mongo import db
from ..models.product import Product
from fastapi import HTTPException
from typing import List


class ProductService:

   ## static para no tener que instanciar un objeto de esta clase y poder llamar directamente al metodo
   @staticmethod
   async def get_productById(product_id: str):
       try:
           product = await db.products.find_one({"product_id": product_id},
                                                {"_id": 0})

           if not product:
               raise HTTPException(status_code=404, detail="Product not found")

           return product

       except HTTPException:
           raise  # Re-lanza HTTPException
       except Exception as e:
           print("Error al encontrar el producto", e)
           raise HTTPException(status_code=500, detail="Error interno del servidor")

   @staticmethod
   async def get_products():
       """Obtiene una lista simple de products"""
       try:
           products = await db.products.find({}, {"_id": 0}).to_list(length=None)

           return [Product(**product) for product in products]

       except Exception as e:
           print(f"Error al obtener products: {e}")
           raise HTTPException(status_code=500, detail="Error interno del servidor")
