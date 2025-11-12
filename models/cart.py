from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from typing import Optional, List

class CartItem(BaseModel):
    product_id: PydanticObjectId
    variant_name: Optional[str] = None  # e.g., "Red Large"
    quantity: int = 1

class Cart(Document):
    user_id: PydanticObjectId
    items: List[CartItem] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None