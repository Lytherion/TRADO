"""
应用入口
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH
from database import DatabaseManager
from models import TaskStatus
from services.task_service import TaskService
from services.recurring_service import RecurringTaskService
from services.reminder_service import ReminderService
from services.permanent_task_service import PermanentTaskService
from ui.main_window import MainWindow
from ui.tray_icon import TrayIcon
from ui.reminder_widget import ReminderWidget


class TaskManagerApp:
    """任务管理应用"""

    def __init__(self):
        # 初始化数据库
        self.db = DatabaseManager(DB_PATH)

        # 初始化服务
        self.task_service = TaskService(self.db)
        self.recurring_service = RecurringTaskService(self.db, self.task_service)
        self.reminder_service = ReminderService(self.task_service)
        self.permanent_task_service = PermanentTaskService(self.db)

        # 设置提醒回调
        self.reminder_service.set_reminder_callback(self.on_reminder)

        self.main_window = None
        self.tray_icon = None

    def on_reminder(self, task):
        """提醒回调"""
        # 标记任务为正在处理,防止重复弹窗
        self.reminder_service.processing_tasks.add(task.id)

        try:
            # 显示模态提醒弹窗(阻塞式,不设置父窗口避免激活主窗口)
            dialog = ReminderWidget(task, self.reminder_service, None)

            # 系统托盘通知
            if self.tray_icon:
                self.tray_icon.show_message("任务提醒", f"⏰ {task.title}")

            # 模态显示,用户必须处理
            if dialog.exec():
                action = dialog.get_action()
                if action == "complete":
                    self.task_service.mark_complete(task.id)

                    # 标记为已提醒(仅在完成任务时)
                    saved_task = self.task_service.get_task(task.id)
                    if saved_task and saved_task.status == TaskStatus.TODO:
                        saved_task.notified = True
                        self.task_service.update_task(saved_task)

                elif action == "snooze":
                    minutes = dialog.get_snooze_minutes()
                    self.reminder_service.snooze_reminder(task.id, minutes)
                    # snooze_reminder 内部已经设置 notified=False,这里不需要再设置

                # 静默刷新任务列表(不显示窗口)
                if self.main_window:
                    self.main_window.load_tasks()
        finally:
            # 处理完成后从集合中移除
            self.reminder_service.processing_tasks.discard(task.id)

    def run(self):
        """运行应用"""
        app = QApplication(sys.argv)
        app.setApplicationName("任务管理器")

        # 保存 app 和 style_path 供热重载使用
        self.app = app
        self.style_path = Path(__file__).parent / "ui" / "styles.qss"

        # 设置应用图标
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            from PySide6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))

        # 加载样式表
        self.load_stylesheet()

        # 创建主窗口
        self.main_window = MainWindow(
            self.task_service,
            self.recurring_service,
            self.reminder_service,
            self.permanent_task_service,
            self  # 传递 app 实例以支持热重载
        )

        # 设置窗口图标
        if icon_path.exists():
            from PySide6.QtGui import QIcon
            self.main_window.setWindowIcon(QIcon(str(icon_path)))

        # 创建系统托盘
        self.tray_icon = TrayIcon(self.main_window)
        self.tray_icon.show_window_signal.connect(self.main_window.show)
        self.tray_icon.quit_signal.connect(app.quit)

        self.main_window.show()

        sys.exit(app.exec())

    def load_stylesheet(self):
        """加载样式表"""
        if self.style_path.exists():
            with open(self.style_path, "r", encoding="utf-8") as f:
                self.app.setStyleSheet(f.read())
            print("✅ 样式表已重新加载")


if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
