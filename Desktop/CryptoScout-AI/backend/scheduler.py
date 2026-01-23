
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_coingecko


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        scan_coingecko,
        "interval",
        minutes=1,   # TEMPORARY for testing
        id="coingecko_scan"
    )

    scheduler.start()
    print("⏰ Scheduler started (every 1 minute)")

