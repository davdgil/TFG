from ..config.mongo import db
from ..models.order_final import OrderFinal
from fastapi import HTTPException
from typing import List


class OrderFinalService:

   ## static para no tener que instanciar un objeto de esta clase y poder llamar directamente al metodo
   @staticmethod
   async def get_orderById(order_id: str):
       try:
           order = await db.orders_final.find_one({"order_id": order_id},
                                                {"_id": 0})

           if not order:
               raise HTTPException(status_code=404, detail="Order not found")

           return order

       except HTTPException:
           raise  # Re-lanza HTTPException
       except Exception as e:
           print("Error al encontrar el pedido", e)
           raise HTTPException(status_code=500, detail="Error interno del servidor")

   @staticmethod
   async def get_orders(limit: int = 10):
       """Obtiene una lista simple de orders"""
       try:
           orders = await db.orders_final.find({}, {"_id": 0}).limit(limit).to_list(length=None)

           return [OrderFinal(**order) for order in orders]

       except Exception as e:
           print(f"Error al obtener orders: {e}")
           raise HTTPException(status_code=500, detail="Error interno del servidor")