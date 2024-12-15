import inspect
import logging
import sys
from typing import Literal, Optional

from loguru import logger

from .config import settings

logger = logger.opt(colors=not settings.no_color)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def set_logger_level_from_config(log_level):
    """
    Configures the loguru logger with specified log level and integrates it with the standard logging module.

    Args:
        log_level (str): The log level to set for loguru (e.g., "DEBUG", "INFO", "WARNING").

    This function:
    - Removes any existing loguru handlers to ensure a clean slate.
    - Adds a new handler to loguru, directing output to stderr with the specified level.
      - `enqueue=True` ensures thread-safe logging by using a queue, helpful in multi-threaded contexts.
      - `backtrace=False` minimizes detailed traceback to prevent overly verbose output.
      - `diagnose=False` suppresses additional loguru diagnostic information for more concise logs.
    - Redirects the standard logging output to loguru using the InterceptHandler, allowing loguru to handle
      all logs consistently across the application.
    """
    logger.remove()
    logger.add(
        sys.stderr, level=log_level, enqueue=True, backtrace=False, diagnose=False
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.success(f"Log level set to {log_level}!")


COLOR_MAP = {
    "black": {"dark": "white", "light": "black"},
    "blue": {"dark": "light-blue", "light": "blue"},
    "cyan": {"dark": "light-cyan", "light": "cyan"},
    "green": {"dark": "light-green", "light": "green"},
    "magenta": {"dark": "light-magenta", "light": "magenta"},
    "red": {"dark": "light-red", "light": "red"},
    "white": {"dark": "black", "light": "white"},
    "yellow": {"dark": "light-yellow", "light": "yellow"},
}


def colorize_message(
    message_title: Optional[str] = "",
    color: Literal[
        "black", "blue", "cyan", "green", "magenta", "red", "white", "yellow"
    ] = "black",
    style: Literal["bold", "dim", "normal", "italic", "underline"] = "normal",
    message_content: Optional[str] = "",
) -> str:
    # Determine the theme-specific color
    theme_color = COLOR_MAP[color][settings.theme]

    # Open and close tags for color and style
    color_tag = f"<{theme_color}>" if theme_color else ""

    style_tag = f"<{style}>" if style != "normal" else ""

    if color_tag and style_tag:
        close_tag = "</></>"
    elif color_tag or style_tag:
        close_tag = "</>"
    else:
        close_tag = ""

    # Fixed separator and styled title
    styled_title = (
        f"{style_tag}{color_tag}{'=' * 20} {message_title} {'=' * 20}{close_tag}"
        if message_title
        else ""
    )

    # Combine title and content
    return (
        f"\n{styled_title}\n{message_content}\n"
        if message_content
        else f"\n{styled_title}\n"
    )
