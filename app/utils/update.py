# coding: utf-8
import requests
import os
from pathlib import Path
import datetime
import subprocess
import sys
from PyQt5.QtCore import QObject, QPoint, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget
from qfluentwidgets import (MessageBox, InfoBar, InfoBarManager, ProgressBar)
from ..common.setting import VERSION, UPDATE_DATE, VERSION_URL
from .notification import Notification


class CustomMessageBox(MessageBox):
    """自定义消息框，屏蔽ESC键关闭功能"""
    
    def keyPressEvent(self, event: QKeyEvent):
        """重写keyPressEvent方法，屏蔽ESC键"""
        # 如果是ESC键，则忽略该事件
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            # 其他键正常处理
            super().keyPressEvent(event)


class DownloadThread(QThread):
    """下载线程类，用于在后台下载文件并更新进度"""
    progress_signal = pyqtSignal(int)  # 进度信号
    finished_signal = pyqtSignal(bool, str)  # 完成信号，成功/失败标志和消息

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_cancelled = False

    def run(self):
        try:
            # 创建保存目录
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # 开始下载
            response = requests.get(self.url, stream=True)
            response.raise_for_status()  # 如果请求失败，抛出异常
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                self.finished_signal.emit(False, "无法获取文件大小")
                return
                
            # 写入文件
            downloaded_size = 0
            with open(self.save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if self.is_cancelled:
                        file.close()
                        os.remove(self.save_path)
                        self.finished_signal.emit(False, "下载已取消")
                        return
                        
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        # 更新进度
                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_signal.emit(progress)
            
            self.finished_signal.emit(True, "下载完成")
        except requests.exceptions.SSLError as e:
            error_msg = "网络安全连接错误，请检查网络设置或稍后重试"
            print(f"SSL错误: {str(e)}")
            self.finished_signal.emit(False, error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = "无法连接到服务器，请检查网络连接"
            print(f"连接错误: {str(e)}")
            self.finished_signal.emit(False, error_msg)
        except requests.exceptions.Timeout as e:
            error_msg = "连接超时，请检查网络状态后重试"
            print(f"超时错误: {str(e)}")
            self.finished_signal.emit(False, error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = "网络错误，请检查网络设置后重试"
            print(f"请求错误: {str(e)}")
            self.finished_signal.emit(False, error_msg)
        except Exception as e:
            error_msg = "下载失败，请稍后重试"
            print(f"下载错误: {str(e)}")
            self.finished_signal.emit(False, error_msg)
    
    def cancel(self):
        """取消下载"""
        self.is_cancelled = True


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


class CheckUpdateThread(QThread):
    """检查更新线程"""
    # 定义更新检查完成的信号
    updateCheckFinished = pyqtSignal(
        bool, str, str, str, bool
    )  # 是否有更新，版本号，更新日志，下载链接，是否强制更新

    def __init__(self, version_url, current_version, current_date):
        super().__init__()
        self.version_url = version_url
        self.current_version = current_version
        self.current_date = current_date
        
    def run(self):
        """线程执行函数，检查更新"""
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

        except requests.exceptions.RequestException as e:
            # 网络错误处理
            error_msg = "网络连接错误，请检查网络设置后重试"
            print(f"检查更新失败: {e}")
            # 发送信号表示检查失败
            self.updateCheckFinished.emit(False, "", error_msg, "", False)
        except Exception as e:
            # 其他错误处理
            error_msg = "检查更新失败，请稍后重试"
            print(f"检查更新失败: {e}")
            # 发送信号表示检查失败
            self.updateCheckFinished.emit(False, "", error_msg, "", False)
    
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

class UpdateChecker(QObject):
    """检查应用更新的类"""

    # 定义更新检查完成的信号
    updateCheckFinished = pyqtSignal(
        bool, str, str, str, bool
    )  # 是否有更新，版本号，更新日志，下载链接，是否强制更新

    def __init__(self):
        super().__init__()
        self.version_url = VERSION_URL
        self.current_version = VERSION
        self.current_date = UPDATE_DATE  # 获取当前版本更新日期
        self.check_thread = None

    def check_update(self):
        """检查更新"""
        # 创建并启动检查更新线程
        self.check_thread = CheckUpdateThread(
            self.version_url, self.current_version, self.current_date
        )
        # 连接信号
        self.check_thread.updateCheckFinished.connect(self._on_thread_finished)
        # 启动线程
        self.check_thread.start()
    
    def _on_thread_finished(self, has_update, remote_version, changelog_str, download_url, force_update):
        """处理线程完成信号"""
        # 转发信号
        self.updateCheckFinished.emit(has_update, remote_version, changelog_str, download_url, force_update)

class UpdateManager(QObject):
    """更新管理器，处理显示更新信息和下载更新"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = UpdateChecker()
        self.checker.updateCheckFinished.connect(self.on_update_check_finished)
        self.update_dialog = None
        self.download_url = ""
        self.progress_bar = None
        self.is_downloading = False
        self.download_thread = None
        self.force_update = False

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
            if version:
                remote_date_info = f"（版本: {version}）"
                
            # 保存是否强制更新的状态
            self.force_update = force_update
                
            if force_update:
                title = "发现新版本（强制更新）"
                content = f"发现新版本 v{version}{remote_date_info}，需要强制更新。\n\n更新内容:\n{changelog}"
                self.update_dialog = CustomMessageBox(title, content, parent)
                self.update_dialog.yesButton.setText("立即更新")
                self.update_dialog.cancelButton.hide()  # 隐藏取消按钮
            else:
                title = "发现新版本"
                content = f"发现新版本 v{version}{remote_date_info}，是否更新？\n\n更新内容:\n{changelog}"
                self.update_dialog = CustomMessageBox(title, content, parent)
                self.update_dialog.yesButton.setText("立即更新")
                self.update_dialog.cancelButton.setText("稍后再说")
            
            # 保存下载URL
            self.download_url = download_url
            
            # 准备进度条容器
            self._prepare_progress_container()
            
            # 连接确认按钮点击事件
            self.update_dialog.yesButton.clicked.disconnect()  # 断开原有连接
            self.update_dialog.yesButton.clicked.connect(self._start_download)
            
            # 显示对话框
            self.update_dialog.exec()
        else:
            # 没有更新或检查失败
            if changelog and (changelog.startswith("网络") or changelog.startswith("检查更新失败")):
                # 只在检查失败时显示错误信息
                Notification.error(
                    title="检查更新失败",
                    content=changelog,
                    duration=3000,
                    parent=self.parent()
                )
            else:
                # 显示已是最新版本
                Notification.success(
                    title="检查更新",
                    content="当前已是最新版本！",
                    duration=3000,
                    parent=self.parent()
                )
    
    def _prepare_progress_container(self):
        """准备进度条容器"""
        from PyQt5.QtWidgets import QVBoxLayout, QWidget
        
        # 创建进度条容器
        self.progress_container = QWidget(self.update_dialog)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(20, 0, 20, 10)
        self.progress_layout.setSpacing(0)
        
        # 尝试直接使用按钮组作为参考位置
        button_group = None
        for child in self.update_dialog.findChildren(QWidget):
            if hasattr(child, 'objectName') and child.objectName() == "buttonGroup":
                button_group = child
                break
        
        # 在按钮上方插入进度条容器
        if button_group and button_group.parent() and button_group.parent().layout():
            parent_layout = button_group.parent().layout()
            # 找到按钮组在布局中的位置
            for i in range(parent_layout.count()):
                if parent_layout.itemAt(i).widget() == button_group:
                    # 在按钮组之前插入进度条容器
                    parent_layout.insertWidget(i, self.progress_container)
                    break
        else:
            # 如果找不到按钮组，作为最后手段添加到对话框布局中
            main_layout = self.update_dialog.layout()
            if main_layout:
                main_layout.addWidget(self.progress_container)
        
        # 默认隐藏进度容器
        self.progress_container.hide()

    def _start_download(self):
        """开始下载，在原对话框中显示进度条"""
        if not self.update_dialog or not self.download_url or self.is_downloading:
            return
        
        # 标记为正在下载状态
        self.is_downloading = True
        
        # 修改对话框标题
        self.update_dialog.titleLabel.setText("下载更新")
        
        # 修改对话框按钮
        self.update_dialog.yesButton.hide()  # 隐藏确认按钮
        
        # 如果是强制更新，完全隐藏按钮区域
        if self.force_update:
            # 查找并完全隐藏按钮组区域
            for child in self.update_dialog.findChildren(QWidget):
                if hasattr(child, 'objectName') and child.objectName() == "buttonGroup":
                    child.setFixedHeight(0)
                    child.setStyleSheet("background-color: transparent; border: none; margin: 0; padding: 0;")
                    break
        # 只有在非强制更新时才显示取消按钮
        else:
            self.update_dialog.cancelButton.show()  # 显示取消按钮
            self.update_dialog.cancelButton.setText("取消")
            self.update_dialog.cancelButton.clicked.disconnect()  # 断开原有连接
            self.update_dialog.cancelButton.clicked.connect(self._cancel_download)
        
        # 添加进度条到容器
        self.progress_bar = ProgressBar(self.progress_container)
        self.progress_bar.setValue(0)
        # 设置进度条样式和大小
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setFixedHeight(8)
        self.progress_layout.addWidget(self.progress_bar)
        
        # 显示进度容器
        self.progress_container.show()
        
        # 开始下载
        self._open_download_url(self.download_url)
        
    def _cancel_download(self):
        """取消下载"""
        if self.download_thread:
            self.download_thread.cancel()
        self.update_dialog.reject()

    def _open_download_url(self, url):
        """下载更新文件并显示进度条"""
        try:
            # 获取文件名
            file_name = os.path.basename(url) or "update.zip"
            
            # 创建保存路径
            update_dir = Path("update").absolute()
            save_path = os.path.join(update_dir, file_name)
            
            # 创建下载线程
            self.download_thread = DownloadThread(url, save_path)
            
            # 连接信号
            def update_progress(value):
                if self.progress_bar:
                    self.progress_bar.setValue(value)
            
            self.download_thread.progress_signal.connect(update_progress)
            
            # 下载完成处理
            def on_download_finished(success, message):
                # 确保只处理一次
                self.download_thread.finished_signal.disconnect(on_download_finished)
                
                if success:
                    # 关闭对话框
                    self.update_dialog.accept()
                    
                    # 直接启动安装程序
                    try:
                        subprocess.Popen([save_path], shell=True)
                        
                        # 关闭原始程序
                        print("更新程序已启动，正在关闭当前应用...")
                        QApplication.quit()
                        sys.exit(0)
                    except Exception as e:
                        # 显示错误提示
                        error_msg = "启动安装程序失败，请手动运行安装文件"
                        print(f"启动安装程序失败: {str(e)}")
                        Notification.error(
                            title="更新失败",
                            content=error_msg,
                            duration=3000,
                            parent=self.parent()
                        )
                        self.update_dialog.reject()
                else:
                    # 下载失败，显示提示
                    print(f"下载失败: {message}")
                    Notification.error(
                        title="下载失败",
                        content=message,
                        duration=3000,
                        parent=self.parent()
                    )
                    self.update_dialog.reject()
                
                # 重置下载状态
                self.is_downloading = False
            
            self.download_thread.finished_signal.connect(on_download_finished)
            
            # 启动下载线程
            self.download_thread.start()
            
        except Exception as e:
            # 显示错误提示
            error_msg = "启动下载失败，请稍后重试"
            print(f"启动下载时发生错误: {str(e)}")
            Notification.error(
                title="下载失败",
                content=error_msg,
                duration=3000,
                parent=self.parent()
            )
            if self.update_dialog:
                self.update_dialog.reject()
            self.is_downloading = False
