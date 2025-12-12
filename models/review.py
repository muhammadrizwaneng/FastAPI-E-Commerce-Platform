from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Review(Document):
    user_id: str
    product_id: PydanticObjectId
    user_name: str 
    rating: int = Field(..., ge=1, le=5)
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        collection = "reviews"

class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
