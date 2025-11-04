from fastapi import Body, APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext

from auth.jwt_handler import sign_jwt
from database.database import add_admin
from models.admin import Admin
from schemas.admin import AdminData, AdminSignIn

router = APIRouter()

hash_helper = CryptContext(schemes=["bcrypt"])


@router.post("/login")
async def admin_login(admin_credentials: AdminSignIn = Body(...)):
    admin_exists = await Admin.find_one(Admin.email == admin_credentials.username)
    if admin_exists:
        password = hash_helper.verify(admin_credentials.password, admin_exists.password)
        if password:
            # return sign_jwt(admin_credentials.username)
            user_data = jsonable_encoder(admin_exists)
            if "password" in user_data:
                del user_data["password"]

            return {
                "access_token": sign_jwt(admin_credentials.username),
                "user": user_data
            }

        raise HTTPException(status_code=403, detail="Incorrect email or password")

    raise HTTPException(status_code=403, detail="Incorrect email or password")


@router.post("/adminSignup", response_model=AdminData)
async def admin_signup(admin: Admin = Body(...)):
    admin_exists = await Admin.find_one(Admin.email == admin.email)
    if admin_exists:
        raise HTTPException(
            status_code=409, detail="Admin with email supplied already exists"
        )

    admin.password = hash_helper.encrypt(admin.password)
    new_admin = await add_admin(admin)
    return new_admin
