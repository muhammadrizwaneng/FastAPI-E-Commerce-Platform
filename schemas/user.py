from pydantic import BaseModel, EmailStr
from fastapi.security import HTTPBasicCredentials

class UserSignIn(HTTPBasicCredentials):
    class Config:
        json_schema_extra = {
            "example": {"username": "user@example.com", "password": "yourpassword"}
        }

class UserData(BaseModel):
    username: str
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "user@example.com",
            }
        }
