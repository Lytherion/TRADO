# Qt UI 小白完全指南

## 核心概念速查

### 1. 控件 (Widget)
**控件** = 界面上可见的元素(按钮、输入框、列表等)

```python
btn = QPushButton("点我")  # 创建一个按钮控件
label = QLabel("标题")      # 创建一个文本标签控件
input = QLineEdit()        # 创建一个输入框控件
```

**常用控件:**
- `QWidget` - 空白容器,可以放其他控件
- `QPushButton` - 按钮
- `QLabel` - 文本标签(显示文字)
- `QLineEdit` - 单行输入框
- `QTextEdit` - 多行文本框
- `QComboBox` - 下拉选择框
- `QCheckBox` - 复选框
- `QTreeWidget` - 树形列表(可展开/折叠)
- `QDateTimeEdit` - 日期时间选择器
- `QTimeEdit` - 时间选择器

---

### 2. 布局 (Layout)
**布局** = 自动排列控件的管理器(不需要手动设置坐标)

```python
layout = QVBoxLayout()  # 创建垂直布局(从上到下)
layout.addWidget(btn1)  # 添加按钮1
layout.addWidget(btn2)  # 添加按钮2(会自动排在btn1下面)
```

**常用布局:**
- `QVBoxLayout` - 垂直布局(从上到下排列)
- `QHBoxLayout` - 水平布局(从左到右排列)
- `QFormLayout` - 表单布局(自动排列 标签:控件 对)
- `QSplitter` - 分割器(可拖动调整区域大小)

**布局示例:**
```python
# 垂直布局 - 控件从上到下
layout = QVBoxLayout()
layout.addWidget(标题)   # ← 最上面
layout.addWidget(输入框) # ← 中间
layout.addWidget(按钮)   # ← 最下面

# 水平布局 - 控件从左到右
layout = QHBoxLayout()
layout.addWidget(按钮1)  # ← 最左边
layout.addWidget(按钮2)  # ← 中间
layout.addWidget(按钮3)  # ← 最右边
layout.addStretch()     # ← 弹性空间(让前面的控件靠左)
```

---

### 3. 信号与槽 (Signals & Slots)
**信号** = 事件(按钮被点击、文本被修改等)
**槽** = 处理函数(响应事件的方法)

```python
# clicked = 信号(按钮被点击)
# connect = 连接
# self.on_save = 槽(处理函数)
btn.clicked.connect(self.on_save)

# 意思: 当按钮被点击时,调用 self.on_save() 方法
```

**常用信号:**
- `clicked` - 按钮被点击
- `triggered` - 菜单项被触发
- `textChanged` - 文本被修改
- `itemDoubleClicked` - 树形列表项被双击
- `customContextMenuRequested` - 右键菜单被请求

---

### 4. 样式 (Styles)
**两种设置样式的方式:**

#### 方式1: 全局样式文件 (styles.qss)
```css
/* 影响所有 QPushButton */
QPushButton {
    background: purple;
    color: white;
}
```

```python
# 加载全局样式
app.setStyleSheet(f.read())
```

#### 方式2: 内联样式 (代码中设置)
```python
# 只影响这一个按钮
btn.setStyleSheet("background: red; color: white;")
```

---

### 5. QTreeWidget 详解 (树形列表)

**QTreeWidget** = 可以显示分层数据的列表控件

```python
# 创建树形列表
tree = QTreeWidget()

# 设置列名(表头)
tree.setHeaderLabels(["任务", "时间", "状态"])

# 设置列宽
tree.setColumnWidth(0, 600)  # 第0列宽600像素

# 创建一个根节点(分组)
group = QTreeWidgetItem(tree)
group.setText(0, "未完成任务")  # 第0列显示"未完成任务"

# 创建子项(具体任务)
item = QTreeWidgetItem(group)  # 父节点是group
item.setText(0, "完成报告")     # 第0列
item.setText(1, "2024-01-15")  # 第1列
item.setText(2, "未完成")       # 第2列
```

**效果:**
```
📋 未完成任务           ← 根节点(可展开/折叠)
  ├─ 完成报告  2024-01-15  未完成  ← 子项1
  └─ 开会讨论  2024-01-16  未完成  ← 子项2
```

**常用方法:**
- `setHeaderLabels(["列1", "列2"])` - 设置列名
- `setHeaderHidden(True)` - 隐藏表头
- `setColumnWidth(索引, 宽度)` - 设置列宽
- `setRootIsDecorated(True)` - 显示展开/折叠箭头
- `setRootIsDecorated(False)` - 不显示箭头(平铺列表)
- `setText(列索引, 文本)` - 设置某一列的文本
- `setData(列, Qt.UserRole, 数据)` - 存储隐藏数据(用于识别任务)

---

### 6. 对话框 (Dialog)

**QDialog** = 弹窗(用于输入数据或确认操作)

```python
class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("新建任务")  # 设置标题
        self.resize(500, 400)           # 设置大小

        # ...创建输入框、按钮等

        # 保存按钮点击后关闭对话框
        save_btn.clicked.connect(self.accept)  # accept = 确认并关闭

        # 取消按钮点击后关闭对话框
        cancel_btn.clicked.connect(self.reject)  # reject = 取消并关闭

# 使用对话框
dialog = TaskDialog()
if dialog.exec():  # exec() = 显示对话框,返回True/False
    # 用户点击了"保存"
    task = dialog.get_task()
else:
    # 用户点击了"取消"
    pass
```

---

### 7. 右键菜单

```python
# 1. 启用自定义右键菜单
tree.setContextMenuPolicy(Qt.CustomContextMenu)

# 2. 连接右键信号
tree.customContextMenuRequested.connect(self.show_menu)

# 3. 创建菜单处理函数
def show_menu(self, pos):
    # 获取点击的项目
    item = tree.itemAt(pos)
    if not item:
        return

    # 创建菜单
    menu = QMenu(self)

    # 添加菜单项
    edit_action = QAction("编辑", self)
    edit_action.triggered.connect(self.on_edit)  # 点击时触发
    menu.addAction(edit_action)

    delete_action = QAction("删除", self)
    delete_action.triggered.connect(self.on_delete)
    menu.addAction(delete_action)

    # 显示菜单
    menu.exec(tree.viewport().mapToGlobal(pos))
```

---

## 常用方法速查表

### 控件通用方法
```python
widget.setVisible(True/False)       # 显示/隐藏控件
widget.setEnabled(True/False)       # 启用/禁用控件
widget.setStyleSheet("css...")      # 设置内联样式
widget.setToolTip("提示文本")        # 设置鼠标悬停提示
```

### 输入框方法
```python
line_edit.setText("文本")           # 设置文本
line_edit.text()                   # 获取文本
line_edit.setPlaceholderText("提示")# 设置占位符

text_edit.setPlainText("文本")      # 设置纯文本
text_edit.toPlainText()            # 获取纯文本
text_edit.setMaximumHeight(100)    # 设置最大高度
```

### 下拉框方法
```python
combo.addItems(["选项1", "选项2"])  # 添加多个选项
combo.addItem("选项")               # 添加单个选项
combo.currentIndex()               # 获取当前选中索引(0,1,2...)
combo.setCurrentIndex(1)           # 设置当前选中项
combo.currentText()                # 获取当前选中文本
```

### 日期时间方法
```python
dt_edit.setDateTime(QDateTime.currentDateTime())  # 设置当前时间
dt_edit.dateTime()                                # 获取QDateTime对象
dt_edit.dateTime().toPython()                     # 转换为Python datetime
dt_edit.setCalendarPopup(True)                    # 启用日历弹窗
```

### 布局方法
```python
layout.addWidget(控件)              # 添加控件到布局
layout.addLayout(子布局)            # 添加子布局
layout.addStretch()                # 添加弹性空间
layout.setContentsMargins(10,10,10,10)  # 设置内边距(上右下左)
layout.setSpacing(5)               # 设置控件间距
```

### 树形列表方法
```python
tree.clear()                       # 清空所有项目
tree.itemAt(pos)                   # 获取指定位置的项目
tree.selectedItems()               # 获取选中的项目列表

item = QTreeWidgetItem(tree)       # 创建根节点
item = QTreeWidgetItem(parent)     # 创建子节点
item.setText(列, "文本")            # 设置文本
item.setData(列, Qt.UserRole, 数据) # 存储数据
item.data(列, Qt.UserRole)         # 获取数据
```

---

## 完整示例:创建一个简单对话框

```python
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)

class SimpleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置对话框属性
        self.setWindowTitle("输入姓名")
        self.resize(300, 150)

        # 创建主布局(垂直)
        layout = QVBoxLayout(self)

        # 添加标签
        label = QLabel("请输入你的姓名:")
        layout.addWidget(label)

        # 添加输入框
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("在这里输入...")
        layout.addWidget(self.name_input)

        # 创建按钮布局(水平)
        btn_layout = QHBoxLayout()

        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.on_ok)
        btn_layout.addWidget(ok_btn)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        # 将按钮布局添加到主布局
        layout.addLayout(btn_layout)

    def on_ok(self):
        # 获取输入的文本
        name = self.name_input.text()
        if name.strip():  # 如果不为空
            print(f"你好, {name}!")
            self.accept()  # 关闭对话框

# 使用对话框
dialog = SimpleDialog()
if dialog.exec():
    print("用户点击了确定")
else:
    print("用户点击了取消")
```

---

## 调试技巧

### 1. 打印控件信息
```python
print(widget.size())           # 打印控件大小
print(widget.pos())            # 打印控件位置
print(widget.isVisible())      # 是否可见
print(widget.styleSheet())     # 打印样式
```

### 2. 临时修改样式
```python
# 快速测试样式效果
widget.setStyleSheet("background: red;")  # 改成红色看看在哪里
```

### 3. 使用状态栏显示调试信息
```python
self.statusBar().showMessage(f"点击了: {item.text(0)}")
```

---

## 常见问题

### Q: 为什么我的控件不显示?
A: 可能忘记调用 `addWidget()` 或 `show()`

### Q: 为什么布局混乱?
A: 检查是否正确使用了 `QVBoxLayout` 和 `QHBoxLayout`

### Q: 如何让按钮靠右?
A: 在按钮前添加 `layout.addStretch()`

### Q: 如何获取输入框的值?
A: 使用 `line_edit.text()` 或 `text_edit.toPlainText()`

### Q: 如何禁用按钮?
A: 使用 `button.setEnabled(False)`

---

## 学习路径

1. **先学会用基础控件** (QPushButton, QLabel, QLineEdit)
2. **学会用布局排列控件** (QVBoxLayout, QHBoxLayout)
3. **学会信号与槽** (clicked.connect)
4. **学会创建对话框** (QDialog)
5. **学会使用样式** (QSS)
6. **学会复杂控件** (QTreeWidget, QTableWidget)

---

## 参考资源

- Qt 官方文档: https://doc.qt.io/qtforpython-6/
- 本项目样式文件: [ui/styles.qss](ui/styles.qss)
- 按 **F5** 实时重载样式查看效果
