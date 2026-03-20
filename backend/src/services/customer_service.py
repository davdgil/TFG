from ..config.mongo import db
from ..models.customer import Customer
from fastapi import HTTPException
from typing import List


class CustomerService:

   ## static para no tener que instanciar un objeto de esta clase y poder llamar directamente al metodo
   @staticmethod
   async def get_customerById(customer_id: str):
       try:
           customer = await db.customers.find_one({"customer_id": customer_id},
                                                {"_id": 0})

           if not customer:
               raise HTTPException(status_code=404, detail="Customer not found")

           return customer

       except HTTPException:
           raise  # Re-lanza HTTPException
       except Exception as e:
           print("Error al encontrar el usuario", e)
           raise HTTPException(status_code=500, detail="Error interno del servidor")

   @staticmethod
   async def get_customers(limit: int = 10):
       """Obtiene una lista simple de customers"""
       try:
           customers = await db.customers.find({}, {"_id": 0}).limit(limit).to_list(length=None)

           return [Customer(**customer) for customer in customers]

       except Exception as e:
           print(f"Error al obtener customers: {e}")
           raise HTTPException(status_code=500, detail="Error interno del servidor")