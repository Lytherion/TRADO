"""
主窗口
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
    QSplitter, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from datetime import datetime
from models import TaskStatus
from services.task_service import TaskService
from services.recurring_service import RecurringTaskService
from services.reminder_service import ReminderService
from services.permanent_task_service import PermanentTaskService


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, task_service: TaskService, recurring_service: RecurringTaskService,
                 reminder_service: ReminderService,
                 permanent_task_service: PermanentTaskService):
        super().__init__()
        self.task_service = task_service
        self.recurring_service = recurring_service
        self.reminder_service = reminder_service
        self.permanent_task_service = permanent_task_service

        self.current_filter = "all"  # 当前筛选条件

        self.init_ui()
        self.setup_timer()
        self.load_tasks()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("任务管理器")
        self.resize(1400, 800)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧边栏
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)

        # 右侧主视图
        main_view = self.create_main_view()
        splitter.addWidget(main_view)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

        # 创建菜单栏
        self.create_menu_bar()

        # 状态栏
        self.statusBar().showMessage("就绪")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.load_tasks)
        view_menu.addAction(refresh_action)

    def create_sidebar(self) -> QWidget:
        """创建侧边栏"""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)

        # 分类标题
        layout.addWidget(QLabel("<b>筛选</b>"))

        # 分类按钮
        categories = [
            ("all", "📋 所有任务"),
            ("today", "⭐ 今日任务"),
            ("recurring", "🔄 循环任务"),
        ]

        for key, label in categories:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, k=key: self.filter_tasks(k))
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    def create_main_view(self) -> QWidget:
        """创建主视图"""
        main_view = QWidget()
        layout = QVBoxLayout(main_view)

        # 工具栏
        toolbar = QHBoxLayout()
        self.add_task_btn = QPushButton("➕ 新建任务")
        self.add_task_btn.clicked.connect(self.on_add_task)
        self.add_recurring_btn = QPushButton("🔄 新建循环任务")
        self.add_recurring_btn.clicked.connect(self.on_add_recurring_task)
        self.add_permanent_btn = QPushButton("📌 新建常驻任务")
        self.add_permanent_btn.clicked.connect(self.on_add_permanent_task)

        toolbar.addWidget(self.add_task_btn)
        toolbar.addWidget(self.add_recurring_btn)
        toolbar.addWidget(self.add_permanent_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # 左右分栏布局 - 使用 QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # 左侧: 常驻任务区域
        left_widget = QWidget()
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        permanent_label = QLabel("📌 常驻任务")
        permanent_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px; background: transparent; border: none;")
        left_layout.addWidget(permanent_label)

        self.permanent_tree = QTreeWidget()
        self.permanent_tree.setHeaderHidden(True)
        self.permanent_tree.setRootIsDecorated(False)
        self.permanent_tree.setStyleSheet("background: white; border: 1px solid #e0e0e0; border-radius: 4px;")
        self.permanent_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.permanent_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.permanent_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        left_layout.addWidget(self.permanent_tree)

        splitter.addWidget(left_widget)

        # 右侧: 普通任务列表
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["任务", "时间", "状态"])
        self.task_tree.setColumnWidth(0, 600)
        self.task_tree.setColumnWidth(1, 200)
        self.task_tree.setColumnWidth(2, 120)
        self.task_tree.setRootIsDecorated(True)
        self.task_tree.setStyleSheet("background: white; border: 1px solid #e0e0e0; border-radius: 4px;")
        self.task_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.task_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        right_layout.addWidget(self.task_tree)

        splitter.addWidget(right_widget)

        # 设置初始比例 (左:右 = 1:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # 恢复上次的分隔位置
        saved_state = self.load_splitter_state()
        if saved_state:
            splitter.restoreState(saved_state)

        # 保存分隔位置变化
        splitter.splitterMoved.connect(lambda: self.save_splitter_state(splitter.saveState()))

        self.splitter = splitter
        layout.addWidget(splitter)

        return main_view

    def filter_tasks(self, filter_key: str):
        """筛选任务"""
        self.current_filter = filter_key
        self.load_tasks()

    def load_tasks(self):
        """加载任务列表"""
        # 始终加载常驻任务到固定区域
        self.load_permanent_tasks()

        # 加载主任务列表
        self.task_tree.clear()

        if self.current_filter == "all":
            self.load_all_tasks()
        elif self.current_filter == "today":
            self.load_today_tasks()
        elif self.current_filter == "recurring":
            self.load_recurring_tasks()

    def load_all_tasks(self):
        """加载所有任务(未完成和已完成分组显示)"""
        all_tasks = self.task_service.get_all_tasks()
        # 过滤掉循环任务实例
        tasks = [t for t in all_tasks if t.recurring_id is None]

        # 分离已完成和未完成任务
        uncompleted = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]

        # 排序: 按 remind_time 排序,无提醒时间的排在最后
        uncompleted.sort(key=lambda t: t.remind_time if t.remind_time else datetime.max)
        completed.sort(key=lambda t: t.remind_time if t.remind_time else datetime.max)

        # 未完成任务组
        if uncompleted:
            uncompleted_group = QTreeWidgetItem(self.task_tree)
            uncompleted_group.setText(0, f"📋 未完成 ({len(uncompleted)})")
            uncompleted_group.setExpanded(True)
            uncompleted_group.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

            for task in uncompleted:
                item = QTreeWidgetItem(uncompleted_group)
                item.setText(0, task.title)
                item.setText(1, task.remind_time.strftime("%Y-%m-%d %H:%M") if task.remind_time else "")
                item.setText(2, self._status_text(task.status))
                item.setData(0, Qt.UserRole, ("task", task.id))

        # 已完成任务组
        if completed:
            completed_group = QTreeWidgetItem(self.task_tree)
            completed_group.setText(0, f"✅ 已完成 ({len(completed)})")
            completed_group.setExpanded(False)
            completed_group.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

            for task in completed:
                item = QTreeWidgetItem(completed_group)
                item.setText(0, task.title)
                item.setText(1, task.remind_time.strftime("%Y-%m-%d %H:%M") if task.remind_time else "")
                item.setText(2, self._status_text(task.status))
                item.setData(0, Qt.UserRole, ("task", task.id))

    def load_today_tasks(self):
        """加载今日任务(未完成在上,已完成可折叠)"""
        tasks = self.task_service.get_today_tasks()

        # 分离已完成和未完成任务
        uncompleted = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]

        # 排序: 按 remind_time 排序,无提醒时间的排在最后
        uncompleted.sort(key=lambda t: t.remind_time if t.remind_time else datetime.max)
        completed.sort(key=lambda t: t.remind_time if t.remind_time else datetime.max)

        # 显示未完成任务
        for task in uncompleted:
            item = QTreeWidgetItem(self.task_tree)
            item.setText(0, task.title)
            item.setText(1, task.remind_time.strftime("%Y-%m-%d %H:%M") if task.remind_time else "")
            item.setText(2, self._status_text(task.status))
            item.setData(0, Qt.UserRole, ("task", task.id))

        # 显示已完成任务(可折叠)
        if completed:
            completed_group = QTreeWidgetItem(self.task_tree)
            completed_group.setText(0, f"✅ 已完成 ({len(completed)})")
            completed_group.setExpanded(False)  # 默认折叠
            completed_group.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

            for task in completed:
                item = QTreeWidgetItem(completed_group)
                item.setText(0, task.title)
                item.setText(1, task.remind_time.strftime("%Y-%m-%d %H:%M") if task.remind_time else "")
                item.setText(2, self._status_text(task.status))
                item.setData(0, Qt.UserRole, ("task", task.id))

    def load_recurring_tasks(self):
        """加载循环任务"""
        recurring_tasks = self.recurring_service.get_all_recurring_tasks()
        for rt in recurring_tasks:
            item = QTreeWidgetItem(self.task_tree)
            item.setText(0, f"🔄 {rt.title}")
            item.setText(1, rt.remind_time.strftime("%H:%M"))
            item.setText(2, "激活" if rt.is_active else "停用")
            item.setData(0, Qt.UserRole, ("recurring", rt.id))

    def load_permanent_tasks(self):
        """加载常驻任务到固定区域"""
        self.permanent_tree.clear()
        tasks = self.permanent_task_service.get_all_tasks()

        # 按创建时间排序,最新的在前
        tasks_sorted = sorted(tasks, key=lambda t: t.created_at, reverse=True)

        # 直接显示所有常驻任务,不分组
        for task in tasks_sorted:
            item = QTreeWidgetItem(self.permanent_tree)
            item.setText(0, task.title)
            item.setData(0, Qt.UserRole, ("permanent", task.id))

    def _status_text(self, status: TaskStatus) -> str:
        """状态文本"""
        return {0: "未完成", 1: "已完成"}.get(status.value, "未完成")

    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.task_tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)

        if data[0] == "task":
            complete_action = QAction("✅ 标记完成", self)
            complete_action.triggered.connect(lambda: self.mark_task_complete(data[1]))
            menu.addAction(complete_action)

            edit_action = QAction("✏️ 编辑", self)
            edit_action.triggered.connect(lambda: self.edit_task(data[1]))
            menu.addAction(edit_action)

            delete_action = QAction("🗑️ 删除", self)
            delete_action.triggered.connect(lambda: self.delete_task(data[1]))
            menu.addAction(delete_action)

        elif data[0] == "permanent":
            edit_action = QAction("✏️ 编辑", self)
            edit_action.triggered.connect(lambda: self.edit_permanent_task(data[1]))
            menu.addAction(edit_action)

            delete_action = QAction("🗑️ 删除", self)
            delete_action.triggered.connect(lambda: self.delete_permanent_task(data[1]))
            menu.addAction(delete_action)

        menu.exec(self.task_tree.viewport().mapToGlobal(pos))

    def on_item_double_clicked(self, item, column):
        """双击任务项"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type, item_id = data
        if item_type == "task":
            self.edit_task(item_id)
        elif item_type == "recurring":
            self.edit_recurring_task(item_id)
        elif item_type == "permanent":
            self.edit_permanent_task(item_id)

    def mark_task_complete(self, task_id: int):
        """标记任务完成"""
        # 标记完成
        self.task_service.mark_complete(task_id)

        self.load_tasks()
        self.statusBar().showMessage("任务已完成")

    def edit_task(self, task_id: int):
        """编辑任务"""
        from .task_dialog import TaskDialog
        task = self.task_service.get_task(task_id)
        if task:
            dialog = TaskDialog(self, task)
            if dialog.exec():
                self.task_service.update_task(dialog.get_task())
                self.load_tasks()
                self.statusBar().showMessage("任务已更新")

    def delete_task(self, task_id: int):
        """删除任务"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "确认删除", "确定要删除此任务吗？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.task_service.delete_task(task_id)
            self.load_tasks()
            self.statusBar().showMessage("任务已删除")

    def on_add_task(self):
        """添加任务"""
        from .task_dialog import TaskDialog
        dialog = TaskDialog(self)
        if dialog.exec():
            self.task_service.create_task(dialog.get_task())
            self.load_tasks()
            self.statusBar().showMessage("任务已创建")

    def on_add_recurring_task(self):
        """添加循环任务"""
        from .recurring_dialog import RecurringTaskDialog
        dialog = RecurringTaskDialog(self)
        if dialog.exec():
            self.recurring_service.create_recurring_task(dialog.get_recurring_task())
            self.load_tasks()
            self.statusBar().showMessage("循环任务已创建")

    def on_add_permanent_task(self):
        """添加常驻任务"""
        from .permanent_task_dialog import PermanentTaskDialog
        dialog = PermanentTaskDialog(self)
        if dialog.exec():
            self.permanent_task_service.create_task(dialog.get_task())
            self.load_tasks()
            self.statusBar().showMessage("常驻任务已创建")

    def edit_permanent_task(self, task_id: int):
        """编辑常驻任务"""
        from .permanent_task_dialog import PermanentTaskDialog
        task = self.permanent_task_service.get_task(task_id)
        if task:
            dialog = PermanentTaskDialog(self, task)
            if dialog.exec():
                self.permanent_task_service.update_task(dialog.get_task())
                self.load_tasks()
                self.statusBar().showMessage("常驻任务已更新")

    def delete_permanent_task(self, task_id: int):
        """删除常驻任务"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "确认删除", "确定要删除此常驻任务吗？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.permanent_task_service.delete_task(task_id)
            self.load_tasks()
            self.statusBar().showMessage("常驻任务已删除")

    def edit_recurring_task(self, recurring_id: int):
        """编辑循环任务"""
        from .recurring_dialog import RecurringTaskDialog
        recurring_task = self.recurring_service.get_recurring_task(recurring_id)
        if recurring_task:
            dialog = RecurringTaskDialog(self, recurring_task)
            if dialog.exec():
                self.recurring_service.update_recurring_task(dialog.get_recurring_task())
                self.load_tasks()
                self.statusBar().showMessage("循环任务已更新")

    def setup_timer(self):
        """设置定时器"""
        # 重置过期任务的提醒标志
        self.reset_expired_reminders()

        # 提醒检查定时器（每10秒）
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.reminder_service.trigger_reminders)
        self.reminder_timer.start(10000)

        # 启动时立即检查一次提醒
        self.reminder_service.trigger_reminders()

    def reset_expired_reminders(self):
        """重置过期任务的提醒标志"""
        from datetime import datetime

        all_tasks = self.task_service.get_all_tasks()
        now = datetime.now()

        for task in all_tasks:
            # 只处理: 有提醒时间、未完成、已提醒、提醒时间已过期的任务
            if (task.remind_time and
                task.status == TaskStatus.TODO and
                task.notified and
                now >= task.remind_time and
                (not task.snooze_until or now >= task.snooze_until)):

                task.notified = False
                self.task_service.update_task(task)

        # 循环任务处理定时器（每小时检查一次）
        self.recurring_timer = QTimer(self)
        self.recurring_timer.timeout.connect(self.recurring_service.process_all_recurring_tasks)
        self.recurring_timer.start(3600000)  # 1小时

        # 启动时立即处理一次
        self.recurring_service.process_all_recurring_tasks()

    def save_splitter_state(self, state: bytes):
        """保存分隔器状态到数据库"""
        from config import DB_PATH
        from database.manager import DatabaseManager
        db = DatabaseManager(DB_PATH)
        # 将 bytes 转为 base64 字符串存储
        import base64
        state_str = base64.b64encode(state).decode('utf-8')
        db.set_setting("splitter_state", state_str)

    def load_splitter_state(self) -> bytes:
        """从数据库加载分隔器状态"""
        from config import DB_PATH
        from database.manager import DatabaseManager
        db = DatabaseManager(DB_PATH)
        state_str = db.get_setting("splitter_state")
        if state_str:
            import base64
            return base64.b64decode(state_str)
        return None
