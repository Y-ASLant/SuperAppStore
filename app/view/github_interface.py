# coding:utf-8
from qfluentwidgets import (
    ScrollArea,
    CardWidget,
    PushButton,
    LineEdit,
    TransparentToolButton,
    BodyLabel,
    StrongBodyLabel,
    CaptionLabel,
    SubtitleLabel,
    FluentIcon as FIF,
    InfoBarPosition,
    MessageBox,
    ProgressRing,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
import json
import os

from ..common.style_sheet import StyleSheet
from ..common.setting import CONFIG_FOLDER
from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..utils.notification import Notification
from ..utils.github_api import GitHubAPI


# GitHub 仓库配置文件
GITHUB_REPOS_FILE = CONFIG_FOLDER / "github_repos.json"


class FetchReleaseThread(QThread):
    """获取 Release 信息的后台线程"""

    finished = pyqtSignal(dict)  # 成功信号
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, owner, repo, token=None):
        super().__init__()
        self.owner = owner
        self.repo = repo
        self.token = token

    def run(self):
        try:
            api = GitHubAPI(self.token)

            # 获取仓库信息
            repo_info = api.get_repository_info(self.owner, self.repo)
            if not repo_info:
                self.error.emit("无法获取仓库信息，请检查仓库名称是否正确")
                return

            # 获取最新 Release
            latest_release = api.get_latest_release(self.owner, self.repo)

            result = {"repo_info": repo_info, "latest_release": latest_release}

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"获取信息失败: {str(e)}")


class RepoCard(CardWidget):
    """GitHub 仓库卡片"""

    removeClicked = pyqtSignal(str)  # 移除信号
    refreshClicked = pyqtSignal(str)  # 刷新信号
    downloadClicked = pyqtSignal(dict)  # 下载信号

    def __init__(self, repo_data, parent=None):
        super().__init__(parent)
        self.repo_data = repo_data
        self.hBoxLayout = QHBoxLayout(self)
        self.setObjectName("repoCard")

        # 左侧信息部分
        self.infoLayout = QVBoxLayout()

        # 仓库名称和标签
        self.titleLayout = QHBoxLayout()
        self.nameLabel = StrongBodyLabel(repo_data.get("full_name", ""))
        self.nameLabel.setObjectName("nameLabel")

        self.titleLayout.addWidget(self.nameLabel)
        self.titleLayout.addStretch(1)

        # 描述
        description = repo_data.get("description", "")
        if description:
            self.descriptionLabel = BodyLabel(description)
            self.descriptionLabel.setObjectName("descriptionLabel")
            self.descriptionLabel.setWordWrap(True)
            self.descriptionLabel.setMaximumHeight(40)
        else:
            self.descriptionLabel = None

        # Release 信息
        latest_release = repo_data.get("latest_release")
        if latest_release:
            release_text = f"最新版本: {latest_release.get('tag_name', 'N/A')} ({latest_release.get('published_at', 'N/A')})"
            self.releaseLabel = CaptionLabel(release_text)
            self.releaseLabel.setObjectName("releaseLabel")
        else:
            self.releaseLabel = CaptionLabel("暂无 Release")
            self.releaseLabel.setObjectName("releaseLabel")

        # 添加信息到左侧布局
        self.infoLayout.addLayout(self.titleLayout)
        if self.descriptionLabel:
            self.infoLayout.addWidget(self.descriptionLabel)
        self.infoLayout.addWidget(self.releaseLabel)
        self.infoLayout.addStretch(1)

        # 右侧操作按钮区域
        self.buttonLayout = QHBoxLayout()

        # 下载按钮（仅在有 Release 时显示）
        if latest_release and latest_release.get("assets"):
            self.downloadButton = TransparentToolButton(FIF.DOWNLOAD)
            self.downloadButton.setToolTip("下载最新版本")
            self.downloadButton.setObjectName("downloadButton")
            self.downloadButton.clicked.connect(self._onDownloadClicked)
            self.buttonLayout.addWidget(self.downloadButton)

        # 刷新按钮
        self.refreshButton = TransparentToolButton(FIF.SYNC)
        self.refreshButton.setToolTip("刷新")
        self.refreshButton.setObjectName("refreshButton")
        self.refreshButton.clicked.connect(self._onRefreshClicked)

        # 删除按钮
        self.removeButton = TransparentToolButton(FIF.DELETE)
        self.removeButton.setToolTip("移除")
        self.removeButton.setObjectName("removeButton")
        self.removeButton.clicked.connect(self._onRemoveClicked)

        self.buttonLayout.addWidget(self.refreshButton)
        self.buttonLayout.addWidget(self.removeButton)
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)

        # 添加到主布局
        self.hBoxLayout.addLayout(self.infoLayout, 1)
        self.hBoxLayout.addLayout(self.buttonLayout)

        # 设置样式
        self.setFixedHeight(100)
        self.hBoxLayout.setContentsMargins(16, 8, 16, 8)

    def _onRemoveClicked(self):
        """处理移除按钮点击"""
        self.removeClicked.emit(self.repo_data.get("full_name", ""))

    def _onRefreshClicked(self):
        """处理刷新按钮点击"""
        self.refreshClicked.emit(self.repo_data.get("full_name", ""))

    def _onDownloadClicked(self):
        """处理下载按钮点击"""
        self.downloadClicked.emit(self.repo_data)


class GitHubInterface(ScrollArea):
    """GitHub 仓库管理界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.parent = parent

        # GitHub API 客户端（使用配置的 Token）
        self.api = self._create_api_client()

        # 仓库列表
        self.repos = []
        self.repo_cards = []

        # 后台线程
        self.fetch_thread = None

        self._initWidget()
        self._initLayout()
        self._loadRepos()

    def _initWidget(self):
        self.resize(1600, 900)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("githubInterface")

        self.scrollWidget.setObjectName("scrollWidget")
        StyleSheet.SETTING_INTERFACE.apply(self)

    def _initLayout(self):
        """初始化布局"""
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(20)

        # 标题
        self.titleLabel = SubtitleLabel(self.tr("GitHub 仓库订阅"))
        self.vBoxLayout.addWidget(self.titleLabel)

        # 添加仓库区域
        self.addRepoCard = CardWidget(self)
        self.addRepoLayout = QVBoxLayout(self.addRepoCard)

        # 输入区域
        self.inputLayout = QHBoxLayout()
        self.repoInput = LineEdit(self)
        self.repoInput.setPlaceholderText(
            self.tr("输入 GitHub 仓库 (例如: owner/repo 或完整 URL)")
        )
        self.repoInput.setClearButtonEnabled(True)

        self.addButton = PushButton(FIF.ADD, self.tr("添加"))
        self.addButton.clicked.connect(self._onAddRepo)

        # 加载指示器（初始隐藏）
        self.loadingRing = ProgressRing(self)
        self.loadingRing.setFixedSize(24, 24)
        self.loadingRing.hide()

        self.inputLayout.addWidget(self.repoInput, 1)
        self.inputLayout.addWidget(self.loadingRing)
        self.inputLayout.addWidget(self.addButton)

        # 提示文本
        self.hintLabel = CaptionLabel(
            self.tr("支持格式: owner/repo 或 https://github.com/owner/repo")
        )
        self.hintLabel.setObjectName("hintLabel")

        self.addRepoLayout.addLayout(self.inputLayout)
        self.addRepoLayout.addWidget(self.hintLabel)

        self.vBoxLayout.addWidget(self.addRepoCard)

        # 仓库列表标题
        self.repoListLabel = StrongBodyLabel(self.tr("已订阅的仓库"))
        self.vBoxLayout.addWidget(self.repoListLabel)

        # 仓库列表容器
        self.repoListLayout = QVBoxLayout()
        self.repoListLayout.setSpacing(10)
        self.vBoxLayout.addLayout(self.repoListLayout)

        self.vBoxLayout.addStretch(1)

    def _loadRepos(self):
        """加载已保存的仓库列表"""
        try:
            if os.path.exists(GITHUB_REPOS_FILE):
                with open(GITHUB_REPOS_FILE, "r", encoding="utf-8") as f:
                    self.repos = json.load(f)
                self._updateRepoList()
        except Exception as e:
            print(f"加载仓库列表失败: {e}")
            self.repos = []

    def _saveRepos(self):
        """保存仓库列表到文件"""
        try:
            os.makedirs(CONFIG_FOLDER, exist_ok=True)
            with open(GITHUB_REPOS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.repos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存仓库列表失败: {e}")
            self._showErrorNotification(f"保存失败: {e}")

    def _updateRepoList(self):
        """更新仓库列表显示"""
        # 清空现有卡片
        self._clearLayout(self.repoListLayout)
        self.repo_cards = []

        if not self.repos:
            emptyLabel = BodyLabel(self.tr("暂无订阅的仓库，请添加"))
            emptyLabel.setAlignment(Qt.AlignCenter)
            self.repoListLayout.addWidget(emptyLabel)
        else:
            for repo in self.repos:
                card = RepoCard(repo)
                card.removeClicked.connect(self._onRemoveRepo)
                card.refreshClicked.connect(self._onRefreshRepo)
                card.downloadClicked.connect(self._onDownloadRelease)
                self.repoListLayout.addWidget(card)
                self.repo_cards.append(card)

    def _onAddRepo(self):
        """处理添加仓库"""
        repo_url = self.repoInput.text().strip()
        if not repo_url:
            self._showErrorNotification("请输入仓库地址")
            return

        # 解析仓库 URL
        parsed = GitHubAPI.parse_repo_url(repo_url)
        if not parsed:
            self._showErrorNotification("无效的仓库地址格式")
            return

        owner, repo = parsed
        full_name = f"{owner}/{repo}"

        # 检查是否已存在
        if any(r.get("full_name") == full_name for r in self.repos):
            self._showErrorNotification("该仓库已存在")
            return

        # 显示加载指示器
        self.loadingRing.show()
        self.addButton.setEnabled(False)

        # 创建后台线程获取仓库信息（使用配置的 Token）
        token = self._get_token()
        self.fetch_thread = FetchReleaseThread(owner, repo, token)
        self.fetch_thread.finished.connect(self._onFetchFinished)
        self.fetch_thread.error.connect(self._onFetchError)
        self.fetch_thread.start()

    def _onFetchFinished(self, result):
        """获取仓库信息成功"""
        self.loadingRing.hide()
        self.addButton.setEnabled(True)

        repo_info = result.get("repo_info", {})
        latest_release = result.get("latest_release")

        # 构建仓库数据
        repo_data = {
            "full_name": repo_info.get("full_name"),
            "name": repo_info.get("name"),
            "description": repo_info.get("description"),
            "html_url": repo_info.get("html_url"),
            "latest_release": latest_release,
        }

        # 添加到列表
        self.repos.append(repo_data)
        self._saveRepos()
        self._updateRepoList()

        # 清空输入框
        self.repoInput.clear()

        self._showSuccessNotification(f"成功添加仓库: {repo_data['full_name']}")

    def _onFetchError(self, error_msg):
        """获取仓库信息失败"""
        self.loadingRing.hide()
        self.addButton.setEnabled(True)
        self._showErrorNotification(error_msg)

    def _onRemoveRepo(self, full_name):
        """移除仓库"""
        # 显示确认对话框
        w = MessageBox(
            self.tr("确认移除"),
            self.tr(f"确定要移除仓库 {full_name} 吗？"),
            self.window(),
        )
        if w.exec():
            self.repos = [r for r in self.repos if r.get("full_name") != full_name]
            self._saveRepos()
            self._updateRepoList()
            self._showSuccessNotification(f"已移除仓库: {full_name}")

    def _onRefreshRepo(self, full_name):
        """刷新仓库信息"""
        # 解析仓库名称
        parsed = GitHubAPI.parse_repo_url(full_name)
        if not parsed:
            self._showErrorNotification("无效的仓库名称")
            return

        owner, repo = parsed

        # 创建后台线程获取最新信息（使用配置的 Token）
        token = self._get_token()
        self.fetch_thread = FetchReleaseThread(owner, repo, token)
        self.fetch_thread.finished.connect(
            lambda result: self._onRefreshFinished(full_name, result)
        )
        self.fetch_thread.error.connect(self._onFetchError)
        self.fetch_thread.start()

        self._showSuccessNotification(f"正在刷新 {full_name}...")

    def _onRefreshFinished(self, full_name, result):
        """刷新完成"""
        repo_info = result.get("repo_info", {})
        latest_release = result.get("latest_release")

        # 更新仓库数据
        for repo in self.repos:
            if repo.get("full_name") == full_name:
                repo["description"] = repo_info.get("description")
                repo["latest_release"] = latest_release
                break

        self._saveRepos()
        self._updateRepoList()
        self._showSuccessNotification(f"刷新完成: {full_name}")

    def _onDownloadRelease(self, repo_data):
        """处理下载 Release"""
        latest_release = repo_data.get("latest_release")
        if not latest_release:
            self._showErrorNotification("该仓库暂无可用的 Release")
            return

        assets = latest_release.get("assets", [])
        if not assets:
            self._showErrorNotification("该 Release 没有可下载的文件")
            return

        # 如果只有一个文件，直接下载
        if len(assets) == 1:
            self._downloadAsset(repo_data, assets[0])
        else:
            # 多个文件，显示选择对话框
            self._showAssetSelectionDialog(repo_data, assets)

    def _showAssetSelectionDialog(self, repo_data, assets):
        """显示资源文件选择对话框"""
        from PyQt5.QtWidgets import QDialog, QListWidget

        dialog = QDialog(self.window())
        dialog.setWindowTitle(self.tr("选择下载文件"))
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        # 提示标签
        label = BodyLabel(self.tr("请选择要下载的文件:"))
        layout.addWidget(label)

        # 文件列表
        listWidget = QListWidget()
        for asset in assets:
            size_mb = asset.get("size", 0) / (1024 * 1024)
            item_text = f"{asset.get('name')} ({size_mb:.2f} MB)"
            listWidget.addItem(item_text)
        layout.addWidget(listWidget)

        # 按钮
        buttonLayout = QHBoxLayout()
        downloadBtn = PushButton(self.tr("下载"))
        cancelBtn = PushButton(self.tr("取消"))

        def on_download():
            current_row = listWidget.currentRow()
            if current_row >= 0:
                self._downloadAsset(repo_data, assets[current_row])
                dialog.accept()

        downloadBtn.clicked.connect(on_download)
        cancelBtn.clicked.connect(dialog.reject)

        buttonLayout.addStretch(1)
        buttonLayout.addWidget(downloadBtn)
        buttonLayout.addWidget(cancelBtn)
        layout.addLayout(buttonLayout)

        dialog.exec()

    def _downloadAsset(self, repo_data, asset):
        """下载资源文件"""
        # 构建应用数据格式，兼容现有下载系统
        app_data = {
            "id": f"github_{repo_data.get('full_name', '').replace('/', '_')}",
            "name": repo_data.get("name", ""),
            "version": repo_data.get("latest_release", {}).get("tag_name", ""),
            "description": repo_data.get("description", ""),
            "category": "应用",
            "download_url": asset.get("browser_download_url"),
            "file_name": asset.get("name"),
            "source": "GitHub Release",
        }

        # 发送下载信号
        signalBus.downloadApp.emit(app_data)
        self._showSuccessNotification(f"已添加到下载队列: {asset.get('name')}")

    def _create_api_client(self):
        """创建 GitHub API 客户端，使用配置的 Token"""
        token = self._get_token()
        return GitHubAPI(token)

    def _get_token(self):
        """获取配置的 GitHub Token"""
        if cfg.githubTokenEnabled.value and cfg.githubToken.value:
            return cfg.githubToken.value
        return None

    def _clearLayout(self, layout):
        """清空布局"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _showErrorNotification(self, message):
        """显示错误通知"""
        Notification.error(
            title=self.tr("错误"),
            content=message,
            duration=3000,
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT,
        )

    def _showSuccessNotification(self, message):
        """显示成功通知"""
        Notification.success(
            title=self.tr("成功"),
            content=message,
            duration=2000,
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT,
        )
