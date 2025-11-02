import logging
from logging.config import dictConfig
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
            "rich": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s | req_id=%(request_id)s user_id=%(user_id)s"
            },
        },
        "filters": {
            "request_context": {
                "()": "app.core.log_setup.RequestContextFilter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "rich",
                "filters": ["request_context"],
                "level": LOG_LEVEL,
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": LOG_LEVEL,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "fastapi": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "celery": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "app": {"level": LOG_LEVEL, "handlers": ["console"], "propagate": False},
        },
    })

class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "user_id"):
            record.user_id = "-"
        return True