"""SMS service for weather alerts using Twilio.

Handles OTP verification and weather alert notifications for Martinique.
"""
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    VIGILANCE_COLORS, PHENOMENON_TYPES
)

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages via Twilio."""

    def __init__(self):
        """Initialize Twilio client."""
        self.client = None
        self.from_number = TWILIO_PHONE_NUMBER

        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not configured - SMS disabled")

    def is_configured(self) -> bool:
        """Check if SMS service is properly configured."""
        return self.client is not None and self.from_number is not None

    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS message.

        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message content

        Returns:
            Dictionary with status and message SID or error
        """
        if not self.is_configured():
            logger.warning("SMS service not configured - message not sent")
            return {"success": False, "error": "SMS service not configured"}

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number[:8]}*** - SID: {msg.sid}")
            return {"success": True, "sid": msg.sid, "status": msg.status}

        except TwilioRestException as e:
            logger.error(f"Twilio error sending to {to_number[:8]}***: {e}")
            return {"success": False, "error": str(e), "code": e.code}
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return {"success": False, "error": str(e)}


class OTPService:
    """Service for generating and validating OTP codes."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10

    def __init__(self, sms_service: SMSService):
        """Initialize OTP service.

        Args:
            sms_service: SMSService instance for sending codes
        """
        self.sms_service = sms_service
        self._pending_otps: Dict[str, Dict[str, Any]] = {}

    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP code."""
        return ''.join(random.choices(string.digits, k=self.OTP_LENGTH))

    def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """Generate and send OTP to phone number.

        Args:
            phone_number: Recipient phone number

        Returns:
            Dictionary with success status
        """
        otp = self.generate_otp()
        expiry = datetime.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

        message = (
            f"Météo Martinique - Code de vérification: {otp}\n"
            f"Ce code expire dans {self.OTP_EXPIRY_MINUTES} minutes.\n"
            "Ne partagez pas ce code."
        )

        result = self.sms_service.send_sms(phone_number, message)

        if result["success"]:
            self._pending_otps[phone_number] = {
                "otp": otp,
                "expiry": expiry,
                "attempts": 0
            }
            return {"success": True, "expires_in": self.OTP_EXPIRY_MINUTES}

        return result

    def verify_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """Verify OTP code for phone number.

        Args:
            phone_number: Phone number to verify
            otp: OTP code to validate

        Returns:
            Dictionary with verification result
        """
        if phone_number not in self._pending_otps:
            return {"success": False, "error": "No pending verification"}

        pending = self._pending_otps[phone_number]

        if datetime.now() > pending["expiry"]:
            del self._pending_otps[phone_number]
            return {"success": False, "error": "Code expired"}

        pending["attempts"] += 1
        if pending["attempts"] > 3:
            del self._pending_otps[phone_number]
            return {"success": False, "error": "Too many attempts"}

        if pending["otp"] == otp:
            del self._pending_otps[phone_number]
            return {"success": True, "verified": True}

        return {"success": False, "error": "Invalid code"}

    def cleanup_expired(self):
        """Remove expired OTP entries."""
        now = datetime.now()
        expired = [
            phone for phone, data in self._pending_otps.items()
            if now > data["expiry"]
        ]
        for phone in expired:
            del self._pending_otps[phone]


class AlertService:
    """Service for sending weather alert notifications."""

    ALERT_TEMPLATES = {
        "Wind": "⚠️ ALERTE VENT FORT — Martinique.\nRafales possibles jusqu'à {intensity}.\nConseil: {advice}",
        "Rain-Flood": "⚠️ ALERTE PLUIES INTENSES — Martinique.\n{description}\nConseil: {advice}",
        "Storm": "⚠️ ALERTE ORAGES — Martinique.\n{description}\nConseil: {advice}",
        "Waves-Submersion": "🌊 ALERTE HOULE/SUBMERSION — Martinique.\n{description}\nConseil: {advice}",
        "Heat Wave": "🌡️ ALERTE CHALEUR — Martinique.\nTempératures élevées prévues.\nConseil: {advice}",
        "Cyclone": "🌀 ALERTE CYCLONE — Martinique.\n{description}\nConseil: {advice}"
    }

    PROFILE_ADVICE = {
        "Particulier": {
            "Wind": "Limitez les déplacements et sécurisez les objets extérieurs.",
            "Rain-Flood": "Évitez les ravines et routes inondables.",
            "Storm": "Restez à l'abri et débranchez les appareils électriques.",
            "Waves-Submersion": "Éloignez-vous du littoral.",
            "Heat Wave": "Hydratez-vous régulièrement, restez au frais.",
            "Cyclone": "Préparez vos réserves (eau, lampe, batteries, papiers)."
        },
        "Professionnel (BTP / agriculture)": {
            "Wind": "Suspendez les travaux en hauteur, sécurisez le chantier.",
            "Rain-Flood": "Reportez les travaux de terrassement.",
            "Storm": "Mettez le matériel à l'abri.",
            "Waves-Submersion": "Évacuez les zones côtières de travail.",
            "Heat Wave": "Adaptez les horaires, prévoyez des pauses.",
            "Cyclone": "Sécurisez tout matériel et évacuez."
        },
        "Nautique / pêche / plaisance": {
            "Wind": "Restez au port, vérifiez les amarres.",
            "Rain-Flood": "Attention à la visibilité réduite.",
            "Storm": "Ne prenez pas la mer.",
            "Waves-Submersion": "Ne prenez pas la mer, houle dangereuse.",
            "Heat Wave": "Hydratation renforcée en mer.",
            "Cyclone": "Mettez les embarcations à l'abri."
        },
        "Tourisme / plages": {
            "Wind": "Évitez les activités nautiques.",
            "Rain-Flood": "Reportez les excursions en montagne.",
            "Storm": "Restez à l'hôtel ou en lieu sûr.",
            "Waves-Submersion": "Plages interdites, éloignez-vous du bord de mer.",
            "Heat Wave": "Limitez l'exposition au soleil 11h-16h.",
            "Cyclone": "Suivez les consignes de votre hébergement."
        }
    }

    def __init__(self, sms_service: SMSService):
        """Initialize alert service.

        Args:
            sms_service: SMSService instance for sending alerts
        """
        self.sms_service = sms_service

    def format_alert(
        self,
        phenomenon_type: str,
        color_code: int,
        profile: str = "Particulier",
        description: str = "",
        intensity: str = ""
    ) -> str:
        """Format alert message based on phenomenon and profile.

        Args:
            phenomenon_type: Type of weather phenomenon
            color_code: Vigilance color code (1-4)
            profile: Subscriber profile type
            description: Additional description
            intensity: Intensity info (e.g., wind speed)

        Returns:
            Formatted alert message
        """
        template = self.ALERT_TEMPLATES.get(
            phenomenon_type,
            "⚠️ ALERTE MÉTÉO — Martinique.\n{description}\nConseil: {advice}"
        )

        advice = self.PROFILE_ADVICE.get(profile, self.PROFILE_ADVICE["Particulier"]).get(
            phenomenon_type, "Restez vigilant et suivez les consignes."
        )

        color_name = VIGILANCE_COLORS.get(color_code, {}).get("name", "")
        level = VIGILANCE_COLORS.get(color_code, {}).get("level", "")

        message = template.format(
            intensity=intensity or "conditions dangereuses",
            description=description or f"Vigilance {color_name} - {level}",
            advice=advice
        )

        message += "\n\nMétéo Martinique • STOP pour se désinscrire"

        return message

    def send_alert(
        self,
        phone_number: str,
        phenomenon_type: str,
        color_code: int,
        profile: str = "Particulier",
        **kwargs
    ) -> Dict[str, Any]:
        """Send weather alert to subscriber.

        Args:
            phone_number: Recipient phone number
            phenomenon_type: Type of phenomenon
            color_code: Vigilance color code
            profile: Subscriber profile
            **kwargs: Additional formatting parameters

        Returns:
            Dictionary with send result
        """
        message = self.format_alert(phenomenon_type, color_code, profile, **kwargs)
        return self.sms_service.send_sms(phone_number, message)

    def send_welcome(self, phone_number: str, profile: str) -> Dict[str, Any]:
        """Send welcome/activation SMS.

        Args:
            phone_number: Recipient phone number
            profile: Subscriber profile

        Returns:
            Dictionary with send result
        """
        message = (
            f"✅ Bienvenue sur Météo Martinique Alertes SMS!\n\n"
            f"Profil: {profile}\n"
            f"Couverture: Martinique entière\n"
            f"Phénomènes: Tous (vent, pluie, orages, houle, cyclone, chaleur)\n\n"
            f"Vous recevrez des alertes adaptées à votre profil.\n"
            f"Envoyez STOP pour vous désinscrire."
        )
        return self.sms_service.send_sms(phone_number, message)

    def send_test_alert(self, phone_number: str, profile: str) -> Dict[str, Any]:
        """Send test alert to subscriber.

        Args:
            phone_number: Recipient phone number
            profile: Subscriber profile

        Returns:
            Dictionary with send result
        """
        message = self.format_alert(
            phenomenon_type="Wind",
            color_code=2,
            profile=profile,
            intensity="70 km/h entre 16:00–20:00"
        )
        message = "🧪 TEST ALERTE\n\n" + message
        return self.sms_service.send_sms(phone_number, message)
