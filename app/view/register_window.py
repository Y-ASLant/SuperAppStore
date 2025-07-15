# coding:utf-8
import sys
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (MSFluentTitleBar, isDarkTheme, ImageLabel, BodyLabel, LineEdit,
                            PasswordLineEdit, PrimaryPushButton, CheckBox, InfoBar,
                            InfoBarPosition)
from ..common import resource
from ..common.license_service import LicenseService
from ..common.config import cfg


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class RegisterWindow(Window):
    """ Register window """

    loginSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitleBar(MSFluentTitleBar(self))
        self.register = LicenseService()

        self.imageLabel = ImageLabel(':/app/images/background.jpg', self)
        self.iconLabel = ImageLabel(':/app/images/logo.png', self)

        self.usernameLabel = BodyLabel(self.tr('用户名'), self)
        self.usernameLineEdit = LineEdit(self)

        self.passwordLabel = BodyLabel(self.tr('密码'))
        self.passwordLineEdit = PasswordLineEdit(self)

        self.rememberCheckBox = CheckBox(self.tr('记住我'), self)

        self.loginButton = PrimaryPushButton(self.tr('登录'), self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.__initWidgets()

    def __initWidgets(self):
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        self.rememberCheckBox.setChecked(cfg.get(cfg.rememberMe))

        self.usernameLineEdit.setPlaceholderText('请输入用户名')
        self.passwordLineEdit.setPlaceholderText('请输入密码')

        if self.rememberCheckBox.isChecked():
            self.usernameLineEdit.setText(cfg.get(cfg.email))
            self.passwordLineEdit.setText(cfg.get(cfg.activationCode))

        self.__connectSignalToSlot()
        self.__initLayout()

        if isWin11():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())
        else:
            color = QColor(25, 33, 42) if isDarkTheme(
            ) else QColor(240, 244, 249)
            self.setStyleSheet(f"RegisterWindow{{background: {color.name()}}}")

        self.setWindowTitle('Super App Store')
        self.setWindowIcon(QIcon(":/app/images/logo.png"))
        self.resize(1000, 650)

        if sys.platform == "darwin":
            self.titleBar.minBtn.hide()
            self.titleBar.closeBtn.hide()
            self.setSystemTitleBarButtonVisible(True)
            self.setWindowFlags((self.windowFlags() & ~Qt.WindowFullscreenButtonHint)
                                & ~Qt.WindowMaximizeButtonHint | Qt.CustomizeWindowHint)

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI', 'Microsoft YaHei', 'PingFang SC';
                padding: 0 4px;
                color: white
            }
        """)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.titleBar.raise_()

    def __initLayout(self):
        self.imageLabel.scaledToHeight(650)
        self.iconLabel.scaledToHeight(100)

        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setContentsMargins(20, 0, 20, 0)
        self.vBoxLayout.setSpacing(0)
        self.hBoxLayout.setSpacing(0)

        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(
            self.iconLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(38)
        self.vBoxLayout.addWidget(self.usernameLabel)
        self.vBoxLayout.addSpacing(11)
        self.vBoxLayout.addWidget(self.usernameLineEdit)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addWidget(self.passwordLabel)
        self.vBoxLayout.addSpacing(11)
        self.vBoxLayout.addWidget(self.passwordLineEdit)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addWidget(self.rememberCheckBox)
        self.vBoxLayout.addSpacing(15)
        self.vBoxLayout.addWidget(self.loginButton)
        self.vBoxLayout.addSpacing(30)
        self.vBoxLayout.addStretch(1)

    def __connectSignalToSlot(self):
        self.loginButton.clicked.connect(self._login)
        self.rememberCheckBox.stateChanged.connect(
            lambda: cfg.set(cfg.rememberMe, self.rememberCheckBox.isChecked()))

    def _login(self):
        password = self.passwordLineEdit.text().strip()
        username = self.usernameLineEdit.text().strip()

        # 简单的登录验证，可以替换为实际验证逻辑
        if not username or not password or password != "123456":
            InfoBar.error(
                self.tr("登录失败"),
                self.tr('请检查用户名或密码是否正确'),
                position=InfoBarPosition.TOP,
                duration=2000,
                isClosable=False,
                parent=self.window()
            )
        else:
            InfoBar.success(
                self.tr("登录成功"),
                self.tr('欢迎回来，') + username,
                position=InfoBarPosition.TOP,
                isClosable=False,
                parent=self.window()
            )

            if cfg.get(cfg.rememberMe):
                cfg.set(cfg.email, username)
                cfg.set(cfg.activationCode, password)

            self.loginButton.setDisabled(True)
            QTimer.singleShot(1500, self._showMainWindow)

    def _showMainWindow(self):
        self.close()
        # 移除此处的主题色设置，使用main.py中的全局设置

        self.loginSignal.emit()

    def systemTitleBarRect(self, size):
        """ Returns the system title bar rect, only works for macOS """
        return QRect(size.width() - 75, 0, 75, size.height())
