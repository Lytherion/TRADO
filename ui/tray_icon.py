"""
系统托盘图标
"""
from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal


class TrayIcon(QObject):
    """系统托盘图标"""

    show_window_signal = Signal()
    quit_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_tray()

    def init_tray(self):
        """初始化托盘"""
        self.tray = QSystemTrayIcon(self.parent())

        # 设置图标
        icon_path = Path(__file__).parent.parent / "icon.png"
        if icon_path.exists():
            self.tray.setIcon(QIcon(str(icon_path)))

        # 创建右键菜单
        menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_window_signal.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_signal.emit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

        # 双击显示主窗口
        self.tray.activated.connect(self.on_activated)

        # 显示托盘图标
        self.tray.show()

    def on_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_signal.emit()

    def show_message(self, title: str, message: str):
        """显示系统通知"""
        self.tray.showMessage(
            title,
            message,
            QSystemTrayIcon.Information,
            3000  # 显示3秒
        )
