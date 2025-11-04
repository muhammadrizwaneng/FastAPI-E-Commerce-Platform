from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from fastapi.security import HTTPBasicCredentials

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class User(Document):
    username: str
    email: EmailStr
    password: str 
    role: RoleEnum = RoleEnum.user 
    verificationCode: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "Saar",
                "email": "soleberry012@gmail.com",
                "password": "Changeme123",
                "role":"user",
                "verificationCode":1234
            }
        }

    class Settings:
        name = "user"


class UserSignIn(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    verificationCode: Optional[int] = None
    password: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "Saar",
                "email": "soleberry012@gmail.com",
                "password": "Changeme123"
            }
        }

class UserData(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.user 

    class Config:
        json_schema_extra = {
            "example": {
                "fullname": "Abdulazeez Abdulazeez Adeshina",
                "email": "abdul@youngest.dev",
            }
        }

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "soleberry012@gmail.com"
            }
        }

class VerifyPasswordRequest(BaseModel):
    email: EmailStr
    verificationCode: Optional[int]

    class Config:
        json_schema_extra = {
            "example": {
                "email": "soleberry012@gmail.com",
                "verificationCode":1234
            }
        }

class ForgotPasswordResponse(BaseModel):
    message: str
    verificationCode: Optional[int]  

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Verification code generated and saved successfully.",
                "verificationCode": 1234
            }
        }

class VerifytPasswordResponse(BaseModel):
    message: str
    isCodeVerify: bool  

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Code is verified Now you can reset your password.",
                "isCodeVerify": False
            }
        }

class ResetPasswordResponse(BaseModel):
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Code is verified Now you can reset your password."
            }
        }

class ResetPasswordRequest(BaseModel):
    email : EmailStr
    password: str
    confrim_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email":"soleberry012@gmail.com",
                "password": "password",
                "confrim_password": "password"
            }
        }
