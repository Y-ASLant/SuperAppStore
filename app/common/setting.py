# coding: utf-8
from pathlib import Path
import os
import sys

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2025
AUTHOR = "ASLant"
VERSION = "1.0.0"
UPDATE_DATE = "2025.07.16"
APP_NAME = "SuperAppStore"
HOME_URL = "https://aslant.top"
HELP_URL = "https://aslant.top"
REPO_URL = "https://github.com/Y-ASLant/SuperAppStore"
APPS_LIST_URL = "https://aslant.top/Demo_1/apps.json" # 应用列表JSON数据
VERSION_URL = "https://aslant.top/Demo_1/version.json" # 版本信息JSON数据

CONFIG_FOLDER = Path('AppData').absolute() # 配置文件夹
CONFIG_FILE = CONFIG_FOLDER / "config.json" # 配置文件
APPS_FILE = CONFIG_FOLDER / "apps.json" # 本地应用列表文件
DOWNLOADED_APPS_FILE = CONFIG_FOLDER / "downloaded_apps.json" # 已下载应用记录文件

# 默认下载路径 - 从Windows注册表获取系统下载文件夹位置
def get_default_download_path():
    """从注册表获取Windows系统的默认下载路径"""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                download_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                # 处理可能的环境变量
                if '%' in download_path:
                    download_path = os.path.expandvars(download_path)
                if os.path.exists(download_path):
                    return download_path
        except Exception:
            # 注册表访问失败时使用备用方案
            pass
    
    # 备用方案: 使用用户主目录下的Downloads文件夹
    return os.path.join(os.path.expanduser("~"), "Downloads")

# 将默认下载路径修改为函数，每次调用时获取最新的配置
def get_download_path():
    """获取当前配置的下载路径"""
    try:
        from .config import cfg
        return cfg.downloadPath.value
    except (ImportError, AttributeError):
        # 如果配置尚未加载，则返回默认值
        return get_default_download_path()

# 保留原始的默认下载路径常量，用于重置操作
DEFAULT_DOWNLOAD_PATH = get_default_download_path()
