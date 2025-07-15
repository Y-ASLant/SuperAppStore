# coding:utf-8
from qfluentwidgets import ScrollArea, SegmentedWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget
from qfluentwidgets import FluentIcon as FIF

from ..common.style_sheet import StyleSheet
from qfluentwidgets import setFont


class ApplicationInterface(ScrollArea):
    """ 应用界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # 添加分段导航栏
        self.segmentedWidget = SegmentedWidget(self)
        
        # 创建堆叠小部件用于切换内容
        self.stackedWidget = QStackedWidget(self)
        
        # 应用页面
        self.appPage = QWidget(self)
        self.appPageLayout = QVBoxLayout(self.appPage)
        self.appInfoLabel = QLabel(self.tr("这里显示所有可用的应用"), self.appPage)
        self.appPageLayout.addWidget(self.appInfoLabel)
        self.appPage.setObjectName("appPage")
        
        # 游戏页面
        self.gamePage = QWidget(self)
        self.gamePageLayout = QVBoxLayout(self.gamePage)
        self.gameInfoLabel = QLabel(self.tr("这里显示所有可用的游戏"), self.gamePage)
        self.gamePageLayout.addWidget(self.gameInfoLabel)
        self.gamePage.setObjectName("gamePage")
        
        # 添加子界面（带图标）
        self.addSubInterface(self.appPage, "appPage", self.tr("  应用  "), FIF.APPLICATION)
        self.addSubInterface(self.gamePage, "gamePage", self.tr("  游戏  "), FIF.GAME)

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
        self.setObjectName('applicationInterface')

        # 初始化样式表
        setFont(self.appInfoLabel, 16, QFont.Weight.Normal)
        setFont(self.gameInfoLabel, 16, QFont.Weight.Normal)
        self.scrollWidget.setObjectName('scrollWidget')
        self.segmentedWidget.setFixedWidth(200)
        StyleSheet.SETTING_INTERFACE.apply(self)
        self.scrollWidget.setStyleSheet("QWidget{background:transparent}")

        # 设置默认显示的页面
        self.stackedWidget.setCurrentWidget(self.appPage)
        self.segmentedWidget.setCurrentItem("appPage")

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(36, 10, 36, 0)
        self.vBoxLayout.addSpacing(24)
        self.vBoxLayout.addWidget(self.segmentedWidget, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.addStretch(1)
        
    def __connectSignalToSlot(self):
        self.segmentedWidget.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        ) 