
from apscheduler.schedulers.background import BackgroundScheduler
from scanner import scan_coingecko

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scan_coingecko, "interval", hours=1)
    scheduler.start()
