from fastapi import APIRouter, HTTPException, Depends, Body
from services.payment import create_payment_intent
from auth.jwt_bearer import get_current_user

router = APIRouter()

@router.post("/create-payment-intent")
async def create_payment_intent_api(
    amount: float = Body(...),
    currency: str = Body("usd"),
    user_id: str = Depends(get_current_user)
):
    """
    Create a PaymentIntent for the given amount.
    Returns the client_secret for the frontend to confirm payment.
    """
    intent = await create_payment_intent(amount, currency)
    if not intent:
        raise HTTPException(status_code=400, detail="Payment creation failed")
    
    return {
        "clientSecret": intent.client_secret,
        "id": intent.id
    }
