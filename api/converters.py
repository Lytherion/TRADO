"""
数据转换函数 - 将模型对象转换为字典
"""


def task_to_dict(task):
    """普通任务转字典"""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_time': task.due_time.isoformat() if task.due_time else None,
        'remind_time': task.remind_time.isoformat() if task.remind_time else None,
        'status': task.status.value,
        'tags': task.tags,
        'recurring_id': task.recurring_id,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    }


def recurring_task_to_dict(task):
    """循环任务转字典"""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'remind_time': task.remind_time.isoformat() if task.remind_time else None,
        'recur_type': task.recur_type.name,
        'recur_days': task.recur_days,
        'recur_end_date': task.recur_end_date.isoformat() if task.recur_end_date else None,
        'tags': task.tags,
        'is_active': task.is_active,
        'created_at': task.created_at.isoformat() if task.created_at else None
    }


def permanent_task_to_dict(task):
    """常驻任务转字典"""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'tags': task.tags,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'updated_at': task.updated_at.isoformat() if task.updated_at else None
    }
