from datetime import datetime
from typing import Optional
from bson import ObjectId
from models.cart import Cart, CartItem
from models.wishlist import Wishlist, WishlistItem


# ===== WISHLIST =====
async def add_to_wishlist(user_id: str, product_id: str, variant_name: Optional[str] = None):
    """Add product (with optional variant) to wishlist"""
    wishlist = await Wishlist.find_one({"user_id": ObjectId(user_id)})
    
    if not wishlist:
        wishlist = Wishlist(
            user_id=ObjectId(user_id),
            items=[],
            created_at=str(datetime.utcnow())
        )
    
    # Check if item already exists
    item_exists = any(
        item.product_id == ObjectId(product_id) and item.variant_name == variant_name
        for item in wishlist.items
    )
    
    if not item_exists:
        wishlist.items.append(WishlistItem(product_id=ObjectId(product_id), variant_name=variant_name))
        wishlist.updated_at = str(datetime.utcnow())
        await wishlist.save()
    
    return wishlist

async def remove_from_wishlist(user_id: str, product_id: str, variant_name: Optional[str] = None):
    """Remove product from wishlist"""
    wishlist = await Wishlist.find_one({"user_id": ObjectId(user_id)})
    
    if wishlist:
        wishlist.items = [
            item for item in wishlist.items
            if not (item.product_id == ObjectId(product_id) and item.variant_name == variant_name)
        ]
        wishlist.updated_at = str(datetime.utcnow())
        await wishlist.save()
    
    return wishlist

async def get_wishlist(user_id: str):
    """Get user's wishlist"""
    wishlist = await Wishlist.find_one({"user_id": ObjectId(user_id)})
    return wishlist

# ===== CART =====
async def add_to_cart(user_id: str, product_id: str, quantity: int = 1, variant_name: Optional[str] = None):
    """Add product (with optional variant) to cart"""
    cart = await Cart.find_one({"user_id": ObjectId(user_id)})
    
    if not cart:
        cart = Cart(
            user_id=ObjectId(user_id),
            items=[],
            created_at=str(datetime.utcnow())
        )
    
    # Check if item already exists
    existing_item = next(
        (item for item in cart.items if item.product_id == ObjectId(product_id) and item.variant_name == variant_name),
        None
    )
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart.items.append(CartItem(product_id=ObjectId(product_id), variant_name=variant_name, quantity=quantity))
    
    cart.updated_at = str(datetime.utcnow())
    await cart.save()
    
    return cart

async def remove_from_cart(user_id: str, product_id: str, variant_name: Optional[str] = None):
    """Remove product from cart"""
    cart = await Cart.find_one({"user_id": ObjectId(user_id)})
    
    if cart:
        cart.items = [
            item for item in cart.items
            if not (item.product_id == ObjectId(product_id) and item.variant_name == variant_name)
        ]
        cart.updated_at = str(datetime.utcnow())
        await cart.save()
    
    return cart

async def get_cart(user_id: str):
    """Get user's cart"""
    cart = await Cart.find_one({"user_id": ObjectId(user_id)})
    return cart

async def clear_cart(user_id: str):
    """Clear user's cart"""
    cart = await Cart.find_one({"user_id": ObjectId(user_id)})
    if cart:
        cart.items = []
        cart.updated_at = str(datetime.utcnow())
        await cart.save()
    return cart
