# coding:utf-8
from qfluentwidgets import ScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

from ..common.style_sheet import StyleSheet
from qfluentwidgets import setFont, setTheme
from ..common.config import cfg


class HomeInterface(ScrollArea):
    """ 首页界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 首页标签
        self.homeLabel = QLabel(self.tr("首页"), self)
        
        # 添加欢迎信息
        self.welcomeLabel = QLabel(self.tr("欢迎使用 Super App Store."), self.scrollWidget)
        self.welcomeLabel.setObjectName('contentLabel')  # 设置对象名

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('homeInterface')

        # 初始化样式表
        setFont(self.homeLabel, 23, QFont.Weight.DemiBold)
        setFont(self.welcomeLabel, 16, QFont.Weight.Normal)
        self.scrollWidget.setObjectName('scrollWidget')
        self.homeLabel.setObjectName('settingLabel')  # 使用与settingLabel相同的对象名
        
        # 应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)  # 暂时使用相同样式

        # 初始化布局
        self.__initLayout()
        
        # 连接主题变更信号
        cfg.themeChanged.connect(self.__onThemeChanged)

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.addSpacing(36)
        self.vBoxLayout.addWidget(self.homeLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.welcomeLabel)
        self.vBoxLayout.addStretch(1)
        
    def __onThemeChanged(self, theme):
        """处理主题变更"""
        setTheme(theme)
        # 重新应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self) 