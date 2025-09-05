"""Logging utilities for aif_workflow_helpers package."""

import logging

LOGGER_NAME = "aif_workflow_helpers"
_logger = logging.getLogger(LOGGER_NAME)

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"

_configured = False

def configure_logging(level: int = logging.INFO, *, propagate: bool = False, force: bool = False,
                      fmt: str = _DEFAULT_FORMAT, stream=None) -> logging.Logger:
    """Configure and return the shared package logger.

    Idempotently initializes the module-level logger used across helper modules.
    Subsequent calls without `force` will only adjust the log level. Setting
    `force=True` clears existing handlers and reconfigures from scratch.

    Args:
        level (int): Logging level to apply (default: logging.INFO).
        propagate (bool): If True, log records propagate to the root logger.
        force (bool): If True, always reconfigure even if already configured.
        fmt (str): Log message format string.
        stream (IO | None): Optional stream for the handler; defaults to
            `sys.stderr` when None.

    Returns:
        logging.Logger: The configured shared logger instance.
    """
    global _configured
    if _configured and not force:
        _logger.setLevel(level)
        return _logger
    if force and _logger.handlers:
        _logger.handlers.clear()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(fmt))
    _logger.addHandler(handler)
    _logger.setLevel(level)
    _logger.propagate = propagate
    _configured = True
    return _logger

logger = _logger  # public shared logger instance

__all__ = ["logger", "configure_logging", "LOGGER_NAME"]