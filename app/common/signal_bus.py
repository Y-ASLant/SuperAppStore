# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """ Signal bus """

    checkUpdateSig = pyqtSignal()
    micaEnableChanged = pyqtSignal(bool)
    animationEnableChanged = pyqtSignal(bool)
    downloadApp = pyqtSignal(dict)  # 传递app_data字典


signalBus = SignalBus()