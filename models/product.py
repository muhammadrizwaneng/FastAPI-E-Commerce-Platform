from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ValidationInfo
from typing import Optional, List
from datetime import datetime
from beanie import Document, PydanticObjectId # Assuming you use PydanticObjectId

# ---------------- Feature Model ----------------
class Feature(BaseModel):
    label: str
    value: str

# ---------------- Variant Model ----------------
class Variant(BaseModel):
    # Note: Backend model expects price as float and stock as int
    # Your frontend sends 'name' and 'price'. You might need to adjust frontend 
    # logic to include 'stock' if you plan to track it per variant.
    name: Optional[str] = None # Added 'name' to match typical frontend structure
    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    discountprice: Optional[float] = None
    discount_percent: Optional[float] = None
    stock: int = Field(0, ge=0, description="Stock cannot be negative.")


# ---------------- Product Model (ADJUSTED) ----------------
class Product(Document):
    # Basic Info
    name: str
    description: Optional[str] = None
    category: PydanticObjectId # Corresponds to 'category_id' from the payload
    category_hierarchy: Optional[List[str]] = None
    brand: Optional[str] = None
    tags: Optional[List[str]] = None
    features: Optional[List[Feature]] = None
    materials: Optional[List[str]] = None
    category_name: Optional[str] = None
    # Pricing & Inventory (For Simple Products)
    # Payload has 'price' and 'stock' when has_variants is False
    price: Optional[float] = None          # ✅ ADDED: The selling price for a simple product
    stock: Optional[int] = Field(None, ge=0, description="Stock for non-variant products.") # ✅ USED

    # Optional Prices (Use base/discount for tracking or if 'price' is calculated)
    # base_price: Optional[float] = None     # Your payload has an empty string, Pydantic handles conversion
    discount_price: Optional[float] = None
    discount_percent: Optional[float] = None # Your payload has an empty string
    currency: str = Field(default="USD")

    # Images
    main_image_url: Optional[HttpUrl] = None
    gallery_images: Optional[List[HttpUrl]] = None

    # Inventory & Variants
    has_variants: bool = False
    variants: Optional[List[Variant]] = None # Empty array in the payload for simple product
    delivery_options: Optional[List[str]] = None 

    # ... (Other audit/metadata fields like availability_status, rating, created_at)

    # ---------------- Validators ----------------

    # Validator to ensure consistency for simple vs. variant product types
    @model_validator(mode='before')
    @classmethod
    def check_simple_vs_variant_data(cls, data: any) -> any:
        # data will be the incoming dict (or object) before validation
        if not isinstance(data, dict):
            return data # Skip if not a dictionary (e.g., if a model instance is passed)
            
        is_variant_product = data.get("has_variants")
        
        # 1. Variant product checks
        if is_variant_product:
            if not data.get("variants"):
                raise ValueError("Variants array must be present if has_variants is True.")
            # Ensure price and stock are NOT set at the top level
            if data.get("price") is not None or data.get("stock") is not None:
                # Remove them before model construction if they exist, or raise error.
                # Removing is often cleaner for data sent from a non-strict source (like your frontend)
                if data.get("price") is not None:
                    del data["price"]
                if data.get("stock") is not None:
                    del data["stock"]
                # Optionally: raise ValueError("Top-level price/stock must not be set when variants are used.")

        # 2. Simple product checks
        else: # has_variants is False or missing (default is False)
            if data.get("price") is None or data.get("stock") is None:
                raise ValueError("Price and stock are required when has_variants is False.")
                
        return data
        
    def apply_discount(self, discount_percent: float, variant_name: Optional[str] = None):
        if self.has_variants and self.variants and variant_name:
            for variant in self.variants:
                if variant.name == variant_name:
                    original_price = variant.price
                    variant.discountprice = round(original_price * (1 - discount_percent / 100), 2)
                    variant.discount_percent = discount_percent
                    return {
                        "variant_name": variant_name,
                        "original_price": original_price,
                        "discounted_price": variant.discountprice,
                        "discount_percent": discount_percent,
                        "success": True
                    }
            return None  # Variant not found
        elif not self.has_variants and self.price is not None:
            original_price = self.price
            self.discount_percent = discount_percent
            self.discount_price = round(original_price * (1 - discount_percent / 100), 2)
            return {
                "original_price": original_price,
                "discounted_price": self.discount_price,
                "discount_percent": discount_percent,
                "success": True
            }
        return None

    # Use @field_validator for base_price, checking for a dependency (has_variants)
    # Note: 'base_price' is validated before the model is fully built, 
    # so we must access 'has_variants' via info.data.
    # @field_validator("base_price")
    # @classmethod
    # def ensure_base_price(cls, base_price, info: ValidationInfo):
    #     if info.data.get("has_variants") and base_price is not None:
    #         raise ValueError("Base price should not be used if has_variants is True.")
    #     return base_price


# ---------------- Collection Settings ----------------
class Settings:
    collection = "products"