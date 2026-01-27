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
    daily = "daily"      # 每天
    weekly = "weekly"    # 每周
    monthly = "monthly"  # 每月
