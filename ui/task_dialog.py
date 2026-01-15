"""
任务对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QDateTimeEdit, QComboBox,
    QPushButton, QLabel
)
from PySide6.QtCore import QDateTime
from datetime import datetime, timedelta
from models import Task, TaskStatus


class TaskDialog(QDialog):
    """任务对话框"""

    def __init__(self, parent=None, task: Task = None):
        super().__init__(parent)
        self.task = task or Task()
        self.is_edit = task is not None

        self.init_ui()
        if self.is_edit:
            self.load_task_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑任务" if self.is_edit else "新建任务")
        self.resize(500, 400)
        # 对话框样式: styles.qss -> QDialog (白色背景、圆角)

        layout = QVBoxLayout(self)

        # 表单
        form_layout = QFormLayout()

        # 标题输入框
        # 样式: styles.qss -> QLineEdit (边框、圆角、内边距)
        # 聚焦时: QLineEdit:focus (紫色边框、浅蓝背景)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入任务标题")
        form_layout.addRow("标题*:", self.title_edit)

        # 描述输入框(多行文本)
        # 样式: styles.qss -> QTextEdit (边框、圆角、内边距)
        # 聚焦时: QTextEdit:focus (紫色边框、浅蓝背景)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入任务描述（可选）")
        self.desc_edit.setMaximumHeight(80)
        form_layout.addRow("描述:", self.desc_edit)

        # 开始时间选择器
        # 样式: styles.qss -> QDateTimeEdit (边框、圆角、内边距)
        # 聚焦时: QDateTimeEdit:focus (紫色边框、浅蓝背景)
        # 日历弹窗: QCalendarWidget (白色背景、圆角)
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime())
        self.start_time_edit.setCalendarPopup(True)  # 点击弹出日历
        form_layout.addRow("开始时间:", self.start_time_edit)

        # 截止时间选择器(也是提醒时间)
        # 样式: styles.qss -> QDateTimeEdit (同上)
        self.due_time_edit = QDateTimeEdit()
        self.due_time_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.due_time_edit.setCalendarPopup(True)
        form_layout.addRow("截止时间*:", self.due_time_edit)

        # 状态下拉框（仅编辑时显示）
        # 样式: styles.qss -> QComboBox (边框、圆角、紫色箭头)
        # 下拉列表: QComboBox QAbstractItemView (白色背景、紫色选中项)
        if self.is_edit:
            self.status_combo = QComboBox()
            self.status_combo.addItems(["未完成", "已完成"])
            form_layout.addRow("状态:", self.status_combo)

        # 标签输入框
        # 样式: styles.qss -> QLineEdit (同标题输入框)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("输入标签，用逗号分隔（如：工作,紧急）")
        form_layout.addRow("标签:", self.tags_edit)

        layout.addLayout(form_layout)

        # 按钮
        # 样式: styles.qss -> QPushButton (紫色渐变、白色文字、圆角)
        # 悬停时: QPushButton:hover (颜色变亮)
        # 按下时: QPushButton:pressed (颜色变深、视觉下沉)
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def load_task_data(self):
        """加载任务数据到表单"""
        self.title_edit.setText(self.task.title)
        self.desc_edit.setPlainText(self.task.description)

        if self.task.start_time:
            self.start_time_edit.setDateTime(QDateTime(self.task.start_time))

        if self.task.due_time:
            self.due_time_edit.setDateTime(QDateTime(self.task.due_time))

        if self.is_edit and hasattr(self, "status_combo"):
            self.status_combo.setCurrentIndex(self.task.status.value)

        if self.task.tags:
            self.tags_edit.setText(",".join(self.task.tags))

    def on_save(self):
        """保存任务"""
        # 验证
        if not self.title_edit.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "请输入任务标题！")
            return

        # 更新任务对象
        self.task.title = self.title_edit.text().strip()
        self.task.description = self.desc_edit.toPlainText().strip()
        self.task.start_time = self.start_time_edit.dateTime().toPython()

        # 截止时间和提醒时间相同
        due_time = self.due_time_edit.dateTime().toPython()
        self.task.due_time = due_time
        self.task.remind_time = due_time

        if self.is_edit and hasattr(self, "status_combo"):
            self.task.status = TaskStatus(self.status_combo.currentIndex())

        tags_text = self.tags_edit.text().strip()
        self.task.tags = [t.strip() for t in tags_text.split(",") if t.strip()]

        self.accept()

    def get_task(self) -> Task:
        """获取任务对象"""
        return self.task
