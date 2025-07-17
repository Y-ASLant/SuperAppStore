# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

from qfluentwidgets import ScrollArea, SimpleCardWidget, SubtitleLabel, BodyLabel, setFont, setTheme

from ..common.style_sheet import StyleSheet
from ..common.config import cfg


class CustomInterface(ScrollArea):
    """ 自定义界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("customInterface")
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # 设置边距和间距
        self.vBoxLayout.setContentsMargins(36, 36, 36, 36)
        self.vBoxLayout.setSpacing(28)
        self.scrollWidget.setObjectName("scrollWidget")

        # 创建界面元素
        self.titleLabel = SubtitleLabel(self.tr("自定义界面"), self)
        self.titleLabel.setObjectName("customInterfaceTitle")
        
        # 添加说明文字
        self.descriptionLabel = BodyLabel(
            self.tr("这是一个空白的自定义界面"), 
            self
        )
         
        # 初始化界面
        self.__initWidget()
        
        # 连接信号槽
        self.__connectSignalToSlot()

    def __initWidget(self):
        """初始化界面"""
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # 设置字体
        setFont(self.titleLabel, 23, QFont.Weight.DemiBold)
        setFont(self.descriptionLabel, 16, QFont.Weight.Normal)
        
        # 应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)
        
        # 初始化布局
        self.__initLayout()
        
    def __initLayout(self):
        """初始化布局"""
        # 添加到主布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.descriptionLabel)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addStretch(1)
        
    def __connectSignalToSlot(self):
        """连接信号和槽"""
        # 连接主题变更信号
        cfg.themeChanged.connect(self.__onThemeChanged)
        
    def __onThemeChanged(self, theme):
        """处理主题变更"""
        setTheme(theme)
        # 重新应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self) 