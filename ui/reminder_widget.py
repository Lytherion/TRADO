"""
提醒弹窗
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from models import Task


class ReminderWidget(QDialog):
    """提醒弹窗"""

    def __init__(self, task: Task, reminder_service, parent=None):
        super().__init__(parent)
        self.task = task
        self.reminder_service = reminder_service
        self.result_action = None  # "complete", "snooze"

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("🔔 任务提醒")
        self.setModal(True)  # 模态窗口,用户必须处理
        self.resize(450, 250)

        # 强制置顶,始终在最前面,禁止移动窗口
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.MSWindowsFixedSizeDialogHint  # 禁止移动和调整大小
        )

        # 设置样式:醒目的提醒弹窗
        self.setStyleSheet("""
            QDialog {
                background-color: #fff3cd;
                border: 3px solid #ff6b6b;
            }
            QLabel {
                color: #1c1c1e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 小标题
        title_label = QLabel(f"⏰ 任务提醒")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ff6b6b;")
        layout.addWidget(title_label)

        # 任务名称 - 超大醒目
        task_label = QLabel(f"📌 {self.task.title}")
        task_font = QFont()
        task_font.setPointSize(18)
        task_font.setBold(True)
        task_label.setFont(task_font)
        task_label.setWordWrap(True)
        task_label.setStyleSheet("color: #1c1c1e; padding: 10px 0;")
        layout.addWidget(task_label)

        # 描述
        if self.task.description:
            desc_label = QLabel(self.task.description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 时间
        if self.task.due_time:
            time_label = QLabel(f"截止时间: {self.task.due_time.strftime('%Y-%m-%d %H:%M')}")
            layout.addWidget(time_label)

        layout.addStretch()

        # 延迟输入
        snooze_layout = QHBoxLayout()
        snooze_layout.addWidget(QLabel("延迟"))
        self.snooze_spin = QSpinBox()
        self.snooze_spin.setRange(1, 120)
        self.snooze_spin.setValue(10)
        self.snooze_spin.setSuffix(" 分钟")
        snooze_layout.addWidget(self.snooze_spin)
        snooze_layout.addStretch()
        layout.addLayout(snooze_layout)

        # 按钮
        btn_layout = QHBoxLayout()

        self.complete_btn = QPushButton("✅ 标记完成")
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.complete_btn.setAutoDefault(False)  # 禁用默认按钮行为
        self.complete_btn.setDefault(False)  # 禁用回车键触发
        self.complete_btn.clicked.connect(self.on_complete)
        btn_layout.addWidget(self.complete_btn)

        self.snooze_btn = QPushButton("⏰ 延迟提醒")
        self.snooze_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #1c1c1e;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.snooze_btn.setAutoDefault(False)  # 禁用默认按钮行为
        self.snooze_btn.setDefault(False)  # 禁用回车键触发
        self.snooze_btn.clicked.connect(self.on_snooze)
        btn_layout.addWidget(self.snooze_btn)

        layout.addLayout(btn_layout)

    def on_complete(self):
        """标记完成"""
        self.result_action = "complete"
        self.accept()  # 接受对话框

    def on_snooze(self):
        """延迟提醒"""
        self.result_action = "snooze"
        self.snooze_minutes = self.snooze_spin.value()
        self.accept()  # 接受对话框

    def get_action(self):
        """获取用户操作"""
        return self.result_action

    def get_snooze_minutes(self):
        """获取延迟分钟数"""
        return getattr(self, "snooze_minutes", 10)

    def keyPressEvent(self, event):
        """禁用所有键盘操作"""
        # 忽略所有键盘事件,包括回车、ESC等
        event.ignore()
