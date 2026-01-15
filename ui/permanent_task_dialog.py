"""
常驻任务对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton
)
from models.permanent_task import PermanentTask


class PermanentTaskDialog(QDialog):
    """常驻任务对话框"""

    def __init__(self, parent=None, task: PermanentTask = None):
        super().__init__(parent)
        self.task = task or PermanentTask()
        self.is_edit = task is not None

        self.init_ui()
        if self.is_edit:
            self.load_task_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑常驻任务" if self.is_edit else "新建常驻任务")
        self.resize(500, 350)

        layout = QVBoxLayout(self)

        # 表单
        form_layout = QFormLayout()

        # 标题
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入任务标题")
        form_layout.addRow("标题*:", self.title_edit)

        # 描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入任务描述（可选）")
        self.desc_edit.setMaximumHeight(120)
        form_layout.addRow("描述:", self.desc_edit)

        # 标签
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("输入标签,用逗号分隔(如:工作,备忘)")
        form_layout.addRow("标签:", self.tags_edit)

        layout.addLayout(form_layout)

        # 按钮
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
        self.tags_edit.setText(self.task.tags)

    def on_save(self):
        """保存"""
        title = self.title_edit.text().strip()
        if not title:
            return

        self.task.title = title
        self.task.description = self.desc_edit.toPlainText().strip()
        self.task.tags = self.tags_edit.text().strip()

        self.accept()

    def get_task(self) -> PermanentTask:
        """获取任务"""
        return self.task
