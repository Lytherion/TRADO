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
        # 根据是否为编辑模式设置窗口标题
        # if self.is_edit 为True则显示"编辑任务",否则显示"新建任务"
        self.setWindowTitle("编辑任务" if self.is_edit else "新建任务")

        # 设置对话框大小(宽500像素 x 高400像素)
        self.resize(500, 400)
        # 对话框样式: styles.qss -> QDialog (白色背景、圆角)

        # 创建垂直布局(控件从上到下排列)
        # self 表示这个布局属于当前对话框
        layout = QVBoxLayout(self)

        # 创建表单布局(自动排列 标签:输入框 对)
        # QFormLayout = 表单布局,会自动将标签和输入框成对排列
        # 例如: "标题*:" [输入框]
        form_layout = QFormLayout()

        # ===== 标题输入框 =====
        # QLineEdit = 单行文本输入框(只能输入一行)
        # 样式: styles.qss -> QLineEdit (边框、圆角、内边距)
        # 聚焦时: QLineEdit:focus (紫色边框、浅蓝背景)
        self.title_edit = QLineEdit()

        # setPlaceholderText = 设置占位符文本(输入框为空时显示的灰色提示)
        self.title_edit.setPlaceholderText("输入任务标题")

        # addRow = 添加一行(标签, 控件)
        # "标题*:" 是左侧标签(* 表示必填)
        # self.title_edit 是右侧输入框
        form_layout.addRow("标题*:", self.title_edit)

        # ===== 描述输入框(多行文本) =====
        # QTextEdit = 多行文本输入框(可以输入多行,支持换行)
        # 样式: styles.qss -> QTextEdit (边框、圆角、内边距)
        # 聚焦时: QTextEdit:focus (紫色边框、浅蓝背景)
        self.desc_edit = QTextEdit()

        # 设置占位符
        self.desc_edit.setPlaceholderText("输入任务描述（可选）")

        # setMaximumHeight = 设置最大高度(80像素)
        # 防止描述框占用太多空间
        self.desc_edit.setMaximumHeight(80)

        form_layout.addRow("描述:", self.desc_edit)

        # ===== 开始时间选择器 =====
        # QDateTimeEdit = 日期时间选择器(可以选择年月日时分)
        # 样式: styles.qss -> QDateTimeEdit (边框、圆角、内边距)
        # 聚焦时: QDateTimeEdit:focus (紫色边框、浅蓝背景)
        # 日历弹窗: QCalendarWidget (白色背景、圆角)
        self.start_time_edit = QDateTimeEdit()

        # setDateTime = 设置初始日期时间
        # QDateTime.currentDateTime() = 获取当前系统日期时间
        self.start_time_edit.setDateTime(QDateTime.currentDateTime())

        # setCalendarPopup(True) = 点击输入框时弹出日历面板
        # 可以直接在日历上点选日期,更方便
        self.start_time_edit.setCalendarPopup(True)

        form_layout.addRow("开始时间:", self.start_time_edit)

        # ===== 截止时间选择器(也是提醒时间) =====
        # 样式: styles.qss -> QDateTimeEdit (同上)
        self.due_time_edit = QDateTimeEdit()

        # addDays(1) = 在当前时间基础上加1天
        # 默认截止时间为明天
        self.due_time_edit.setDateTime(QDateTime.currentDateTime().addDays(1))

        self.due_time_edit.setCalendarPopup(True)  # 启用日历弹窗
        form_layout.addRow("截止时间*:", self.due_time_edit)

        # ===== 状态下拉框(仅编辑任务时显示) =====
        # QComboBox = 下拉选择框(类似 HTML 的 <select>)
        # 样式: styles.qss -> QComboBox (边框、圆角、紫色箭头)
        # 下拉列表: QComboBox QAbstractItemView (白色背景、紫色选中项)
        if self.is_edit:  # 只有编辑模式才显示状态选择
            self.status_combo = QComboBox()

            # addItems = 添加多个选项(列表)
            # 索引0="未完成", 索引1="已完成"
            self.status_combo.addItems(["未完成", "已完成"])

            form_layout.addRow("状态:", self.status_combo)

        # ===== 标签输入框 =====
        # 样式: styles.qss -> QLineEdit (同标题输入框)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("输入标签，用逗号分隔（如：工作,紧急）")
        form_layout.addRow("标签:", self.tags_edit)

        # 将表单布局添加到主布局
        # addLayout = 添加一个布局(不是控件)
        layout.addLayout(form_layout)

        # ===== 底部按钮区域 =====
        # 样式: styles.qss -> QPushButton (紫色渐变、白色文字、圆角)
        # 悬停时: QPushButton:hover (颜色变亮)
        # 按下时: QPushButton:pressed (颜色变深、视觉下沉)

        # 创建水平布局(按钮从左到右排列)
        btn_layout = QHBoxLayout()

        # 创建"保存"按钮
        self.save_btn = QPushButton("保存")

        # clicked.connect = 点击按钮时触发
        # self.on_save = 调用保存方法
        self.save_btn.clicked.connect(self.on_save)

        # 创建"取消"按钮
        self.cancel_btn = QPushButton("取消")

        # self.reject = Qt对话框的内置方法,关闭对话框并返回False
        self.cancel_btn.clicked.connect(self.reject)

        # 添加弹性空间(让按钮靠右)
        btn_layout.addStretch()

        # 添加两个按钮
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        # 将按钮布局添加到主布局
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
