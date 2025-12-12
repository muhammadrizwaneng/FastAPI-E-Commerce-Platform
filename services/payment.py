from config.config import Settings
import stripe
# Configure Stripe
# In production, this MUST be in .env
STRIPE_SECRET_KEY = Settings().stripe_secret_key
if not STRIPE_SECRET_KEY:
    # Fallback for dev or raise warning
    print("Warning: STRIPE_SECRET_KEY not set. Payments will fail.")

stripe.api_key = STRIPE_SECRET_KEY

async def create_payment_intent(amount: float, currency: str = "usd"):
    """
    Create a Stripe PaymentIntent.
    Amount should be in dollars (float), converted to cents for Stripe.
    """
    try:
        if not STRIPE_SECRET_KEY:
             raise Exception("Stripe API key not configured")

        # Convert amount to cents (integer)
        amount_cents = int(amount * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return intent
    except Exception as e:
        print(f"Stripe Error: {e}")
        return None
