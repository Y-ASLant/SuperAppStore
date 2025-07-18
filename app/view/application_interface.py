# coding:utf-8
from qfluentwidgets import (
    ScrollArea, SegmentedWidget, CardWidget, SearchLineEdit, ComboBox, InfoBarPosition,
    TransparentToolButton, BodyLabel, CaptionLabel, StrongBodyLabel, SubtitleLabel, ToolButton,
    FluentIcon as FIF
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
import json
import os

from ..common.style_sheet import StyleSheet
from ..common.setting import APPS_FILE, DOWNLOADED_APPS_FILE
from ..common.signal_bus import signalBus
from ..utils.notification import Notification


class AppCard(CardWidget):
    """应用卡片"""
    downloadClicked = pyqtSignal(dict)
    
    def __init__(self, app_data, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.hBoxLayout = QHBoxLayout(self)
        self.setObjectName("appCard")
        
        # 左侧信息部分
        self.infoLayout = QVBoxLayout()
        
        # 标题和版本
        self.titleLayout = QHBoxLayout()
        self.nameLabel = StrongBodyLabel(app_data['name'])
        self.nameLabel.setObjectName("nameLabel")
        
        if app_data['version']:
            self.versionLabel = CaptionLabel(f"v{app_data['version']}")
            self.versionLabel.setObjectName("versionLabel")
        else:
            self.versionLabel = None
        
        self.titleLayout.addWidget(self.nameLabel)
        if self.versionLabel:
            self.titleLayout.addWidget(self.versionLabel)
        self.titleLayout.addStretch(1)
        
        # 描述标签
        if app_data.get('description'):
            self.descriptionLabel = BodyLabel(app_data['description'])
            self.descriptionLabel.setObjectName("descriptionLabel")
            self.descriptionLabel.setWordWrap(True)
            self.descriptionLabel.setMaximumHeight(40)
        else:
            self.descriptionLabel = None
            
        # 添加信息到左侧布局
        self.infoLayout.addLayout(self.titleLayout)
        if self.descriptionLabel:
            self.infoLayout.addWidget(self.descriptionLabel)
        self.infoLayout.addStretch(1)
        
        # 右侧操作按钮区域
        self.buttonLayout = QHBoxLayout()
        
        # 下载按钮
        self.downloadButton = TransparentToolButton(FIF.DOWNLOAD)
        self.downloadButton.setToolTip("下载")
        self.downloadButton.setObjectName("downloadButton")
        
        self.buttonLayout.addWidget(self.downloadButton)
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        
        # 添加到主布局
        self.hBoxLayout.addLayout(self.infoLayout, 1)
        self.hBoxLayout.addLayout(self.buttonLayout)
        
        # 设置样式
        self.setFixedHeight(70)
        self.hBoxLayout.setContentsMargins(16, 8, 16, 8)
        
        # 连接信号
        self.downloadButton.clicked.connect(self.__onDownloadClicked)
        
    def __onDownloadClicked(self):
        """处理下载按钮点击事件"""
        self.downloadClicked.emit(self.app_data)


class ApplicationInterface(ScrollArea):
    """ 应用界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.parent = parent  # 保存父窗口引用
        
        # 应用和游戏数据
        self.apps = []
        self.games = []
        self.filtered_apps = []
        self.filtered_games = []
        self.original_apps_order = []
        self.original_games_order = []
        
        # 已添加到下载队列的应用ID
        self.downloaded_app_ids = set()
        # 正在下载的应用ID（临时记录，不保存到文件）
        self.tracking_downloads = set()
        
        # 添加分段导航栏
        self.segmentedWidget = SegmentedWidget(self)
        
        # 创建堆叠小部件用于切换内容
        self.stackedWidget = QStackedWidget(self)
        
        # 应用页面
        self.appPage = QWidget(self)
        self.appPageLayout = QVBoxLayout(self.appPage)
        
        # 搜索和排序区域
        self.appControlLayout = QHBoxLayout()
        self.appSearchEdit = SearchLineEdit(self)
        self.appSearchEdit.setPlaceholderText(self.tr("搜索应用..."))
        self.appSearchEdit.textChanged.connect(self.__onAppSearchTextChanged)
        
        self.appSortComboBox = ComboBox(self)
        self.appSortComboBox.addItems([self.tr("默认排序"), self.tr("名称排序")])
        self.appSortComboBox.setCurrentIndex(0)
        self.appSortComboBox.currentIndexChanged.connect(self.__onAppSortOptionChanged)
        
        # 添加刷新按钮
        self.refreshButton = ToolButton(FIF.SYNC)
        self.refreshButton.setToolTip(self.tr("刷新应用列表"))
        self.refreshButton.clicked.connect(self.__onRefreshClicked)
        
        self.appControlLayout.addWidget(self.appSearchEdit, 1)
        self.appControlLayout.addWidget(self.appSortComboBox)
        self.appControlLayout.addWidget(self.refreshButton)
        
        # 应用卡片列表
        self.appListLayout = QVBoxLayout()
        
        # 添加到应用页面布局
        self.appPageLayout.addLayout(self.appControlLayout)
        self.appPageLayout.addLayout(self.appListLayout)
        self.appPage.setObjectName("appPage")
        
        # 游戏页面
        self.gamePage = QWidget(self)
        self.gamePageLayout = QVBoxLayout(self.gamePage)
        
        # 游戏搜索和排序区域
        self.gameControlLayout = QHBoxLayout()
        self.gameSearchEdit = SearchLineEdit(self)
        self.gameSearchEdit.setPlaceholderText(self.tr("搜索游戏..."))
        self.gameSearchEdit.textChanged.connect(self.__onGameSearchTextChanged)
        
        self.gameSortComboBox = ComboBox(self)
        self.gameSortComboBox.addItems([self.tr("默认排序"), self.tr("名称排序")])
        self.gameSortComboBox.setCurrentIndex(0)
        self.gameSortComboBox.currentIndexChanged.connect(self.__onGameSortOptionChanged)
        
        self.gameControlLayout.addWidget(self.gameSearchEdit, 1)
        self.gameControlLayout.addWidget(self.gameSortComboBox)
        
        # 游戏卡片列表
        self.gameListLayout = QVBoxLayout()
        
        # 添加到游戏页面布局
        self.gamePageLayout.addLayout(self.gameControlLayout)
        self.gamePageLayout.addLayout(self.gameListLayout)
        self.gamePage.setObjectName("gamePage")
        
        # 添加子界面（带图标）
        self.addSubInterface(self.appPage, "appPage", self.tr("  应用  "), FIF.APPLICATION)
        self.addSubInterface(self.gamePage, "gamePage", self.tr("  游戏  "), FIF.GAME)

        self.__initWidget()
        self.__loadApps()
        
        # 连接信号
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
        self.scrollWidget.setObjectName('scrollWidget')
        self.segmentedWidget.setFixedWidth(200)
        
        # 应用样式表
        StyleSheet.SETTING_INTERFACE.apply(self)

        # 设置默认显示的页面
        self.stackedWidget.setCurrentWidget(self.appPage)
        self.segmentedWidget.setCurrentItem("appPage")

        # 初始化布局
        self.__initLayout()
        
        # 加载已下载的应用记录
        self.__loadDownloadedAppIds()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(36, 10, 36, 0)
        self.vBoxLayout.addSpacing(24)
        self.vBoxLayout.addWidget(self.segmentedWidget, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.addStretch(1)
        
        # 设置垂直列表布局的属性
        self.appListLayout.setSpacing(10)
        self.gameListLayout.setSpacing(10)
        self.appListLayout.setContentsMargins(0, 20, 0, 0)
        self.gameListLayout.setContentsMargins(0, 20, 0, 0)
        
    def __loadApps(self):
        """加载应用列表"""
        try:
            # 读取应用数据
            if not os.path.exists(APPS_FILE):
                self.__showErrorNotification("应用列表文件不存在，尝试创建...")
                # 如果文件不存在，创建一个空的应用列表文件
                try:
                    os.makedirs(os.path.dirname(APPS_FILE), exist_ok=True)
                    with open(APPS_FILE, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    self.__showSuccessNotification("已创建空的应用列表文件，请刷新或重启应用")
                    # 使用空列表继续
                    apps = []
                except Exception as e:
                    self.__showErrorNotification(f"创建应用列表文件失败: {e}")
                    return
            else:
                with open(APPS_FILE, 'r', encoding='utf-8') as f:
                    apps = json.load(f)
            
            # 分类应用和游戏
            self.apps = [app for app in apps if app.get('category') == '应用']
            self.games = [app for app in apps if app.get('category') == '游戏']
            
            # 保存原始顺序
            self.original_apps_order = self.apps.copy()
            self.original_games_order = self.games.copy()
            
            # 初始化筛选后的列表
            self.filtered_apps = self.apps.copy()
            self.filtered_games = self.games.copy()
            
            # 更新UI显示
            self.__updateAppList()
            self.__updateGameList()
                
        except Exception as e:
            print(f"加载应用列表出错: {e}")
            self.__showErrorNotification(f"加载应用列表出错: {e}")
    
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
            self.__showErrorNotification(f"保存下载记录出错: {e}")
    
    def __updateAppList(self):
        """更新应用列表显示"""
        self.__clearLayout(self.appListLayout)
        
        if not self.filtered_apps:
            emptyLabel = SubtitleLabel(self.tr("没有找到匹配的应用"))
            emptyLabel.setAlignment(Qt.AlignCenter)
            self.appListLayout.addWidget(emptyLabel)
        else:
            for app in self.filtered_apps:
                card = AppCard(app)
                card.downloadClicked.connect(self.__onDownloadApp)
                # 如果应用已经在下载队列中或正在下载中，隐藏下载按钮
                app_id = app.get('id', app['name'])
                if app_id in self.downloaded_app_ids or app_id in self.tracking_downloads:
                    card.downloadButton.setVisible(False)
                self.appListLayout.addWidget(card)
        
        self.appListLayout.addStretch(1)
    
    def __updateGameList(self):
        """更新游戏列表显示"""
        self.__clearLayout(self.gameListLayout)
        
        if not self.filtered_games:
            emptyLabel = SubtitleLabel(self.tr("没有找到匹配的游戏"))
            emptyLabel.setAlignment(Qt.AlignCenter)
            self.gameListLayout.addWidget(emptyLabel)
        else:
            for game in self.filtered_games:
                card = AppCard(game)
                card.downloadClicked.connect(self.__onDownloadApp)
                # 如果游戏已经在下载队列中或正在下载中，隐藏下载按钮
                game_id = game.get('id', game['name'])
                if game_id in self.downloaded_app_ids or game_id in self.tracking_downloads:
                    card.downloadButton.setVisible(False)
                self.gameListLayout.addWidget(card)
            
        self.gameListLayout.addStretch(1)
    
    def __clearLayout(self, layout):
        """清空布局中的所有控件"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                layout_to_clear = item.layout()
                if layout_to_clear is not None:
                    self.__clearLayout(layout_to_clear)
    
    def __showErrorNotification(self, message):
        """显示错误通知"""
        Notification.error(
            title=self.tr('错误'),
            content=message,
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
    def __showSuccessNotification(self, message):
        """显示成功通知"""
        Notification.success(
            title=self.tr('成功'),
            content=message,
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.window()
        )
            
    def __onAppSearchTextChanged(self, text):
        """处理应用搜索文本变化"""
        if not text:
            self.filtered_apps = self.apps.copy()
        else:
            self.filtered_apps = [app for app in self.apps if 
                                text.lower() in app['name'].lower() or 
                                (app.get('description') and text.lower() in app['description'].lower())]
        self.__onAppSortOptionChanged(self.appSortComboBox.currentIndex())
    
    def __onGameSearchTextChanged(self, text):
        """处理游戏搜索文本变化"""
        if not text:
            self.filtered_games = self.games.copy()
        else:
            self.filtered_games = [game for game in self.games if 
                                 text.lower() in game['name'].lower() or 
                                 (game.get('description') and text.lower() in game['description'].lower())]
        self.__onGameSortOptionChanged(self.gameSortComboBox.currentIndex())
    
    def __onAppSortOptionChanged(self, index):
        """处理应用排序选项变化"""
        if index == 0:  # 默认排序
            if self.filtered_apps:
                original_order_dict = {app['name']: i for i, app in enumerate(self.original_apps_order)}
                self.filtered_apps.sort(key=lambda x: original_order_dict.get(x['name'], 999999))
        elif index == 1:  # 名称排序
            self.filtered_apps.sort(key=lambda x: x['name'])
        self.__updateAppList()
    
    def __onGameSortOptionChanged(self, index):
        """处理游戏排序选项变化"""
        if index == 0:  # 默认排序
            if self.filtered_games:
                original_order_dict = {game['name']: i for i, game in enumerate(self.original_games_order)}
                self.filtered_games.sort(key=lambda x: original_order_dict.get(x['name'], 999999))
        elif index == 1:  # 名称排序
            self.filtered_games.sort(key=lambda x: x['name'])
        self.__updateGameList()
            
    def __onDownloadApp(self, app_data):
        """处理应用下载"""
        try:
            if app_data.get('download_url'):
                # 获取应用ID
                app_id = app_data.get('id', app_data['name'])
                
                # 将任务添加到下载界面
                signalBus.downloadApp.emit(app_data)
                
                # 添加到正在下载的临时集合中
                self.tracking_downloads.add(app_id)
                
                # 隐藏发送信号的卡片上的下载按钮
                sender = self.sender()
                if isinstance(sender, AppCard):
                    sender.downloadButton.setVisible(False)
                
                self.__showSuccessNotification(f"已添加 {app_data['name']} {app_data.get('version', '')} 到下载队列")
            else:
                self.__showErrorNotification(f"应用 {app_data['name']} 没有可用的下载链接")
        except Exception as e:
            self.__showErrorNotification(f"下载 {app_data['name']} 时出错: {str(e)}")
        
    def __onRefreshClicked(self):
        """处理刷新按钮点击事件"""
        # 如果父窗口存在并且有refreshAppsList方法，调用它
        if hasattr(self.parent, 'refreshAppsList'):
            self.parent.refreshAppsList()
        else:
            # 否则只重新加载本地文件
            self.__loadApps()
            self.__showSuccessNotification(self.tr("应用列表已刷新"))

    def __connectSignalToSlot(self):
        """连接信号和槽"""
        # 连接分段导航栏的信号
        self.segmentedWidget.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        ) 