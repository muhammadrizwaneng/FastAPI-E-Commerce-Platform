from typing import List, Optional, Union

from bson import ObjectId
from models.category import Category
from models.product import Product
from models.admin import Admin
from models.user import User
from models.order import Order

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
    product_dict = product.dict()
    product_dict["category_name"] = category.name if category else None


    return product_dict
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
    order = await Order.find_one(Order.id == ObjectId(order_id))
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