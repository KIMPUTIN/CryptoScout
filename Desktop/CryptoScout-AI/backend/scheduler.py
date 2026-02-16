
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_coingecko


def start_scheduler():
    try:
        scheduler = BackgroundScheduler()

        scheduler.add_job(
            scan_coingecko,
            "interval",
            minutes=30,   # TEMPORARY for testing
            id="coingecko_scan",
            replace_existing=True
        )

        scheduler.start()
        print("⏰ Scheduler started (every 1 minute)")
        print("⏰ First scan will run in 1 minute...")
    except Exception as e:
        print(f"❌ ERROR: Could not start scheduler: {e}")
        print("   App will continue without automatic scanning")
        import traceback
        traceback.print_exc()

