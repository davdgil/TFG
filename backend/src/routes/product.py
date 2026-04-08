from fastapi import APIRouter
from typing import List

from ..models.product import Product


router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Product])
async def get_products(limit: int = 10):
    """Obtiene una lista de products"""
    products = await ProductService.get_products(limit)
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product_by_id(product_id: str):
    """Obtiene un producto específico por su ID"""
    product = await ProductService.get_productById(product_id)
    return Product(**product)