from beanie import Document, PydanticObjectId
from typing import List, Optional
from datetime import datetime

class RecentlyViewed(Document):
    user_id: PydanticObjectId
    product_ids: List[PydanticObjectId] = []  # Max 10 items
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_id_here",
                "product_ids": ["product_id_1", "product_id_2"],
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }