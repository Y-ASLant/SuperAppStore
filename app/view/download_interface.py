# coding:utf-8
from qfluentwidgets import ScrollArea, SegmentedWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget
from qfluentwidgets import FluentIcon as FIF

from ..common.style_sheet import StyleSheet
from qfluentwidgets import setFont


class DownloadInterface(ScrollArea):
    """下载界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 添加分段导航栏
        self.segmentedWidget = SegmentedWidget(self)

        # 创建堆叠小部件用于切换内容
        self.stackedWidget = QStackedWidget(self)

        # 下载中页面
        self.downloadingPage = QWidget(self)
        self.downloadingPageLayout = QVBoxLayout(self.downloadingPage)
        self.downloadingInfoLabel = QLabel(
            self.tr("这里显示正在下载的应用"), self.downloadingPage
        )
        self.downloadingPageLayout.addWidget(self.downloadingInfoLabel)
        self.downloadingPage.setObjectName("downloadingPage")

        # 已完成页面
        self.completedPage = QWidget(self)
        self.completedPageLayout = QVBoxLayout(self.completedPage)
        self.completedInfoLabel = QLabel(
            self.tr("这里显示下载已完成的应用"), self.completedPage
        )
        self.completedPageLayout.addWidget(self.completedInfoLabel)
        self.completedPage.setObjectName("completedPage")

        # 失败页面
        self.failedPage = QWidget(self)
        self.failedPageLayout = QVBoxLayout(self.failedPage)
        self.failedInfoLabel = QLabel(
            self.tr("这里显示下载失败的应用"), self.failedPage
        )
        self.failedPageLayout.addWidget(self.failedInfoLabel)
        self.failedPage.setObjectName("failedPage")

        # 添加子界面（带图标）
        self.addSubInterface(
            self.downloadingPage, "downloadingPage", self.tr("正在下载"), FIF.DOWNLOAD
        )
        self.addSubInterface(
            self.completedPage, "completedPage", self.tr("下载完成"), FIF.COMPLETED
        )
        self.addSubInterface(self.failedPage, "failedPage", self.tr("下载失败"), FIF.INFO)

        self.__initWidget()
        self.__connectSignalToSlot()

    def addSubInterface(self, widget, objectName, text, icon=None):
        """添加子界面"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.segmentedWidget.addItem(routeKey=objectName, text=text, icon=icon)

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("downloadInterface")

        # 初始化样式表
        setFont(self.downloadingInfoLabel, 16, QFont.Weight.Normal)
        setFont(self.completedInfoLabel, 16, QFont.Weight.Normal)
        setFont(self.failedInfoLabel, 16, QFont.Weight.Normal)
        self.scrollWidget.setObjectName("scrollWidget")
        self.segmentedWidget.setFixedWidth(200)
        StyleSheet.SETTING_INTERFACE.apply(self)
        self.scrollWidget.setStyleSheet("QWidget{background:transparent}")

        # 设置默认显示的页面
        self.stackedWidget.setCurrentWidget(self.downloadingPage)
        self.segmentedWidget.setCurrentItem("downloadingPage")

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setSpacing(28)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 0)
        self.vBoxLayout.addWidget(self.segmentedWidget, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.addStretch(1)

    def __connectSignalToSlot(self):
        self.segmentedWidget.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )
