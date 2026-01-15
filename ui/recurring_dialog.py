"""
循环任务对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QTimeEdit, QComboBox,
    QPushButton, QDateEdit, QCheckBox, QWidget, QLabel
)
from PySide6.QtCore import QTime, QDate
from datetime import time, date
from models import RecurringTask, RecurType


class RecurringTaskDialog(QDialog):
    """循环任务对话框"""

    def __init__(self, parent=None, recurring_task: RecurringTask = None):
        super().__init__(parent)
        self.recurring_task = recurring_task or RecurringTask()
        self.is_edit = recurring_task is not None

        self.init_ui()
        if self.is_edit:
            self.load_task_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑循环任务" if self.is_edit else "新建循环任务")
        self.resize(500, 450)

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
        self.desc_edit.setMaximumHeight(60)
        form_layout.addRow("描述:", self.desc_edit)

        # 提醒时间
        self.remind_time_edit = QTimeEdit()
        self.remind_time_edit.setTime(QTime(9, 0))
        form_layout.addRow("每日提醒时间*:", self.remind_time_edit)

        # 循环类型
        self.recur_type_combo = QComboBox()
        self.recur_type_combo.addItems(["每天", "每周", "每月"])
        self.recur_type_combo.currentIndexChanged.connect(self.on_recur_type_changed)
        form_layout.addRow("循环类型*:", self.recur_type_combo)

        # 每周的哪几天（仅每周时显示）
        self.weekdays_widget = QWidget()
        weekdays_layout = QHBoxLayout(self.weekdays_widget)
        weekdays_layout.setContentsMargins(0, 0, 0, 0)

        self.weekday_checks = []
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for name in weekday_names:
            cb = QCheckBox(name)
            self.weekday_checks.append(cb)
            weekdays_layout.addWidget(cb)

        form_layout.addRow("重复日期:", self.weekdays_widget)
        self.weekdays_widget.setVisible(False)

        # 结束日期
        self.has_end_date = QCheckBox("设置结束日期")
        self.has_end_date.stateChanged.connect(self.on_has_end_date_changed)
        form_layout.addRow("", self.has_end_date)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addMonths(1))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setEnabled(False)
        form_layout.addRow("结束日期:", self.end_date_edit)

        # 标签
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("输入标签，用逗号分隔")
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

    def on_recur_type_changed(self, index):
        """循环类型改变"""
        self.weekdays_widget.setVisible(index == 1)  # 每周

    def on_has_end_date_changed(self, state):
        """是否设置结束日期"""
        self.end_date_edit.setEnabled(state == 2)

    def load_task_data(self):
        """加载任务数据到表单"""
        self.title_edit.setText(self.recurring_task.title)
        self.desc_edit.setPlainText(self.recurring_task.description)
        self.remind_time_edit.setTime(QTime(self.recurring_task.remind_time))

        # 循环类型
        type_map = {RecurType.DAILY: 0, RecurType.WEEKLY: 1, RecurType.MONTHLY: 2}
        self.recur_type_combo.setCurrentIndex(type_map.get(self.recurring_task.recur_type, 0))

        # 每周的日期
        if self.recurring_task.recur_days:
            for day in self.recurring_task.recur_days:
                if 0 <= day < 7:
                    self.weekday_checks[day].setChecked(True)

        # 结束日期
        if self.recurring_task.recur_end_date:
            self.has_end_date.setChecked(True)
            self.end_date_edit.setDate(QDate(self.recurring_task.recur_end_date))

        # 标签
        if self.recurring_task.tags:
            self.tags_edit.setText(",".join(self.recurring_task.tags))

    def on_save(self):
        """保存任务"""
        # 验证
        if not self.title_edit.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "请输入任务标题！")
            return

        # 更新任务对象
        self.recurring_task.title = self.title_edit.text().strip()
        self.recurring_task.description = self.desc_edit.toPlainText().strip()
        self.recurring_task.remind_time = self.remind_time_edit.time().toPython()

        # 循环类型
        type_map = [RecurType.DAILY, RecurType.WEEKLY, RecurType.MONTHLY]
        self.recurring_task.recur_type = type_map[self.recur_type_combo.currentIndex()]

        # 每周的日期
        if self.recurring_task.recur_type == RecurType.WEEKLY:
            self.recurring_task.recur_days = [
                i for i, cb in enumerate(self.weekday_checks) if cb.isChecked()
            ]
            if not self.recurring_task.recur_days:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", "请至少选择一天！")
                return

        # 结束日期
        if self.has_end_date.isChecked():
            self.recurring_task.recur_end_date = self.end_date_edit.date().toPython()
        else:
            self.recurring_task.recur_end_date = None

        # 标签
        tags_text = self.tags_edit.text().strip()
        self.recurring_task.tags = [t.strip() for t in tags_text.split(",") if t.strip()]

        self.accept()

    def get_recurring_task(self) -> RecurringTask:
        """获取循环任务对象"""
        return self.recurring_task
