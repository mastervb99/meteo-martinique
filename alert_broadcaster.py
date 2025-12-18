"""Alert broadcaster for sending weather alerts to all subscribers.

Monitors vigilance alerts and broadcasts SMS to all active subscribers
when vigilance levels change to Yellow (2) or higher.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import DATA_DIR, VIGILANCE_COLORS, PHENOMENON_TYPES
from sms_service import SMSService, AlertService
from subscriptions import SubscriptionManager

logger = logging.getLogger(__name__)


class AlertBroadcaster:
    """Broadcasts weather alerts to all active subscribers."""

    ALERT_THRESHOLD = 2  # Yellow or higher

    def __init__(self):
        """Initialize broadcaster with services."""
        self.sms_service = SMSService()
        self.alert_service = AlertService(self.sms_service)
        self.subscription_manager = SubscriptionManager()
        self._last_alert_state: Dict[str, int] = {}

    def load_current_vigilance(self) -> Optional[Dict[str, Any]]:
        """Load current vigilance data from file.

        Returns:
            Vigilance data dictionary or None
        """
        vigilance_file = Path(DATA_DIR) / "vigilance_alerts.json"

        if not vigilance_file.exists():
            logger.warning("No vigilance data file found")
            return None

        try:
            with open(vigilance_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load vigilance data: {e}")
            return None

    def get_alertable_phenomenons(
        self,
        vigilance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get phenomenons that require alerting.

        Args:
            vigilance: Vigilance data dictionary

        Returns:
            List of phenomenons at or above alert threshold
        """
        alertable = []

        for phenomenon in vigilance.get("phenomenons", []):
            color_code = phenomenon.get("color_code", 1)
            phenomenon_type = phenomenon.get("type", "Unknown")

            if color_code >= self.ALERT_THRESHOLD:
                prev_color = self._last_alert_state.get(phenomenon_type, 1)

                if color_code > prev_color:
                    alertable.append(phenomenon)

        return alertable

    def broadcast_alert(
        self,
        phenomenon: Dict[str, Any],
        description: str = "",
        intensity: str = ""
    ) -> Dict[str, Any]:
        """Broadcast alert to all active subscribers.

        Args:
            phenomenon: Phenomenon data dictionary
            description: Additional description
            intensity: Intensity info

        Returns:
            Broadcast result summary
        """
        subscribers = self.subscription_manager.get_active_subscribers()

        if not subscribers:
            logger.info("No active subscribers to alert")
            return {"sent": 0, "failed": 0, "skipped": 0}

        phenomenon_type = phenomenon.get("type", "Unknown")
        color_code = phenomenon.get("color_code", 2)

        results = {"sent": 0, "failed": 0, "errors": []}

        logger.info(f"Broadcasting {phenomenon_type} alert to {len(subscribers)} subscribers")

        for subscriber in subscribers:
            try:
                result = self.alert_service.send_alert(
                    phone_number=subscriber["phone_number"],
                    phenomenon_type=phenomenon_type,
                    color_code=color_code,
                    profile=subscriber["profile"],
                    description=description,
                    intensity=intensity
                )

                if result["success"]:
                    results["sent"] += 1
                    self.subscription_manager.log_alert(
                        subscriber_id=subscriber["id"],
                        phenomenon_type=phenomenon_type,
                        color_code=color_code,
                        message=f"Alert: {phenomenon_type}",
                        delivery_status="sent",
                        twilio_sid=result.get("sid")
                    )
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "phone": subscriber["phone_number"][:8] + "***",
                        "error": result.get("error")
                    })

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "phone": subscriber["phone_number"][:8] + "***",
                    "error": str(e)
                })
                logger.error(f"Failed to send alert to subscriber {subscriber['id']}: {e}")

        logger.info(f"Broadcast complete: {results['sent']} sent, {results['failed']} failed")
        return results

    def check_and_broadcast(self) -> Dict[str, Any]:
        """Check vigilance and broadcast alerts if needed.

        Returns:
            Summary of actions taken
        """
        vigilance = self.load_current_vigilance()

        if not vigilance:
            return {"status": "no_data", "alerts_sent": 0}

        alertable = self.get_alertable_phenomenons(vigilance)

        if not alertable:
            logger.info("No new alerts to broadcast")
            return {"status": "no_alerts", "alerts_sent": 0}

        total_sent = 0
        total_failed = 0
        broadcast_results = []

        for phenomenon in alertable:
            phenomenon_type = phenomenon.get("type", "Unknown")
            color_code = phenomenon.get("color_code", 2)
            color_name = VIGILANCE_COLORS.get(color_code, {}).get("name", "")
            level = VIGILANCE_COLORS.get(color_code, {}).get("level", "")

            description = f"Vigilance {color_name} - {level}"

            result = self.broadcast_alert(
                phenomenon=phenomenon,
                description=description
            )

            self._last_alert_state[phenomenon_type] = color_code

            total_sent += result["sent"]
            total_failed += result["failed"]
            broadcast_results.append({
                "phenomenon": phenomenon_type,
                "color": color_code,
                **result
            })

        self._save_alert_state()

        return {
            "status": "alerts_sent",
            "total_sent": total_sent,
            "total_failed": total_failed,
            "broadcasts": broadcast_results,
            "timestamp": datetime.now().isoformat()
        }

    def _save_alert_state(self):
        """Save last alert state to file for persistence."""
        state_file = Path(DATA_DIR) / "last_alert_state.json"

        try:
            with open(state_file, "w") as f:
                json.dump({
                    "state": self._last_alert_state,
                    "updated_at": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alert state: {e}")

    def _load_alert_state(self):
        """Load last alert state from file."""
        state_file = Path(DATA_DIR) / "last_alert_state.json"

        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    self._last_alert_state = data.get("state", {})
            except Exception as e:
                logger.error(f"Failed to load alert state: {e}")

    def reset_alert_state(self):
        """Reset alert state (for testing or manual intervention)."""
        self._last_alert_state = {}
        self._save_alert_state()
        logger.info("Alert state reset")


def integrate_with_scheduler():
    """Hook for integrating broadcaster with WeatherScheduler.

    Add this to scheduler.py run_vigilance_update method.
    """
    broadcaster = AlertBroadcaster()
    broadcaster._load_alert_state()
    result = broadcaster.check_and_broadcast()
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    broadcaster = AlertBroadcaster()
    broadcaster._load_alert_state()

    result = broadcaster.check_and_broadcast()
    print(json.dumps(result, indent=2))
