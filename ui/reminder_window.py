"""
强制提醒窗口模块 - 使用 Tkinter 创建置顶提醒
"""
import sys
from threading import Thread


def show_reminder_window(task_id, task_title, on_complete_callback, on_snooze_callback):
    """
    显示强制置顶的提醒窗口

    Args:
        task_id: 任务ID
        task_title: 任务标题
        on_complete_callback: 完成回调函数 callback(task_id)
        on_snooze_callback: 延期回调函数 callback(task_id, minutes)
    """
    if sys.platform != 'win32':
        return

    def show_dialog():
        try:
            import tkinter as tk
            from tkinter import ttk

            # 创建置顶窗口
            root = tk.Tk()
            root.withdraw()  # 先隐藏,设置好后再显示,避免闪烁
            root.title("任务提醒")
            root.resizable(False, False)

            # 移除窗口装饰(无边框)
            root.overrideredirect(True)

            # 强制置顶设置
            root.attributes('-topmost', True)
            root.attributes('-toolwindow', True)

            # 禁用键盘操作
            root.bind('<Key>', lambda _: 'break')

            # 先更新窗口以获取正确的屏幕尺寸
            root.update_idletasks()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()

            # 设置窗口大小和居中位置
            window_width = 480
            window_height = 260
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            root.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # 主框架 - 添加边框
            main_frame = tk.Frame(root, bg='#2c3e50', bd=2, relief=tk.RAISED)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 内容框架
            content_frame = tk.Frame(main_frame, bg='#ecf0f1', padx=20, pady=15)
            content_frame.pack(fill=tk.BOTH, expand=True)

            # 标题栏
            title_bar = tk.Frame(content_frame, bg='#34495e', height=40)
            title_bar.pack(fill=tk.X, pady=(0, 15))
            title_bar.pack_propagate(False)

            title_label = tk.Label(
                title_bar,
                text="⏰ 任务提醒",
                font=('Microsoft YaHei', 13, 'bold'),
                bg='#34495e',
                fg='white',
                anchor=tk.W,
                padx=15
            )
            title_label.pack(fill=tk.BOTH, expand=True)

            # 任务内容区域
            task_label = tk.Label(
                content_frame,
                text=task_title,
                font=('Microsoft YaHei', 11),
                bg='#ecf0f1',
                fg='#2c3e50',
                wraplength=420,
                justify=tk.LEFT,
                anchor=tk.W
            )
            task_label.pack(fill=tk.X, pady=(0, 15))

            # 延期时间选择区域
            snooze_frame = tk.Frame(content_frame, bg='#ecf0f1')
            snooze_frame.pack(fill=tk.X, pady=(0, 15))

            snooze_label = tk.Label(
                snooze_frame,
                text="延期时间:",
                font=('Microsoft YaHei', 10),
                bg='#ecf0f1',
                fg='#34495e'
            )
            snooze_label.pack(side=tk.LEFT, padx=(0, 8))

            # 延期时间输入框
            snooze_var = tk.StringVar(root)
            snooze_entry = tk.Entry(
                snooze_frame,
                textvariable=snooze_var,
                font=('Microsoft YaHei', 10),
                width=8,
                justify=tk.CENTER,
                bg='white',
                fg='#2c3e50',
                relief=tk.SOLID,
                bd=1
            )
            snooze_entry.pack(side=tk.LEFT, padx=(0, 5))
            snooze_var.set("9")  # 延后设置默认值

            # 时间单位下拉框
            unit_var = tk.StringVar(root)
            unit_combo = ttk.Combobox(
                snooze_frame,
                textvariable=unit_var,
                values=["分钟", "小时"],
                font=('Microsoft YaHei', 10),
                width=6,
                state='readonly'
            )
            unit_combo.pack(side=tk.LEFT, padx=(0, 10))
            unit_var.set("分钟")  # 延后设置默认值

            # 快捷选项
            quick_frame = tk.Frame(snooze_frame, bg='#ecf0f1')
            quick_frame.pack(side=tk.LEFT)

            quick_options = [
                ("5分钟", 5, "分钟"),
                ("10分钟", 10, "分钟"),
                ("30分钟", 30, "分钟"),
                ("1小时", 1, "小时")
            ]

            def set_quick_time(value, unit):
                snooze_var.set(str(value))
                unit_var.set(unit)

            for label, value, unit in quick_options:
                btn = tk.Label(
                    quick_frame,
                    text=label,
                    font=('Microsoft YaHei', 9),
                    bg='#bdc3c7',
                    fg='#2c3e50',
                    cursor='hand2',
                    padx=6,
                    pady=2,
                    relief=tk.RAISED,
                    bd=1
                )
                btn.pack(side=tk.LEFT, padx=2)
                btn.bind('<Button-1>', lambda e, v=value, u=unit: set_quick_time(v, u))
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#95a5a6'))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#bdc3c7'))

            # 按钮区域
            button_frame = tk.Frame(content_frame, bg='#ecf0f1')
            button_frame.pack(fill=tk.X)

            # 操作结果处理
            def mark_complete():
                try:
                    root.destroy()
                    on_complete_callback(task_id)
                except:
                    pass

            def snooze_reminder():
                try:
                    value = int(snooze_var.get())
                    unit = unit_var.get()
                    minutes = value if unit == "分钟" else value * 60
                    if minutes <= 0:
                        return
                    root.destroy()
                    on_snooze_callback(task_id, minutes)
                except ValueError:
                    pass
                except Exception as e:
                    print(f"延期失败: {e}")
                    try:
                        root.destroy()
                    except:
                        pass

            # 完成按钮
            complete_btn = tk.Button(
                button_frame,
                text="✓ 已完成",
                font=('Microsoft YaHei', 11, 'bold'),
                bg='#27ae60',
                fg='white',
                activebackground='#229954',
                activeforeground='white',
                cursor='hand2',
                relief=tk.FLAT,
                padx=30,
                pady=12,
                command=mark_complete
            )
            complete_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))

            # 延期按钮
            snooze_btn = tk.Button(
                button_frame,
                text="⏰ 延期",
                font=('Microsoft YaHei', 11, 'bold'),
                bg='#3498db',
                fg='white',
                activebackground='#2980b9',
                activeforeground='white',
                cursor='hand2',
                relief=tk.FLAT,
                padx=30,
                pady=12,
                command=snooze_reminder
            )
            snooze_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)

            # 鼠标悬停效果
            def on_enter(e, btn, color):
                btn['bg'] = color

            def on_leave(e, btn, color):
                btn['bg'] = color

            complete_btn.bind('<Enter>', lambda e: on_enter(e, complete_btn, '#229954'))
            complete_btn.bind('<Leave>', lambda e: on_leave(e, complete_btn, '#27ae60'))
            snooze_btn.bind('<Enter>', lambda e: on_enter(e, snooze_btn, '#2980b9'))
            snooze_btn.bind('<Leave>', lambda e: on_leave(e, snooze_btn, '#3498db'))

            # 允许通过回车键确认延期
            root.bind('<Return>', lambda e: snooze_reminder())

            # 保持窗口始终在最前(不强制抢夺焦点)
            root.lift()
            root.attributes('-topmost', True)

            # 显示窗口
            root.deiconify()
            root.focus_force()

            # 运行窗口
            root.mainloop()

        except Exception as e:
            print(f"提醒窗口显示失败: {e}")
            import traceback
            traceback.print_exc()

    # 在独立线程中运行
    Thread(target=show_dialog, daemon=True).start()
