from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from typing import Optional, List

class WishlistItem(BaseModel):
    product_id: PydanticObjectId
    variant_name: Optional[str] = None  # e.g., "Red Large"

class Wishlist(Document):
    user_id: PydanticObjectId
    items: List[WishlistItem] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None