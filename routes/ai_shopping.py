from fastapi import APIRouter, HTTPException, Body
from services.ai_service import get_shopping_assistant_response
from pydantic import BaseModel

router = APIRouter()

class ShoppingQuery(BaseModel):
    query: str

@router.post("/assist")
async def ai_shopping_assistant(request: ShoppingQuery):
    """
    AI Shopping Assistant that helps users find products or gives fashion advice.
    """
    try:
        response_text = get_shopping_assistant_response(request.query)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
