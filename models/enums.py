"""
枚举类型定义
"""
from enum import IntEnum, Enum


class TaskStatus(IntEnum):
    """任务状态"""
    TODO = 0         # 未完成
    COMPLETED = 1    # 已完成


class RecurType(Enum):
    """循环类型"""
    DAILY = "daily"      # 每天
    WEEKLY = "weekly"    # 每周
    MONTHLY = "monthly"  # 每月
