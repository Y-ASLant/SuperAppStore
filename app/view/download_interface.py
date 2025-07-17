# coding:utf-8
from qfluentwidgets import ScrollArea, SegmentedWidget, CardWidget, ProgressBar
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget, QHBoxLayout, QSizePolicy
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TransparentToolButton, MessageBox
import os
import requests
import threading
import json

from ..common.style_sheet import StyleSheet
from qfluentwidgets import setFont, setTheme
from ..common.config import cfg
from ..common.setting import APPS_FILE, DOWNLOADED_APPS_FILE, get_download_path
from ..utils.notification import Notification


class DownloadSignals(QObject):
    """下载相关信号"""
    updateProgressSignal = pyqtSignal(str, int)  # 更新进度信号 (app_id, progress)
    moveToCompletedSignal = pyqtSignal(str)  # 移至已完成信号 (app_id)
    moveToFailedSignal = pyqtSignal(str, str)  # 移至失败信号 (app_id, error_msg)


class DownloadTaskCard(CardWidget):
    """下载任务卡片"""
    
    # 添加重新下载信号
    redownloadSignal = pyqtSignal(object)
    # 添加文件删除信号
    deleteFileSignal = pyqtSignal(object)
    
    def __init__(self, app_data, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.vBoxLayout = QVBoxLayout(self)
        self.filename = ""
        self.local_file_path = ""
        self.is_downloaded = False
        
        # 应用名称和版本
        self.headerLayout = QHBoxLayout()
        self.nameLabel = QLabel(app_data['name'])
        setFont(self.nameLabel, 14, QFont.Weight.Medium)
        
        if app_data.get('version'):
            self.versionLabel = QLabel(f"v{app_data['version']}")
            setFont(self.versionLabel, 12)
            self.headerLayout.addWidget(self.nameLabel)
            self.headerLayout.addWidget(self.versionLabel)
        else:
            self.headerLayout.addWidget(self.nameLabel)
            
        self.headerLayout.addStretch(1)
        
        # 进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setFixedHeight(4)
        self.progressBar.setValue(0)
        
        # 状态信息和按钮布局
        self.statusLayout = QHBoxLayout()
        self.statusLabel = QLabel(self.tr("正在准备下载..."))
        setFont(self.statusLabel, 12)
        self.statusLayout.addWidget(self.statusLabel)
        self.statusLayout.addStretch(1)
        
        # 按钮布局（水平排列）
        self.buttonsLayout = QHBoxLayout()
        
        # 创建操作按钮
        self.buttons = {
            'open_file': self._createButton(FIF.DOCUMENT, self.tr("打开文件"), self._handleFile),
            'open_folder': self._createButton(FIF.FOLDER, self.tr("打开文件夹"), self._handleFolder),
            'delete_file': self._createButton(FIF.DELETE, self.tr("删除本地文件"), self._confirmDeleteFile),
            'redownload': self._createButton(FIF.SCROLL, self.tr("重新下载"), self._handleRedownload)
        }
        
        # 将按钮布局添加到状态布局
        self.statusLayout.addLayout(self.buttonsLayout)
        
        # 添加到布局
        self.vBoxLayout.addLayout(self.headerLayout)
        self.vBoxLayout.addWidget(self.progressBar)
        self.vBoxLayout.addLayout(self.statusLayout)
        
        # 设置样式
        self.setFixedHeight(100)
        self.vBoxLayout.setContentsMargins(16, 10, 16, 10)
        
        # 设置大小策略，使卡片水平方向可以拉伸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _createButton(self, icon, tooltip, callback):
        """创建操作按钮"""
        button = TransparentToolButton(icon, self)
        button.setToolTip(tooltip)
        button.setVisible(False)
        button.clicked.connect(callback)
        self.buttonsLayout.addWidget(button)
        return button

    @pyqtSlot(int)
    def updateProgress(self, progress):
        """更新下载进度"""
        self.progressBar.setValue(progress)
        if progress < 100:
            self.statusLabel.setText(f"{self.tr('正在下载')} {progress}%")
        else:
            self.is_downloaded = True
            self.statusLabel.setText(self.tr("下载完成"))
            
            # 设置本地路径（确保路径正确）
            if not self.local_file_path and self.filename:
                self.local_file_path = os.path.join(get_download_path(), self.filename)
                
            # 显示所有操作按钮
            if os.path.exists(self.local_file_path):
                self._setButtonsVisible(True)
    
    def _handleRedownload(self):
        """处理重新下载请求"""
        # 发送重新下载信号
        self.redownloadSignal.emit(self.app_data)
        
        # 重置进度条和状态
        self.progressBar.setValue(0)
        self.statusLabel.setText(self.tr("正在准备下载..."))
        self.is_downloaded = False
        self._setButtonsVisible(False)

    def setFilename(self, filename):
        """设置下载的文件名"""
        self.filename = filename
        self.local_file_path = os.path.join(get_download_path(), filename)
    
    def _setButtonsVisible(self, visible=True):
        """设置所有按钮的可见性"""
        for button in self.buttons.values():
            button.setVisible(visible)
    
    def _handleFile(self):
        """处理打开文件"""
        # 获取最新的文件路径
        current_path = os.path.join(get_download_path(), self.filename)
        if self.is_downloaded and os.path.exists(current_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(current_path))
        elif self.is_downloaded and os.path.exists(self.local_file_path):
            # 尝试使用原始保存的路径
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.local_file_path))
    
    def _handleFolder(self):
        """处理打开文件夹"""
        # 获取最新的下载路径
        current_path = get_download_path()
        if os.path.exists(current_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(current_path))
            
    def _confirmDeleteFile(self):
        """确认删除文件"""
        # 获取最新的文件路径
        current_path = os.path.join(get_download_path(), self.filename)
        file_exists = os.path.exists(current_path) or os.path.exists(self.local_file_path)
        
        # 如果文件不存在但记录存在，直接删除记录
        if not file_exists and self.is_downloaded:
            self._deleteFile()
            return
            
        # 如果没有下载完成，直接返回
        if not self.is_downloaded:
            return
            
        # 弹出确认对话框
        box = MessageBox(
            self.tr('确认删除'),
            self.tr(f'确定要删除 {self.filename} 吗？'),
            self.window()
        )
        
        if box.exec():
            self._deleteFile()
    
    def _deleteFile(self):
        """执行删除文件操作"""
        try:
            # 获取最新的文件路径
            current_path = os.path.join(get_download_path(), self.filename)
            
            # 如果新路径存在文件，删除它
            if os.path.exists(current_path):
                os.remove(current_path)
            # 如果原始路径存在文件，删除它
            elif os.path.exists(self.local_file_path):
                os.remove(self.local_file_path)
                
            # 无论文件是否存在，都更新UI状态并发出信号
            self.local_file_path = ""
            self.statusLabel.setText(self.tr("文件已删除"))
            self.buttons['open_file'].setVisible(False)
            self.buttons['delete_file'].setVisible(False)
            self.is_downloaded = False
            
            # 发出删除文件信号
            self.deleteFileSignal.emit(self.app_data)
                
        except Exception as e:
            # 删除失败
            MessageBox(
                self.tr('删除失败'),
                self.tr(f'无法删除文件: {str(e)}'),
                self.window()
            ).exec()


class DownloadInterface(ScrollArea):
    """下载界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # 创建信号对象
        self.signals = DownloadSignals()
        
        # 连接信号到槽
        self.signals.updateProgressSignal.connect(self._onUpdateProgress)
        self.signals.moveToCompletedSignal.connect(self._moveToCompleted)
        self.signals.moveToFailedSignal.connect(self._moveToFailed)
        
        # 确保下载目录存在
        os.makedirs(get_download_path(), exist_ok=True)
        
        # 存储已下载应用ID
        self.downloaded_app_ids = set()
        # 加载已下载的应用ID
        self._loadDownloadedAppIds()

        # 添加标题
        self.titleLabel = QLabel(self.tr("下载任务"), self)
        setFont(self.titleLabel, 24, QFont.Weight.Medium)

        # 添加分段导航栏
        self.segmentedWidget = SegmentedWidget(self)

        # 创建堆叠小部件用于切换内容
        self.stackedWidget = QStackedWidget(self)

        # 下载中页面
        self.downloadingPage = QWidget(self)
        self.downloadingPageLayout = QVBoxLayout(self.downloadingPage)
        self.downloadingInfoLabel = QLabel(
            self.tr("暂无正在下载的应用"), self.downloadingPage
        )
        self.downloadingInfoLabel.setObjectName("contentLabel")  # 确保设置对象名
        self.downloadingPageLayout.addWidget(self.downloadingInfoLabel)
        self.downloadingPage.setObjectName("downloadingPage")
        
        # 存储下载任务
        self.downloadingTasks = {}
        self.completedTasks = {}
        self.failedTasks = {}

        # 已完成页面
        self.completedPage = QWidget(self)
        self.completedPageLayout = QVBoxLayout(self.completedPage)
        self.completedInfoLabel = QLabel(
            self.tr("暂无下载已完成的应用"), self.completedPage
        )
        self.completedInfoLabel.setObjectName("contentLabel")  # 确保设置对象名
        self.completedPageLayout.addWidget(self.completedInfoLabel)
        self.completedPage.setObjectName("completedPage")

        # 失败页面
        self.failedPage = QWidget(self)
        self.failedPageLayout = QVBoxLayout(self.failedPage)
        self.failedInfoLabel = QLabel(self.tr("暂无下载失败的应用"), self.failedPage)
        self.failedInfoLabel.setObjectName("contentLabel")  # 确保设置对象名
        self.failedPageLayout.addWidget(self.failedInfoLabel)
        self.failedPage.setObjectName("failedPage")

        # 添加子界面（带图标）
        self.addSubInterface(
            self.downloadingPage, "downloadingPage", self.tr("正在下载"), FIF.DOWNLOAD
        )
        self.addSubInterface(
            self.completedPage, "completedPage", self.tr("下载完成"), FIF.COMPLETED
        )
        self.addSubInterface(
            self.failedPage, "failedPage", self.tr("下载失败"), FIF.INFO
        )

        self._initWidget()
        self._connectSignalToSlot()
        
        # 加载已完成的下载
        self._loadCompletedDownloads()

    def addSubInterface(self, widget, objectName, text, icon=None):
        """添加子界面"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.segmentedWidget.addItem(routeKey=objectName, text=text, icon=icon)

    def _initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("downloadInterface")

        # 初始化样式表
        setFont(self.titleLabel, 24, QFont.Weight.Medium)
        setFont(self.downloadingInfoLabel, 16, QFont.Weight.Normal)
        setFont(self.completedInfoLabel, 16, QFont.Weight.Normal)
        setFont(self.failedInfoLabel, 16, QFont.Weight.Normal)
        
        self.scrollWidget.setObjectName("scrollWidget")
        self.titleLabel.setObjectName("settingLabel")  # 使用与settingLabel相同的对象名
        
        self.segmentedWidget.setFixedWidth(200)
        
        # 应用样式表 - 确保在设置所有对象名之后再应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)
        
        # 设置默认显示的页面
        self.stackedWidget.setCurrentWidget(self.downloadingPage)
        self.segmentedWidget.setCurrentItem("downloadingPage")

        # 初始化布局
        self._initLayout()

    def _connectSignalToSlot(self):
        self.segmentedWidget.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )
        
        # 连接主题变更信号
        cfg.themeChanged.connect(self._onThemeChanged)
        
    def _initLayout(self):
        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.addSpacing(36)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.segmentedWidget, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget, 1, Qt.AlignHCenter)
        self.vBoxLayout.addStretch(1)

        # 设置下载页面布局，确保卡片能占满宽度
        self.downloadingPageLayout.setContentsMargins(0, 20, 0, 20)
        self.downloadingPageLayout.addStretch(1)
        self.downloadingPageLayout.addWidget(
            self.downloadingInfoLabel, 0, Qt.AlignHCenter
        )
        self.downloadingPageLayout.addStretch(1)

        # 设置已完成页面布局
        self.completedPageLayout.setContentsMargins(0, 20, 0, 20)
        self.completedPageLayout.addStretch(1)
        self.completedPageLayout.addWidget(self.completedInfoLabel, 0, Qt.AlignHCenter)
        self.completedPageLayout.addStretch(1)

        # 设置失败页面布局
        self.failedPageLayout.setContentsMargins(0, 20, 0, 20)
        self.failedPageLayout.addStretch(1)
        self.failedPageLayout.addWidget(self.failedInfoLabel, 0, Qt.AlignHCenter)
        self.failedPageLayout.addStretch(1)
        
    def _onThemeChanged(self, theme):
        """处理主题变更"""
        # 应用主题
        setTheme(theme)
        # 重新应用样式表，确保样式更新
        StyleSheet.SETTING_INTERFACE.apply(self)
        
    def addDownloadTask(self, app_data):
        """添加下载任务"""
        # 如果已存在，则不重复添加
        app_id = app_data.get('id', app_data['name'])
        if app_id in self.downloadingTasks:
            # 显示提示
            self._showNotification('提示', f"{app_data['name']} {self.tr('已在下载队列中')}", 'warning')
            return False
            
        # 直接隐藏"暂无下载"提示
        self.downloadingInfoLabel.hide()
            
        # 创建下载任务卡片
        task_card = DownloadTaskCard(app_data)
        # 连接重新下载信号
        task_card.redownloadSignal.connect(self._handleRedownload)
        # 连接文件删除信号
        task_card.deleteFileSignal.connect(self._handleDeleteFile)
        self.downloadingTasks[app_id] = task_card
        
        # 添加到下载中界面，并确保占满宽度
        self.downloadingPageLayout.insertWidget(0, task_card, 0, Qt.AlignTop | Qt.AlignHCenter)
        task_card.setMinimumWidth(self.width() - 80)
        
        # 开始实际下载
        self._startDownloadThread(app_data, app_id, task_card)
        
        # 切换到下载界面
        self.stackedWidget.setCurrentWidget(self.downloadingPage)
        self.segmentedWidget.setCurrentItem("downloadingPage")
        
        # 更新界面
        self.downloadingPage.update()
        self.update()
        
        return True
        
    def _startDownloadThread(self, app_data, app_id, task_card):
        """启动下载线程的通用方法"""
        # 获取文件名，格式为name_version
        version = app_data.get('version', '')
        name = app_data['name']
        format = app_data.get('format', 'exe')  # 从JSON中获取格式，默认为exe
        
        # 构建文件名为name_version.format格式
        if version:
            filename = f"{name}_{version}.{format}"
        else:
            filename = f"{name}.{format}"
        
        # 设置文件名
        task_card.setFilename(filename)
        
        # 启动下载线程
        if app_data.get('download_url'):
            download_thread = threading.Thread(
                target=self._downloadFile,
                args=(app_data['download_url'], filename, app_id)
            )
            download_thread.daemon = True
            download_thread.start()
            return True
        else:
            # 如果没有下载URL，显示错误
            self._moveToFailed(app_id, "没有可用的下载链接")
            return False
            
    def _downloadFile(self, url, filename, app_id):
        """下载文件"""
        # 获取最新的下载路径
        download_path = get_download_path()
        local_path = os.path.join(download_path, filename)
        task_card = self.downloadingTasks.get(app_id)
        
        if not task_card:
            return
            
        try:
            # 如果是重新下载，需要删除原有文件
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass  # 如果无法删除，会覆盖写入
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 使用requests流式下载文件
            with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                # 确保请求成功
                response.raise_for_status()
                
                # 获取文件大小
                file_size = int(response.headers.get('Content-Length', 0))
                
                # 确保目录存在
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # 保存文件名
                task_card.setFilename(filename)
                
                # 已下载的数据大小
                downloaded = 0
                # 增大块大小到 1MB，提高下载效率
                chunk_size = 1024 * 1024
                
                # 打开文件准备写入
                with open(local_path, 'wb') as f:
                    # 读取和写入数据块
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # 过滤keep-alive新块
                            # 写入文件
                            f.write(chunk)
                            
                            # 更新下载进度
                            downloaded += len(chunk)
                            progress = int(downloaded / file_size * 100) if file_size > 0 else 100
                            
                            # 使用信号槽更新UI
                            self.signals.updateProgressSignal.emit(app_id, progress)
            
            # 下载完成后，发送完成信号
            self.signals.moveToCompletedSignal.emit(app_id)
            
        except requests.RequestException as e:
            print(f"下载请求出错: {str(e)}")
            # 发送失败信号
            self.signals.moveToFailedSignal.emit(app_id, str(e))
        except Exception as e:
            print(f"下载过程出错: {str(e)}")
            # 发送失败信号
            self.signals.moveToFailedSignal.emit(app_id, str(e))

    @pyqtSlot(str, int)
    def _onUpdateProgress(self, app_id, progress):
        """处理进度更新信号"""
        task_card = self.downloadingTasks.get(app_id)
        if task_card:
            task_card.updateProgress(progress)
            
    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        
        # 调整所有下载任务卡片的宽度
        width = self.width() - 80  # 考虑左右边距
        
        # 调整下载中的任务卡片宽度
        for task_card in self.downloadingTasks.values():
            task_card.setMinimumWidth(width)
            
        # 调整已完成的任务卡片宽度
        for task_card in self.completedTasks.values():
            task_card.setMinimumWidth(width)
            
        # 调整失败的任务卡片宽度
        for task_card in self.failedTasks.values():
            task_card.setMinimumWidth(width)
            
    def _loadDownloadedAppIds(self):
        """加载已下载的应用ID记录"""
        try:
            if os.path.exists(DOWNLOADED_APPS_FILE):
                with open(DOWNLOADED_APPS_FILE, 'r', encoding='utf-8') as f:
                    downloaded_ids = json.load(f)
                    self.downloaded_app_ids = set(downloaded_ids)
        except Exception as e:
            print(f"加载下载记录出错: {e}")
            # 如果加载失败，使用空集合
            self.downloaded_app_ids = set()
    
    def _saveDownloadedAppIds(self):
        """保存已下载的应用ID记录"""
        try:
            # 确保AppData目录存在
            os.makedirs(os.path.dirname(DOWNLOADED_APPS_FILE), exist_ok=True)
            with open(DOWNLOADED_APPS_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.downloaded_app_ids), f, ensure_ascii=False)
        except Exception as e:
            print(f"保存下载记录出错: {e}")
    
    def _loadCompletedDownloads(self):
        """加载已完成的下载记录"""
        try:
            # 加载已下载应用列表
            if not os.path.exists(APPS_FILE):
                return
                
            with open(APPS_FILE, 'r', encoding='utf-8') as f:
                all_apps = json.load(f)
                
            # 用于存储真正已下载完成的应用ID
            verified_download_ids = set()
                
            # 检查每个已下载的应用ID
            for app_id in self.downloaded_app_ids:
                for app in all_apps:
                    app_identifier = app.get('id', app['name'])
                    if app_identifier == app_id:
                        # 构建文件名为name_version.format格式
                        name = app['name']
                        version = app.get('version', '')
                        format = app.get('format', 'exe')  # 从JSON中获取格式，默认为exe
                        
                        if version:
                            filename = f"{name}_{version}.{format}"
                        else:
                            filename = f"{name}.{format}"
                            
                        # 获取当前下载路径
                        download_path = get_download_path()
                        local_path = os.path.join(download_path, filename)
                        
                        # 如果文件存在，添加到已完成列表
                        if os.path.exists(local_path):
                            verified_download_ids.add(app_id)
                            
                            task_card = DownloadTaskCard(app)
                            task_card.setFilename(filename)
                            task_card.is_downloaded = True
                            task_card.statusLabel.setText(self.tr("下载完成"))
                            task_card.updateProgress(100)  # 设置进度条为100%
                            # 确保按钮可见
                            task_card._setButtonsVisible(True)
                            
                            # 连接重新下载信号
                            task_card.redownloadSignal.connect(self._handleRedownload)
                            # 连接文件删除信号
                            task_card.deleteFileSignal.connect(self._handleDeleteFile)
                            
                            # 添加到已完成列表
                            self.completedTasks[app_id] = task_card
                            
                            # 隐藏"暂无完成"提示
                            self.completedInfoLabel.hide()
                            
                            # 添加到已完成界面
                            self.completedPageLayout.insertWidget(0, task_card, 0, Qt.AlignTop | Qt.AlignHCenter)
                            task_card.setMinimumWidth(self.width() - 80)  # 设置最小宽度，考虑左右边距
                        
                        break
            
            # 更新下载记录，只保留真正已下载的应用ID
            self.downloaded_app_ids = verified_download_ids
            # 保存更新后的下载记录
            self._saveDownloadedAppIds()
            
        except Exception as e:
            print(f"加载已完成下载记录出错: {e}")

    def _moveTaskBetweenLists(self, app_id, source_dict, source_layout, target_dict, target_layout, empty_label, status_text=None):
        """在不同任务列表间移动任务卡片的通用方法"""
        if app_id in source_dict:
            # 从源列表移除
            task_card = source_dict.pop(app_id)
            source_layout.removeWidget(task_card)
            
            # 更新状态文本（如果提供）
            if status_text:
                task_card.statusLabel.setText(status_text)
                
            # 添加到目标列表
            target_dict[app_id] = task_card
            
            # 隐藏"暂无数据"提示
            empty_label.hide()
                
            # 添加到目标界面，并确保占满宽度
            target_layout.insertWidget(0, task_card, 0, Qt.AlignTop | Qt.AlignHCenter)
            task_card.setMinimumWidth(self.width() - 80)  # 设置最小宽度，考虑左右边距
            
            # 如果源列表为空，显示其"暂无数据"提示
            source_empty_label = None
            if source_dict == self.downloadingTasks:
                source_empty_label = self.downloadingInfoLabel
            elif source_dict == self.completedTasks:
                source_empty_label = self.completedInfoLabel
            elif source_dict == self.failedTasks:
                source_empty_label = self.failedInfoLabel
                
            if source_empty_label and not source_dict:
                source_empty_label.show()
                
            return task_card
        return None
        
    def _showNotification(self, title, content, type_='info', duration=2000):
        """显示通知的统一方法"""
        Notification.show(
            title=self.tr(title),
            content=content,
            type_=type_,
            duration=duration,
            parent=self.window()
        )
            
    @pyqtSlot(str)
    def _moveToCompleted(self, app_id):
        """将任务移至完成界面"""
        task_card = self._moveTaskBetweenLists(
            app_id, 
            self.downloadingTasks, 
            self.downloadingPageLayout,
            self.completedTasks, 
            self.completedPageLayout,
            self.completedInfoLabel
        )
        
        if task_card:
            # 添加到已下载应用ID列表并保存
            self.downloaded_app_ids.add(app_id)
            self._saveDownloadedAppIds()
            
            # 确保按钮可见
            task_card._setButtonsVisible(True)
                
            # 显示通知
            app_name = task_card.app_data['name']
            self._showNotification('下载完成', f"{app_name} {self.tr('已成功下载')}", 'success')
            
            # 更新界面
            self.completedPage.update()
            self.update()
    
    @pyqtSlot(str, str)
    def _moveToFailed(self, app_id, error_msg):
        """将任务移至失败界面"""
        task_card = self._moveTaskBetweenLists(
            app_id, 
            self.downloadingTasks, 
            self.downloadingPageLayout,
            self.failedTasks, 
            self.failedPageLayout,
            self.failedInfoLabel,
            f"{self.tr('下载失败')}: {error_msg}"
        )
        
        if task_card:
            # 显示通知
            app_name = task_card.app_data['name']
            self._showNotification(
                '下载失败', 
                f"{app_name} {self.tr('下载失败')}: {error_msg}", 
                'error',
                3000
            )
            
            # 更新界面
            self.failedPage.update()
            self.update()

    @pyqtSlot(object)
    def _handleRedownload(self, app_data):
        """处理重新下载请求"""
        # 获取应用ID
        app_id = app_data.get('id', app_data['name'])
        task_card = None
        
        # 根据来源列表移回下载中列表
        if app_id in self.completedTasks:
            task_card = self._moveTaskBetweenLists(
                app_id, 
                self.completedTasks, 
                self.completedPageLayout,
                self.downloadingTasks, 
                self.downloadingPageLayout,
                self.downloadingInfoLabel
            )
        elif app_id in self.failedTasks:
            task_card = self._moveTaskBetweenLists(
                app_id, 
                self.failedTasks, 
                self.failedPageLayout,
                self.downloadingTasks, 
                self.downloadingPageLayout,
                self.downloadingInfoLabel
            )
            
        if task_card:
            # 切换到下载界面
            self.stackedWidget.setCurrentWidget(self.downloadingPage)
            self.segmentedWidget.setCurrentItem("downloadingPage")
            
            # 从已下载应用ID列表中移除
            if app_id in self.downloaded_app_ids:
                self.downloaded_app_ids.remove(app_id)
                # 保存到文件
                self._saveDownloadedAppIds()
            
            # 开始重新下载
            if self._startDownloadThread(app_data, app_id, task_card):
                # 显示通知
                self._showNotification('重新下载', f"{app_data['name']} {self.tr('开始重新下载')}")
                
            # 更新界面
            self.update()

    @pyqtSlot(object)
    def _handleDeleteFile(self, app_data):
        """处理文件删除事件"""
        # 获取应用ID
        app_id = app_data.get('id', app_data['name'])
        
        # 从已下载应用ID列表中移除
        if app_id in self.downloaded_app_ids:
            self.downloaded_app_ids.remove(app_id)
            # 保存到JSON文件
            self._saveDownloadedAppIds()
        
        # 从已完成列表中移除卡片
        if app_id in self.completedTasks:
            task_card = self.completedTasks.pop(app_id)
            self.completedPageLayout.removeWidget(task_card)
            task_card.deleteLater()  # 释放卡片资源
            
            # 如果完成列表为空，显示"暂无完成"提示
            if not self.completedTasks:
                self.completedInfoLabel.show()
        
        # 发送信号通知主窗口同步记录
        self.signals.moveToCompletedSignal.emit(app_id)
