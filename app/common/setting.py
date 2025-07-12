# coding: utf-8
from pathlib import Path

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2025
AUTHOR = "ASLant"
VERSION = "v1.0.0"
APP_NAME = "SuperAppStore"
HELP_URL = "https://aslant.top"
REPO_URL = "https://aslant.top"
FEEDBACK_URL = "https://aslant.top"
DOC_URL = "https://qfluentwidgets.com/"

CONFIG_FOLDER = Path('AppData').absolute()
CONFIG_FILE = CONFIG_FOLDER / "config.json"
