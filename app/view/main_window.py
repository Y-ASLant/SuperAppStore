# coding:utf-8
import os
import requests

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import (NavigationItemPosition, MSFluentWindow,
                           SplashScreen, FluentIcon as FIF, InfoBarPosition)
from .home_interface import HomeInterface
from .setting_interface import SettingInterface
from .application_interface import ApplicationInterface
from .download_interface import DownloadInterface
from .custom_interface import CustomInterface
from ..common.config import cfg
from ..common.icon import Icon
from ..common import resource
from ..common.signal_bus import signalBus
from ..common.setting import APPS_LIST_URL, CONFIG_FOLDER, APPS_FILE
from ..utils.update import UpdateManager
from ..utils.notification import Notification


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

        # 获取应用列表
        self.fetchAppsList()

        # TODO: create sub interface
        self.homeInterface = HomeInterface(self)
        self.applicationInterface = ApplicationInterface(self)
        self.downloadInterface = DownloadInterface(self)
        self.settingInterface = SettingInterface(self)
        self.customInterface = CustomInterface(self)

        # 初始化更新管理器
        self.updateManager = UpdateManager(self)
        
        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        
        # 同步两个界面的下载记录
        self.syncDownloadRecords()

        # 如果配置中启用了启动时检查更新，则在启动时检查更新
        if cfg.get(cfg.checkUpdateAtStartUp):
            self.checkUpdate()

    def refreshAppsList(self):
        """重新获取应用列表并刷新应用界面"""
        # 先获取应用列表
        self.fetchAppsList()
        
        # 然后重新加载应用界面
        if hasattr(self, 'applicationInterface'):
            self.applicationInterface._ApplicationInterface__loadApps()
            self.__showInfoMessage("应用列表已刷新")
            
    def __showInfoMessage(self, message):
        """显示信息通知"""
        Notification.info(
            title=self.tr("提示"),
            content=self.tr(message),
            duration=2000,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        # 连接检查更新信号
        signalBus.checkUpdateSig.connect(self.checkUpdate)
        # 连接下载应用信号
        signalBus.downloadApp.connect(self.onDownloadApp)
        # 连接下载完成信号到同步记录函数
        self.downloadInterface.signals.moveToCompletedSignal.connect(self.onDownloadComplete)
        # 连接下载失败信号
        self.downloadInterface.signals.moveToFailedSignal.connect(self.onDownloadFailed)
        
    def syncDownloadRecords(self):
        """同步应用界面和下载界面的下载记录"""
        # 合并两个界面的下载记录
        merged_ids = self.applicationInterface.downloaded_app_ids.union(
            self.downloadInterface.downloaded_app_ids
        )
        
        # 更新两个界面的下载记录
        self.applicationInterface.downloaded_app_ids = merged_ids
        self.downloadInterface.downloaded_app_ids = merged_ids.copy()
        
        # 保存合并后的记录
        self.applicationInterface._ApplicationInterface__saveDownloadedAppIds()

    def onDownloadApp(self, app_data):
        """处理应用下载请求"""
        self.downloadInterface.addDownloadTask(app_data)
        
            
    def onDownloadComplete(self, app_id):
        """处理下载完成或删除文件事件"""
        # 获取下载界面的下载记录
        downloaded_ids = self.downloadInterface.downloaded_app_ids
        
        # 更新应用界面的下载记录（同步两边的记录）
        self.applicationInterface.downloaded_app_ids = set(downloaded_ids)
        self.applicationInterface._ApplicationInterface__saveDownloadedAppIds()
        
        # 从正在下载的临时集合中移除
        if hasattr(self.applicationInterface, 'tracking_downloads') and app_id in self.applicationInterface.tracking_downloads:
            self.applicationInterface.tracking_downloads.remove(app_id)
        
        # 刷新应用列表显示
        if hasattr(self.applicationInterface, '_ApplicationInterface__updateAppList'):
            self.applicationInterface._ApplicationInterface__updateAppList()
            self.applicationInterface._ApplicationInterface__updateGameList()
            
    def onDownloadFailed(self, app_id, error_msg):
        """处理下载失败事件"""
        # 从正在下载的临时集合中移除
        if hasattr(self.applicationInterface, 'tracking_downloads') and app_id in self.applicationInterface.tracking_downloads:
            self.applicationInterface.tracking_downloads.remove(app_id)
        
        # 刷新应用列表显示
        if hasattr(self.applicationInterface, '_ApplicationInterface__updateAppList'):
            self.applicationInterface._ApplicationInterface__updateAppList()
            self.applicationInterface._ApplicationInterface__updateGameList()

    def checkUpdate(self):
        """检查更新"""
        self.updateManager.check_for_updates()
        
    def fetchAppsList(self):
        """从指定URL获取应用列表并保存到AppData目录"""
        try:
            response = requests.get(APPS_LIST_URL, timeout=5)
            
            if response.status_code == 200:
                # 确保AppData目录存在
                os.makedirs(CONFIG_FOLDER, exist_ok=True)
                
                # 保存到AppData目录中的apps.json文件
                with open(APPS_FILE, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"应用列表已更新: {APPS_FILE}")
            else:
                print(f"获取应用列表失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"获取应用列表出错: {str(e)}")

    def initNavigation(self):
        # TODO: add navigation items
        self.addSubInterface(
            self.homeInterface, FIF.HOME, self.tr("首页"), FIF.HOME_FILL
        )
        self.addSubInterface(
            self.applicationInterface, FIF.APPLICATION, self.tr("应用")
        )
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, self.tr("下载"))
        self.downloadInterface.setObjectName('downloadInterface')

        # 添加 BotSparkle_Filled 图标，无任何功能
        self.addSubInterface(
            self.customInterface,
            Icon.BOT_SPARKLE,
            self.tr("自定义"),
            Icon.BOT_SPARKLE_FILLED,
            NavigationItemPosition.BOTTOM,
        )
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
