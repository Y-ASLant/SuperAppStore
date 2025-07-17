# coding: utf-8
from pathlib import Path

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
