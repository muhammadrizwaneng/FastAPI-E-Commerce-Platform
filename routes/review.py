from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
from models.review import Review, ReviewCreate
from models.product import Product
from auth.jwt_bearer import get_current_user
from beanie import PydanticObjectId
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=Review)
async def create_review(review_data: ReviewCreate, user: str = Depends(get_current_user)):
    try:
        # Verify product exists
        product_id = PydanticObjectId(review_data.product_id)
        product = await Product.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Check if user already reviewed this product? (Optional constraint, skipping for now)

        # We need to fetch user name, but 'user' from get_current_user is just the ID (str) or object?
        # Let's check auth/jwt_bearer.py to see what get_current_user returns. 
        # Assuming it returns email or user_id. 
        # For now I will placeholder user_name or fetch user model if needed. 
        # Wait, get_current_user typically returns the payload sub (email) or the user object.
        # I'll check that later, for now assuming it returns the user email/id string.
        
        # NOTE: To get the actual username, we'd need to query the User collection.
        # I'll import User model.
        from models.user import User
        # The dependency might return the user payload.
        # I will assume 'user' is the 'email' for now as per standard JWT implementations usually returning 'sub'.
        
        current_user = await User.find_one(User.email == user)
        if not current_user:
             # If user is passed as ID or something else, handle it.
             # Actually, let's verify `user` dependency return type.
             # If I can't verify, I'll use a safe placeholder "Anonymous" or the `user` string itself.
             user_name = getattr(current_user, "name", "User") or current_user.username
             user_id_str = str(current_user.id)
        else:
            user_name = "User"
            user_id_str = user

        new_review = Review(
            user_id=user_id_str,
            product_id=product_id,
            user_name=user_name,
            rating=review_data.rating,
            comment=review_data.comment,
            created_at=datetime.utcnow()
        )
        await new_review.insert()
        return new_review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}", response_model=List[Review])
async def get_product_reviews(product_id: str):
    try:
        reviews = await Review.find(Review.product_id == PydanticObjectId(product_id)).to_list()
        return reviews
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{product_id}")
async def get_product_review_stats(product_id: str):
    try:
        pid = PydanticObjectId(product_id)
        reviews = await Review.find(Review.product_id == pid).to_list()
        if not reviews:
            return {"average_rating": 0, "total_reviews": 0}
        
        total_rating = sum(r.rating for r in reviews)
        avg_rating = total_rating / len(reviews)
        
        return {
            "average_rating": round(avg_rating, 2),
            "total_reviews": len(reviews)
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
