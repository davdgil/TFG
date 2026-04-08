from fastapi import APIRouter
from typing import List

from ..models.order_final import OrderFinal


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[OrderFinal])
async def get_orders(limit: int = 10):
    """Obtiene una lista de orders"""
    orders = await OrderFinalService.get_orders(limit)
    return orders


@router.get("/{order_id}", response_model=OrderFinal)
async def get_order_by_id(order_id: str):
    """Obtiene un pedido específico por su ID"""
    order = await OrderFinalService.get_orderById(order_id)
    return OrderFinal(**order)