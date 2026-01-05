from models.user import User
from models.admin import Admin

async def user_update_password(email: str, hashed_password: str):
    user = await User.find_one({"email": email})
    if not user:
        return None
    
    user.password = hashed_password
    
    user.verificationCode = None
    
    await user.save()

    return user

async def find_user_by_email(email: str):
    print('===================', email)
    user_data = await User.find_one({"email": email}) 
    return user_data 

async def find_user_by_email_code(email: str,code:int):
    user_data = await User.find_one({"email": email,"verificationCode":code}) 
    return user_data 

async def add_admin(new_admin: Admin) -> Admin:
    admin = await new_admin.create()
    return admin

async def add_user(new_user: User) -> User:
    user = await new_user.create()
    return user
