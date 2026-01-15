"""
常驻任务服务
"""
from datetime import datetime
from typing import List
from models.permanent_task import PermanentTask
from database.manager import DatabaseManager


class PermanentTaskService:
    """常驻任务服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_task(self, task: PermanentTask) -> int:
        """创建常驻任务"""
        task_dict = task.to_dict()
        task_dict.pop("id", None)
        task_id = self.db.insert_permanent_task(task_dict)
        task.id = task_id
        return task_id

    def update_task(self, task: PermanentTask):
        """更新常驻任务"""
        task.updated_at = datetime.now()
        task_dict = task.to_dict()
        task_dict.pop("id", None)
        self.db.update_permanent_task(task.id, task_dict)

    def delete_task(self, task_id: int):
        """删除常驻任务"""
        self.db.delete_permanent_task(task_id)

    def get_task(self, task_id: int) -> PermanentTask:
        """获取单个常驻任务"""
        data = self.db.get_permanent_task(task_id)
        return PermanentTask.from_dict(data) if data else None

    def get_all_tasks(self) -> List[PermanentTask]:
        """获取所有常驻任务"""
        data_list = self.db.get_all_permanent_tasks()
        return [PermanentTask.from_dict(data) for data in data_list]
