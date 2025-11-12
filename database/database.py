from datetime import datetime
from typing import List, Optional, Union

from beanie import PydanticObjectId
from bson import ObjectId
from models.cart import Cart, CartItem
from models.category import Category
from models.product import Product
from models.admin import Admin
from models.recently_viewed import RecentlyViewed
from models.user import User
from models.order import Order
from models.wishlist import Wishlist, WishlistItem

admin_collection = Admin


async def user_update_password(email: str, hashed_password: str):
    user = await User.find_one({"email": email})
    if not user:
        return None
    
    user.password = hashed_password
    
    user.verificationCode = None
    
    await user.save()

    return user


async def find_user_by_email(email: str):
    user_data = await User.find_one({"email": email}) 
    return user_data 

async def find_user_by_email_code(email: str,code:int):
    user_data = await User.find_one({"email": email,"verificationCode":code}) 
    return user_data 

async def add_admin(new_admin: Admin) -> Admin:
    admin = await new_admin.create()
    return admin

async def add_user(new_user: User) -> User:
    user = await new_user.create()
    return user

async def add_product(new_product: Product) -> Product:
    product = await new_product.create()
    return product

async def get_all_products() -> List[dict]:
    products = await Product.find_all().to_list()
    result = []
    for product in products:
        category = await Category.get(product.category)
        product_dict = product.dict()
        product_dict["category_name"] = category.name if category else None
        result.append(product_dict)
    return result

async def get_product_by_id(product_id: str) -> Optional[Product]:
    
    product = await Product.find_one(Product.id == ObjectId(product_id))
    if not product:
        return None
    category = await Category.get(product.category)

    # return product as dict with category_name
    if category:
        product.category_name = category.name


    return product
    # return product

async def update_product(product_id: str, product_data: dict) -> Optional[Product]:
    product = await Product.find_one(Product.id == ObjectId(product_id))
    if product:
        await product.update({"$set": product_data})
    return product

async def delete_product(product_id: str) -> bool:
    print("product_id",product_id)
    product = await Product.find_one(Product.id == ObjectId(product_id))
    if product:
        await product.delete()
        return True
    return False

async def add_order(new_order: dict) -> Order:
    order = Order(**new_order)
    created_order = await order.create()
    return created_order

async def get_order_by_id(order_id: str) -> Optional[Order]:
    print("order_id", order_id)
    try:
        order = await Order.get(PydanticObjectId(order_id))  # safer
    except Exception:
        return None
    return order

async def seed_categories(names: list[str]):
    categories = []
    for name in names:
        category = Category(name=name)
        created = await category.create()
        categories.append(created)
    return categories

async def get_all_categories():
    categories = await Category.find_all().to_list()
    return categories

async def apply_discount(product_id: str, discount_percent: float, variant_name: str = None):
    product = await Product.find_one(Product.id == ObjectId(product_id))
    if not product:
        return None

    result = product.apply_discount(discount_percent, variant_name)
    if result:
        await product.save()
    return result

async def get_categories_with_product_count():
    categories = await Category.find_all().to_list()
    result = []
    for category in categories:
        count = await Product.find(Product.category == category.id).count()
        result.append({
            "category_id": str(category.id),
            "category_name": category.name,
            "product_count": count,
            "success":True
        })
    return result

async def get_products_by_category(category_id: str) -> List[dict]:
    products = await Product.find(Product.category == ObjectId(category_id)).to_list()
    result = []
    # Get the category once, since all products share the same category
    category = await Category.get(ObjectId(category_id))
    category_name = category.name if category else None
    for product in products:
        product_dict = product.dict()
        product_dict["category_name"] = category_name
        result.append(product_dict)
    return result

async def get_discounted_products() -> List[dict]:
    """
    Return products that have discounts applied either at product level
    (discount_price / discount_percent) or on any variant (variants.discountprice / variants.discount_percent).
    """
    # Use a Mongo OR query to find products with any discount field present and not null
    products = await Product.find(
        {
            "$or": [
                {"discount_price": {"$ne": None}},  # Product-level discount
                {"discount_percent": {"$ne": None}},  # Product-level discount
                {"variants": {"$elemMatch": {"discountprice": {"$ne": None}}}},  # Variant discount
                {"variants": {"$elemMatch": {"discount_percent": {"$ne": None}}}}  # Variant discount
            ]
        }
    ).to_list()
    print(f"Found {len(products)} products with discounts.")
    result = []
    for product in products:
        category = await Category.get(product.category)
        product_dict = product.dict()
        product_dict["category_name"] = category.name if category else None
        result.append(product_dict)
    return result

async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    """
    Update order status.
    Valid statuses: 'processing', 'shipped', 'delivered', 'cancelled'
    """
    print("order_id",order_id)
    print("status",status)
    valid_statuses = ['processing', 'shipped', 'delivered', 'cancelled']
    if status not in valid_statuses:
        return None
    
    order = await Order.find_one(Order.id == ObjectId(order_id))
    if not order:
        return None
    
    order.status = status
    await order.save()
    return order

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