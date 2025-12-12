from fastapi import APIRouter, HTTPException, Body, Depends
from auth.jwt_bearer import get_current_user
from services.cart_wishlist import (
    add_to_wishlist, remove_from_wishlist, get_wishlist,
    add_to_cart, remove_from_cart, get_cart, clear_cart
)
from typing import Optional

router = APIRouter()

# ===== WISHLIST ENDPOINTS =====

@router.post("/wishlist/add")
async def add_wishlist(
    user_id: str = Depends(get_current_user),
    product_id: str = Body(...),
    variant_name: Optional[str] = Body(None)
):
    """Add product to wishlist"""
    result = await add_to_wishlist(user_id, product_id, variant_name)
    return {"success": True, "message": "Added to wishlist", "wishlist": result}

@router.post("/wishlist/remove")
async def remove_wishlist(
    user_id: str = Depends(get_current_user),
    product_id: str = Body(...),
    variant_name: Optional[str] = Body(None)
):
    """Remove product from wishlist"""
    result = await remove_from_wishlist(user_id, product_id, variant_name)
    return {"success": True, "message": "Removed from wishlist", "wishlist": result}

@router.get("/wishlist")
async def get_user_wishlist(user_id: str = Depends(get_current_user)):
    """Get user's wishlist"""
    wishlist = await get_wishlist(user_id)
    if not wishlist:
        return {"items": []}
    return wishlist

# ===== CART ENDPOINTS =====

@router.post("/cart/add")
async def add_cart(
    user_id: str = Depends(get_current_user),
    product_id: str = Body(...),
    quantity: int = Body(1),
    variant_name: Optional[str] = Body(None)
):
    """Add product to cart"""
    result = await add_to_cart(user_id, product_id, quantity, variant_name)
    return {"success": True, "message": "Added to cart", "cart": result}

@router.post("/cart/remove")
async def remove_cart(
    user_id: str = Depends(get_current_user),
    product_id: str = Body(...),
    variant_name: Optional[str] = Body(None)
):
    """Remove product from cart"""
    result = await remove_from_cart(user_id, product_id, variant_name)
    return {"success": True, "message": "Removed from cart", "cart": result}

@router.get("/cart")
async def get_user_cart(user_id: str = Depends(get_current_user)):
    """Get user's cart"""
    cart = await get_cart(user_id)
    if not cart:
        return {"items": []}
    return cart

@router.delete("/cart")
async def clear_user_cart(user_id: str = Depends(get_current_user)):
    """Clear user's cart"""
    await clear_cart(user_id)
    return {"success": True, "message": "Cart cleared"}