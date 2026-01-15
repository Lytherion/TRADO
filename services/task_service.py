"""
任务服务
"""
from datetime import datetime
from typing import List, Optional
from models import Task, TaskStatus
from database import DatabaseManager


class TaskService:
    """任务服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, task: Task) -> int:
        """创建任务"""
        task.created_at = datetime.now()
        task_dict = task.to_dict()
        task_dict.pop("id", None)  # 移除id字段
        task_id = self.db.insert_task(task_dict)
        task.id = task_id
        return task_id

    def update_task(self, task: Task):
        """更新任务"""
        # 检查是否修改了提醒时间
        old_task = self.get_task(task.id)
        if old_task and old_task.remind_time != task.remind_time:
            # 提醒时间改变时重置已提醒标志
            task.notified = False

        task.updated_at = datetime.now()
        task_dict = task.to_dict()
        task_dict.pop("id", None)
        self.db.update_task(task.id, task_dict)

    def delete_task(self, task_id: int):
        """删除任务"""
        self.db.delete_task(task_id)

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        data = self.db.get_task(task_id)
        return Task.from_dict(data) if data else None

    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """获取所有任务"""
        filters = {}
        if status is not None:
            filters["status"] = status.value

        data_list = self.db.get_all_tasks(filters)
        return [Task.from_dict(data) for data in data_list]

    def get_uncompleted_tasks(self) -> List[Task]:
        """获取未完成的任务(待办+进行中)"""
        data_list = self.db.get_uncompleted_tasks()
        return [Task.from_dict(data) for data in data_list]

    def get_today_tasks(self) -> List[Task]:
        """获取今日任务(包括已完成和未完成)"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)

        all_tasks = self.get_all_tasks()
        return [
            t for t in all_tasks
            if t.due_time and today_start <= t.due_time <= today_end
        ]

    def mark_complete(self, task_id: int):
        """标记任务完成"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self.update_task(task)

    def snooze_task(self, task_id: int, minutes: int):
        """延迟任务提醒"""
        task = self.get_task(task_id)
        if task and task.remind_time:
            from datetime import timedelta
            new_time = datetime.now() + timedelta(minutes=minutes)
            task.snooze_until = new_time
            task.remind_time = new_time
            task.due_time = new_time  # 截止时间也同步延迟
            task.notified = False
            self.update_task(task)
