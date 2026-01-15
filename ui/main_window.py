"""
主窗口
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
    QSplitter, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
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
                 permanent_task_service: PermanentTaskService,
                 app_instance=None):
        super().__init__()
        self.task_service = task_service
        self.recurring_service = recurring_service
        self.reminder_service = reminder_service
        self.permanent_task_service = permanent_task_service
        self.app_instance = app_instance  # 保存 app 实例用于热重载

        self.current_filter = "all"  # 当前筛选条件

        self.init_ui()
        self.setup_timer()
        self.load_tasks()
        self.setup_shortcuts()  # 设置快捷键

    def init_ui(self):
        """初始化界面"""
        # 设置窗口标题(显示在标题栏)
        self.setWindowTitle("任务管理器")

        # 设置窗口大小(宽1400像素 x 高800像素)
        self.resize(1400, 800)

        # 创建中心容器(QMainWindow必须有一个中心部件)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)  # 将容器设置为窗口的中心区域

        # 创建水平布局(让内部元素从左到右排列)
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器(可拖动的分隔线,用于调整左右区域大小)
        splitter = QSplitter(Qt.Horizontal)  # Qt.Horizontal = 水平分割

        # 左侧边栏(筛选按钮区域)
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)  # 将侧边栏添加到分割器左侧

        # 右侧主视图(任务列表区域)
        main_view = self.create_main_view()
        splitter.addWidget(main_view)  # 将主视图添加到分割器右侧

        # 设置左右区域的初始比例(左:右 = 1:4)
        splitter.setStretchFactor(0, 1)  # 索引0=左侧,占1份
        splitter.setStretchFactor(1, 4)  # 索引1=右侧,占4份

        # 将分割器添加到主布局
        main_layout.addWidget(splitter)

        # 创建菜单栏(文件、视图等菜单)
        self.create_menu_bar()

        # 状态栏(窗口底部显示提示信息的区域)
        self.statusBar().showMessage("就绪")  # 显示初始提示文本

    def create_menu_bar(self):
        """创建菜单栏(窗口顶部的 文件/视图 菜单)"""
        # 获取菜单栏(QMainWindow自带的顶部菜单区域)
        menubar = self.menuBar()

        # 文件菜单(第一个菜单)
        file_menu = menubar.addMenu("文件")  # addMenu = 添加一个下拉菜单

        # 创建"退出"菜单项
        exit_action = QAction("退出", self)  # QAction = 可点击的菜单项
        exit_action.triggered.connect(self.close)  # triggered.connect = 点击时触发,调用self.close()关闭窗口
        file_menu.addAction(exit_action)  # 将菜单项添加到文件菜单

        # 视图菜单(第二个菜单)
        view_menu = menubar.addMenu("视图")

        # 创建"刷新"菜单项
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.load_tasks)  # 点击时调用self.load_tasks()重新加载任务
        view_menu.addAction(refresh_action)

    def create_sidebar(self) -> QWidget:
        """创建左侧边栏(筛选视图切换区域)"""
        # 创建侧边栏容器
        sidebar = QWidget()

        # 创建垂直布局(让内部元素从上到下排列)
        layout = QVBoxLayout(sidebar)

        # 分类标题标签
        # QLabel = 文本标签控件,用于显示不可编辑的文本
        # <b>筛选</b> = HTML标签,让文字加粗
        # 样式: styles.qss -> QLabel (深色文字、透明背景)
        layout.addWidget(QLabel("<b>筛选</b>"))  # addWidget = 将控件添加到布局

        # 分类按钮列表
        # 注意:这些按钮需要设置 objectName="sidebarButton" 才能应用特殊样式
        # 样式: styles.qss -> QPushButton#sidebarButton (透明背景、左对齐)
        # 选中时: QPushButton#sidebarButton:checked (浅蓝背景、左侧紫色边框)
        categories = [
            ("all", "📋 所有任务"),      # key="all", 显示文本="📋 所有任务"
            ("today", "⭐ 今日任务"),    # key="today"
            ("recurring", "🔄 循环任务"), # key="recurring"
        ]

        # 循环创建每个按钮
        for key, label in categories:
            btn = QPushButton(label)  # 创建按钮,显示文本为label

            # clicked.connect = 按钮被点击时触发
            # lambda = 匿名函数,捕获key值传递给filter_tasks
            # checked参数是Qt自动传入的(按钮是否被勾选),这里不用
            btn.clicked.connect(lambda checked, k=key: self.filter_tasks(k))

            layout.addWidget(btn)  # 将按钮添加到布局

        # 添加弹性空间(让上面的按钮靠上,下面留空)
        layout.addStretch()

        return sidebar  # 返回创建好的侧边栏控件

    def create_main_view(self) -> QWidget:
        """创建右侧主视图(任务列表和工具栏区域)"""
        # 创建主视图容器
        main_view = QWidget()

        # 创建垂直布局(工具栏在上,任务列表在下)
        layout = QVBoxLayout(main_view)

        # 工具栏(顶部按钮区域)
        # 样式: styles.qss -> QPushButton (紫色渐变、白色文字、圆角)
        # 悬停时: QPushButton:hover (颜色变亮)
        # 按下时: QPushButton:pressed (颜色变深、视觉下沉)

        # 创建水平布局(让按钮从左到右排列)
        toolbar = QHBoxLayout()

        # 创建"新建任务"按钮
        self.add_task_btn = QPushButton("➕ 新建任务")
        self.add_task_btn.clicked.connect(self.on_add_task)  # 点击时调用on_add_task方法

        # 创建"新建循环任务"按钮
        self.add_recurring_btn = QPushButton("🔄 新建循环任务")
        self.add_recurring_btn.clicked.connect(self.on_add_recurring_task)

        # 创建"新建常驻任务"按钮
        self.add_permanent_btn = QPushButton("📌 新建常驻任务")
        self.add_permanent_btn.clicked.connect(self.on_add_permanent_task)

        # 将三个按钮添加到工具栏
        toolbar.addWidget(self.add_task_btn)
        toolbar.addWidget(self.add_recurring_btn)
        toolbar.addWidget(self.add_permanent_btn)

        # 添加弹性空间(让按钮靠左,右侧留空)
        toolbar.addStretch()

        # 将工具栏添加到主布局(addLayout = 添加一个布局)
        layout.addLayout(toolbar)

        # 左右分栏布局 - 使用可拖动分割器
        # QSplitter = 分割器,可以拖动中间的分隔线调整左右区域大小
        splitter = QSplitter(Qt.Horizontal)  # Horizontal = 水平分割(左右布局)

        # ========== 左侧区域: 常驻任务 ==========
        left_widget = QWidget()  # 创建左侧容器

        # setObjectName = 设置对象名称,用于在 QSS 中通过 #名称 选择
        # 这样可以在 styles.qss 中用 #permanentArea 来设置样式
        left_widget.setObjectName("permanentArea")

        # 创建垂直布局(标题在上,列表在下)
        left_layout = QVBoxLayout(left_widget)

        # setContentsMargins = 设置内边距(上,右,下,左)
        # 让内容距离边框10像素
        # 注意:这个无法在 QSS 中设置,必须在代码中设置
        left_layout.setContentsMargins(10, 10, 10, 10)

        # 常驻任务区域标题
        permanent_label = QLabel("📌 常驻任务")

        # 设置对象名称,方便在 QSS 中设置样式
        permanent_label.setObjectName("permanentLabel")
        left_layout.addWidget(permanent_label)  # 添加到布局

        # ===== 常驻任务列表(树形控件) =====
        # QTreeWidget = 树形列表控件,可以显示分层数据(支持展开/折叠)
        # 样式: styles.qss -> QTreeWidget (白色背景、圆角、无边框)
        # 任务行: QTreeWidget::item (内边距12px 8px、圆角8px、行间距2px)
        # 悬停: QTreeWidget::item:hover (浅灰色背景)
        # 选中: QTreeWidget::item:selected (浅蓝色背景、左侧紫色边框)
        self.permanent_tree = QTreeWidget()

        # setHeaderHidden(True) = 隐藏表头(常驻任务不需要显示"任务/时间/状态"列名)
        self.permanent_tree.setHeaderHidden(True)

        # setRootIsDecorated(False) = 不显示根节点的展开/折叠箭头(因为常驻任务是平铺的)
        self.permanent_tree.setRootIsDecorated(False)

        # 设置对象名称,样式在 styles.qss 中定义
        self.permanent_tree.setObjectName("permanentTree")

        # setContextMenuPolicy = 设置右键菜单策略
        # Qt.CustomContextMenu = 使用自定义右键菜单
        self.permanent_tree.setContextMenuPolicy(Qt.CustomContextMenu)

        # customContextMenuRequested.connect = 右键点击时触发
        # 连接到 show_permanent_context_menu 方法显示菜单
        self.permanent_tree.customContextMenuRequested.connect(self.show_permanent_context_menu)

        # itemDoubleClicked.connect = 双击任务项时触发
        # 连接到 on_item_double_clicked 方法打开编辑对话框
        self.permanent_tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        left_layout.addWidget(self.permanent_tree)  # 将树形控件添加到布局

        # 将左侧区域添加到分割器
        splitter.addWidget(left_widget)

        # ========== 右侧区域: 普通任务列表 ==========
        right_widget = QWidget()  # 创建右侧容器

        # 设置对象名称,样式在 styles.qss 中定义
        right_widget.setObjectName("taskArea")

        # 创建垂直布局
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)  # 10像素内边距(无法在QSS中设置)

        # ===== 普通任务列表(树形控件) - 核心UI =====
        # 这是最重要的控件,显示所有普通任务和循环任务实例
        # 样式: styles.qss -> QTreeWidget (白色背景、圆角、无边框)
        # 表头: QHeaderView::section (浅灰背景、大写字母、底部边框)
        # 任务行: QTreeWidget::item (内边距12px 8px、圆角8px、行间距2px)
        # 悬停: QTreeWidget::item:hover (浅灰色背景 #f7fafc)
        # 选中: QTreeWidget::item:selected (浅蓝色背景 #e6f0ff、左侧紫色边框4px)
        # 滚动条: QScrollBar:vertical (10px宽、透明背景、灰色滑块)
        self.task_tree = QTreeWidget()

        # setHeaderLabels = 设置列名(表头文字)
        # 这个树形控件有3列: 任务标题、时间、状态
        self.task_tree.setHeaderLabels(["任务", "时间", "状态"])

        # setColumnWidth = 设置列宽(像素)
        self.task_tree.setColumnWidth(0, 600)  # 第0列(任务标题)宽600像素
        self.task_tree.setColumnWidth(1, 200)  # 第1列(时间)宽200像素
        self.task_tree.setColumnWidth(2, 120)  # 第2列(状态)宽120像素

        # setRootIsDecorated(True) = 显示展开/折叠箭头
        # 因为普通任务有分组("未完成"/"已完成"),需要展开/折叠
        self.task_tree.setRootIsDecorated(False)

        # 设置对象名称,样式在 styles.qss 中定义
        self.task_tree.setObjectName("taskTree")

        # 启用自定义右键菜单
        self.task_tree.setContextMenuPolicy(Qt.CustomContextMenu)

        # 右键点击时显示菜单
        self.task_tree.customContextMenuRequested.connect(self.show_context_menu)

        # 双击任务时编辑
        self.task_tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 将任务树添加到布局
        right_layout.addWidget(self.task_tree)

        # 将右侧区域添加到分割器
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
            #uncompleted_group.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

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
            #completed_group.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

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
        """显示任务列表右键菜单"""
        item = self.task_tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        # 右键菜单
        # 样式: styles.qss -> QMenu (白色背景、圆角12px、边框)
        # 菜单项: QMenu::item (内边距10px 24px、圆角8px)
        # 选中项: QMenu::item:selected (浅灰背景、紫色文字)
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

        elif data[0] == "recurring":
            edit_action = QAction("✏️ 编辑", self)
            edit_action.triggered.connect(lambda: self.edit_recurring_task(data[1]))
            menu.addAction(edit_action)

            delete_action = QAction("🗑️ 删除", self)
            delete_action.triggered.connect(lambda: self.delete_recurring_task(data[1]))
            menu.addAction(delete_action)

        menu.exec(self.task_tree.viewport().mapToGlobal(pos))

    def show_permanent_context_menu(self, pos):
        """显示常驻任务右键菜单"""
        item = self.permanent_tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)

        edit_action = QAction("✏️ 编辑", self)
        edit_action.triggered.connect(lambda: self.edit_permanent_task(data[1]))
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ 删除", self)
        delete_action.triggered.connect(lambda: self.delete_permanent_task(data[1]))
        menu.addAction(delete_action)

        menu.exec(self.permanent_tree.viewport().mapToGlobal(pos))

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

    def delete_recurring_task(self, recurring_id: int):
        """删除循环任务"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "确认删除", "确定要删除此循环任务吗？\n关联的任务实例也会被删除。",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.recurring_service.delete_recurring_task(recurring_id)
            self.load_tasks()
            self.statusBar().showMessage("循环任务已删除")

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

    def setup_shortcuts(self):
        """设置快捷键"""
        # F5: 重新加载样式表
        reload_style = QShortcut(QKeySequence("F5"), self)
        reload_style.activated.connect(self.reload_stylesheet)

    def reload_stylesheet(self):
        """重新加载样式表(F5)"""
        if self.app_instance:
            self.app_instance.load_stylesheet()
            self.statusBar().showMessage("样式表已重新加载 (F5)", 2000)
