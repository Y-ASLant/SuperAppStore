# coding: utf-8
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen
from qfluentwidgets import FluentIcon as FIF

from .setting_interface import SettingInterface
from .home_interface import HomeInterface
from .application_interface import ApplicationInterface
from .download_interface import DownloadInterface
from ..common.config import cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common import resource


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

        # TODO: create sub interface
        self.homeInterface = HomeInterface(self)
        self.applicationInterface = ApplicationInterface(self)
        self.downloadInterface = DownloadInterface(self)
        self.settingInterface = SettingInterface(self)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def initNavigation(self):
        # self.navigationInterface.setAcrylicEnabled(True)

        # TODO: add navigation items
        self.addSubInterface(
            self.homeInterface, FIF.HOME, self.tr("首页"), FIF.HOME_FILL
        )
        self.addSubInterface(
            self.applicationInterface, FIF.APPLICATION, self.tr("应用")
        )
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, self.tr("下载"))

        # add custom widget to bottom
        self.addSubInterface(
            self.settingInterface,
            Icon.SETTINGS,
            self.tr("设置"),
            Icon.SETTINGS_FILLED,
            NavigationItemPosition.BOTTOM,
        )

        self.splashScreen.finish()

    def initWindow(self):
        self.resize(1000, 700)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(":/app/images/logo.png"))
        self.setWindowTitle("Super App Store")

        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())
