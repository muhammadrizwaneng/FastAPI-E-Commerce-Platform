from fastapi import APIRouter
from database.database import get_categories_with_product_count, seed_categories, get_all_categories

router = APIRouter()

@router.post("/seed-categories")
async def seed_category(names: list[str]):
    return await seed_categories(names)

@router.get("/categories")
async def fetch_categories():
    return await get_all_categories()

@router.get("/categories-with-product-count")
async def categories_with_product_count():
    return await get_categories_with_product_count()