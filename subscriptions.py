"""Subscription management for SMS alerts using SQLite.

Handles subscriber data, profiles, and subscription lifecycle.
"""
import logging
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import DATA_DIR

logger = logging.getLogger(__name__)

DB_PATH = Path(DATA_DIR) / "subscriptions.db"


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                email TEXT,
                profile TEXT NOT NULL DEFAULT 'Particulier',
                reference_code TEXT UNIQUE NOT NULL,
                notification_prefs TEXT DEFAULT 'sms',
                verified BOOLEAN DEFAULT FALSE,
                email_verified BOOLEAN DEFAULT FALSE,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                unsubscribed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                phenomenon_type TEXT NOT NULL,
                color_code INTEGER NOT NULL,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_status TEXT,
                delivery_channel TEXT DEFAULT 'sms',
                message_id TEXT,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
            );

            CREATE INDEX IF NOT EXISTS idx_phone ON subscribers(phone_number);
            CREATE INDEX IF NOT EXISTS idx_email ON subscribers(email);
            CREATE INDEX IF NOT EXISTS idx_active ON subscribers(active, verified);
            CREATE INDEX IF NOT EXISTS idx_ref_code ON subscribers(reference_code);
        """)
        # Migration: add new columns if they don't exist
        try:
            conn.execute("ALTER TABLE subscribers ADD COLUMN email TEXT")
        except:
            pass
        try:
            conn.execute("ALTER TABLE subscribers ADD COLUMN email_verified BOOLEAN DEFAULT FALSE")
        except:
            pass
        try:
            conn.execute("ALTER TABLE subscribers ADD COLUMN notification_prefs TEXT DEFAULT 'sms'")
        except:
            pass
        try:
            conn.execute("ALTER TABLE alert_history ADD COLUMN delivery_channel TEXT DEFAULT 'sms'")
        except:
            pass
        try:
            conn.execute("ALTER TABLE alert_history ADD COLUMN message_id TEXT")
        except:
            pass
        logger.info("Database initialized")


def generate_reference_code() -> str:
    """Generate unique subscription reference code (MM-XXXXX format)."""
    return f"MM-{secrets.token_hex(3).upper()}"


class SubscriptionManager:
    """Manager for SMS alert subscriptions."""

    PROFILES = [
        "Particulier",
        "Professionnel (BTP / agriculture)",
        "Nautique / pêche / plaisance",
        "Tourisme / plages"
    ]

    def __init__(self):
        """Initialize subscription manager and ensure DB exists."""
        init_database()

    def create_subscription(
        self,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        profile: str = "Particulier",
        notification_prefs: str = "sms"
    ) -> Dict[str, Any]:
        """Create new subscription (pending verification).

        Args:
            phone_number: Subscriber phone number (E.164 format)
            email: Subscriber email address
            profile: Subscriber profile type
            notification_prefs: 'sms', 'email', or 'both'

        Returns:
            Dictionary with subscription data or error
        """
        if profile not in self.PROFILES:
            profile = "Particulier"

        if notification_prefs not in ("sms", "email", "both"):
            notification_prefs = "sms"

        phone = self._normalize_phone(phone_number) if phone_number else None
        email = email.strip().lower() if email else None

        # Validate we have at least one contact method
        if not phone and not email:
            return {"success": False, "error": "Phone or email required"}

        # Validate based on notification preference
        if notification_prefs == "sms" and not phone:
            return {"success": False, "error": "Phone required for SMS notifications"}
        if notification_prefs == "email" and not email:
            return {"success": False, "error": "Email required for email notifications"}
        if notification_prefs == "both" and (not phone or not email):
            return {"success": False, "error": "Both phone and email required"}

        ref_code = generate_reference_code()

        try:
            with get_db() as conn:
                # Check for existing by phone or email
                existing = None
                if phone:
                    existing = conn.execute(
                        "SELECT id, active, verified FROM subscribers WHERE phone_number = ?",
                        (phone,)
                    ).fetchone()
                if not existing and email:
                    existing = conn.execute(
                        "SELECT id, active, verified FROM subscribers WHERE email = ?",
                        (email,)
                    ).fetchone()

                if existing:
                    if existing["active"] and existing["verified"]:
                        return {
                            "success": False,
                            "error": "Already subscribed",
                            "subscriber_id": existing["id"]
                        }
                    conn.execute(
                        """UPDATE subscribers
                           SET profile = ?, active = TRUE, verified = FALSE,
                               reference_code = ?, unsubscribed_at = NULL,
                               phone_number = ?, email = ?, notification_prefs = ?
                           WHERE id = ?""",
                        (profile, ref_code, phone, email, notification_prefs, existing["id"])
                    )
                    return {
                        "success": True,
                        "subscriber_id": existing["id"],
                        "reference_code": ref_code,
                        "reactivated": True
                    }

                cursor = conn.execute(
                    """INSERT INTO subscribers
                       (phone_number, email, profile, reference_code, notification_prefs)
                       VALUES (?, ?, ?, ?, ?)""",
                    (phone, email, profile, ref_code, notification_prefs)
                )
                return {
                    "success": True,
                    "subscriber_id": cursor.lastrowid,
                    "reference_code": ref_code
                }

        except sqlite3.IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
            return {"success": False, "error": "Database error"}

    def verify_subscription(self, phone_number: str) -> Dict[str, Any]:
        """Mark subscription as verified after OTP validation.

        Args:
            phone_number: Phone number to verify

        Returns:
            Dictionary with verification result
        """
        phone = self._normalize_phone(phone_number)

        with get_db() as conn:
            result = conn.execute(
                """UPDATE subscribers
                   SET verified = TRUE, verified_at = ?
                   WHERE phone_number = ? AND active = TRUE
                   RETURNING id, reference_code, profile""",
                (datetime.now(), phone)
            ).fetchone()

            if result:
                return {
                    "success": True,
                    "subscriber_id": result["id"],
                    "reference_code": result["reference_code"],
                    "profile": result["profile"]
                }

            return {"success": False, "error": "Subscription not found"}

    def unsubscribe(
        self,
        phone_number: Optional[str] = None,
        reference_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deactivate subscription.

        Args:
            phone_number: Phone number (optional)
            reference_code: Reference code (optional)

        Returns:
            Dictionary with result
        """
        with get_db() as conn:
            if phone_number:
                phone = self._normalize_phone(phone_number)
                result = conn.execute(
                    """UPDATE subscribers
                       SET active = FALSE, unsubscribed_at = ?
                       WHERE phone_number = ? AND active = TRUE
                       RETURNING id""",
                    (datetime.now(), phone)
                ).fetchone()
            elif reference_code:
                result = conn.execute(
                    """UPDATE subscribers
                       SET active = FALSE, unsubscribed_at = ?
                       WHERE reference_code = ? AND active = TRUE
                       RETURNING id""",
                    (datetime.now(), reference_code)
                ).fetchone()
            else:
                return {"success": False, "error": "Phone or reference required"}

            if result:
                return {"success": True, "subscriber_id": result["id"]}

            return {"success": False, "error": "Active subscription not found"}

    def get_subscriber(
        self,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        reference_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get subscriber details.

        Args:
            phone_number: Phone to look up
            email: Email to look up
            reference_code: Reference code to look up

        Returns:
            Subscriber data or None
        """
        with get_db() as conn:
            if phone_number:
                phone = self._normalize_phone(phone_number)
                row = conn.execute(
                    "SELECT * FROM subscribers WHERE phone_number = ?",
                    (phone,)
                ).fetchone()
            elif email:
                row = conn.execute(
                    "SELECT * FROM subscribers WHERE email = ?",
                    (email.strip().lower(),)
                ).fetchone()
            elif reference_code:
                row = conn.execute(
                    "SELECT * FROM subscribers WHERE reference_code = ?",
                    (reference_code,)
                ).fetchone()
            else:
                return None

            return dict(row) if row else None

    def update_profile(
        self,
        phone_number: str,
        profile: str
    ) -> Dict[str, Any]:
        """Update subscriber profile.

        Args:
            phone_number: Phone number
            profile: New profile type

        Returns:
            Update result
        """
        if profile not in self.PROFILES:
            return {"success": False, "error": "Invalid profile"}

        phone = self._normalize_phone(phone_number)

        with get_db() as conn:
            result = conn.execute(
                """UPDATE subscribers SET profile = ?
                   WHERE phone_number = ? AND active = TRUE
                   RETURNING id""",
                (profile, phone)
            ).fetchone()

            if result:
                return {"success": True, "subscriber_id": result["id"]}

            return {"success": False, "error": "Active subscription not found"}

    def get_active_subscribers(self) -> List[Dict[str, Any]]:
        """Get all active, verified subscribers.

        Returns:
            List of subscriber dictionaries
        """
        with get_db() as conn:
            rows = conn.execute(
                """SELECT id, phone_number, email, profile, reference_code, notification_prefs
                   FROM subscribers
                   WHERE active = TRUE AND verified = TRUE"""
            ).fetchall()
            return [dict(row) for row in rows]

    def log_alert(
        self,
        subscriber_id: int,
        phenomenon_type: str,
        color_code: int,
        message: str,
        delivery_status: str = "pending",
        delivery_channel: str = "sms",
        message_id: Optional[str] = None
    ):
        """Log sent alert to history.

        Args:
            subscriber_id: Subscriber ID
            phenomenon_type: Type of phenomenon
            color_code: Vigilance color code
            message: Message content
            delivery_status: Delivery status
            delivery_channel: 'sms' or 'email'
            message_id: Provider message ID (Brevo)
        """
        with get_db() as conn:
            conn.execute(
                """INSERT INTO alert_history
                   (subscriber_id, phenomenon_type, color_code, message, delivery_status, delivery_channel, message_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (subscriber_id, phenomenon_type, color_code, message, delivery_status, delivery_channel, message_id)
            )

    def get_alert_history(
        self,
        subscriber_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alert history.

        Args:
            subscriber_id: Filter by subscriber (optional)
            limit: Max records to return

        Returns:
            List of alert records
        """
        with get_db() as conn:
            if subscriber_id:
                rows = conn.execute(
                    """SELECT * FROM alert_history
                       WHERE subscriber_id = ?
                       ORDER BY sent_at DESC LIMIT ?""",
                    (subscriber_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM alert_history
                       ORDER BY sent_at DESC LIMIT ?""",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics.

        Returns:
            Dictionary with statistics
        """
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM subscribers WHERE active = TRUE AND verified = TRUE"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM subscribers WHERE active = TRUE AND verified = FALSE"
            ).fetchone()[0]
            alerts_sent = conn.execute("SELECT COUNT(*) FROM alert_history").fetchone()[0]

            profiles = conn.execute(
                """SELECT profile, COUNT(*) as count
                   FROM subscribers WHERE active = TRUE AND verified = TRUE
                   GROUP BY profile"""
            ).fetchall()

            return {
                "total_subscribers": total,
                "active_verified": active,
                "pending_verification": pending,
                "total_alerts_sent": alerts_sent,
                "by_profile": {row["profile"]: row["count"] for row in profiles}
            }

    @staticmethod
    def _normalize_phone(phone: str) -> Optional[str]:
        """Normalize phone number to E.164 format.

        Args:
            phone: Input phone number

        Returns:
            Normalized phone or None if invalid
        """
        if not phone:
            return None

        digits = ''.join(c for c in phone if c.isdigit() or c == '+')

        if digits.startswith('+'):
            return digits if len(digits) >= 11 else None

        if digits.startswith('0') and len(digits) == 10:
            return f"+596{digits[1:]}"

        if digits.startswith('596') and len(digits) >= 12:
            return f"+{digits}"

        if len(digits) == 9:
            return f"+596{digits}"

        return None
