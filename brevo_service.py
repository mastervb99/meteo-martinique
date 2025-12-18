"""Brevo service for SMS and Email alerts.

Handles OTP verification and weather alert notifications via Brevo API.
Replaces Twilio integration.
"""
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import (
    BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME, BREVO_SMS_SENDER,
    VIGILANCE_COLORS, PHENOMENON_TYPES
)

logger = logging.getLogger(__name__)

# Try to import Brevo SDK
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_SDK_AVAILABLE = True
except ImportError:
    BREVO_SDK_AVAILABLE = False
    logger.warning("Brevo SDK not installed. Run: pip install sib-api-v3-sdk")


class BrevoSMSService:
    """Service for sending SMS via Brevo Transactional SMS API."""

    def __init__(self):
        """Initialize Brevo SMS client."""
        self.client = None
        self.api_instance = None
        self.sender = BREVO_SMS_SENDER or "MeteoMQ"

        if BREVO_SDK_AVAILABLE and BREVO_API_KEY:
            try:
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = BREVO_API_KEY
                self.client = sib_api_v3_sdk.ApiClient(configuration)
                self.api_instance = sib_api_v3_sdk.TransactionalSMSApi(self.client)
                logger.info("Brevo SMS client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Brevo SMS client: {e}")
        else:
            logger.warning("Brevo SMS not configured - SMS in demo mode")

    def is_configured(self) -> bool:
        """Check if SMS service is properly configured."""
        return self.api_instance is not None

    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS message via Brevo.

        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message content (max 160 chars for single SMS)

        Returns:
            Dictionary with status and message reference or error
        """
        if not self.is_configured():
            logger.warning(f"SMS demo mode - would send to {to_number[:8]}***: {message[:50]}...")
            return {"success": True, "demo": True, "message_id": f"demo-{random.randint(1000,9999)}"}

        try:
            send_sms = sib_api_v3_sdk.SendTransacSms(
                sender=self.sender,
                recipient=to_number,
                content=message,
                type="transactional"
            )
            response = self.api_instance.send_transac_sms(send_sms)
            logger.info(f"SMS sent to {to_number[:8]}*** - Ref: {response.message_id}")
            return {"success": True, "message_id": response.message_id, "credits": response.credits_used}

        except ApiException as e:
            logger.error(f"Brevo SMS error sending to {to_number[:8]}***: {e}")
            return {"success": False, "error": str(e), "code": e.status}
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return {"success": False, "error": str(e)}


class BrevoEmailService:
    """Service for sending emails via Brevo Transactional Email API."""

    def __init__(self):
        """Initialize Brevo Email client."""
        self.client = None
        self.api_instance = None
        self.sender_email = BREVO_SENDER_EMAIL or "alertes@meteo-martinique.fr"
        self.sender_name = BREVO_SENDER_NAME or "Météo Martinique"

        if BREVO_SDK_AVAILABLE and BREVO_API_KEY:
            try:
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = BREVO_API_KEY
                self.client = sib_api_v3_sdk.ApiClient(configuration)
                self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(self.client)
                logger.info("Brevo Email client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Brevo Email client: {e}")
        else:
            logger.warning("Brevo Email not configured - Email in demo mode")

    def is_configured(self) -> bool:
        """Check if Email service is properly configured."""
        return self.api_instance is not None

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via Brevo.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)

        Returns:
            Dictionary with status and message ID or error
        """
        if not self.is_configured():
            logger.warning(f"Email demo mode - would send to {to_email}: {subject}")
            return {"success": True, "demo": True, "message_id": f"demo-{random.randint(1000,9999)}"}

        try:
            send_email = sib_api_v3_sdk.SendSmtpEmail(
                sender={"email": self.sender_email, "name": self.sender_name},
                to=[{"email": to_email, "name": to_name}],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            response = self.api_instance.send_transac_email(send_email)
            logger.info(f"Email sent to {to_email} - ID: {response.message_id}")
            return {"success": True, "message_id": response.message_id}

        except ApiException as e:
            logger.error(f"Brevo Email error sending to {to_email}: {e}")
            return {"success": False, "error": str(e), "code": e.status}
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return {"success": False, "error": str(e)}


class OTPService:
    """Service for generating and validating OTP codes via SMS or Email."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10

    def __init__(self, sms_service: BrevoSMSService, email_service: BrevoEmailService):
        """Initialize OTP service.

        Args:
            sms_service: BrevoSMSService instance
            email_service: BrevoEmailService instance
        """
        self.sms_service = sms_service
        self.email_service = email_service
        self._pending_otps: Dict[str, Dict[str, Any]] = {}

    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP code."""
        return ''.join(random.choices(string.digits, k=self.OTP_LENGTH))

    def send_otp(
        self,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        channel: str = "sms"
    ) -> Dict[str, Any]:
        """Generate and send OTP via SMS or Email.

        Args:
            phone_number: Recipient phone (for SMS)
            email: Recipient email (for email)
            channel: 'sms', 'email', or 'both'

        Returns:
            Dictionary with success status
        """
        otp = self.generate_otp()
        expiry = datetime.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        identifier = phone_number or email

        results = {"success": False, "channels": []}

        # Send via SMS
        if channel in ("sms", "both") and phone_number:
            message = (
                f"Meteo Martinique - Code: {otp}\n"
                f"Expire dans {self.OTP_EXPIRY_MINUTES} min.\n"
                "Ne partagez pas ce code."
            )
            sms_result = self.sms_service.send_sms(phone_number, message)
            if sms_result["success"]:
                results["channels"].append("sms")
                results["success"] = True

        # Send via Email
        if channel in ("email", "both") and email:
            subject = f"Code de verification Meteo Martinique: {otp}"
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Meteo Martinique</h2>
                <p>Votre code de verification:</p>
                <div style="background: #f0f9ff; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1d4ed8;">{otp}</span>
                </div>
                <p style="color: #64748b;">Ce code expire dans {self.OTP_EXPIRY_MINUTES} minutes.</p>
                <p style="color: #64748b;">Ne partagez pas ce code.</p>
            </div>
            """
            email_result = self.email_service.send_email(
                to_email=email,
                to_name="Abonne Meteo Martinique",
                subject=subject,
                html_content=html_content,
                text_content=f"Code: {otp} - Expire dans {self.OTP_EXPIRY_MINUTES} min."
            )
            if email_result["success"]:
                results["channels"].append("email")
                results["success"] = True

        if results["success"]:
            self._pending_otps[identifier] = {
                "otp": otp,
                "expiry": expiry,
                "attempts": 0
            }
            results["expires_in"] = self.OTP_EXPIRY_MINUTES

        return results

    def verify_otp(self, identifier: str, otp: str) -> Dict[str, Any]:
        """Verify OTP code.

        Args:
            identifier: Phone number or email used for OTP
            otp: OTP code to validate

        Returns:
            Dictionary with verification result
        """
        if identifier not in self._pending_otps:
            return {"success": False, "error": "No pending verification"}

        pending = self._pending_otps[identifier]

        if datetime.now() > pending["expiry"]:
            del self._pending_otps[identifier]
            return {"success": False, "error": "Code expired"}

        pending["attempts"] += 1
        if pending["attempts"] > 3:
            del self._pending_otps[identifier]
            return {"success": False, "error": "Too many attempts"}

        if pending["otp"] == otp:
            del self._pending_otps[identifier]
            return {"success": True, "verified": True}

        return {"success": False, "error": "Invalid code"}

    def cleanup_expired(self):
        """Remove expired OTP entries."""
        now = datetime.now()
        expired = [k for k, v in self._pending_otps.items() if now > v["expiry"]]
        for k in expired:
            del self._pending_otps[k]


class AlertService:
    """Service for sending weather alert notifications via SMS and Email."""

    ALERT_TEMPLATES_SMS = {
        "Wind": "ALERTE VENT FORT - Martinique.\nRafales: {intensity}.\nConseil: {advice}",
        "Rain-Flood": "ALERTE PLUIES - Martinique.\n{description}\nConseil: {advice}",
        "Storm": "ALERTE ORAGES - Martinique.\n{description}\nConseil: {advice}",
        "Waves-Submersion": "ALERTE HOULE - Martinique.\n{description}\nConseil: {advice}",
        "Heat Wave": "ALERTE CHALEUR - Martinique.\nTemperatures elevees.\nConseil: {advice}",
        "Cyclone": "ALERTE CYCLONE - Martinique.\n{description}\nConseil: {advice}"
    }

    PROFILE_ADVICE = {
        "Particulier": {
            "Wind": "Limitez les deplacements et securisez les objets exterieurs.",
            "Rain-Flood": "Evitez les ravines et routes inondables.",
            "Storm": "Restez a l'abri et debranchez les appareils electriques.",
            "Waves-Submersion": "Eloignez-vous du littoral.",
            "Heat Wave": "Hydratez-vous regulierement, restez au frais.",
            "Cyclone": "Preparez vos reserves (eau, lampe, batteries, papiers)."
        },
        "Professionnel (BTP / agriculture)": {
            "Wind": "Suspendez les travaux en hauteur, securisez le chantier.",
            "Rain-Flood": "Reportez les travaux de terrassement.",
            "Storm": "Mettez le materiel a l'abri.",
            "Waves-Submersion": "Evacuez les zones cotieres de travail.",
            "Heat Wave": "Adaptez les horaires, prevoyez des pauses.",
            "Cyclone": "Securisez tout materiel et evacuez."
        },
        "Nautique / peche / plaisance": {
            "Wind": "Restez au port, verifiez les amarres.",
            "Rain-Flood": "Attention a la visibilite reduite.",
            "Storm": "Ne prenez pas la mer.",
            "Waves-Submersion": "Ne prenez pas la mer, houle dangereuse.",
            "Heat Wave": "Hydratation renforcee en mer.",
            "Cyclone": "Mettez les embarcations a l'abri."
        },
        "Tourisme / plages": {
            "Wind": "Evitez les activites nautiques.",
            "Rain-Flood": "Reportez les excursions en montagne.",
            "Storm": "Restez a l'hotel ou en lieu sur.",
            "Waves-Submersion": "Plages interdites, eloignez-vous du bord de mer.",
            "Heat Wave": "Limitez l'exposition au soleil 11h-16h.",
            "Cyclone": "Suivez les consignes de votre hebergement."
        }
    }

    def __init__(self, sms_service: BrevoSMSService, email_service: BrevoEmailService):
        """Initialize alert service."""
        self.sms_service = sms_service
        self.email_service = email_service

    def get_advice(self, profile: str, phenomenon_type: str) -> str:
        """Get profile-specific advice for phenomenon."""
        return self.PROFILE_ADVICE.get(
            profile, self.PROFILE_ADVICE["Particulier"]
        ).get(phenomenon_type, "Restez vigilant et suivez les consignes.")

    def format_sms_alert(
        self,
        phenomenon_type: str,
        color_code: int,
        profile: str = "Particulier",
        description: str = "",
        intensity: str = ""
    ) -> str:
        """Format SMS alert message."""
        template = self.ALERT_TEMPLATES_SMS.get(
            phenomenon_type,
            "ALERTE METEO - Martinique.\n{description}\nConseil: {advice}"
        )
        advice = self.get_advice(profile, phenomenon_type)
        color_name = VIGILANCE_COLORS.get(color_code, {}).get("name", "")
        level = VIGILANCE_COLORS.get(color_code, {}).get("level", "")

        message = template.format(
            intensity=intensity or "conditions dangereuses",
            description=description or f"Vigilance {color_name} - {level}",
            advice=advice
        )
        message += "\n\nMeteo Martinique - STOP pour se desinscrire"
        return message

    def format_email_alert(
        self,
        phenomenon_type: str,
        color_code: int,
        profile: str = "Particulier",
        description: str = "",
        intensity: str = "",
        unsubscribe_token: str = ""
    ) -> tuple:
        """Format email alert (subject, html_content)."""
        advice = self.get_advice(profile, phenomenon_type)
        color_info = VIGILANCE_COLORS.get(color_code, {})
        color_name = color_info.get("name", "")
        color_hex = color_info.get("hex", "#FFFF00")

        subject = f"ALERTE {phenomenon_type.upper()} - Martinique - Vigilance {color_name}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2563eb, #06b6d4); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Meteo Martinique</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Alerte Meteorologique</p>
            </div>
            <div style="background: {color_hex}; padding: 15px; text-align: center;">
                <h2 style="margin: 0; color: #000;">VIGILANCE {color_name.upper()}</h2>
                <p style="margin: 5px 0 0; font-weight: bold;">{phenomenon_type}</p>
            </div>
            <div style="padding: 20px; background: #f8fafc; border: 1px solid #e2e8f0;">
                <p style="font-size: 16px;">{description or f'Alerte {phenomenon_type} en cours sur la Martinique.'}</p>
                {f'<p><strong>Intensite:</strong> {intensity}</p>' if intensity else ''}
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb; margin: 15px 0;">
                    <p style="margin: 0;"><strong>Conseil ({profile}):</strong></p>
                    <p style="margin: 10px 0 0;">{advice}</p>
                </div>
            </div>
            <div style="padding: 15px; background: #f1f5f9; text-align: center; border-radius: 0 0 12px 12px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">
                    Meteo Martinique - Alertes SMS & Email<br>
                    <a href="{{{{unsubscribe_url}}}}" style="color: #2563eb;">Se desinscrire</a>
                </p>
            </div>
        </div>
        """
        return subject, html_content

    def send_alert(
        self,
        phone_number: Optional[str],
        email: Optional[str],
        phenomenon_type: str,
        color_code: int,
        profile: str = "Particulier",
        notification_prefs: str = "sms",
        **kwargs
    ) -> Dict[str, Any]:
        """Send weather alert via configured channels.

        Args:
            phone_number: Recipient phone
            email: Recipient email
            phenomenon_type: Type of phenomenon
            color_code: Vigilance color code
            profile: Subscriber profile
            notification_prefs: 'sms', 'email', or 'both'

        Returns:
            Dictionary with send results per channel
        """
        results = {"sms": None, "email": None}

        if notification_prefs in ("sms", "both") and phone_number:
            message = self.format_sms_alert(phenomenon_type, color_code, profile, **kwargs)
            results["sms"] = self.sms_service.send_sms(phone_number, message)

        if notification_prefs in ("email", "both") and email:
            subject, html = self.format_email_alert(phenomenon_type, color_code, profile, **kwargs)
            results["email"] = self.email_service.send_email(
                to_email=email,
                to_name="Abonne Meteo Martinique",
                subject=subject,
                html_content=html
            )

        results["success"] = any(
            r and r.get("success") for r in [results["sms"], results["email"]] if r
        )
        return results

    def send_welcome(
        self,
        phone_number: Optional[str],
        email: Optional[str],
        profile: str,
        notification_prefs: str = "sms"
    ) -> Dict[str, Any]:
        """Send welcome/activation message."""
        results = {"sms": None, "email": None}

        if notification_prefs in ("sms", "both") and phone_number:
            message = (
                f"Bienvenue sur Meteo Martinique Alertes!\n\n"
                f"Profil: {profile}\n"
                f"Zone: Martinique entiere\n"
                f"Phenomenes: Tous\n\n"
                f"STOP pour se desinscrire."
            )
            results["sms"] = self.sms_service.send_sms(phone_number, message)

        if notification_prefs in ("email", "both") and email:
            subject = "Bienvenue sur Meteo Martinique Alertes"
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2563eb, #06b6d4); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0;">Bienvenue!</h1>
                </div>
                <div style="padding: 30px; background: white; border: 1px solid #e2e8f0;">
                    <p style="font-size: 18px;">Votre abonnement aux alertes meteo est actif.</p>
                    <table style="width: 100%; margin: 20px 0;">
                        <tr><td style="padding: 8px 0; color: #64748b;">Profil</td><td style="padding: 8px 0; font-weight: bold;">{profile}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Zone</td><td style="padding: 8px 0; font-weight: bold;">Martinique entiere</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Phenomenes</td><td style="padding: 8px 0; font-weight: bold;">Tous (vent, pluie, orages, houle, cyclone, chaleur)</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b;">Notifications</td><td style="padding: 8px 0; font-weight: bold;">{notification_prefs.upper()}</td></tr>
                    </table>
                    <p>Vous recevrez des alertes adaptees a votre profil.</p>
                </div>
                <div style="padding: 15px; background: #f1f5f9; text-align: center; border-radius: 0 0 12px 12px;">
                    <p style="margin: 0; color: #64748b; font-size: 12px;">Meteo Martinique</p>
                </div>
            </div>
            """
            results["email"] = self.email_service.send_email(
                to_email=email,
                to_name="Abonne Meteo Martinique",
                subject=subject,
                html_content=html
            )

        results["success"] = any(
            r and r.get("success") for r in [results["sms"], results["email"]] if r
        )
        return results

    def send_test_alert(
        self,
        phone_number: Optional[str],
        email: Optional[str],
        profile: str,
        notification_prefs: str = "sms"
    ) -> Dict[str, Any]:
        """Send test alert."""
        results = self.send_alert(
            phone_number=phone_number,
            email=email,
            phenomenon_type="Wind",
            color_code=2,
            profile=profile,
            notification_prefs=notification_prefs,
            intensity="70 km/h entre 16:00-20:00",
            description="TEST ALERTE - Ceci est un test."
        )
        return results
