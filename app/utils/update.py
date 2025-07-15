# coding: utf-8
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QUrl, Qt, QPoint
from PyQt5.QtGui import QDesktopServices
import datetime
from qfluentwidgets import MessageBox, InfoBar, InfoBarPosition, InfoBarManager
from ..common.setting import VERSION, UPDATE_DATE


@InfoBarManager.register('Custom')
class CustomInfoBarManager(InfoBarManager):
    """ Custom info bar manager """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # the position of first info bar
        x = (parentSize.width() - infoBar.width()) // 2
        y = (parentSize.height() - infoBar.height()) // 2

        # get the position of current info bar
        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


class UpdateChecker(QObject):
    """检查应用更新的类"""

    # 定义更新检查完成的信号
    updateCheckFinished = pyqtSignal(
        bool, str, str, str, bool
    )  # 是否有更新，版本号，更新日志，下载链接，是否强制更新

    def __init__(self):
        super().__init__()
        self.version_url = "https://aslant.top/Demo_1/version.json"
        self.current_version = VERSION
        self.current_date = UPDATE_DATE  # 获取当前版本更新日期

    def check_update(self):
        """检查更新"""
        try:
            # 发送请求获取最新版本信息
            response = requests.get(self.version_url, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常

            # 解析JSON数据
            data = response.json()
            remote_version = data.get("version")
            remote_date = data.get("update_date", "")
            changelog = data.get("changelog", [])
            download_url = data.get("download_url", "")
            force_update = data.get("force_update", False)

            # 将更新日志列表转换为字符串
            changelog_str = "\n".join([f"• {item}" for item in changelog])

            # 比较版本号和日期
            has_update_version = self._compare_version(remote_version)
            has_update_date = False
            if remote_date:
                has_update_date = self._compare_date(remote_date)
            
            # 如果版本号或日期有一个更新，则认为有更新
            has_update = has_update_version or has_update_date

            # 发送信号
            self.updateCheckFinished.emit(
                has_update, remote_version, changelog_str, download_url, force_update
            )

            return has_update, remote_version, changelog_str, download_url, force_update

        except Exception as e:
            print(f"检查更新失败: {e}")
            # 发送信号表示检查失败
            self.updateCheckFinished.emit(False, "", f"检查更新失败: {e}", "", False)
            return False, "", f"检查更新失败: {e}", "", False

    def _compare_version(self, remote_version):
        """比较版本号，如果远程版本号大于当前版本号，则返回True"""
        current_parts = [int(x) for x in self.current_version.split(".")]
        remote_parts = [int(x) for x in remote_version.split(".")]

        # 补齐版本号长度
        while len(current_parts) < len(remote_parts):
            current_parts.append(0)
        while len(remote_parts) < len(current_parts):
            remote_parts.append(0)

        # 逐位比较
        for i in range(len(current_parts)):
            if remote_parts[i] > current_parts[i]:
                return True
            elif remote_parts[i] < current_parts[i]:
                return False

        # 版本号完全相同
        return False
        
    def _compare_date(self, remote_date):
        """比较日期，如果远程日期大于当前日期，则返回True"""
        try:
            current_date_str = self.current_date.replace("-", ".")
            current_date = datetime.datetime.strptime(current_date_str, "%Y.%m.%d")
            
            # 直接使用点分隔的日期格式解析
            remote_date = datetime.datetime.strptime(remote_date, "%Y.%m.%d")
            
            # 比较日期
            return remote_date > current_date
        except Exception as e:
            print(f"更新日期比较错误: {e}")
            return False


class UpdateManager(QObject):
    """更新管理器，处理显示更新信息和下载更新"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = UpdateChecker()
        self.checker.updateCheckFinished.connect(self.on_update_check_finished)

    def check_for_updates(self):
        """检查更新"""
        self.checker.check_update()

    def on_update_check_finished(
        self, has_update, version, changelog, download_url, force_update
    ):
        """处理更新检查完成的信号"""
        if has_update:
            # 创建FluentUI消息框
            parent = self.parent()
            
            # 获取远程日期信息
            remote_date_info = ""
            try:
                data = requests.get(self.checker.version_url, timeout=10).json()
                remote_date = data.get("update_date", "")
                if remote_date:
                    remote_date_info = f"（更新日期: {remote_date}）"
            except Exception as e:
                print(f"获取更新日期失败: {e}")
                
            if force_update:
                title = "发现新版本（强制更新）"
                content = f"发现新版本 v{version}{remote_date_info}，需要强制更新。\n\n更新内容:\n{changelog}"
                msg_box = MessageBox(title, content, parent)
                msg_box.yesButton.setText("立即更新")
                msg_box.cancelButton.hide()  # 隐藏取消按钮
            else:
                title = "发现新版本"
                content = f"发现新版本 v{version}{remote_date_info}，是否更新？\n\n更新内容:\n{changelog}"
                msg_box = MessageBox(title, content, parent)
                msg_box.yesButton.setText("立即更新")
                msg_box.cancelButton.setText("稍后再说")
            
            # 显示带遮罩的对话框
            if msg_box.exec():
                # 点击了"立即更新"按钮
                self._open_download_url(download_url)
            elif force_update:
                # 如果是强制更新但用户关闭了对话框，仍然打开下载链接
                self._open_download_url(download_url)
        else:
            # 没有更新或检查失败
            if changelog and changelog.startswith("检查更新失败"):
                # 显示错误信息
                InfoBar.error(
                    title="检查更新失败",
                    content=changelog,
                    orient=Qt.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.TOP,
                    parent=self.parent(),
                    duration=3000
                )
            else:
                # 显示已是最新版本
                InfoBar.success(
                    title="检查更新",
                    content="当前已是最新版本！",
                    orient=Qt.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.TOP,
                    parent=self.parent(),
                    duration=3000
                )
                

    def _open_download_url(self, url):
        """打开下载链接"""
        QDesktopServices.openUrl(QUrl(url))
