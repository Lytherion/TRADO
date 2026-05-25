"""
提醒服务
"""
from datetime import datetime
from typing import List, Callable
from models import Task
from .task_service import TaskService
from .is_trade_day import is_today_trade_day


class ReminderService:
    """提醒服务"""

    def __init__(self, task_service: TaskService):
        self.task_service = task_service
        self.reminder_callback: Callable[[Task], None] = None
        self.processing_tasks = set()  # 正在处理的任务ID集合

    def set_reminder_callback(self, callback: Callable[[Task], None]):
        """设置提醒回调函数"""
        self.reminder_callback = callback

    def check_reminders(self) -> List[Task]:
        """检查需要提醒的任务"""
        now = datetime.now()
        # 直接从数据库获取未完成的任务(status = 0)
        uncompleted_tasks = self.task_service.get_uncompleted_tasks()

        tasks_to_remind = []
        for task in uncompleted_tasks:
            if not task.remind_time:
                continue

            # 跳过已提醒的任务
            if task.notified:
                continue

            # 跳过正在处理中的任务
            if task.id in self.processing_tasks:
                continue

            # 检查是否延迟中
            if task.snooze_until and now < task.snooze_until:
                continue

            # 检查是否到期
            if now >= task.remind_time:
                tasks_to_remind.append(task)

        return tasks_to_remind

    def trigger_reminders(self):
        """触发提醒检查并执行回调（仅交易日）"""
        if not is_today_trade_day():
            return
        tasks = self.check_reminders()

        for task in tasks:
            # 加入处理中集合,防止重复触发
            self.processing_tasks.add(task.id)

            # 立即标记为已提醒,防止重复弹窗
            task.notified = True
            self.task_service.update_task(task)

            # 触发回调
            if self.reminder_callback:
                self.reminder_callback(task)

            # 从处理集合中移除
            self.processing_tasks.discard(task.id)

    def snooze_reminder(self, task_id: int, minutes: int):
        """延迟提醒"""
        self.task_service.snooze_task(task_id, minutes)
