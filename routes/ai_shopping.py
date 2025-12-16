import os
from fastapi import APIRouter, HTTPException, Body
# from services.ai_service import get_shopping_assistant_response
from pydantic import BaseModel
from config.config import Settings
import google.generativeai as genai
import openai

router = APIRouter()

class ShoppingQuery(BaseModel):
    query: str

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GEMINI_API_KEY = Settings().gemini_api_key
genai.configure(api_key=GEMINI_API_KEY)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY



def get_shopping_assistant_response(user_query: str):
    """
    Uses Gemini to provide a shopping assistant experience.
    """
    try:
        # Using the recommended model for speed and general intelligence
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        system_prompt = (
            "You are a helpful and knowledgeable AI Shopping Assistant for a fashion e-commerce store. "
            "Help the user find products, suggestions, or advice. "
            "If the user asks for products, suggest generic terms they can search for if you don't have catalog access, "
            "or just give fashion advice. "
            "Be concise and friendly.\n\n"
        )
        
        full_prompt = f"{system_prompt}User Query: {user_query}\nAnswer:"
        
        # This is where the error 429 occurs due to quota limits
        response = model.generate_content(full_prompt) 
        return response.text
    except Exception as e:
        # This will catch the 429 error, which should disappear after your quota resets/is increased.
        return f"I'm having trouble thinking right now. Error: {str(e)}"


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
