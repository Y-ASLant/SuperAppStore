import os

args = [
    "nuitka",
    "--standalone",
    "--windows-console-mode=disable",  # 更新控制台模式参数
    "--enable-plugin=pyqt5",
    "--include-qt-plugins=sensible,sqldrivers",
    "--assume-yes-for-downloads",
    "--mingw64",  # Use MinGW
    "--show-memory",
    "--show-progress",
    "--windows-icon-from-ico=App.ico",
    '--windows-company-name="ASLant Top."',
    "--windows-product-name=SuperAppStore",
    "--product-version=1.0.0",  # 添加固定的产品版本号
    '--windows-file-description="SuperAppStore"',
    "--output-dir=dist",
    "--output-filename=SuperAppStore.exe",  # 指定输出文件名
    "main.py",
]

os.system(" ".join(args))
