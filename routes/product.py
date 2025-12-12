from typing import List
from fastapi import APIRouter, Body, HTTPException, Path, Depends
from services.product import add_product, apply_discount, get_all_products, get_discounted_products, get_product_by_id, get_products_by_category, update_product, delete_product
from services.recently_viewed import add_to_recently_viewed, clear_recently_viewed, get_recently_viewed
from models.product import Product
from auth.jwt_bearer import get_current_user

router = APIRouter()

@router.post("/create", response_model=Product)
async def create_product(product: Product, user_id: str = Depends(get_current_user)):
    new_product = await add_product(product)
    return new_product

@router.get("/getAllProducts", response_model=List[Product])
async def list_products():
    return await get_all_products()

@router.get("/product/{product_id}", response_model=Product)
async def read_product(product_id: str):
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/updateProduct/{product_id}", response_model=Product)
async def update_product_route(product_id: str, product: Product, user_id: str = Depends(get_current_user)):
    print("product_id",product_id)
    updated_product = await update_product(product_id, product.dict(exclude_unset=True))
    print("updated_product",updated_product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/deleteProducct/{product_id}")
async def delete_product_route(product_id: str, user_id: str = Depends(get_current_user)):
    success = await delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}


@router.post("/apply-discount")
async def apply_discount_api(
    product_id: str = Body(...),
    discount_percent: float = Body(...),
    variant_name: str = Body(None),
    user_id: str = Depends(get_current_user)
):
    result = await apply_discount(
        product_id=product_id,
        discount_percent=discount_percent,
        variant_name=variant_name
    )
    if not result:
        raise HTTPException(status_code=404, detail="Product or variant not found")
    return result


@router.get("/get-products-by-category/{category_id}", response_model=List[Product])
async def get_products_by_category_route(category_id: str):
    products = await get_products_by_category(category_id)
    return products

@router.get("/get-discounted-products", response_model=List[dict])
async def list_discounted_products():
    """
    Get all products that have discounts applied (product-level or variant-level).
    """
    return await get_discounted_products()



@router.post("/recently-viewed/add")
async def add_recently_viewed(
    product_id: str = Body(...),
    user_id: str = Depends(get_current_user)
):
    """Add product to recently viewed (max 10, newest first)"""
    result = await add_to_recently_viewed(user_id, product_id)
    return {
        "success": True,
        "message": "Added to recently viewed",
        "product_ids": [str(pid) for pid in result.product_ids]
    }

@router.get("/recently-viewed")
async def get_user_recently_viewed(user_id: str = Depends(get_current_user)):
    """Get user's recently viewed products"""
    recently_viewed = await get_recently_viewed(user_id)
    if not recently_viewed:
        return {"product_ids": []}
    return {
        "product_ids": [str(pid) for pid in recently_viewed.product_ids]
    }

@router.delete("/recently-viewed")
async def clear_user_recently_viewed(user_id: str = Depends(get_current_user)):
    """Clear user's recently viewed list"""
    await clear_recently_viewed(user_id)
    return {"success": True, "message": "Recently viewed cleared"}