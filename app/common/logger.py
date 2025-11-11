# coding: utf-8
"""
统一的日志配置
使用 loguru 进行日志管理
"""
import sys
from loguru import logger
from pathlib import Path

# 移除默认的 handler
logger.remove()

# 添加控制台输出（彩色，简洁格式）
# 在 PyInstaller windowed 模式下，sys.stderr 可能是 None，需要判断
if sys.stderr is not None:
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

# 添加文件输出（详细格式，用于调试）
log_dir = Path("AppData/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    log_dir / "app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="00:00",  # 每天午夜轮换
    retention="7 days",  # 保留7天
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
)

# 导出 logger 供其他模块使用
__all__ = ["logger"]
