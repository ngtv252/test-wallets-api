import logging

import structlog


_LOGGING_CONFIGURED = False


def configure_logging(settings) -> None:
    """Configure stdlib logging and structlog once.

    Idempotent: safe to call multiple times.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    level_name = str(getattr(settings, "log_level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    # Stdlib logging: stream only (Docker log driver handles rotation)
    root_handlers = [logging.StreamHandler()]
    logging.basicConfig(level=level, handlers=root_handlers)

    # Make uvicorn loggers propagate to root so they share handlers/format
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = True
        # Clear their own handlers if any to avoid duplicate logs
        logger.handlers.clear()

    # Structlog to JSON lines
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _LOGGING_CONFIGURED = True


