# coding:utf-8
from qfluentwidgets import ScrollArea, SegmentedWidget, CardWidget, ProgressBar, InfoBar, InfoBarPosition
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget, QHBoxLayout, QSizePolicy
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TransparentToolButton, MessageBox
import os
import urllib.request
import threading
import time
import json

from ..common.style_sheet import StyleSheet
from qfluentwidgets import setFont, setTheme
from ..common.config import cfg
from ..common.setting import APPS_FILE, DOWNLOADED_APPS_FILE


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
        self.download_path = cfg.downloadPath.value
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
            'open_file': self.__createButton(FIF.DOCUMENT, self.tr("打开文件"), self.__handleFile),
            'open_folder': self.__createButton(FIF.FOLDER, self.tr("打开文件夹"), self.__handleFolder),
            'delete_file': self.__createButton(FIF.DELETE, self.tr("删除本地文件"), self.__confirmDeleteFile),
            'redownload': self.__createButton(FIF.SCROLL, self.tr("重新下载"), self.__handleRedownload)
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

    def __createButton(self, icon, tooltip, callback):
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
            
            # 显示所有操作按钮
            if os.path.exists(self.local_file_path):
                self.__setButtonsVisible(True)
    
    def __handleRedownload(self):
        """处理重新下载请求"""
        # 发送重新下载信号
        self.redownloadSignal.emit(self.app_data)
        
        # 重置进度条和状态
        self.progressBar.setValue(0)
        self.statusLabel.setText(self.tr("正在准备下载..."))
        self.is_downloaded = False
        self.__setButtonsVisible(False)

    def setFilename(self, filename):
        """设置下载的文件名"""
        self.filename = filename
        self.local_file_path = os.path.join(self.download_path, filename)
    
    def __setButtonsVisible(self, visible=True):
        """设置所有按钮的可见性"""
        for button in self.buttons.values():
            button.setVisible(visible)
    
    def __handleFile(self):
        """处理打开文件"""
        if self.is_downloaded and os.path.exists(self.local_file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.local_file_path))
    
    def __handleFolder(self):
        """处理打开文件夹"""
        if os.path.exists(self.download_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.download_path))
            
    def __confirmDeleteFile(self):
        """确认删除文件"""
        if not self.is_downloaded or not os.path.exists(self.local_file_path):
            return
            
        # 弹出确认对话框
        box = MessageBox(
            self.tr('确认删除'),
            self.tr(f'确定要删除 {self.filename} 吗？'),
            self.window()
        )
        
        if box.exec():
            self.__deleteFile()
    
    def __deleteFile(self):
        """执行删除文件操作"""
        try:
            os.remove(self.local_file_path)
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
        self.signals.updateProgressSignal.connect(self.__onUpdateProgress)
        self.signals.moveToCompletedSignal.connect(self.__moveToCompleted)
        self.signals.moveToFailedSignal.connect(self.__moveToFailed)
        
        # 下载路径
        self.download_path = cfg.downloadPath.value
        # 确保下载目录存在
        os.makedirs(self.download_path, exist_ok=True)
        
        # 存储已下载应用ID
        self.downloaded_app_ids = set()
        # 加载已下载的应用ID
        self.__loadDownloadedAppIds()

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

        self.__initWidget()
        self.__connectSignalToSlot()
        
        # 加载已完成的下载
        self.__loadCompletedDownloads()

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
        self.__initLayout()

    def __initLayout(self):
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

    def __connectSignalToSlot(self):
        self.segmentedWidget.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )
        
        # 连接主题变更信号
        cfg.themeChanged.connect(self.__onThemeChanged)
        
    def __onThemeChanged(self, theme):
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
            self.__showNotification('提示', f"{app_data['name']} {self.tr('已在下载队列中')}", 'warning')
            return False
            
        # 直接隐藏"暂无下载"提示
        self.downloadingInfoLabel.hide()
            
        # 创建下载任务卡片
        task_card = DownloadTaskCard(app_data)
        # 连接重新下载信号
        task_card.redownloadSignal.connect(self.__handleRedownload)
        # 连接文件删除信号
        task_card.deleteFileSignal.connect(self.__handleDeleteFile)
        self.downloadingTasks[app_id] = task_card
        
        # 添加到下载中界面，并确保占满宽度
        self.downloadingPageLayout.insertWidget(0, task_card, 0, Qt.AlignTop | Qt.AlignHCenter)
        task_card.setMinimumWidth(self.width() - 80)
        
        # 开始实际下载
        self.__startDownloadThread(app_data, app_id, task_card)
        
        # 切换到下载界面
        self.stackedWidget.setCurrentWidget(self.downloadingPage)
        self.segmentedWidget.setCurrentItem("downloadingPage")
        
        # 更新界面
        self.downloadingPage.update()
        self.update()
        
        return True
        
    def __downloadFile(self, url, filename, app_id):
        """下载文件"""
        local_path = os.path.join(self.download_path, filename)
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
            
            # 创建请求对象
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            # 打开URL
            response = urllib.request.urlopen(req)
            file_size = int(response.info().get('Content-Length', 0))
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 已下载的数据块数量
            downloaded = 0
            block_size = 1024 * 8
            
            # 保存文件名
            task_card.setFilename(filename)
            
            # 打开文件准备写入
            with open(local_path, 'wb') as f:
                # 读取和写入数据块
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    
                    # 写入文件
                    f.write(buffer)
                    
                    # 更新下载进度
                    downloaded += len(buffer)
                    progress = int(downloaded / file_size * 100) if file_size > 0 else 100
                    
                    # 使用信号槽更新UI，而不是直接调用方法
                    self.signals.updateProgressSignal.emit(app_id, progress)
                    
                    # 为了不过于频繁更新UI，添加一个小的休眠
                    time.sleep(0.01)
            
            # 下载完成后，发送完成信号
            self.signals.moveToCompletedSignal.emit(app_id)
            
        except Exception as e:
            print(f"下载出错: {str(e)}")
            # 发送失败信号
            self.signals.moveToFailedSignal.emit(app_id, str(e))

    @pyqtSlot(str, int)
    def __onUpdateProgress(self, app_id, progress):
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
            
    def __loadDownloadedAppIds(self):
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
    
    def __saveDownloadedAppIds(self):
        """保存已下载的应用ID记录"""
        try:
            # 确保AppData目录存在
            os.makedirs(os.path.dirname(DOWNLOADED_APPS_FILE), exist_ok=True)
            with open(DOWNLOADED_APPS_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.downloaded_app_ids), f, ensure_ascii=False)
        except Exception as e:
            print(f"保存下载记录出错: {e}")
    
    def __loadCompletedDownloads(self):
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
                        # 检查本地是否有对应的下载文件
                        filename = ""
                        if app.get('download_url'):
                            filename = os.path.basename(app['download_url'].split('?')[0])
                            if not filename:
                                filename = f"{app['name']}.exe"
                        else:
                            filename = f"{app['name']}.exe"
                            
                        local_path = os.path.join(self.download_path, filename)
                        
                        # 如果文件存在，添加到已完成列表
                        if os.path.exists(local_path):
                            verified_download_ids.add(app_id)
                            
                            task_card = DownloadTaskCard(app)
                            task_card.setFilename(filename)
                            task_card.is_downloaded = True
                            task_card.statusLabel.setText(self.tr("下载完成"))
                            task_card.updateProgress(100)  # 设置进度条为100%
                            
                            # 连接重新下载信号
                            task_card.redownloadSignal.connect(self.__handleRedownload)
                            # 连接文件删除信号
                            task_card.deleteFileSignal.connect(self.__handleDeleteFile)
                            
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
            self.__saveDownloadedAppIds()
            
        except Exception as e:
            print(f"加载已完成下载记录出错: {e}")

    def __moveTaskBetweenLists(self, app_id, source_dict, source_layout, target_dict, target_layout, empty_label, status_text=None):
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
        
    def __showNotification(self, title, content, type_='info', duration=2000):
        """显示通知的统一方法"""
        notification_func = InfoBar.info  # 默认为普通提示
        if type_ == 'success':
            notification_func = InfoBar.success
        elif type_ == 'error':
            notification_func = InfoBar.error
        elif type_ == 'warning':
            notification_func = InfoBar.warning
            
        notification_func(
            title=self.tr(title),
            content=content,
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
        
    def __startDownloadThread(self, app_data, app_id, task_card):
        """启动下载线程的通用方法"""
        # 获取文件名
        filename = ""
        if app_data.get('download_url'):
            filename = os.path.basename(app_data['download_url'].split('?')[0])
            if not filename:
                filename = f"{app_data['name']}.exe"
        else:
            filename = f"{app_data['name']}.exe"
        
        # 设置文件名
        task_card.setFilename(filename)
        
        # 启动下载线程
        if app_data.get('download_url'):
            download_thread = threading.Thread(
                target=self.__downloadFile,
                args=(app_data['download_url'], filename, app_id)
            )
            download_thread.daemon = True
            download_thread.start()
            return True
        else:
            # 如果没有下载URL，显示错误
            self.__moveToFailed(app_id, "没有可用的下载链接")
            return False
            
    @pyqtSlot(str)
    def __moveToCompleted(self, app_id):
        """将任务移至完成界面"""
        task_card = self.__moveTaskBetweenLists(
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
            self.__saveDownloadedAppIds()
                
            # 显示通知
            app_name = task_card.app_data['name']
            self.__showNotification('下载完成', f"{app_name} {self.tr('已成功下载')}", 'success')
            
            # 更新界面
            self.completedPage.update()
            self.update()
    
    @pyqtSlot(str, str)
    def __moveToFailed(self, app_id, error_msg):
        """将任务移至失败界面"""
        task_card = self.__moveTaskBetweenLists(
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
            self.__showNotification(
                '下载失败', 
                f"{app_name} {self.tr('下载失败')}: {error_msg}", 
                'error',
                3000
            )
            
            # 更新界面
            self.failedPage.update()
            self.update()

    @pyqtSlot(object)
    def __handleRedownload(self, app_data):
        """处理重新下载请求"""
        # 获取应用ID
        app_id = app_data.get('id', app_data['name'])
        task_card = None
        
        # 根据来源列表移回下载中列表
        if app_id in self.completedTasks:
            task_card = self.__moveTaskBetweenLists(
                app_id, 
                self.completedTasks, 
                self.completedPageLayout,
                self.downloadingTasks, 
                self.downloadingPageLayout,
                self.downloadingInfoLabel
            )
        elif app_id in self.failedTasks:
            task_card = self.__moveTaskBetweenLists(
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
                self.__saveDownloadedAppIds()
            
            # 开始重新下载
            if self.__startDownloadThread(app_data, app_id, task_card):
                # 显示通知
                self.__showNotification('重新下载', f"{app_data['name']} {self.tr('开始重新下载')}")
                
            # 更新界面
            self.update()

    @pyqtSlot(object)
    def __handleDeleteFile(self, app_data):
        """处理文件删除事件"""
        # 获取应用ID
        app_id = app_data.get('id', app_data['name'])
        
        # 从已下载应用ID列表中移除
        if app_id in self.downloaded_app_ids:
            self.downloaded_app_ids.remove(app_id)
            # 保存到JSON文件
            self.__saveDownloadedAppIds()
        
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
