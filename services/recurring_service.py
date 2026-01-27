"""
循环任务服务
"""
from datetime import datetime, date, time, timedelta
from typing import List
from models import RecurringTask, Task, RecurType, TaskStatus
from database import DatabaseManager
from .task_service import TaskService


class RecurringTaskService:
    """循环任务服务"""

    def __init__(self, db: DatabaseManager, task_service: TaskService):
        self.db = db
        self.task_service = task_service

    def create_recurring_task(self, recurring_task: RecurringTask) -> int:
        """创建循环任务"""
        recurring_task.created_at = datetime.now()
        task_dict = recurring_task.to_dict()
        task_dict.pop("id", None)
        task_id = self.db.insert_recurring_task(task_dict)
        recurring_task.id = task_id
        return task_id

    def update_recurring_task(self, recurring_task: RecurringTask):
        """更新循环任务"""
        task_dict = recurring_task.to_dict()
        task_dict.pop("id", None)
        self.db.update_recurring_task(recurring_task.id, task_dict)

    def delete_recurring_task(self, task_id: int):
        """删除循环任务（级联删除所有实例）"""
        self.db.delete_recurring_task(task_id)

    def get_recurring_task(self, task_id: int) -> RecurringTask:
        """获取循环任务"""
        data = self.db.get_recurring_task(task_id)
        return RecurringTask.from_dict(data) if data else None

    def get_all_recurring_tasks(self) -> List[RecurringTask]:
        """获取所有循环任务"""
        data_list = self.db.get_all_recurring_tasks()
        return [RecurringTask.from_dict(data) for data in data_list]

    def should_generate_today(self, recurring_task: RecurringTask, target_date: date) -> bool:
        """判断是否应该为目标日期生成实例"""
        # 检查是否已过结束日期
        if recurring_task.recur_end_date and target_date > recurring_task.recur_end_date:
            return False

        # 检查是否已生成
        if recurring_task.last_generated_date and recurring_task.last_generated_date >= target_date:
            return False

        # 根据循环类型判断
        if recurring_task.recur_type == RecurType.daily:
            return True
        elif recurring_task.recur_type == RecurType.weekly:
            weekday = target_date.weekday()  # 0-6
            return weekday in recurring_task.recur_days
        elif recurring_task.recur_type == RecurType.monthly:
            # 每月的相同日期
            return True

        return False

    def generate_instance(self, recurring_task: RecurringTask, target_date: date) -> int:
        """为目标日期生成任务实例"""
        # 创建任务实例
        remind_datetime = datetime.combine(target_date, recurring_task.remind_time)

        task = Task(
            title=recurring_task.title,
            description=recurring_task.description,
            due_time=remind_datetime,
            remind_time=remind_datetime,
            status=TaskStatus.TODO,
            tags=recurring_task.tags,
            recurring_id=recurring_task.id,
        )

        task_id = self.task_service.create_task(task)

        # 更新循环任务的生成日期
        recurring_task.last_generated_date = target_date
        self.update_recurring_task(recurring_task)

        return task_id

    def cleanup_old_instances(self, recurring_task: RecurringTask):
        """清理过期的任务实例"""
        today = date.today()

        # 获取该循环任务的所有实例
        all_tasks = self.task_service.get_all_tasks()
        for task in all_tasks:
            if task.recurring_id == recurring_task.id:
                # 删除昨天及之前的实例
                if task.due_time and task.due_time.date() < today:
                    self.task_service.delete_task(task.id)

    def process_all_recurring_tasks(self):
        """处理所有循环任务（生成今日实例，清理旧实例）"""
        today = date.today()
        recurring_tasks = self.get_all_recurring_tasks()

        for rt in recurring_tasks:
            if not rt.is_active:
                continue

            # 清理昨日实例
            self.cleanup_old_instances(rt)

            # 生成今日实例
            if self.should_generate_today(rt, today):
                self.generate_instance(rt, today)
