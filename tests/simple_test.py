import requests
import time

BASE_URL = "http://localhost:8000"

def test():
    email = f"test_stripe_{int(time.time())}@example.com"
    password = "password123"
    payload = {
        "name": "Tester",
        "email": email,
        "password": password,
        "confirmPassword": password,
        "phoneNumber": "1234567890"
        # Omitted country to avoid validation issues
    }
    
    print(f"Signup {email}...")
    try:
        r = requests.post(f"{BASE_URL}/user/signup", json=payload)
        if r.status_code != 200:
            print(f"Signup failed: {r.status_code} {r.text}")
            return
        
        token = r.json().get("access_token")
        if not token:
            print("No token received")
            return
            
        print("Got token. Testing Payment...")
        r_pay = requests.post(
            f"{BASE_URL}/payment/create-payment-intent",
            json={"amount": 10.0, "currency": "usd"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Payment Status: {r_pay.status_code}")
        print(r_pay.json())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
