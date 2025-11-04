from fastapi import APIRouter, HTTPException, status
from models.order import OrderCreate, Order, OrderStatus
from datetime import datetime
import uuid
from database.database import add_order, get_product_by_id, get_order_by_id

router = APIRouter()

@router.post("/create_order", response_model=Order)
async def create_order(order: OrderCreate, user_id: str):
    # Calculate total amount
    total_amount = 0
    for item in order.items:
        product = await get_product_by_id(item.product_id)
        print("product---------",product)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )
        # Check if the product has variants
        if product.has_variants:
            # Find the matching variant based on color and size
            matching_variant = next(
                (
                    variant for variant in product.variants
                    if variant.color == item.color and variant.size == item.size
                ),
                None
            )

            if not matching_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No matching variant found for product {item.product_id} with color '{item.color}' and size '{item.size}'"
                )

            # Check stock for the matching variant
            if matching_variant.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {item.product_id} (color: {item.color}, size: {item.size})"
                )

            total_amount += matching_variant.price * item.quantity
    
    order_dict = order.dict()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["user_id"] = user_id
    order_dict["total_amount"] = total_amount
    order_dict["status"] = OrderStatus.PENDING
    order_dict["created_at"] = datetime.utcnow()
    order_dict["updated_at"] = datetime.utcnow()
    
    await add_order(order_dict)
    return order_dict

@router.get("/get_order/{order_id}", response_model=Order)
async def get_order(order_id: str):
    order = await get_order_by_id({"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order