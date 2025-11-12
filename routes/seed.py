from fastapi import APIRouter
from faker import Faker
from bson import ObjectId
import random
from models.product import Product, Variant

router = APIRouter()
fake = Faker()

# List of 10 category IDs
categories = {
    "68df9e81804b55b55c50bb17": "Books",
    "68df9e80804b55b55c50bb16": "Home Goods",
    "68df9e81804b55b55c50bb18": "Sports & Outdoors",
    "68df9e81804b55b55c50bb19": "Toys & Games",
    "68df9e82804b55b55c50bb1b": "Automotive",
    "68df9e82804b55b55c50bb1c": "Tools & Home Improvement",
    "68df9e82804b55b55c50bb1d": "Groceries",
    "68df9e83804b55b55c50bb1f": "Pet Supplies",
    "68df9e84804b55b55c50bb21": "Office Supplies",
    "68df9e84804b55b55c50bb22": "Baby & Kids"
}

async def generate_bulk_products(n=20):
    products = []

    for _ in range(n):
        has_variants = random.choice([True, False])
        variants = []

        if has_variants:
            colors = ["Red", "Blue", "Black", "White", "Green", "Yellow"]
            sizes = ["S", "M", "L", "XL", "XXL"]
            for _ in range(random.randint(1, 3)):  # 1-3 variants per product
                variants.append(
                    Variant(
                        name=f"{random.choice(colors)} - {random.choice(sizes)}",
                        color=random.choice(colors),
                        size=random.choice(sizes),
                        price=round(random.uniform(10, 100), 2),
                        discountprice=None,
                        discount_percent=None,
                        stock=random.randint(10, 100)
                    )
                )
        category_id, category_name = random.choice(list(categories.items()))

        product = Product(
            name=fake.sentence(nb_words=3),
            description=fake.paragraph(),
            category=ObjectId(category_id),
            category_name=category_name,  # assign category name automatically
            category_hierarchy=["Category", "Subcategory"],
            brand=fake.company(),
            tags=[fake.word() for _ in range(3)],
            features=[{"label": "Feature1", "value": fake.word()}],
            materials=[fake.word()],
            currency="USD",
            main_image_url=fake.image_url(),
            gallery_images=[fake.image_url() for _ in range(2)],
            has_variants=has_variants,
            variants=variants if has_variants else None,
            price=round(random.uniform(10, 100), 2) if not has_variants else None,
            stock=random.randint(5, 50) if not has_variants else None,
            delivery_options=["Standard Shipping", "Express Shipping"]
        )

        products.append(product)

    # Bulk insert
    await Product.insert_many(products)
    return f"{n} products inserted successfully!"

@router.get("/seed-products")
async def seed_products(count: int = 20):
    """
    Seed the database with fake products.
    Usage: POST /seed/seed-products?count=20
    """
    result = await generate_bulk_products(count)
    return {"message": result}