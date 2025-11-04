from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from auth.jwt_handler import sign_jwt
from database.database import add_user, find_user_by_email, find_user_by_email_code, user_update_password  
from models.user import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse, User, VerifyPasswordRequest, VerifytPasswordResponse
from models.user import UserData, UserSignIn
import random

router = APIRouter()

hash_helper = CryptContext(schemes=["bcrypt"])

@router.post("/login")
async def user_login(user_credentials: UserSignIn = Body(...)):
    user_exists = await find_user_by_email(user_credentials.email)
    
    if not user_exists:
        raise HTTPException(status_code=403, detail="User not exists")

    if not hash_helper.verify(user_credentials.password, user_exists.password):
        raise HTTPException(status_code=403, detail="Incorrect password")

    # ✅ Convert to dict and remove password
    user_data = jsonable_encoder(user_exists)
    if "password" in user_data:
        del user_data["password"]

    return {
        "access_token": sign_jwt(user_exists.email),
        "user": user_data,
        "status":200
    }

@router.post("/signup", response_model=UserData)
async def user_signup(user: User = Body(...)):
    user_exists = await find_user_by_email(user.email)
    if user_exists:
        raise HTTPException(status_code=409, detail="User with email supplied already exists")
    user.password = hash_helper.encrypt(user.password)
    new_user =await add_user(user)
    return new_user

@router.post("/forgotPassword", response_model=ForgotPasswordResponse)
async def user_forgot_password(user: ForgotPasswordRequest):
    user_exists = await find_user_by_email(user.email)
    if not user_exists:
        raise HTTPException(status_code=409, detail="User with this email does not exists.")
    
    verification_code = random.randint(1000, 9999)

    user_exists.verificationCode = verification_code
    await user_exists.save() 

    return {
        "message": "Verification code generated and saved successfully.",
        "verificationCode": verification_code
    }

@router.post("/verifyPasswordCode", response_model=VerifytPasswordResponse)
async def verify_password_code(user: VerifyPasswordRequest):

    user_exists = await find_user_by_email(user.email)
    if not user_exists:
        raise HTTPException(status_code=409, detail="User with this email does not exists.")
    
    is_user_verify = await find_user_by_email_code(user.email,user.verificationCode)
    if not is_user_verify:
        raise HTTPException(status_code=409, detail="Invalid Code.")
    
    isCodeVerify = True

    return {
                "message": "Code is verified Now you can reset your password.",
                "isCodeVerify": isCodeVerify
            }

@router.post("/passreset", response_model=ResetPasswordResponse)
async def user_pass_reset(user: ResetPasswordRequest):
    if user.password != user.confrim_password:
        raise HTTPException(status_code=409, detail="confirm password not match with password.")
    
    user_exists = await find_user_by_email(user.email)
    if not user_exists:
        raise HTTPException(status_code=409, detail="User with this email does not exists.")
    
    password = hash_helper.encrypt(user.password)
    update_user = await user_update_password(user.email,password)
    print(update_user)

    return {
                "message": "Your Password reset successfully."
            }