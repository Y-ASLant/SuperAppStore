from PyQt5.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

class Notification:
    """通知工具类，用于统一管理应用内通知"""
    
    @staticmethod
    def show(title, content, type_='info', duration=2000, parent=None, position=InfoBarPosition.TOP, orient=Qt.Horizontal, isClosable=False):
        """显示通知的统一方法
        
        Args:
            title (str): 通知标题
            content (str): 通知内容
            type_ (str): 通知类型，可选值: 'info', 'success', 'warning', 'error'
            duration (int): 显示时长(毫秒)
            parent (QWidget): 父级窗口
            position (InfoBarPosition): 通知显示位置
            orient (Qt.Orientation): 通知方向，水平或垂直
            isClosable (bool): 是否可关闭
        """
        # 根据类型选择不同的通知函数
        notification_func = InfoBar.info  # 默认为普通提示
        if type_ == 'success':
            notification_func = InfoBar.success
        elif type_ == 'error':
            notification_func = InfoBar.error
        elif type_ == 'warning':
            notification_func = InfoBar.warning
            
        # 显示通知
        notification_func(
            title=title,
            content=content,
            orient=orient,
            isClosable=isClosable,
            position=position,
            duration=duration,
            parent=parent
        )
    
    @staticmethod
    def info(title, content, duration=2000, parent=None, position=InfoBarPosition.TOP, orient=Qt.Horizontal, isClosable=False):
        """显示信息通知"""
        Notification.show(title, content, 'info', duration, parent, position, orient, isClosable)
    
    @staticmethod
    def success(title, content, duration=2000, parent=None, position=InfoBarPosition.TOP, orient=Qt.Horizontal, isClosable=False):
        """显示成功通知"""
        Notification.show(title, content, 'success', duration, parent, position, orient, isClosable)
    
    @staticmethod
    def warning(title, content, duration=2000, parent=None, position=InfoBarPosition.TOP, orient=Qt.Horizontal, isClosable=False):
        """显示警告通知"""
        Notification.show(title, content, 'warning', duration, parent, position, orient, isClosable)
    
    @staticmethod
    def error(title, content, duration=3000, parent=None, position=InfoBarPosition.TOP, orient=Qt.Horizontal, isClosable=False):
        """显示错误通知"""
        Notification.show(title, content, 'error', duration, parent, position, orient, isClosable) 