# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    ScrollArea,
    SubtitleLabel,
    BodyLabel,
    setFont,
    PrimaryPushButton,
    LineEdit,
    SwitchButton,
    PasswordLineEdit,
    InfoBarPosition,
)

from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.setting import DEFAULT_DOWNLOAD_PATH
from ..utils.notification import Notification


class CustomInterface(ScrollArea):
    """自定义界面"""

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

        # 下载路径设置
        self.downloadPathLabel = SubtitleLabel(self.tr("下载路径设置"), self)
        self.downloadPathLabel.setObjectName("downloadPathLabel")

        # 下载路径说明
        self.downloadPathDescriptionLabel = BodyLabel(
            self.tr("设置应用下载的默认保存位置"), self
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

        # GitHub Token 设置
        self.githubTokenLabel = SubtitleLabel(self.tr("GitHub Token 设置"), self)
        self.githubTokenLabel.setObjectName("githubTokenLabel")

        # GitHub Token 说明
        self.githubTokenDescriptionLabel = BodyLabel(
            self.tr("配置 GitHub Personal Access Token 以提高 API 访问限制（可选）"),
            self,
        )

        # Token 启用开关
        self.tokenEnableLayout = QHBoxLayout()
        self.tokenEnableLabel = BodyLabel(self.tr("启用 GitHub Token"), self)
        self.tokenEnableSwitch = SwitchButton(self)
        self.tokenEnableSwitch.setChecked(cfg.githubTokenEnabled.value)
        self.tokenEnableSwitch.checkedChanged.connect(self.__onTokenEnableChanged)
        self.tokenEnableLayout.addWidget(self.tokenEnableLabel)
        self.tokenEnableLayout.addStretch(1)
        self.tokenEnableLayout.addWidget(self.tokenEnableSwitch)

        # Token 输入框和保存按钮
        self.tokenInputLayout = QHBoxLayout()
        self.tokenEdit = PasswordLineEdit(self)
        self.tokenEdit.setPlaceholderText(
            self.tr("输入你的 GitHub Personal Access Token")
        )
        self.tokenEdit.setText(cfg.githubToken.value)

        self.saveTokenButton = PrimaryPushButton(self.tr("保存"), self)
        self.saveTokenButton.clicked.connect(self.__onSaveTokenClicked)

        self.clearTokenButton = PrimaryPushButton(self.tr("清除"), self)
        self.clearTokenButton.clicked.connect(self.__onClearTokenClicked)

        self.tokenInputLayout.addWidget(self.tokenEdit)
        self.tokenInputLayout.addWidget(self.saveTokenButton)
        self.tokenInputLayout.addWidget(self.clearTokenButton)

        # Token 提示信息
        self.tokenHintLabel = BodyLabel(
            self.tr(
                "如何获取 Token: GitHub Settings → Developer settings → Personal access tokens → Generate new token"
            ),
            self,
        )
        self.tokenHintLabel.setWordWrap(True)

        # 初始化界面
        self.__initWidget()

        # 连接信号槽
        self.__connectSignalToSlot()

    def __initLayout(self):
        """初始化布局"""

        # 添加下载路径设置
        self.vBoxLayout.addWidget(self.downloadPathLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.downloadPathDescriptionLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.downloadPathLayout)

        # 添加分隔
        self.vBoxLayout.addSpacing(30)

        # 添加 GitHub Token 设置
        self.vBoxLayout.addWidget(self.githubTokenLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.githubTokenDescriptionLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.tokenEnableLayout)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.tokenInputLayout)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.tokenHintLabel)

        self.vBoxLayout.addStretch(1)

    def __initWidget(self):
        """初始化界面"""
        self.resize(1600, 900)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # 设置字体
        setFont(self.downloadPathLabel, 18, QFont.Weight.DemiBold)
        setFont(self.downloadPathDescriptionLabel, 14, QFont.Weight.Normal)
        setFont(self.githubTokenLabel, 18, QFont.Weight.DemiBold)
        setFont(self.githubTokenDescriptionLabel, 14, QFont.Weight.Normal)

        # 应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)

        # 初始化布局
        self.__initLayout()

    def __connectSignalToSlot(self):
        """连接信号和槽"""
        pass

    def __onBrowseButtonClicked(self):
        """浏览按钮点击事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self, self.tr("选择下载文件夹"), cfg.downloadPath.value
        )

        if folder_path:
            # 更新下载路径配置
            cfg.set(cfg.downloadPath, folder_path)
            self.downloadPathEdit.setText(folder_path)

            # 显示成功提示
            Notification.success(
                self.tr("设置成功"),
                self.tr("下载路径已更新"),
                duration=2000,
                parent=self,
            )

    def __onResetButtonClicked(self):
        """重置按钮点击事件"""
        # 重置为默认下载路径
        cfg.set(cfg.downloadPath, DEFAULT_DOWNLOAD_PATH)
        self.downloadPathEdit.setText(DEFAULT_DOWNLOAD_PATH)

        # 显示提示
        Notification.success(
            self.tr("重置成功"),
            self.tr("下载路径已重置为默认值"),
            duration=2000,
            parent=self,
        )

    def __onTokenEnableChanged(self, checked):
        """Token 启用开关变化事件"""
        # 检查 Token 是否为空
        if checked and not cfg.githubToken.value.strip():
            # Token 为空，不允许启用
            self.tokenEnableSwitch.setChecked(False)
            Notification.warning(
                self.tr('无法启用'),
                self.tr('请先保存 GitHub Token'),
                duration=2000,
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        cfg.set(cfg.githubTokenEnabled, checked)
        
        # 显示提示
        status = self.tr('已启用') if checked else self.tr('已禁用')
        Notification.success(
            self.tr('设置成功'),
            self.tr(f'GitHub Token {status}'),
            duration=2000,
            parent=self
        )

    def __onSaveTokenClicked(self):
        """保存 Token 按钮点击事件"""
        token = self.tokenEdit.text().strip()
        
        if not token:
            Notification.error(
                self.tr('错误'),
                self.tr('Token 不能为空'),
                duration=2000,
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        # 保存 Token
        cfg.set(cfg.githubToken, token)
        
        # 显示提示
        Notification.success(
            self.tr('保存成功'),
            self.tr('GitHub Token 已保存，现在可以启用它'),
            duration=2000,
            parent=self
        )

    def __onClearTokenClicked(self):
        """清除 Token 按钮点击事件"""
        # 先禁用 Token
        if cfg.githubTokenEnabled.value:
            cfg.set(cfg.githubTokenEnabled, False)
            self.tokenEnableSwitch.setChecked(False)
        
        # 清除 Token
        cfg.set(cfg.githubToken, "")
        self.tokenEdit.clear()
        
        # 显示提示
        Notification.success(
            self.tr('清除成功'),
            self.tr('GitHub Token 已清除'),
            duration=2000,
            parent=self
        )
