from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional
from models import Task, TaskStatus
from database import DatabaseManager


class TaskService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, task: Task) -> int:
        task.created_at = datetime.now()
        task_dict = task.to_dict()
        task_dict.pop("id", None)
        task_id = self.db.insert_task(task_dict)
        task.id = task_id
        return task_id

    def update_task(self, task: Task):
        old_task = self.get_task(task.id)
        if old_task and old_task.remind_time != task.remind_time:
            task.notified = False
        task.updated_at = datetime.now()
        task_dict = task.to_dict()
        task_dict.pop("id", None)
        self.db.update_task(task.id, task_dict)

    def delete_task(self, task_id: int):
        self.db.delete_task(task_id)

    def get_task(self, task_id: int) -> Optional[Task]:
        data = self.db.get_task(task_id)
        return Task.from_dict(data) if data else None

    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        filters = {}
        if status is not None:
            filters["status"] = status.value
        return [Task.from_dict(d) for d in self.db.get_all_tasks(filters)]

    def get_uncompleted_tasks(self) -> List[Task]:
        return [Task.from_dict(d) for d in self.db.get_uncompleted_tasks()]

    def get_today_tasks(self) -> List[Task]:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        return [
            t for t in self.get_all_tasks()
            if t.remind_time and today_start <= t.remind_time <= today_end
        ]

    def mark_complete(self, task_id: int):
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self.update_task(task)

    def snooze_task(self, task_id: int, minutes: int):
        """延后提醒：把 remind_time 往后推，若落在非交易日则顺延到下个交易日同时间。"""
        from .is_trade_day import is_trade_day, next_trade_day
        task = self.get_task(task_id)
        if not task:
            return

        new_time = datetime.now() + timedelta(minutes=minutes)

        # 若落在非交易日，顺延到下个交易日的同一时间
        if not is_trade_day(new_time.strftime("%Y-%m-%d")):
            nd = next_trade_day(new_time.date())
            new_time = datetime.combine(nd, dt_time(new_time.hour, new_time.minute))

        task.remind_time = new_time
        task.notified = False
        self.update_task(task)
