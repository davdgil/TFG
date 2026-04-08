
from ..config.mongo import db
from ..models.order_item import OrderItem
from fastapi import HTTPException
from typing import List


class OrderItemService:

   ## static para no tener que instanciar un objeto de esta clase y poder llamar directamente al metodo
   @staticmethod
   async def get_order_itemsByOrderId(order_id: str):
       try:
           order_items = await db.order_items.find({"order_id": order_id},
                                                   {"_id": 0}).to_list(length=None)

           if not order_items:
               raise HTTPException(status_code=404, detail="Order items not found")

           return [OrderItem(**item) for item in order_items]

       except HTTPException:
           raise  # Re-lanza HTTPException
       except Exception as e:
           print("Error al encontrar los items del pedido", e)
           raise HTTPException(status_code=500, detail="Error interno del servidor")

   @staticmethod
   async def get_order_items():
       """Obtiene una lista simple de order items"""
       try:
           order_items = await db.order_items.find({}, {"_id": 0}).to_list(length=None)

           return [OrderItem(**item) for item in order_items]

       except Exception as e:
           print(f"Error al obtener order items: {e}")
           raise HTTPException(status_code=500, detail="Error interno del servidor")
