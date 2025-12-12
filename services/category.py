from models.category import Category
from models.product import Product
from bson import ObjectId

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
