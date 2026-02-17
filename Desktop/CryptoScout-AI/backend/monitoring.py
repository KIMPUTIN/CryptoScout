
from datetime import datetime

SYSTEM_STATUS = {
    "scanner": {
        "last_run": None,
        "last_duration": None,
        "last_result": "UNKNOWN",
        "failure_count": 0
    }
}

def mark_scan_success(duration):
    SYSTEM_STATUS["scanner"]["last_run"] = datetime.utcnow().isoformat()
    SYSTEM_STATUS["scanner"]["last_duration"] = duration
    SYSTEM_STATUS["scanner"]["last_result"] = "HEALTHY"
    SYSTEM_STATUS["scanner"]["failure_count"] = 0

def mark_scan_failure():
    SYSTEM_STATUS["scanner"]["failure_count"] += 1
    SYSTEM_STATUS["scanner"]["last_result"] = "FAILED"

def get_system_status():
    return SYSTEM_STATUS
