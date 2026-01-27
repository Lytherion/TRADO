"""
暴露给前端的 API 函数 - 使用 @eel.expose 装饰
"""
import eel
from datetime import datetime, time as dt_time
from models.enums import TaskStatus, RecurType
from models.task import Task
from models.recurring_task import RecurringTask
from models.permanent_task import PermanentTask
from .converters import task_to_dict, recurring_task_to_dict, permanent_task_to_dict


# 全局应用实例引用
_app = None


def set_app_instance(app):
    """设置应用实例引用"""
    global _app
    _app = app


def _check_ready():
    """检查服务是否就绪"""
    if not _app or not _app._services_ready:
        return False
    return True


# ========== 任务管理 API (7 个) ==========
@eel.expose
def get_all_tasks():
    if not _check_ready():
        return []
    tasks = _app.task_service.get_all_tasks()
    return [task_to_dict(t) for t in tasks]


@eel.expose
def get_today_tasks():
    if not _check_ready():
        return []
    tasks = _app.task_service.get_uncompleted_tasks()
    today = datetime.now().date()
    today_tasks = [t for t in tasks if t.due_time and t.due_time.date() == today]
    return [task_to_dict(t) for t in today_tasks]


@eel.expose
def get_task(task_id):
    if not _check_ready():
        return None
    task = _app.task_service.get_task(task_id)
    return task_to_dict(task) if task else None


@eel.expose
def create_task(task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    task = Task(
        title=task_data['title'],
        description=task_data.get('description', ''),
        due_time=datetime.fromisoformat(task_data['due_time']) if task_data.get('due_time') else None,
        remind_time=datetime.fromisoformat(task_data['remind_time']) if task_data.get('remind_time') else None,
        tags=task_data.get('tags', []),
        status=TaskStatus.TODO
    )
    task_id = _app.task_service.create_task(task)
    return {'success': task_id > 0, 'task_id': task_id, 'message': '任务创建成功' if task_id > 0 else '任务创建失败'}


@eel.expose
def update_task(task_id, task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    task = Task(
        id=task_id,
        title=task_data['title'],
        description=task_data.get('description', ''),
        due_time=datetime.fromisoformat(task_data['due_time']) if task_data.get('due_time') else None,
        remind_time=datetime.fromisoformat(task_data['remind_time']) if task_data.get('remind_time') else None,
        tags=task_data.get('tags', []),
        status=TaskStatus(task_data.get('status', 0))
    )
    _app.task_service.update_task(task)
    return {'success': True, 'message': '任务更新成功'}


@eel.expose
def delete_task(task_id):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    _app.task_service.delete_task(task_id)
    return {'success': True, 'message': '任务删除成功'}


@eel.expose
def toggle_task_status(task_id):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    task = _app.task_service.get_task(task_id)
    if not task:
        return {'success': False, 'message': '任务不存在'}

    if task.status == TaskStatus.TODO:
        _app.task_service.mark_complete(task_id)
    else:
        task.status = TaskStatus.TODO
        task.completed_at = None
        _app.task_service.update_task(task)

    return {'success': True}


# ========== 循环任务 API (4 个) ==========
@eel.expose
def get_all_recurring_tasks():
    if not _check_ready():
        return []
    tasks = _app.recurring_service.get_all_recurring_tasks()
    return [recurring_task_to_dict(t) for t in tasks]


@eel.expose
def create_recurring_task(task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}

    # 解析时间字符串
    remind_time = None
    if task_data.get('remind_time'):
        try:
            remind_time = dt_time.fromisoformat(task_data['remind_time'])
        except:
            # 兼容旧格式
            remind_time = datetime.strptime(task_data['remind_time'], '%H:%M:%S').time()

    # 解析循环类型 (前端传的是小写值,直接使用)
    recur_type = RecurType[task_data['recur_type']]

    task = RecurringTask(
        title=task_data['title'],
        description=task_data.get('description', ''),
        remind_time=remind_time,
        recur_type=recur_type,
        recur_days=task_data.get('recur_days', []),
        recur_end_date=datetime.fromisoformat(task_data['end_date']).date() if task_data.get('end_date') else None,
        tags=task_data.get('tags', [])
    )
    result = _app.recurring_service.create_recurring_task(task)
    return {'success': result > 0, 'message': '循环任务创建成功' if result > 0 else '循环任务创建失败'}


@eel.expose
def update_recurring_task(task_id, task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}

    # 解析时间字符串
    remind_time = None
    if task_data.get('remind_time'):
        try:
            remind_time = dt_time.fromisoformat(task_data['remind_time'])
        except:
            # 兼容旧格式
            remind_time = datetime.strptime(task_data['remind_time'], '%H:%M:%S').time()

    # 解析循环类型 (前端传的是小写值,直接使用)
    recur_type = RecurType[task_data['recur_type']]

    task = RecurringTask(
        id=task_id,
        title=task_data['title'],
        description=task_data.get('description', ''),
        remind_time=remind_time,
        recur_type=recur_type,
        recur_days=task_data.get('recur_days', []),
        recur_end_date=datetime.fromisoformat(task_data['end_date']).date() if task_data.get('end_date') else None,
        tags=task_data.get('tags', [])
    )
    _app.recurring_service.update_recurring_task(task)
    return {'success': True, 'message': '循环任务更新成功'}


@eel.expose
def delete_recurring_task(task_id):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    _app.recurring_service.delete_recurring_task(task_id)
    return {'success': True, 'message': '循环任务删除成功'}


# ========== 常驻任务 API (4 个) ==========
@eel.expose
def get_all_permanent_tasks():
    if not _check_ready():
        return []
    tasks = _app.permanent_service.get_all_tasks()
    return [permanent_task_to_dict(t) for t in tasks]


@eel.expose
def create_permanent_task(task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    task = PermanentTask(
        title=task_data['title'],
        description=task_data.get('description', ''),
        tags=task_data.get('tags', '')
    )
    result = _app.permanent_service.create_task(task)
    return {'success': result > 0, 'message': '常驻任务创建成功' if result > 0 else '常驻任务创建失败'}


@eel.expose
def update_permanent_task(task_id, task_data):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    task = PermanentTask(
        id=task_id,
        title=task_data['title'],
        description=task_data.get('description', ''),
        tags=task_data.get('tags', '')
    )
    _app.permanent_service.update_task(task)
    return {'success': True, 'message': '常驻任务更新成功'}


@eel.expose
def delete_permanent_task(task_id):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    _app.permanent_service.delete_task(task_id)
    return {'success': True, 'message': '常驻任务删除成功'}


# ========== 提醒功能 API (2 个) ==========
@eel.expose
def snooze_reminder(task_id, minutes):
    if not _check_ready():
        return {'success': False, 'message': '服务未就绪'}
    _app.reminder_service.snooze_reminder(task_id, minutes)
    return {'success': True}


@eel.expose
def dismiss_reminder():
    return {'success': True}


# ========== 前端通知 API ==========
@eel.expose
def notify_frontend_ready():
    """前端加载完成后调用此方法,触发后端服务初始化"""
    print("✓ 前端已就绪,开始初始化服务")
    if _app:
        _app.init_services_from_frontend()
    return {'success': True}
