"""
Eel 版本的任务管理器主入口
"""
import eel
import sys
import atexit
import traceback
from pathlib import Path
from threading import Timer, Thread
import time

from database.manager import DatabaseManager
from services.task_service import TaskService
from services.recurring_service import RecurringTaskService
from services.reminder_service import ReminderService
from services.permanent_task_service import PermanentTaskService
from models.enums import TaskStatus
from config import DB_PATH

# 导入 API 和提醒窗口
from api import exposed_api
from ui.reminder_window import show_reminder_window


class TaskManagerEelApp:
    """任务管理器 Eel 应用主类"""

    def __init__(self):
        # 服务实例
        self.db_manager = None
        self.task_service = None
        self.recurring_service = None
        self.permanent_service = None
        self.reminder_service = None

        # 定时器
        self.recurring_timer = None
        self.reminder_timer = None
        self._services_ready = False

        # 注册应用实例到 API 模块
        exposed_api.set_app_instance(self)

    def _init_services(self):
        """在后台线程中初始化所有服务"""
        start = time.time()

        try:
            print("开始初始化数据库...")
            self.db_manager = DatabaseManager(DB_PATH)
            print(f"数据库路径: {DB_PATH}")
            print(f"数据库初始化完成,耗时: {time.time() - start:.2f}秒")

            print("初始化服务层...")
            self.task_service = TaskService(self.db_manager)
            self.recurring_service = RecurringTaskService(self.db_manager, self.task_service)
            self.permanent_service = PermanentTaskService(self.db_manager)
            self.reminder_service = ReminderService(self.task_service)
            self.reminder_service.set_reminder_callback(self.on_reminder)
            print(f"服务层初始化完成,总耗时: {time.time() - start:.2f}秒")

            self._services_ready = True
            print("所有服务已就绪")

            # 通知前端服务就绪，重试直到成功
            last_error = None
            for _ in range(20):
                time.sleep(0.5)
                try:
                    eel.onServicesReady()
                    print("✓ 已通知前端服务就绪")
                    break
                except Exception as exc:
                    last_error = exc
            else:
                print(f"⚠ 无法通知前端,前端可能尚未加载: {last_error}")

            # 启动定时任务
            self.check_recurring_tasks()
            self.check_reminders()
        except Exception:
            print("服务初始化失败:")
            traceback.print_exc()

    def on_reminder(self, task):
        """提醒回调 - 显示强制提醒窗口"""
        if not self._services_ready:
            return

        print(f"✓ 触发任务提醒: {task.title}")

        # 完成回调：用户已响应，写 notified=True
        def on_complete(task_id):
            self.reminder_service.mark_notified(task_id)
            t = self.task_service.get_task(task_id)
            if t and t.status == TaskStatus.TODO:
                self.task_service.mark_complete(task_id)
                print(f"✓ 任务已标记为完成: {task.title}")
            try:
                eel.reloadTasks()
            except Exception:
                pass

        # 延期回调：snooze_task 内部重置 notified=False 并更新 remind_time，无需额外标记
        def on_snooze(task_id, minutes):
            print(f"[提醒] 用户选择延期{minutes}分钟: {task.title}")
            self.reminder_service.snooze_reminder(task_id, minutes)
            print(f"✓ 提醒已延期{minutes}分钟: {task.title}")
            try:
                eel.reloadTasks()
            except Exception:
                pass

        # on_shown 只做日志，不写 notified；processing_tasks 防同次运行重复弹
        def on_shown():
            print(f"✓ 提醒窗口已显示: {task.title}")

        # 显示提醒窗口
        show_reminder_window(task.id, task.title, on_complete, on_snooze, on_shown)

    def check_recurring_tasks(self):
        """检查并处理循环任务"""
        def process():
            try:
                self.recurring_service.process_all_recurring_tasks()
            except Exception as e:
                print(f"循环任务处理失败: {e}")

        Thread(target=process, daemon=True).start()

        if self.recurring_timer:
            self.recurring_timer.cancel()
        self.recurring_timer = Timer(3600, self.check_recurring_tasks)
        self.recurring_timer.daemon = True
        self.recurring_timer.start()

    def check_reminders(self):
        """检查提醒"""
        def process():
            try:
                self.reminder_service.trigger_reminders()
            except Exception as e:
                print(f"提醒检查失败: {e}")

        Thread(target=process, daemon=True).start()

        if self.reminder_timer:
            self.reminder_timer.cancel()
        self.reminder_timer = Timer(10, self.check_reminders)
        self.reminder_timer.daemon = True
        self.reminder_timer.start()

    def _start_hotkey(self):
        """注册全局快捷键 Ctrl+Alt+1，使用 pynput 低级键盘钩子"""
        from pynput import keyboard

        VK_1 = 49  # 数字键 1 的虚拟键码

        def normalize(key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                return keyboard.Key.ctrl
            if key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
                return keyboard.Key.alt
            if getattr(key, 'vk', None) == VK_1:
                return VK_1
            return key

        combo = {keyboard.Key.ctrl, keyboard.Key.alt, VK_1}
        pressed = set()

        _hotkey_triggered = False

        def _bring_to_front():
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "任务管理器")
            if not hwnd:
                print("[热键] 未找到窗口")
                return
            # 用 keybd_event 模拟按键获取前台权限，再 SetForegroundWindow
            user32.keybd_event(0, 0, 0, 0)
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            print(f"[热键] 窗口已前置 hwnd={hwnd}")

        def _fire_hotkey():
            from api.exposed_api import set_hotkey_pending
            _bring_to_front()
            set_hotkey_pending()
            print("[热键] flag 已设置")

        def on_press(key):
            nonlocal _hotkey_triggered
            pressed.add(normalize(key))
            if combo <= pressed and not _hotkey_triggered:
                _hotkey_triggered = True
                print("[热键] 触发 Ctrl+Alt+1")
                Thread(target=_fire_hotkey, daemon=True).start()

        def on_release(key):
            nonlocal _hotkey_triggered
            nk = normalize(key)
            pressed.discard(nk)
            if nk == VK_1:
                _hotkey_triggered = False

        print("全局快捷键 Ctrl+Alt+1 注册成功")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def init_services_from_frontend(self):
        """由前端调用的初始化方法"""
        if self._services_ready:
            print("服务已初始化,跳过")
            return
        init_thread = Thread(target=self._init_services, daemon=True)
        init_thread.start()
        hotkey_thread = Thread(target=self._start_hotkey, daemon=True)
        hotkey_thread.start()

    def cleanup(self):
        """清理资源"""
        if not hasattr(self, '_cleanup_done'):
            self._cleanup_done = True
            print("正在关闭应用...")
            # 取消定时器
            if self.recurring_timer:
                self.recurring_timer.cancel()
            if self.reminder_timer:
                self.reminder_timer.cancel()
            # 关闭数据库
            if self.db_manager:
                try:
                    self.db_manager.close()
                except:
                    pass
            print("应用已关闭")

    def run(self):
        """启动应用"""
        # 注册退出清理
        atexit.register(self.cleanup)

        # 初始化 Eel（打包后资源在 sys._MEIPASS 下）
        if getattr(sys, 'frozen', False):
            web_dir = Path(sys._MEIPASS) / "ui" / "web"
            # 打包后 eel.js 需从包内复制到 web 目录
            eel_js_src = Path(sys._MEIPASS) / "eel" / "eel.js"
            eel_js_dst = web_dir / "eel.js"
            if eel_js_src.exists() and not eel_js_dst.exists():
                import shutil
                shutil.copy2(eel_js_src, eel_js_dst)
        else:
            web_dir = Path(__file__).parent / "ui" / "web"
        eel.init(str(web_dir))

        print("启动 Eel 应用...")

        # 启动 Eel - 优先使用独立窗口模式
        try:
            # 尝试使用 Chrome 应用模式(独立窗口,无地址栏)
            eel.start(
                'index.html',
                size=(1400, 800),
                mode='chrome',
                cmdline_args=[
                    '--disable-http-cache',
                ],
                host='localhost',
                port=0
            )
        except (SystemExit, KeyboardInterrupt):
            # 正常退出
            pass
        except Exception as e:
            print(f"Chrome 模式启动失败: {e}")
            # 降级到默认浏览器
            try:
                eel.start('index.html', size=(1400, 800))
            except (SystemExit, KeyboardInterrupt):
                pass


def main():
    app = TaskManagerEelApp()
    app.run()


if __name__ == '__main__':
    main()
