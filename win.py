import os
from app.common.setting import VERSION  # 导入版本号

args = [
    "nuitka",
    "--standalone",
    "--windows-console-mode=disable",  # force显示控制台 disable不显示控制台
    "--enable-plugin=pyqt5",
    "--include-qt-plugins=sensible,sqldrivers",
    "--assume-yes-for-downloads",
    "--mingw64",  # Use MinGW
    "--show-memory",
    "--show-progress",
    "--windows-icon-from-ico=App.ico",
    '--windows-company-name="ASLant Top."',
    "--windows-product-name=SuperAppStore",
    f"--product-version={VERSION}",  # 从setting中读取版本号
    '--windows-file-description="SuperAppStore"',
    "--output-dir=dist",
    "--output-filename=SuperAppStore.exe",  # 指定输出文件名
    "main.py",
]

os.system(" ".join(args))
