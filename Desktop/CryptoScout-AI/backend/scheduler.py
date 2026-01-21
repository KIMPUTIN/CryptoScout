
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_coingecko

def start_scheduler():
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(scan_coingecko, "interval", hours=1)
        scheduler.start()
        print("⏰ Crypto scanner scheduler started (runs every hour)")
    except Exception as e:
        print(f"⚠️ Warning: Could not start scheduler: {e}")
        print("   App will continue without automatic scanning")
