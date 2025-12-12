import requests
import json
import random
import time

BASE_URL = "http://localhost:8000"

def test_stripe_flow():
    val = int(time.time())
    email = f"test_{val}@example.com"
    password = "password123"
    
    # Correcting payload to match User model (country is a dict)
    signup_payload = {
        "name": "Stripe Tester",
        "email": email,
        "password": password,
        "confirmPassword": password,
        "phoneNumber": "1234567890",
        "country": {"code": "US", "name": "United States"} 
    }
    
    print(f"1. Signing up user: {email}...")
    try:
        r = requests.post(f"{BASE_URL}/user/signup", json=signup_payload)
        
        token = None
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
        else:
            print(f"   Signup failed: {r.status_code} {r.text}")
            # Try login just in case
            r_login = requests.post(f"{BASE_URL}/user/login", json={"email": email, "password": password})
            if r_login.status_code == 200:
                token = r_login.json().get("access_token")

        if not token:
            print("❌ Failed to get access token.")
            return

        print(f"   ✅ Got Token: {token[:10]}...")

        print("2. Creating Payment Intent...")
        r_pay = requests.post(
            f"{BASE_URL}/payment/create-payment-intent", 
            json={"amount": 20.0, "currency": "usd"}, 
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if r_pay.status_code == 200:
            pay_data = r_pay.json()
            if "clientSecret" in pay_data:
                print("   ✅ SUCCESS: Received clientSecret")
                print(f"   ID: {pay_data.get('id')}")
            else:
                print(f"   ⚠️  Missing clientSecret: {pay_data}")
        else:
            print(f"   ❌ Failed: {r_pay.status_code} {r_pay.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_stripe_flow()
