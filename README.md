# 交易日任务管理器

专为**只在交易日工作**的人设计的任务管理工具。提醒到点后会强制弹出置顶窗口，必须处理才能关掉。

## 核心特点

**交易日感知**：提醒和循环任务只在 A 股交易日触发，节假日、休市日自动跳过，不会打扰你。

**强制弹窗**：到达提醒时间时，弹出系统级置顶窗口，覆盖在所有程序之上，必须选择"完成"或"稍后提醒"才能关闭——不会被你忽略。

## 功能

- **普通任务**：一次性任务，支持截止时间和提醒时间
- **循环任务**：按每日 / 每周 / 每月规则自动生成，只在交易日生成实例
- **常驻任务**：长期备忘，无截止时间，始终可见
- **稍后提醒**：支持 5 / 10 / 30 分钟后再次提醒
- **全局快捷键**：`Ctrl+Alt+0` 快速新建任务，无需切换窗口

## 下载

直接下载 [Releases](https://github.com/Lytherion/TRADO/releases) 中的 `TRADO.exe`，双击运行，无需安装 Python。

## 从源码运行

需要 Python >= 3.10 和 [uv](https://github.com/astral-sh/uv)。

```bash
git clone https://github.com/Lytherion/TRADO.git
cd TRADO
uv sync
uv run main_eel.py
```

Windows 下也可以用 `run_task_manager_hidden.bat` 静默启动（不显示控制台窗口）。

## 项目结构

```
TRADO/
├── main_eel.py              # 入口：启动、定时任务、全局快捷键
├── api/
│   ├── exposed_api.py       # 暴露给前端的所有接口（@eel.expose）
│   └── converters.py        # 数据模型 → 字典序列化
├── services/
│   ├── task_service.py      # 普通任务业务逻辑
│   ├── recurring_service.py # 循环任务生成逻辑
│   ├── reminder_service.py  # 提醒触发与强制弹窗
│   └── is_trade_day.py      # 交易日判断（深交所日历接口）
├── database/
│   └── manager.py           # SQLite 操作封装
├── models/                  # 数据模型（dataclass）
└── ui/
    ├── web/                 # 前端（HTML / CSS / JS）
    └── reminder_window.py   # Tkinter 强制置顶弹窗
```

## 截图

（待补充）

## License

MIT
