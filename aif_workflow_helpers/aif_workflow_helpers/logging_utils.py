import logging

LOGGER_NAME = "aif_workflow_helpers"
_logger = logging.getLogger(LOGGER_NAME)

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"

_configured = False

def configure_logging(level: int = logging.INFO, *, propagate: bool = True, force: bool = False,
                      fmt: str = _DEFAULT_FORMAT, stream=None) -> logging.Logger:
    """Configure the shared package logger once.

    Parameters
    ----------
    level : int
        Logging level (default INFO).
    propagate : bool
        Whether to propagate to root logger.
    force : bool
        If True reconfigure even if already configured.
    fmt : str
        Log format string.
    stream : IO
        Optional custom stream (defaults to stderr if None).
    """
    global _configured
    if _configured and not force:
        _logger.setLevel(level)
        return _logger
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
