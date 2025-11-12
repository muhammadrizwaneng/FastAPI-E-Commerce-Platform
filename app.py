from fastapi import FastAPI, Depends
from auth.jwt_bearer import JWTBearer
from config.config import initiate_database
from routes.admin import router as AdminRouter
# from routes.student import router as StudentRouter
from routes.user import router as UserRouter
from routes.product import router as ProductRouter
from routes.order import router as OrderRouter
from routes.aiapi import router as AIRouter
from routes.category_router import router as CategoryRouter
from routes.wishlist_cart import router as WishlistCartRouter
from fastapi.middleware.cors import CORSMiddleware
from routes.seed import router as SeedRouter

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://10.0.2.2:8000", # This is crucial for your emulator
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


token_listener = JWTBearer()


@app.on_event("startup")
async def start_database():
    await initiate_database()


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app."}


app.include_router(AdminRouter, tags=["Administrator"], prefix="/admin")
# app.include_router(StudentRouter,tags=["Students"],prefix="/student",dependencies=[Depends(token_listener)],)
app.include_router(UserRouter, tags=["User"], prefix="/user")
app.include_router(ProductRouter, tags=["Product"], prefix="/products")
app.include_router(OrderRouter, tags=["Orders"], prefix="/order")
app.include_router(AIRouter, tags=["AI"], prefix="/ai")
app.include_router(CategoryRouter, tags=["Category"], prefix="/category")
app.include_router(WishlistCartRouter, tags=["Wishlist & Cart"], prefix="/wishlist_cart")
app.include_router(SeedRouter, tags=["Seed"], prefix="/seed")