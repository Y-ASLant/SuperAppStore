# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QFont

from qfluentwidgets import (ScrollArea, SubtitleLabel, BodyLabel, setFont, PrimaryPushButton, LineEdit)

from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.setting import DEFAULT_DOWNLOAD_PATH
from ..utils.notification import Notification


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
        # 添加说明文字
        self.descriptionLabel = BodyLabel(
            self.tr("在这里可以自定义软件的各项设置"), 
            self
        )
        
        # 下载路径设置
        self.downloadPathLabel = SubtitleLabel(self.tr("下载路径设置"), self)
        self.downloadPathLabel.setObjectName("downloadPathLabel")
        
        # 下载路径说明
        self.downloadPathDescriptionLabel = BodyLabel(
            self.tr("设置应用下载的默认保存位置"), 
            self
        )
        
        # 下载路径输入框和按钮
        self.downloadPathLayout = QHBoxLayout()
        self.downloadPathEdit = LineEdit(self)
        self.downloadPathEdit.setText(cfg.downloadPath.value)
        self.downloadPathEdit.setReadOnly(True)
        
        self.browseButton = PrimaryPushButton(self.tr("浏览"), self)
        self.browseButton.clicked.connect(self.__onBrowseButtonClicked)
        
        self.resetButton = PrimaryPushButton(self.tr("重置"), self)
        self.resetButton.clicked.connect(self.__onResetButtonClicked)
        
        self.downloadPathLayout.addWidget(self.downloadPathEdit)
        self.downloadPathLayout.addWidget(self.browseButton)
        self.downloadPathLayout.addWidget(self.resetButton)
         
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
        setFont(self.descriptionLabel, 16, QFont.Weight.Normal)
        setFont(self.downloadPathLabel, 18, QFont.Weight.DemiBold)
        setFont(self.downloadPathDescriptionLabel, 14, QFont.Weight.Normal)
        
        # 应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)
        
        # 初始化布局
        self.__initLayout()
        
    def __initLayout(self):
        """初始化布局"""
        # 添加到主布局
        self.vBoxLayout.addWidget(self.descriptionLabel)
        self.vBoxLayout.addSpacing(30)
        
        # 添加下载路径设置
        self.vBoxLayout.addWidget(self.downloadPathLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.downloadPathDescriptionLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.downloadPathLayout)
        
        self.vBoxLayout.addStretch(1)
        
    def __connectSignalToSlot(self):
        """连接信号和槽"""
        pass
        
    def __onBrowseButtonClicked(self):
        """浏览按钮点击事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            self.tr("选择下载文件夹"), 
            cfg.downloadPath.value
        )
        
        if folder_path:
            # 更新下载路径配置
            cfg.set(cfg.downloadPath, folder_path)
            self.downloadPathEdit.setText(folder_path)
            
            # 显示成功提示
            Notification.success(
                self.tr('设置成功'),
                self.tr('下载路径已更新'),
                duration=2000,
                parent=self
            )
    
    def __onResetButtonClicked(self):
        """重置按钮点击事件"""
        # 重置为默认下载路径
        cfg.set(cfg.downloadPath, DEFAULT_DOWNLOAD_PATH)
        self.downloadPathEdit.setText(DEFAULT_DOWNLOAD_PATH)
        
        # 显示提示
        Notification.success(
            self.tr('重置成功'),
            self.tr('下载路径已重置为默认值'),
            duration=2000,
            parent=self
        ) 