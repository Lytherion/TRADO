import sys
from threading import Thread

DEFAULT_SNOOZE_MINUTES = 9


def show_reminder_window(task_id, task_title, on_complete_callback, on_snooze_callback, on_shown_callback=None):
    if sys.platform != 'win32':
        return

    def show_dialog():
        try:
            import tkinter as tk
            import ctypes

            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

            root = tk.Tk()
            root.withdraw()
            root.title("任务提醒")
            root.resizable(False, False)
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.attributes('-toolwindow', True)
            root.bind('<Key>', lambda _: 'break')

            root.update_idletasks()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

            W, H, R = 440, 250, 14
            HEADER_H = 50
            x, y = (sw - W) // 2, (sh - H) // 2
            root.geometry(f"{W}x{H}+{x}+{y}")
            root.configure(bg='white')

            # SetWindowRgn 裁出圆角——Header Frame 的角自然跟着裁
            def apply_round():
                try:
                    hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
                    try:
                        v = ctypes.c_int(2)
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, 33, ctypes.byref(v), ctypes.sizeof(v))
                    except Exception:
                        pass
                    rgn = ctypes.windll.gdi32.CreateRoundRectRgn(
                        0, 0, W + 1, H + 1, R * 2, R * 2)
                    ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
                except Exception:
                    pass

            HEADER   = '#667eea'
            BG       = 'white'
            TEXT     = '#111827'
            SUBTEXT  = '#6b7280'
            BORDER   = '#e5e7eb'
            TAG_BG   = '#f3f4f6'
            TAG_FG   = '#667eea'
            TAG_HV   = '#e0e7ff'
            BTN_OK   = '#16a34a'
            BTN_OK_H = '#15803d'
            BTN_SN   = '#667eea'
            BTN_SN_H = '#5568d3'

            F_TITLE = ('Microsoft YaHei UI', 11, 'bold')
            F_TASK  = ('Microsoft YaHei UI', 12, 'bold')
            F_LABEL = ('Microsoft YaHei UI', 9)
            F_BTN   = ('Microsoft YaHei UI', 10, 'bold')
            F_TAG   = ('Microsoft YaHei UI', 9)
            F_ENTRY = ('Microsoft YaHei UI', 11)

            # Header：纯 Frame，圆角由 SetWindowRgn 裁出，不需要 Canvas 画弧
            header = tk.Frame(root, bg=HEADER, height=HEADER_H)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            tk.Label(header, text='任务提醒', font=F_TITLE,
                     bg=HEADER, fg='white').pack(side=tk.LEFT, padx=18)

            # 内容区
            body = tk.Frame(root, bg=BG, padx=18)
            body.pack(fill=tk.BOTH, expand=True)

            display_title = task_title if len(task_title) <= 32 else task_title[:31] + '…'
            tk.Label(body, text=display_title, font=F_TASK,
                     bg=BG, fg=TEXT, anchor=tk.W,
                     wraplength=W - 40, justify=tk.LEFT).pack(fill=tk.X, pady=(12, 8))

            tk.Frame(body, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 10))

            # 延后行
            row = tk.Frame(body, bg=BG)
            row.pack(fill=tk.X)

            tk.Label(row, text='延后', font=F_LABEL,
                     bg=BG, fg=SUBTEXT).pack(side=tk.LEFT, padx=(0, 8))

            entry = tk.Entry(
                row, font=F_ENTRY, width=4, justify=tk.CENTER,
                bg='#f9fafb', fg=TEXT,
                insertbackground=HEADER,
                relief=tk.FLAT,
                highlightthickness=1,
                highlightbackground=BORDER,
                highlightcolor=HEADER,
            )
            entry.pack(side=tk.LEFT, ipady=5, padx=(0, 6))

            unit_var = tk.StringVar(value='分钟')
            uf = tk.Frame(row, bg=BG)
            uf.pack(side=tk.LEFT, padx=(0, 10))
            unit_btns = {}

            def select_unit(u):
                unit_var.set(u)
                for uu, b in unit_btns.items():
                    b.config(bg=HEADER if uu == u else TAG_BG,
                             fg='white' if uu == u else SUBTEXT)

            for u in ['分钟', '小时']:
                sel = u == '分钟'
                b = tk.Label(uf, text=u, font=F_TAG,
                             bg=HEADER if sel else TAG_BG,
                             fg='white' if sel else SUBTEXT,
                             cursor='hand2', padx=8, pady=4, relief=tk.FLAT)
                b.pack(side=tk.LEFT, padx=1)
                b.bind('<Button-1>', lambda _, uu=u: select_unit(uu))
                unit_btns[u] = b

            def set_quick(v, u):
                entry.delete(0, tk.END)
                entry.insert(0, str(v))
                select_unit(u)

            for lbl, v, u in [('5m', 5, '分钟'), ('15m', 15, '分钟'),
                               ('30m', 30, '分钟'), ('1h', 1, '小时')]:
                t = tk.Label(row, text=lbl, font=F_TAG,
                             bg=TAG_BG, fg=TAG_FG,
                             cursor='hand2', padx=7, pady=4, relief=tk.FLAT)
                t.pack(side=tk.LEFT, padx=2)
                t.bind('<Button-1>', lambda _, vv=v, uu=u: set_quick(vv, uu))
                t.bind('<Enter>', lambda _, b=t: b.config(bg=TAG_HV))
                t.bind('<Leave>', lambda _, b=t: b.config(bg=TAG_BG))

            btn_area = tk.Frame(body, bg=BG)
            btn_area.pack(fill=tk.X, pady=(14, 14))

            def mark_complete():
                try:
                    root.destroy()
                    on_complete_callback(task_id)
                except Exception:
                    pass

            def snooze_reminder():
                try:
                    raw = entry.get().strip()
                    minutes = int(raw) if raw else DEFAULT_SNOOZE_MINUTES
                    if unit_var.get() == '小时':
                        minutes *= 60
                    if minutes <= 0:
                        minutes = DEFAULT_SNOOZE_MINUTES
                    root.destroy()
                    on_snooze_callback(task_id, minutes)
                except ValueError:
                    root.destroy()
                    on_snooze_callback(task_id, DEFAULT_SNOOZE_MINUTES)
                except Exception as e:
                    print(f"延期失败: {e}")
                    try:
                        root.destroy()
                    except Exception:
                        pass

            def make_btn(parent, text, cmd, bg, hv):
                b = tk.Button(
                    parent, text=text, command=cmd,
                    font=F_BTN, bg=bg, fg='white',
                    activebackground=hv, activeforeground='white',
                    cursor='hand2', relief=tk.FLAT,
                    bd=0, highlightthickness=0,
                )
                b.bind('<Enter>', lambda _: b.config(bg=hv))
                b.bind('<Leave>', lambda _: b.config(bg=bg))
                return b

            ok_btn = make_btn(btn_area, '✓  已完成', mark_complete, BTN_OK, BTN_OK_H)
            ok_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 8))

            sn_btn = make_btn(btn_area, '⏱  延后', snooze_reminder, BTN_SN, BTN_SN_H)
            sn_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10)

            root.bind('<Return>', lambda _: snooze_reminder())

            root.lift()
            root.attributes('-topmost', True)
            root.deiconify()
            root.update_idletasks()
            apply_round()

            # 填入默认值并聚焦，在事件循环稳定后执行
            def init_entry():
                entry.delete(0, tk.END)
                entry.insert(0, str(DEFAULT_SNOOZE_MINUTES))
                entry.focus_set()
                entry.icursor(tk.END)

            root.after(0, init_entry)

            if on_shown_callback:
                on_shown_callback()

            root.mainloop()

        except Exception as e:
            print(f"提醒窗口显示失败: {e}")
            import traceback
            traceback.print_exc()

    Thread(target=show_dialog, daemon=True).start()
