import inspect
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, Optional

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


# 基础日志目录
BASE_LOG_DIR = Path(".data")


def get_daily_log_path():
    """
    动态生成当天的日志目录，并返回日志文件的路径
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    save_dir = BASE_LOG_DIR / current_date / f"log.log"

    return save_dir


def content_based_rotation(message, file):
    """
    自定义切分逻辑，返回新的固定文件路径。
    """
    if "Log level set to" in message.record["message"]:
        return True
    return False


# 删除过期的日志目录
def clean_old_logs():
    """
    删除超过 3 天的日志目录
    """
    current_date = datetime.now()  # 使用当前时区
    for log_dir in BASE_LOG_DIR.iterdir():
        if log_dir.is_dir():
            try:
                dir_date = datetime.strptime(log_dir.name, "%Y-%m-%d")
                if (current_date - dir_date).days > 3:
                    for log_file in log_dir.iterdir():
                        log_file.unlink()  # 删除日志文件
                    log_dir.rmdir()  # 删除目录
            except ValueError:
                # 如果文件夹名称不是日期格式，跳过
                continue


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
    clean_old_logs()

    logger.add(
        sys.stderr,
        level=log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        filter=lambda record: record["level"].name != "SUCCESS",
    )
    success_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 时间格式
        "<level>{level: <8}</level> | "  # 日志级别
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 模块、函数、行号
        "<bold>{message}</bold>"  # 日志消息
    )

    # SUCCESS 特定格式输出
    logger.add(
        sink=sys.stderr,
        level="SUCCESS",  # 针对 SUCCESS 日志
        format=success_format,
        filter=lambda record: record["level"].name == "SUCCESS",  # 仅过滤 SUCCESS 日志
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    logger.add(
        get_daily_log_path(),  # 动态生成日志路径
        level=log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        rotation=content_based_rotation,  # 使用自定义切分逻辑
        retention=None,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.success(f"Log level set to {log_level}!")


def colorize_message(
    message_title: Optional[str] = "",
    color: Literal[
        "black", "blue", "cyan", "green", "magenta", "red", "white", "yellow"
    ] = "black",
    style: Literal["bold", "dim", "normal", "italic", "underline"] = "normal",
    message_content: Optional[str] | Dict = "",
):
    # Open and close tags for color and style
    color_tag = f"<{color}>" if color else ""
    style_tag = f"<{style}>" if style != "normal" else ""

    # Generate the closing tag properly
    close_tag = ""
    if color_tag and style_tag:
        close_tag = "</></>"
    elif color_tag:
        close_tag = "</>"
    elif style_tag:
        close_tag = "</>"

    # Styled title
    styled_title = (
        f"{style_tag}{color_tag}{'=' * 20} {message_title} {'=' * 20}{close_tag}"
        if message_title
        else ""
    )

    # Format content
    if isinstance(message_content, Dict):
        formatted_content = json.dumps(message_content, ensure_ascii=True, indent=2)
    else:
        formatted_content = str(message_content) if message_content else ""

    # Log the message
    logger.success(
        f"\n{styled_title}\n{formatted_content}\n"
        if formatted_content
        else f"\n{styled_title}\n"
    )
