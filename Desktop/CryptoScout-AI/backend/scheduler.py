
# backend/scheduler.py

import threading
import time
import logging

from services.scanner_service import run_scan

logger = logging.getLogger(__name__)

# =====================================================
# CONFIG
# =====================================================

SCAN_INTERVAL_SECONDS = 300  # 5 minutes

_scheduler_thread = None
_running = False
_lock = threading.Lock()


# =====================================================
# SAFE SCAN WRAPPER
# =====================================================

def _safe_scan():
    """
    Ensures only one scan runs at a time.
    """

    if not _lock.acquire(blocking=False):
        logger.warning("Scan skipped — previous scan still running")
        return

    try:
        run_scan()
    finally:
        _lock.release()


# =====================================================
# BACKGROUND LOOP
# =====================================================

def _scheduler_loop():
    global _running

    logger.info("Scheduler started (interval: %s sec)", SCAN_INTERVAL_SECONDS)

    while _running:
        try:
            _safe_scan()
        except Exception as e:
            logger.error("Scheduler error: %s", e)

        time.sleep(SCAN_INTERVAL_SECONDS)

    logger.info("Scheduler stopped")


# =====================================================
# PUBLIC CONTROL
# =====================================================

def start_scheduler():
    global _scheduler_thread, _running

    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.warning("Scheduler already running")
        return

    _running = True

    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        daemon=True
    )

    _scheduler_thread.start()


def stop_scheduler():
    global _running
    _running = False
