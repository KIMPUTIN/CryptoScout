
# backend/models/scan_status.py

from datetime import datetime


class ScanStatus:
    def __init__(self):
        self.last_run = None
        self.last_result = "UNKNOWN"
        self.failure_count = 0
        self.api_failures = 0

    def success(self):
        self.last_run = datetime.utcnow().isoformat()
        self.last_result = "SUCCESS"
        self.failure_count = 0

    def failure(self):
        self.last_run = datetime.utcnow().isoformat()
        self.last_result = "FAILED"
        self.failure_count += 1

    def api_failure(self):
        self.api_failures += 1

    def snapshot(self):
        return {
            "scanner": {
                "last_run": self.last_run,
                "last_result": self.last_result,
                "failure_count": self.failure_count
            },
            "api_failures": self.api_failures
        }
