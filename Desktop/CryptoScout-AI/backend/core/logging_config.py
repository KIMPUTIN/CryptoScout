
# backend/core/logging_config.py

import logging
import sys
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):

    def format(self, record):

        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        return json.dumps(log_record)


def setup_logging():

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]
