# coding: utf-8
import requests
from typing import List, Dict, Optional
from datetime import datetime
from ..common.logger import logger


class GitHubAPI:
    """GitHub API 工具类，用于获取仓库的 Release 信息"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        初始化 GitHub API 客户端

        Args:
            token: GitHub Personal Access Token (可选，用于提高 API 限制)
        """
        self.token = token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"

    def get_latest_release(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取仓库的最新 Release

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Release 信息字典，如果失败返回 None
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases/latest"
            logger.debug(f"请求 URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            logger.debug(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                release_data = response.json()
                logger.info(f"获取到 Release: {release_data.get('tag_name')}")
                return self._parse_release(release_data)
            elif response.status_code == 404:
                # 没有 latest release 标签，尝试获取所有 Release 的第一个
                logger.debug("没有 latest release，尝试获取所有 releases")
                all_releases = self.get_all_releases(owner, repo, per_page=1)
                if all_releases:
                    logger.info(f"从所有 releases 中获取到第一个: {all_releases[0].get('tag_name')}")
                    return all_releases[0]
                logger.warning("没有找到任何 releases")
                return None
            else:
                logger.error(f"获取最新 Release 失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.exception(f"获取最新 Release 出错: {e}")
            return None

    def get_all_releases(self, owner: str, repo: str, per_page: int = 10) -> List[Dict]:
        """
        获取仓库的所有 Release

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            per_page: 每页数量

        Returns:
            Release 列表
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases"
            params = {"per_page": per_page}
            logger.debug(f"请求所有 releases URL: {url}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            logger.debug(f"所有 releases 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                releases = response.json()
                logger.info(f"获取到 {len(releases)} 个 releases")
                return [self._parse_release(release) for release in releases]
            else:
                logger.error(f"获取 Release 列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.exception(f"获取 Release 列表出错: {e}")
            return []

    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取仓库基本信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            仓库信息字典
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "description": data.get("description"),
                    "html_url": data.get("html_url"),
                    "stargazers_count": data.get("stargazers_count"),
                    "language": data.get("language"),
                    "updated_at": data.get("updated_at"),
                }
            else:
                logger.error(f"获取仓库信息失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取仓库信息出错: {e}")
            return None

    def _parse_release(self, release_data: Dict) -> Dict:
        """
        解析 Release 数据为统一格式
        Args:
            release_data: GitHub API 返回的 Release 数据

        Returns:
            解析后的 Release 信息
        """
        # 解析资源文件
        assets = []
        for asset in release_data.get("assets", []):
            assets.append(
                {
                    "name": asset.get("name"),
                    "size": asset.get("size"),
                    "download_count": asset.get("download_count"),
                    "browser_download_url": asset.get("browser_download_url"),
                    "content_type": asset.get("content_type"),
                }
            )

        # 解析发布时间
        published_at = release_data.get("published_at", "")
        if published_at:
            try:
                dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                published_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass

        return {
            "tag_name": release_data.get("tag_name"),
            "name": release_data.get("name") or release_data.get("tag_name"),
            "body": release_data.get("body", ""),
            "html_url": release_data.get("html_url"),
            "published_at": published_at,
            "prerelease": release_data.get("prerelease", False),
            "draft": release_data.get("draft", False),
            "assets": assets,
        }

    @staticmethod
    def parse_repo_url(url: str) -> Optional[tuple]:
        """
        解析 GitHub 仓库 URL

        Args:
            url: GitHub 仓库 URL 或 owner/repo 格式

        Returns:
            (owner, repo) 元组，如果解析失败返回 None
        """
        url = url.strip()

        # 处理 owner/repo 格式
        if "/" in url and "github.com" not in url:
            parts = url.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]

        # 处理完整 URL
        if "github.com" in url:
            # 移除协议前缀
            url = url.replace("https://", "").replace("http://", "")
            # 移除 github.com
            url = url.replace("github.com/", "")
            # 移除末尾的斜杠和其他路径
            parts = url.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]

        return None
