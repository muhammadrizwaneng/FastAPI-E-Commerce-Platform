from fastapi import APIRouter, Body, HTTPException
from services.order import (
    _compute_discount_amount, 
    choose_best_voucher, 
    apply_voucher_to_order, 
    get_voucher_by_code, 
    find_applicable_vouchers_for_user
)
from typing import Optional

router = APIRouter()

@router.post("/voucher/suggest")
async def suggest_voucher(user_id: str = Body(...), order_total: float = Body(...)):
    """
    Suggest the best available voucher for this user/order.
    """
    best = await choose_best_voucher(user_id, order_total)
    if not best:
        return {"applied": False, "message": "No vouchers available"}
    v = best["voucher"]
    return {
        "applied": True,
        "voucher_code": v.code,
        "voucher_name": v.name,
        "discount": best["discount"]
    }

@router.post("/voucher/validate")
async def validate_voucher(user_id: str = Body(...), voucher_code: str = Body(...), order_total: float = Body(...)):
    v = await get_voucher_by_code(voucher_code)
    if not v:
        raise HTTPException(status_code=404, detail="Voucher not found or inactive")
    
    applicable = await find_applicable_vouchers_for_user(user_id, order_total)
    codes = [x.code for x in applicable]
    if v.code not in codes:
        raise HTTPException(status_code=400, detail="Voucher not applicable")
    discount = _compute_discount_amount(v, order_total)
    return {"valid": True, "discount": discount}

@router.post("/voucher/apply")
async def apply_voucher(order_id: str = Body(...), voucher_code: str = Body(...)):
    order = await apply_voucher_to_order(order_id, voucher_code)
    if not order:
        raise HTTPException(status_code=400, detail="Cannot apply voucher")
    return {"success": True, "order_id": str(order.id), "discount_amount": order.discount_amount, "total_after_discount": order.total_after_discount}