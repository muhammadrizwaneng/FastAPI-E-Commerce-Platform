from beanie import Document
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Voucher(Document):
    code: str                       # e.g. NEWUSER, BIGORDER, LOYAL
    name: Optional[str] = None
    type: str = "fixed"             # "fixed" or "percent"
    amount: float = 0.0             # fixed amount or percent (if type=="percent")
    min_order_value: Optional[float] = 0.0
    first_order_only: bool = False
    min_orders_required: Optional[int] = None
    usage_limit_per_user: int = 1
    active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "vouchers"