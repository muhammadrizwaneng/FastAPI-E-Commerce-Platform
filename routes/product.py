from typing import List
from fastapi import APIRouter, Body, HTTPException, Path
from database.database import add_product, apply_discount, get_all_products, get_discounted_products, get_product_by_id, get_products_by_category, update_product, delete_product
from models.product import Product
# from schemas.student import Response, UpdateStudentModel


router = APIRouter()


# @router.post("/products/", response_model=Product)
# async def create_product(product: Product, current_user: User = Depends(get_current_user)):
#     # Check if the user has admin permissions
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Not authorized to add products.")
    
#     # Insert into MongoDB
#     product_data = product.dict(by_alias=True)
#     result = await db["products"].insert_one(product_data)
#     product_data["_id"] = result.inserted_id
#     return product_data
@router.post("/create", response_model=Product)
async def create_product(product: Product):
    #  if not product.description:
    #     completion = client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=[
    #             {"role": "system", "content": "You are an assistant that writes catchy product descriptions."},
    #             {"role": "user", "content": f"Write a short description for a product named {product.name} in category {product.category}."}
    #         ],
    #         max_tokens=100
    #     )
    #     product.ai_generated_description = completion.choices[0].message.content.strip()

    # # ✅ Generate embedding vector
    # embedding = client.embeddings.create(
    #     model="text-embedding-3-small",
    #     input=product.name + " " + (product.description or "")
    # )
    # product.embedding_vector = embedding.data[0].embedding

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
async def update_product_route(product_id: str, product: Product):
    updated_product = await update_product(product_id, product.dict(exclude_unset=True))
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/deleteProducct/{product_id}")
async def delete_product_route(product_id: str):
    success = await delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}


@router.post("/apply-discount")
async def apply_discount_api(
    product_id: str = Body(...),
    discount_percent: float = Body(...),
    variant_name: str = Body(None)
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