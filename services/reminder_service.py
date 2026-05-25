from datetime import datetime
from typing import List, Callable
from models import Task
from .task_service import TaskService
from .is_trade_day import is_today_trade_day


class ReminderService:

    def __init__(self, task_service: TaskService):
        self.task_service = task_service
        self.reminder_callback: Callable[[Task], None] = None
        self.processing_tasks = set()

    def set_reminder_callback(self, callback: Callable[[Task], None]):
        self.reminder_callback = callback

    def check_reminders(self) -> List[Task]:
        now = datetime.now()
        tasks_to_remind = []
        for task in self.task_service.get_uncompleted_tasks():
            if not task.remind_time:
                continue
            if task.notified:
                continue
            if task.id in self.processing_tasks:
                continue
            if now >= task.remind_time:
                tasks_to_remind.append(task)
        return tasks_to_remind

    def mark_notified(self, task_id: int):
        """用户完成任务后标记已提醒，释放 processing 锁"""
        self.processing_tasks.discard(task_id)
        task = self.task_service.get_task(task_id)
        if task:
            task.notified = True
            self.task_service.update_task(task)

    def trigger_reminders(self):
        """触发提醒检查（仅交易日），每轮只弹第一个到期任务"""
        if not is_today_trade_day():
            return
        tasks = self.check_reminders()
        if not tasks:
            return
        task = tasks[0]
        self.processing_tasks.add(task.id)
        if self.reminder_callback:
            self.reminder_callback(task)

    def snooze_reminder(self, task_id: int, minutes: int):
        self.processing_tasks.discard(task_id)
        self.task_service.snooze_task(task_id, minutes)
