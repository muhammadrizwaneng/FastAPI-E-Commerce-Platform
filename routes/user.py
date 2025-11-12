from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from auth.jwt_handler import sign_jwt
from database.database import add_user, find_user_by_email, find_user_by_email_code, user_update_password  
from models.user import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse, User, VerifyPasswordRequest, VerifytPasswordResponse
from models.user import UserData, UserSignIn
import random
import os
import cloudinary
import cloudinary.uploader
import base64
import uuid

router = APIRouter()

hash_helper = CryptContext(schemes=["bcrypt"])

cloudinary.config(
    # cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    # api_key=os.getenv("CLOUDINARY_API_KEY"),
    # api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    # secure=True
    cloud_name="dnrqj5cgh",
    api_key="844539458168897",
    api_secret="X6bTL_duujuxMgIAzvH6tESdHTU",
    secure=True
)

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


async def _upload_image_to_cloudinary(image_value: str) -> str | None:
    if not image_value:
        return None

    try:
        if image_value.startswith("data:"):
            header, b64data = image_value.split(",", 1)
            ext = "png" if "png" in header else "jpg"
            raw = base64.b64decode(b64data)
            tmp_path = f"/tmp/{uuid.uuid4().hex}.{ext}"

            with open(tmp_path, "wb") as f:
                f.write(raw)

            res = cloudinary.uploader.upload(tmp_path)

            try:
                os.remove(tmp_path)
            except:
                pass

        else:
            res = cloudinary.uploader.upload(image_value)

        return res.get("secure_url")

    except Exception as e:
        print("Cloudinary upload error:", e)
        return None

@router.post("/signup")
async def user_signup(user_payload: dict = Body(...)):
    # Basic validation
    if user_payload.get("password") != user_payload.get("confirmPassword"):
        raise HTTPException(status_code=400, detail="confirm password not match with password.")
    email = user_payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    user_exists = await find_user_by_email(email)
    if user_exists:
        raise HTTPException(status_code=409, detail="User with email supplied already exists")

    # Upload image if provided
    profile_image_value = user_payload.get("profileImage")
    profile_image_url = None
    if profile_image_value:
        profile_image_url = await _upload_image_to_cloudinary(profile_image_value)
        if not profile_image_url:
            raise HTTPException(status_code=400, detail="Profile image upload failed. Please try again.")
    print("profile_image_url",profile_image_url)
    # Hash password once
    hashed_pwd = hash_helper.hash(user_payload["password"])

    # Prepare user data matching your User model fields
    print("profile_image_url",profile_image_url)
    user_data = {
        "name": user_payload.get("name"),
        "username": email.split("@")[0],
        "email": email,
        "password": hashed_pwd,
        "phoneNumber": user_payload.get("phoneNumber"),
        "profileImage": profile_image_url,
        "country": user_payload.get("country"),
        "role": user_payload.get("role", "user")
    }

    # Create User model instance and save
    new_user = User(**{k: v for k, v in user_data.items() if v is not None})
    created = await add_user(new_user)

    # Return created user without password
    created_data = jsonable_encoder(created)
    access_token = sign_jwt(created.email)
    created_data.pop("password", None)
    created_data["access_token"] = access_token
    return JSONResponse(status_code=200, content=created_data)

@router.post("/signup2", response_model=UserData)
async def user_signup(user: User = Body(...)):
    print('===================')
    user_exists = await find_user_by_email(user.email)
    if user.get("password") != user.get("confirmPassword"):
        raise HTTPException(status_code=400, detail="confirm password not match with password.")
    
    user.password = hash_helper.encrypt(user.password)

    email = user.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    user_exists = await find_user_by_email(email)
    if user_exists:
        raise HTTPException(status_code=409, detail="User with email supplied already exists")

    # upload image if provided
    profile_image_value = user.get("profileImage")
    profile_image_url = await _upload_image_to_cloudinary(profile_image_value) if profile_image_value else None

    # create User model instance (adjust fields to your models.user.User as needed)
    hashed_pwd = hash_helper.encrypt(user.get("password"))
    new_user = User(
        name=user.get("name"),
        email=email,
        password=hashed_pwd,
        phoneNumber=user.get("phoneNumber"),
        profileImage=profile_image_url,
        country=user.get("country"),
        role=user.get("role", "user")
        # add any other fields your User model requires or accept defaults
    )
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