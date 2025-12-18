"""Automated weather data extraction and visualization scheduler."""
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import schedule

from config import OUTPUT_DIR
from weather_extractor import MartiniqueWeatherExtractor
from map_generator import MartiniqueMapGenerator
from chart_generator import MartiniqueChartGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(OUTPUT_DIR) / "scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeatherScheduler:
    """Automated scheduler for weather data updates."""

    def __init__(self):
        self.extractor = MartiniqueWeatherExtractor()
        self.map_generator = MartiniqueMapGenerator()
        self.chart_generator = MartiniqueChartGenerator()

    def run_full_update(self) -> dict:
        """Execute full data extraction and visualization update."""
        logger.info("Starting full weather update cycle...")
        start_time = datetime.now()

        results = {
            "started_at": start_time.isoformat(),
            "extraction": None,
            "maps": None,
            "charts": None,
            "status": "running"
        }

        try:
            logger.info("Phase 1: Extracting weather data...")
            results["extraction"] = self.extractor.extract_all()

            logger.info("Phase 2: Generating maps...")
            results["maps"] = self.map_generator.generate_all_maps()

            logger.info("Phase 3: Generating charts...")
            results["charts"] = self.chart_generator.generate_all_charts()

            results["status"] = "success"
            results["completed_at"] = datetime.now().isoformat()
            results["duration_seconds"] = (datetime.now() - start_time).total_seconds()

            logger.info(f"Update cycle completed in {results['duration_seconds']:.1f}s")

        except Exception as e:
            logger.error(f"Update cycle failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)

        with open(Path(OUTPUT_DIR) / "last_update.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        return results

    def run_vigilance_update(self) -> dict:
        """Quick update of vigilance alerts only."""
        logger.info("Running vigilance alert check...")

        try:
            alerts = self.extractor.get_vigilance_alerts()
            self.map_generator.generate_vigilance_map(alerts)
            self.chart_generator.generate_vigilance_gauge(alerts)

            # Broadcast SMS alerts to subscribers
            from alert_broadcaster import AlertBroadcaster
            broadcaster = AlertBroadcaster()
            broadcaster._load_alert_state()
            broadcast_result = broadcaster.check_and_broadcast()
            logger.info(f"SMS broadcast result: {broadcast_result.get('total_sent', 0)} sent")

            return {"status": "success", "alerts": alerts, "sms_broadcast": broadcast_result}

        except Exception as e:
            logger.error(f"Vigilance update failed: {e}")
            return {"status": "error", "error": str(e)}

    def setup_schedule(self):
        """Configure automated update schedule."""
        schedule.every(3).hours.do(self.run_full_update)
        schedule.every(30).minutes.do(self.run_vigilance_update)
        schedule.every().day.at("06:00").do(self.run_full_update)
        schedule.every().day.at("18:00").do(self.run_full_update)

        logger.info("Schedule configured:")
        logger.info("  - Full update: every 3 hours + 06:00 + 18:00")
        logger.info("  - Vigilance check: every 30 minutes")

    def run(self):
        """Start the scheduler loop."""
        logger.info("Starting Martinique Weather Scheduler...")

        self.run_full_update()
        self.setup_schedule()

        logger.info("Scheduler running. Press Ctrl+C to stop.")

        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """Entry point for scheduler."""
    scheduler = WeatherScheduler()

    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            scheduler.run_full_update()
        elif sys.argv[1] == "--vigilance":
            scheduler.run_vigilance_update()
        else:
            print(f"Usage: {sys.argv[0]} [--once|--vigilance]")
    else:
        scheduler.run()


if __name__ == "__main__":
    main()
