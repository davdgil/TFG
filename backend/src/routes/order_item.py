from fastapi import APIRouter
from typing import List

from ..models.order_item import OrderItem
from ..services.order_item_service import OrderItemService

router = APIRouter(
    prefix="/order-items",
    tags=["order-items"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[OrderItem])
async def get_order_items(limit: int = 10):
    """Obtiene una lista de order items"""
    order_items = await OrderItemService.get_order_items(limit)
    return order_items


@router.get("/{order_id}", response_model=List[OrderItem])
async def get_order_items_by_order_id(order_id: str):
    """Obtiene los items de un pedido específico"""
    order_items = await OrderItemService.get_order_itemsByOrderId(order_id)
    return order_items