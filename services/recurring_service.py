from datetime import datetime, date, timedelta
from typing import List
from models import RecurringTask, Task, RecurType, TaskStatus
from database import DatabaseManager
from .task_service import TaskService
from .is_trade_day import is_trade_day


class RecurringTaskService:

    def __init__(self, db: DatabaseManager, task_service: TaskService):
        self.db = db
        self.task_service = task_service

    def create_recurring_task(self, recurring_task: RecurringTask) -> int:
        recurring_task.created_at = datetime.now()
        task_dict = recurring_task.to_dict()
        task_dict.pop("id", None)
        task_id = self.db.insert_recurring_task(task_dict)
        recurring_task.id = task_id
        return task_id

    def update_recurring_task(self, recurring_task: RecurringTask):
        task_dict = recurring_task.to_dict()
        task_dict.pop("id", None)
        self.db.update_recurring_task(recurring_task.id, task_dict)

    def delete_recurring_task(self, task_id: int):
        self.db.delete_recurring_task(task_id)

    def get_recurring_task(self, task_id: int) -> RecurringTask:
        data = self.db.get_recurring_task(task_id)
        return RecurringTask.from_dict(data) if data else None

    def get_all_recurring_tasks(self) -> List[RecurringTask]:
        return [RecurringTask.from_dict(d) for d in self.db.get_all_recurring_tasks()]

    def should_generate_today(self, recurring_task: RecurringTask, target_date: date) -> bool:
        if recurring_task.recur_end_date and target_date > recurring_task.recur_end_date:
            return False
        if recurring_task.last_generated_date and recurring_task.last_generated_date >= target_date:
            return False

        date_str = target_date.strftime('%Y-%m-%d')
        if not is_trade_day(date_str):
            return False

        if recurring_task.recur_type == RecurType.daily:
            return True
        elif recurring_task.recur_type == RecurType.weekly:
            return target_date.weekday() in recurring_task.recur_days
        elif recurring_task.recur_type == RecurType.monthly:
            return bool(recurring_task.recur_days) and target_date.day in recurring_task.recur_days

        return False

    def _get_instances(self, recurring_task: RecurringTask) -> List[Task]:
        return [
            t for t in self.task_service.get_all_tasks()
            if t.recurring_id == recurring_task.id
        ]

    def cleanup_old_instances(self, recurring_task: RecurringTask):
        """生成新实例前调用：删除该循环任务的所有未完成旧实例。
        已完成的实例保留作为历史记录。
        """
        for task in self._get_instances(recurring_task):
            if task.status != TaskStatus.COMPLETED:
                self.task_service.delete_task(task.id)

    def generate_instance(self, recurring_task: RecurringTask, target_date: date) -> int:
        remind_datetime = datetime.combine(target_date, recurring_task.remind_time)
        task = Task(
            title=recurring_task.title,
            description=recurring_task.description,
            remind_time=remind_datetime,
            status=TaskStatus.TODO,
            tags=recurring_task.tags,
            recurring_id=recurring_task.id,
        )
        task_id = self.task_service.create_task(task)
        recurring_task.last_generated_date = target_date
        self.update_recurring_task(recurring_task)
        return task_id

    def process_all_recurring_tasks(self):
        today = date.today()
        for rt in self.get_all_recurring_tasks():
            if not rt.is_active:
                continue
            if self.should_generate_today(rt, today):
                # 生成新实例前先清理旧的未完成实例，避免双实例并存
                self.cleanup_old_instances(rt)
                self.generate_instance(rt, today)
