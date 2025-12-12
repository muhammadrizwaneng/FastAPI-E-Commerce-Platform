from typing import List, Optional
from beanie import PydanticObjectId
from bson import ObjectId
from models.product import Product
from models.category import Category

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

    if category:
        product.category_name = category.name
    return product

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

async def apply_discount(product_id: str, discount_percent: float, variant_name: str = None):
    product = await Product.find_one(Product.id == ObjectId(product_id))
    if not product:
        return None

    result = product.apply_discount(discount_percent, variant_name)
    if result:
        await product.save()
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
