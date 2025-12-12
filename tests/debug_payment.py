import asyncio
import sys
import os

# Add root to path so we can import modules
sys.path.append(os.getcwd())

try:
    from services.payment import create_payment_intent
    from config.config import Settings
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test():
    print("Testing Settings...")
    try:
        settings = Settings()
        print(f"Stripe Key in Settings: {settings.stripe_secret_key.__class__.__name__}")
        if settings.stripe_secret_key:
             print(f"Stripe Key starts with: {settings.stripe_secret_key[:10]}")
        else:
             print("Stripe Key is None")
    except Exception as e:
         print(f"Settings Error: {e}")
         return

    print("\nTesting create_payment_intent...")
    try:
        intent = await create_payment_intent(10.0, "usd")
        if intent:
            print("Sucess! Intent created.")
            print(f"ID: {intent.id}")
            print(f"Client Secret: {intent.client_secret}")
        else:
            print("Failed (returned None). Check previous output for 'Stripe Error'.")
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
