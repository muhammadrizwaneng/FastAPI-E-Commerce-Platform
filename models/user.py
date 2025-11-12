from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from fastapi.security import HTTPBasicCredentials

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class User(Document):
    name: Optional[str] = None
    username: str
    email: EmailStr
    password: str
    phoneNumber: Optional[str] = None
    profileImage: Optional[str] = None
    country: Optional[dict] = None   # or create Country model & use Country
    role: RoleEnum = RoleEnum.user
    verificationCode: Optional[int] = None

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

class Country(BaseModel):
    code: Optional[str] = None
    callingCode: Optional[str] = None
    flag: Optional[str] = None

class UserData(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    email: EmailStr
    phoneNumber: Optional[str] = None
    profileImage: Optional[str] = None  # stored URL from Cloudinary
    country: Optional[Country] = None
    role: RoleEnum = RoleEnum.user

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rizwan",
                "username": "rizwan123",
                "email": "email@gmail.com",
                "phoneNumber": "03000795296",
                "profileImage": "https://res.cloudinary.com/yourcloud/image/upload/v.../profile.jpg",
                "country": { "code": "PK", "callingCode": "92", "flag": "🇵🇰" },
                "role": "user"
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
