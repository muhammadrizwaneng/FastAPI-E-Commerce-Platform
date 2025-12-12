from datetime import datetime
from bson import ObjectId
from models.recently_viewed import RecentlyViewed

async def add_to_recently_viewed(user_id: str, product_id: str):
    """
    Add product to recently viewed.
    - Max 10 products
    - If product already exists, move it to first index
    - If more than 10, remove the oldest (last) one
    """
    recently_viewed = await RecentlyViewed.find_one({"user_id": ObjectId(user_id)})
    
    product_obj_id = ObjectId(product_id)
    
    if not recently_viewed:
        recently_viewed = RecentlyViewed(
            user_id=ObjectId(user_id),
            product_ids=[product_obj_id],
            created_at=str(datetime.utcnow()),
            updated_at=str(datetime.utcnow())
        )
        await recently_viewed.save()
        return recently_viewed
    
    # If product already exists, remove it (we'll add it to front)
    if product_obj_id in recently_viewed.product_ids:
        recently_viewed.product_ids.remove(product_obj_id)
    
    # Add product to front (index 0)
    recently_viewed.product_ids.insert(0, product_obj_id)
    
    # Keep only last 10 products
    if len(recently_viewed.product_ids) > 10:
        recently_viewed.product_ids = recently_viewed.product_ids[:10]
    
    recently_viewed.updated_at = str(datetime.utcnow())
    await recently_viewed.save()
    
    return recently_viewed

async def get_recently_viewed(user_id: str):
    """Get user's recently viewed products"""
    recently_viewed = await RecentlyViewed.find_one({"user_id": ObjectId(user_id)})
    return recently_viewed

async def clear_recently_viewed(user_id: str):
    """Clear user's recently viewed list"""
    recently_viewed = await RecentlyViewed.find_one({"user_id": ObjectId(user_id)})
    if recently_viewed:
        recently_viewed.product_ids = []
        recently_viewed.updated_at = str(datetime.utcnow())
        await recently_viewed.save()
    return recently_viewed
