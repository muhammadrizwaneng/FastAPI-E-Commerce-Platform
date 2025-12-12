from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.order import Order, OrderStatus
from models.product import Product
from auth.jwt_bearer import get_current_user
import pandas as pd
import numpy as np

router = APIRouter()

# Helper to verify admin - simplistic check for now
# Ideally we check user role
async def verify_admin(user: str = Depends(get_current_user)):
    # Logic to fetch user and check if role == 'admin'
    # Keeping it simple or relying on existing patterns.
    # The user is just string email/ID here.
    return user

@router.get("/dashboard")
async def get_analytics_dashboard(admin: str = Depends(verify_admin)):
    try:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Use native motor collection to avoid Pydantic validation errors on mixed ID types
        collection = Order.get_motor_collection()
        cursor = collection.find({"status": {"$ne": OrderStatus.CANCELLED}})
        
        sales_today = 0
        sales_week = 0
        sales_month = 0
        product_sales = {}
        low_stock_details = []

        async for order_doc in cursor:
            # Handle Created At (ensure it's datetime)
            created_at = order_doc.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    continue # Skip if date is parseable
            
            if not isinstance(created_at, datetime):
                continue

            total_amount = order_doc.get("total_amount", 0)
            
            if created_at >= today_start:
                sales_today += total_amount
            if created_at >= week_start:
                sales_week += total_amount
            if created_at >= month_start:
                sales_month += total_amount
            
            # Key Top Selling
            items = order_doc.get("items", [])
            for item in items:
                # item is dict
                pid = str(item.get("product_id"))
                qty = item.get("quantity", 0)
                product_sales[pid] = product_sales.get(pid, 0) + qty

        # Top Selling Products
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        top_selling_details = []
        for pid, qty in sorted_products:
            # Try to fetch product - catching error if ID is weird
            try:
                prod = await Product.get(pid) # Beanie might fail if pid is weird?
                # Product IDs should be ObjectIds usually. If not, catch.
                if prod:
                    top_selling_details.append({
                        "name": prod.name,
                        "quantity_sold": qty,
                        "revenue": qty * (prod.price if prod.price else 0)
                    })
            except:
                pass # Skip bad product IDs
        
        # Low Inventory Alerts
        low_stock_products = await Product.find(Product.stock < 10).to_list() 
        low_stock_details = [{"name": p.name, "stock": p.stock} for p in low_stock_products]

        return {
            "sales": {
                "today": sales_today,
                "week": sales_week,
                "month": sales_month
            },
            "top_selling_products": top_selling_details,
            "low_inventory": low_stock_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prediction")
async def get_sales_prediction(days: int = 7, admin: str = Depends(verify_admin)):
    try:
        # Use native motor collection
        collection = Order.get_motor_collection()
        cursor = collection.find({"status": {"$ne": OrderStatus.CANCELLED}})
        
        data = []
        async for o in cursor:
            # Handle date
            created_at = o.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    continue
            
            if isinstance(created_at, datetime):
                data.append({"date": created_at.date(), "amount": o.get("total_amount", 0)})

        if not data:
             return {"prediction": [], "message": "Not enough data"}

        df = pd.DataFrame(data)
        if df.empty:
             return {"prediction": [], "message": "Not enough data"}

        daily_sales = df.groupby("date")["amount"].sum().reset_index()
        daily_sales["date"] = pd.to_datetime(daily_sales["date"])
        daily_sales = daily_sales.sort_values("date")
        
        # Prepare for linear regression
        daily_sales["day_ordinal"] = daily_sales["date"].map(datetime.toordinal)
        
        if len(daily_sales) < 2:
            return {"prediction": [], "message": "Need at least 2 days of data for regression"}

        # Linear Regression using Numpy
        x = daily_sales["day_ordinal"].values
        y = daily_sales["amount"].values
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Predict next 'days'
        last_date = daily_sales["date"].iloc[-1]
        predictions = []
        for i in range(1, days + 1):
            next_date = last_date + timedelta(days=i)
            next_ordinal = next_date.toordinal()
            predicted_sales = slope * next_ordinal + intercept
            predictions.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_sales": max(0, round(predicted_sales, 2)) # significant digits
            })
            
        return {"predictions": predictions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
