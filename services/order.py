from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId
from bson import ObjectId
from models.order import Order
from models.voucher import Voucher

async def get_user_order_count(user_id: str) -> int:
    return await Order.find(Order.user_id == PydanticObjectId(user_id)).count()

async def is_user_first_order(user_id: str) -> bool:
    cnt = await get_user_order_count(user_id)
    return cnt == 0

async def get_voucher_by_code(code: str) -> Optional[Voucher]:
    return await Voucher.find_one({"code": code, "active": True})

def _compute_discount_amount(v: Voucher, order_total: float) -> float:
    if v.type == "percent":
        return round(order_total * (v.amount / 100.0), 2)
    return round(min(v.amount, order_total), 2)

async def find_applicable_vouchers_for_user(user_id: str, order_total: float) -> list:
    """
    Return list of Voucher that are applicable given user/order.
    """
    now = datetime.utcnow()
    vouchers = await Voucher.find({"active": True}).to_list()
    applicable = []
    user_order_count = await get_user_order_count(user_id)

    for v in vouchers:
        if v.expires_at and v.expires_at < now:
            continue
        if v.min_order_value and order_total < v.min_order_value:
            continue
        if v.first_order_only and user_order_count > 0:
            continue
        if v.min_orders_required and user_order_count < v.min_orders_required:
            continue
        applicable.append(v)
    return applicable

async def choose_best_voucher(user_id: str, order_total: float) -> Optional[dict]:
    """
    Return best voucher (max discount) or None.
    """
    applicable = await find_applicable_vouchers_for_user(user_id, order_total)
    best = None
    best_discount = 0.0
    for v in applicable:
        discount = _compute_discount_amount(v, order_total)
        if discount > best_discount:
            best_discount = discount
            best = v
    if not best:
        return None
    return {"voucher": best, "discount": best_discount}

async def apply_voucher_to_order(order_id: str, voucher_code: str) -> Optional[Order]:
    """
    Validate voucher then apply to order document: set voucher_code, discount_amount and update totals.
    Returns updated Order or None if invalid.
    """
    order = await Order.find_one(Order.id == PydanticObjectId(order_id))
    if not order:
        return None
    voucher = await get_voucher_by_code(voucher_code)
    if not voucher:
        return None

    # check eligibility
    user_id = str(order.user_id)
    user_order_count = await get_user_order_count(user_id)
    if voucher.first_order_only and user_order_count > 0:
        return None
    if voucher.min_orders_required and user_order_count < voucher.min_orders_required:
        return None
    if voucher.min_order_value and order.total_price < voucher.min_order_value:
        return None
    now = datetime.utcnow()
    if voucher.expires_at and voucher.expires_at < now:
        return None

    discount_amount = _compute_discount_amount(voucher, order.total_price)
    order.voucher_code = voucher.code
    order.discount_amount = discount_amount
    order.total_after_discount = round(order.total_price - discount_amount, 2)
    # Track that voucher used (you can add VoucherUsage tracking if needed)
    await order.save()
    return order

async def add_order(new_order: dict) -> Order:
    order = Order(**new_order)
    created_order = await order.create()

    # auto apply best voucher (new-user / big-order / loyal) if any
    try:
        best = await choose_best_voucher(str(created_order.user_id), created_order.total_price)
        if best:
            await apply_voucher_to_order(str(created_order.id), best["voucher"].code)
            # refresh created_order after voucher application
            try:
                created_order = await Order.get(created_order.id)
            except Exception:
                pass
    except Exception as e:
        print("Voucher auto-apply failed:", e)

    return created_order

async def get_order_by_id(order_id: str) -> Optional[Order]:
    print("order_id", order_id)
    try:
        order = await Order.get(PydanticObjectId(order_id))  # safer
    except Exception:
        return None
    return order

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
