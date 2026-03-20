from fastapi import APIRouter
from typing import List

from ..models.customer import Customer
from ..services.customer_service import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Customer])
async def get_customers(limit: int = 10):
    """Obtiene una lista de customers"""
    customers = await CustomerService.get_customers(limit)
    return customers


@router.get("/{customer_id}", response_model=Customer)
async def get_customer_by_id(customer_id: str):
    """Obtiene un cliente específico por su ID"""
    customer = await CustomerService.get_customerById(customer_id)
    return Customer(**customer)
