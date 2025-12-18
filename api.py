"""FastAPI REST API for SMS alert subscriptions.

Provides endpoints for:
- OTP verification flow
- Subscription management
- Alert testing
- Statistics
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import re

from sms_service import SMSService, OTPService, AlertService
from subscriptions import SubscriptionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Météo Martinique - Alertes SMS API",
    description="API for SMS weather alert subscriptions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sms_service = SMSService()
otp_service = OTPService(sms_service)
alert_service = AlertService(sms_service)
subscription_manager = SubscriptionManager()

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


class PhoneRequest(BaseModel):
    """Request model with phone number."""
    phone: str
    profile: Optional[str] = "Particulier"

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Invalid phone number')
        return cleaned


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


@app.post("/api/otp/send")
async def send_otp(request: PhoneRequest):
    """Send OTP verification code.

    Step 1 of double validation flow.
    """
    result = subscription_manager.create_subscription(
        phone_number=request.phone,
        profile=request.profile
    )

    if not result["success"]:
        if "already subscribed" in result.get("error", ""):
            raise HTTPException(status_code=409, detail=result["error"])
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create subscription"))

    otp_result = otp_service.send_otp(request.phone)

    if not otp_result["success"]:
        return {
            "success": False,
            "error": otp_result.get("error", "Failed to send OTP"),
            "demo_mode": not sms_service.is_configured()
        }

    return {
        "success": True,
        "message": "Verification code sent",
        "expires_in": otp_result.get("expires_in", 10),
        "reference_code": result.get("reference_code")
    }


@app.post("/api/otp/verify")
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP code.

    Validates the code sent via SMS.
    """
    result = otp_service.verify_otp(request.phone, request.otp)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Verification failed"))

    verify_result = subscription_manager.verify_subscription(request.phone)

    if not verify_result["success"]:
        raise HTTPException(status_code=400, detail="Failed to verify subscription")

    return {
        "success": True,
        "verified": True,
        "reference_code": verify_result.get("reference_code"),
        "profile": verify_result.get("profile")
    }


@app.post("/api/subscribe/confirm")
async def confirm_subscription(request: PhoneRequest):
    """Confirm subscription and send welcome SMS.

    Step 2 of double validation flow - sends activation SMS.
    """
    subscriber = subscription_manager.get_subscriber(phone_number=request.phone)

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if not subscriber["verified"]:
        raise HTTPException(status_code=400, detail="Phone not verified - complete OTP first")

    if not subscriber["active"]:
        raise HTTPException(status_code=400, detail="Subscription is inactive")

    result = alert_service.send_welcome(request.phone, subscriber["profile"])

    return {
        "success": result["success"],
        "message": "Subscription confirmed - welcome SMS sent" if result["success"] else "Failed to send welcome SMS",
        "reference_code": subscriber["reference_code"],
        "profile": subscriber["profile"]
    }


@app.post("/api/subscribe/test")
async def send_test_alert(request: PhoneRequest):
    """Send test alert to subscriber."""
    subscriber = subscription_manager.get_subscriber(phone_number=request.phone)

    if not subscriber or not subscriber["active"] or not subscriber["verified"]:
        raise HTTPException(status_code=404, detail="Active verified subscription not found")

    result = alert_service.send_test_alert(request.phone, subscriber["profile"])

    if result["success"]:
        subscription_manager.log_alert(
            subscriber_id=subscriber["id"],
            phenomenon_type="Test",
            color_code=2,
            message="Test alert",
            delivery_status="sent",
            twilio_sid=result.get("sid")
        )

    return {
        "success": result["success"],
        "message": "Test alert sent" if result["success"] else result.get("error")
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


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
