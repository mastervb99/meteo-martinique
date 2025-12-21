"""FastAPI REST API for SMS and Email alert subscriptions.

Provides endpoints for:
- OTP verification flow (SMS + Email)
- Subscription management
- Alert testing
- Statistics

Uses Brevo for SMS and Email delivery.
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, model_validator
import re

from brevo_service import BrevoSMSService, BrevoEmailService, OTPService, AlertService
from subscriptions import SubscriptionManager
from stripe_service import stripe_service
from config import OUTPUT_DIR, MAPS_DIR, CHARTS_DIR, DATA_DIR, MARTINIQUE, STRIPE_PUBLISHABLE_KEY, SUBSCRIPTION_PRICES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Meteo Martinique - Weather Dashboard & Alerts API",
    description="Weather maps, charts, forecasts, and SMS/Email alert subscriptions",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sms_service = BrevoSMSService()
email_service = BrevoEmailService()
otp_service = OTPService(sms_service, email_service)
alert_service = AlertService(sms_service, email_service)
subscription_manager = SubscriptionManager()

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


class SubscribeRequest(BaseModel):
    """Request model for subscription."""
    phone: Optional[str] = None
    email: Optional[str] = None
    profile: Optional[str] = "Particulier"
    notification_prefs: Optional[str] = "sms"

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None or v == "":
            return None
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Invalid phone number')
        return cleaned

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None or v == "":
            return None
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email address')
        return v.strip().lower()

    @field_validator('notification_prefs')
    @classmethod
    def validate_prefs(cls, v):
        if v not in ('sms', 'email', 'both'):
            return 'sms'
        return v

    @model_validator(mode='after')
    def check_contact_method(self):
        if self.notification_prefs == 'sms' and not self.phone:
            raise ValueError('Phone required for SMS notifications')
        if self.notification_prefs == 'email' and not self.email:
            raise ValueError('Email required for email notifications')
        if self.notification_prefs == 'both' and (not self.phone or not self.email):
            raise ValueError('Both phone and email required')
        return self


# Alias for backward compatibility
PhoneRequest = SubscribeRequest


class OTPVerifyRequest(BaseModel):
    """Request model for OTP verification."""
    phone: str
    otp: str

    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be 6 digits')
        return v


class SubscriptionUpdate(BaseModel):
    """Request model for subscription updates."""
    phone: Optional[str] = None
    reference_code: Optional[str] = None
    profile: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the alerts subscription page."""
    html_path = STATIC_DIR / "alerte.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>Météo Martinique - Alertes SMS</h1><p>API is running</p>")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "sms_configured": sms_service.is_configured(),
        "service": "Météo Martinique Alertes SMS"
    }


@app.post("/api/subscribe")
async def subscribe(request: SubscribeRequest):
    """Subscribe to weather alerts.

    Creates subscription and sends welcome message immediately.
    No OTP verification required.
    """
    # Create subscription
    result = subscription_manager.create_subscription(
        phone_number=request.phone,
        email=request.email,
        profile=request.profile,
        notification_prefs=request.notification_prefs
    )

    if not result["success"]:
        if "already subscribed" in result.get("error", "").lower():
            raise HTTPException(status_code=409, detail=result["error"])
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create subscription"))

    # Mark as verified immediately
    if request.phone:
        subscription_manager.verify_subscription(request.phone)
    if request.email:
        # Also mark email verified
        from subscriptions import get_db
        with get_db() as conn:
            conn.execute(
                "UPDATE subscribers SET verified = TRUE, email_verified = TRUE WHERE email = ?",
                (request.email.strip().lower(),)
            )

    # Send welcome message
    welcome_result = alert_service.send_welcome(
        phone_number=request.phone,
        email=request.email,
        profile=request.profile,
        notification_prefs=request.notification_prefs
    )

    return {
        "success": True,
        "message": "Subscription confirmed",
        "reference_code": result.get("reference_code"),
        "profile": request.profile,
        "notification_prefs": request.notification_prefs,
        "welcome_sent": welcome_result.get("success", False)
    }


@app.post("/api/subscribe/test")
async def send_test_alert(request: SubscribeRequest):
    """Send test alert to subscriber via configured channel(s)."""
    subscriber = None
    if request.phone:
        subscriber = subscription_manager.get_subscriber(phone_number=request.phone)
    if not subscriber and request.email:
        subscriber = subscription_manager.get_subscriber(email=request.email)

    if not subscriber or not subscriber["active"] or not subscriber["verified"]:
        raise HTTPException(status_code=404, detail="Active verified subscription not found")

    notification_prefs = subscriber.get("notification_prefs", "sms")
    result = alert_service.send_test_alert(
        phone_number=subscriber.get("phone_number"),
        email=subscriber.get("email"),
        profile=subscriber["profile"],
        notification_prefs=notification_prefs
    )

    if result["success"]:
        # Log for each channel
        if result.get("sms") and result["sms"].get("success"):
            subscription_manager.log_alert(
                subscriber_id=subscriber["id"],
                phenomenon_type="Test",
                color_code=2,
                message="Test alert",
                delivery_status="sent",
                delivery_channel="sms",
                message_id=result["sms"].get("message_id")
            )
        if result.get("email") and result["email"].get("success"):
            subscription_manager.log_alert(
                subscriber_id=subscriber["id"],
                phenomenon_type="Test",
                color_code=2,
                message="Test alert",
                delivery_status="sent",
                delivery_channel="email",
                message_id=result["email"].get("message_id")
            )

    return {
        "success": result["success"],
        "message": f"Test alert sent via {notification_prefs}" if result["success"] else "Failed to send test alert"
    }


@app.get("/api/subscribe/{reference_code}")
async def get_subscription(reference_code: str):
    """Get subscription details by reference code."""
    subscriber = subscription_manager.get_subscriber(reference_code=reference_code)

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "reference_code": subscriber["reference_code"],
        "profile": subscriber["profile"],
        "notification_prefs": subscriber.get("notification_prefs", "sms"),
        "active": subscriber["active"],
        "verified": subscriber["verified"],
        "created_at": subscriber["created_at"]
    }


@app.put("/api/subscribe/update")
async def update_subscription(request: SubscriptionUpdate):
    """Update subscription profile."""
    if not request.phone and not request.reference_code:
        raise HTTPException(status_code=400, detail="Phone or reference code required")

    if not request.profile:
        raise HTTPException(status_code=400, detail="Profile is required")

    phone = request.phone
    if request.reference_code and not phone:
        subscriber = subscription_manager.get_subscriber(reference_code=request.reference_code)
        if subscriber:
            phone = subscriber["phone_number"]

    if not phone:
        raise HTTPException(status_code=404, detail="Subscription not found")

    result = subscription_manager.update_profile(phone, request.profile)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return {"success": True, "message": "Profile updated"}


@app.delete("/api/subscribe/unsubscribe")
async def unsubscribe(request: SubscriptionUpdate):
    """Unsubscribe from alerts."""
    result = subscription_manager.unsubscribe(
        phone_number=request.phone,
        reference_code=request.reference_code
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return {"success": True, "message": "Unsubscribed successfully"}


@app.post("/api/webhook/incoming")
async def incoming_sms(request: Request):
    """Handle incoming SMS (for STOP commands).

    Twilio webhook endpoint.
    """
    form_data = await request.form()
    from_number = form_data.get("From", "")
    body = form_data.get("Body", "").strip().upper()

    logger.info(f"Incoming SMS from {from_number[:8]}***: {body}")

    if body == "STOP":
        result = subscription_manager.unsubscribe(phone_number=from_number)
        logger.info(f"STOP processed for {from_number[:8]}***: {result}")

    return {"status": "received"}


@app.get("/api/stats")
async def get_stats():
    """Get subscription statistics."""
    return subscription_manager.get_stats()


@app.get("/api/profiles")
async def get_profiles():
    """Get available profile types."""
    return {
        "profiles": subscription_manager.PROFILES,
        "descriptions": {
            "Particulier": "Pour les particuliers - conseils généraux",
            "Professionnel (BTP / agriculture)": "Conseils adaptés aux professionnels de terrain",
            "Nautique / pêche / plaisance": "Alertes marines et conseils nautiques",
            "Tourisme / plages": "Conseils pour touristes et activités plage"
        }
    }


# ============================================================================
# STRIPE PAYMENT ENDPOINTS
# ============================================================================

class CheckoutRequest(BaseModel):
    """Request model for Stripe checkout."""
    plan_type: str  # "sms_monthly" or "email_yearly"
    email: str
    phone: Optional[str] = None

    @field_validator('plan_type')
    @classmethod
    def validate_plan(cls, v):
        if v not in ("sms_monthly", "email_yearly"):
            raise ValueError('Plan must be sms_monthly or email_yearly')
        return v


@app.get("/api/stripe/config")
async def get_stripe_config():
    """Get Stripe publishable key and pricing info."""
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "prices": {
            "sms_monthly": {
                "amount": SUBSCRIPTION_PRICES["sms_monthly"]["amount"] / 100,
                "currency": "EUR",
                "interval": "mois",
                "name": "Alertes SMS"
            },
            "email_yearly": {
                "amount": SUBSCRIPTION_PRICES["email_yearly"]["amount"] / 100,
                "currency": "EUR",
                "interval": "an",
                "name": "Alertes Email"
            }
        }
    }


class PaymentIntentRequest(BaseModel):
    """Request model for embedded payment."""
    plan_type: str
    email: str
    phone: Optional[str] = None

    @field_validator('plan_type')
    @classmethod
    def validate_plan(cls, v):
        if v not in ("sms_monthly", "email_yearly"):
            raise ValueError('Plan must be sms_monthly or email_yearly')
        return v


@app.post("/api/stripe/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    """Create PaymentIntent for embedded payment form."""
    result = stripe_service.create_payment_intent(
        plan_type=request.plan_type,
        customer_email=request.email,
        customer_phone=request.phone
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Payment intent creation failed"))

    return result


@app.post("/api/stripe/confirm-payment")
async def confirm_payment(payment_intent_id: str):
    """Confirm payment and activate subscription."""
    result = stripe_service.confirm_payment_intent(payment_intent_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Payment confirmation failed"))

    # If payment succeeded, create subscription in our DB
    if result.get("paid"):
        phone = result.get("customer_phone")
        email = result.get("customer_email")
        plan_type = result.get("plan_type")

        # Determine notification type based on plan
        notification_prefs = "sms" if plan_type == "sms_monthly" else "email"

        # Create subscription in our database
        sub_result = subscription_manager.create_subscription(
            phone_number=phone if phone else None,
            email=email,
            profile="Particulier",
            notification_prefs=notification_prefs
        )

        if sub_result["success"]:
            # Mark as verified and update with Stripe info
            from subscriptions import get_db
            with get_db() as conn:
                conn.execute(
                    """UPDATE subscribers
                       SET verified = TRUE, email_verified = TRUE,
                           stripe_subscription_id = ?, payment_status = 'active'
                       WHERE (phone_number = ? OR email = ?)""",
                    (result.get("subscription_id"), phone, email)
                )

            # Send welcome message
            alert_service.send_welcome(
                phone_number=phone if notification_prefs == "sms" else None,
                email=email if notification_prefs == "email" else None,
                profile="Particulier",
                notification_prefs=notification_prefs
            )

        result["subscription_created"] = sub_result.get("success", False)
        result["reference_code"] = sub_result.get("reference_code")

    return result


@app.post("/api/stripe/checkout")
async def create_checkout(request: CheckoutRequest):
    """Create Stripe checkout session (legacy - redirect flow)."""
    result = stripe_service.create_checkout_session(
        plan_type=request.plan_type,
        customer_email=request.email,
        customer_phone=request.phone,
        success_url="https://meteo-martinique.onrender.com/success",
        cancel_url="https://meteo-martinique.onrender.com/"
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Checkout failed"))

    return result


@app.get("/api/stripe/verify/{session_id}")
async def verify_payment(session_id: str):
    """Verify payment and activate subscription."""
    result = stripe_service.verify_session(session_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Verification failed"))

    if result.get("paid"):
        # Activate subscription in our database
        phone = result.get("customer_phone")
        plan_type = result.get("plan_type")

        # Update subscription with payment info
        if phone:
            from subscriptions import get_db
            with get_db() as conn:
                conn.execute(
                    """UPDATE subscribers
                       SET stripe_subscription_id = ?, payment_status = 'active'
                       WHERE phone_number = ?""",
                    (result.get("subscription_id"), phone)
                )

        logger.info(f"Payment verified for {plan_type}: {result.get('subscription_id')}")

    return result


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    result = stripe_service.handle_webhook(payload, sig_header)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    # Handle events
    if result.get("event") == "checkout_completed":
        logger.info(f"Checkout completed: {result.get('subscription_id')}")
    elif result.get("event") == "subscription_cancelled":
        logger.info(f"Subscription cancelled: {result.get('subscription_id')}")
    elif result.get("event") == "payment_failed":
        logger.warning(f"Payment failed: {result.get('customer_id')}")

    return {"received": True}


@app.get("/api/stripe/status")
async def get_payment_status(email: str):
    """Check subscription status for a customer."""
    result = stripe_service.get_subscription_status(email)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ============================================================================
# WEATHER DATA API ENDPOINTS
# ============================================================================

@app.get("/api/weather/current")
async def get_current_weather():
    """Get current weather summary for Martinique."""
    import json
    import pandas as pd

    result = {"cities": [], "vigilance": None, "updated_at": None}

    # Load city forecasts
    forecast_path = Path(DATA_DIR) / "city_forecasts.csv"
    if forecast_path.exists():
        df = pd.read_csv(forecast_path)
        today_df = df.drop_duplicates(subset=["city"], keep="first")
        result["cities"] = today_df.to_dict(orient="records")

    # Load vigilance
    vigilance_path = Path(DATA_DIR) / "vigilance_alerts.json"
    if vigilance_path.exists():
        with open(vigilance_path) as f:
            result["vigilance"] = json.load(f)

    result["martinique"] = MARTINIQUE
    return result


@app.get("/api/weather/forecast/{city}")
async def get_city_forecast(city: str):
    """Get 7-day forecast for a specific city."""
    import pandas as pd

    forecast_path = Path(DATA_DIR) / "city_forecasts.csv"
    if not forecast_path.exists():
        raise HTTPException(status_code=404, detail="Forecast data not available")

    df = pd.read_csv(forecast_path)
    city_df = df[df["city"].str.lower() == city.lower()]

    if city_df.empty:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    return {"city": city, "forecasts": city_df.to_dict(orient="records")}


@app.get("/api/weather/hourly/{city}")
async def get_hourly_forecast(city: str):
    """Get hourly forecast for a specific city."""
    import pandas as pd
    import unicodedata

    # Normalize city name (remove accents, lowercase, hyphens)
    city_normalized = unicodedata.normalize('NFD', city)
    city_normalized = ''.join(c for c in city_normalized if unicodedata.category(c) != 'Mn')
    city_slug = city_normalized.lower().replace(' ', '-')

    hourly_path = Path(DATA_DIR) / f"hourly_{city_slug}.csv"

    if not hourly_path.exists():
        raise HTTPException(status_code=404, detail=f"Hourly data not available for '{city}'")

    df = pd.read_csv(hourly_path)
    return {"city": city, "hourly": df.to_dict(orient="records")}


@app.get("/api/weather/vigilance")
async def get_vigilance():
    """Get current vigilance alerts."""
    import json

    vigilance_path = Path(DATA_DIR) / "vigilance_alerts.json"
    if not vigilance_path.exists():
        return {"max_color": 1, "phenomenons": [], "message": "No vigilance data"}

    with open(vigilance_path) as f:
        return json.load(f)


@app.get("/api/cities")
async def get_cities():
    """Get list of Martinique cities with coordinates."""
    return {"cities": MARTINIQUE["major_cities"]}


# ============================================================================
# MAPS API ENDPOINTS
# ============================================================================

@app.get("/api/maps/vigilance")
async def get_vigilance_map():
    """Get vigilance map HTML."""
    map_path = Path(MAPS_DIR) / "vigilance_map.html"
    if not map_path.exists():
        # Generate map on demand
        from map_generator import MartiniqueMapGenerator
        MartiniqueMapGenerator().generate_vigilance_map()

    if map_path.exists():
        return FileResponse(map_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Vigilance map not available")


@app.get("/api/maps/forecast")
async def get_forecast_map():
    """Get forecast map HTML."""
    map_path = Path(MAPS_DIR) / "forecast_map.html"
    if not map_path.exists():
        from map_generator import MartiniqueMapGenerator
        MartiniqueMapGenerator().generate_forecast_map()

    if map_path.exists():
        return FileResponse(map_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Forecast map not available")


@app.get("/api/maps/rain")
async def get_rain_map():
    """Get rain/precipitation map HTML."""
    map_path = Path(MAPS_DIR) / "rain_map.html"
    if not map_path.exists():
        from map_generator import MartiniqueMapGenerator
        MartiniqueMapGenerator().generate_rain_map()

    if map_path.exists():
        return FileResponse(map_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Rain map not available")


# ============================================================================
# CHARTS API ENDPOINTS
# ============================================================================

@app.get("/api/charts/temperature")
async def get_temperature_chart():
    """Get temperature forecast chart HTML."""
    chart_path = Path(CHARTS_DIR) / "temperature_chart.html"
    if not chart_path.exists():
        from chart_generator import MartiniqueChartGenerator
        MartiniqueChartGenerator().generate_temperature_chart()

    if chart_path.exists():
        return FileResponse(chart_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Temperature chart not available")


def _normalize_city_name(name: str) -> str:
    """Normalize city name for filename (remove accents, lowercase, hyphens)."""
    import unicodedata
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().replace(' ', '-')


@app.get("/api/charts/hourly/{city}")
async def get_hourly_chart(city: str = "fort-de-france"):
    """Get hourly dashboard chart for a city."""
    city_slug = _normalize_city_name(city)
    chart_path = Path(CHARTS_DIR) / f"hourly_dashboard_{city_slug}.html"

    if not chart_path.exists():
        from chart_generator import MartiniqueChartGenerator
        MartiniqueChartGenerator().generate_hourly_dashboard(city)

    if chart_path.exists():
        return FileResponse(chart_path, media_type="text/html")
    raise HTTPException(status_code=404, detail=f"Hourly chart not available for {city}")


@app.get("/api/charts/comparison")
async def get_comparison_chart():
    """Get city comparison chart HTML."""
    chart_path = Path(CHARTS_DIR) / "city_comparison.html"
    if not chart_path.exists():
        from chart_generator import MartiniqueChartGenerator
        MartiniqueChartGenerator().generate_city_comparison()

    if chart_path.exists():
        return FileResponse(chart_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Comparison chart not available")


@app.get("/api/charts/vigilance")
async def get_vigilance_chart():
    """Get vigilance gauge chart HTML."""
    chart_path = Path(CHARTS_DIR) / "vigilance_gauge.html"
    if not chart_path.exists():
        from chart_generator import MartiniqueChartGenerator
        MartiniqueChartGenerator().generate_vigilance_gauge()

    if chart_path.exists():
        return FileResponse(chart_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Vigilance chart not available")


# ============================================================================
# GENERATE DATA ON DEMAND
# ============================================================================

@app.post("/api/generate/demo")
async def generate_demo_data():
    """Generate demo data for testing."""
    from main import generate_sample_data
    from map_generator import MartiniqueMapGenerator
    from chart_generator import MartiniqueChartGenerator

    logger.info("Generating demo data...")
    generate_sample_data(logger)

    map_gen = MartiniqueMapGenerator()
    map_results = map_gen.generate_all_maps()

    chart_gen = MartiniqueChartGenerator()
    chart_results = chart_gen.generate_all_charts()

    return {
        "success": True,
        "maps": list(map_results.keys()),
        "charts": list(chart_results.keys())
    }


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.get("/aujourd-hui", response_class=HTMLResponse)
async def page_aujourdhui():
    """Today's weather page."""
    html_path = STATIC_DIR / "aujourdhui.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/previsions", response_class=HTMLResponse)
async def page_previsions():
    """Forecasts page."""
    html_path = STATIC_DIR / "previsions.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/cartes", response_class=HTMLResponse)
async def page_cartes():
    """Maps page."""
    html_path = STATIC_DIR / "cartes.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/success", response_class=HTMLResponse)
async def page_success():
    """Payment success page."""
    html_path = STATIC_DIR / "success.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/alerte-sms", response_class=HTMLResponse)
async def page_alerte_sms():
    """SMS subscription page with embedded payment."""
    html_path = STATIC_DIR / "alerte-sms.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/alerte-email", response_class=HTMLResponse)
async def page_alerte_email():
    """Email subscription page with embedded payment."""
    html_path = STATIC_DIR / "alerte-email.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/gerer", response_class=HTMLResponse)
async def page_gerer():
    """Subscription management page."""
    html_path = STATIC_DIR / "gerer.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
