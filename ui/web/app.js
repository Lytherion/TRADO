// ===== 全局状态 =====
const state = {
    currentFilter: 'all',
    tasks: [],
    recurringTasks: [],
    permanentTasks: [],
    editingTask: null,
    editingRecurring: null,
    editingPermanent: null,
    reminderTask: null,
    selectedGroupHeader: null
};

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    showLoadingIndicator();
    eel.notify_frontend_ready()();
});

let servicesReadyCalled = false;

window.onServicesReady = function() {
    if (servicesReadyCalled) return;
    servicesReadyCalled = true;
    hideLoadingIndicator();
    loadAllData().catch(err => console.error('数据加载失败:', err));
};

window.reloadTasks = function() {
    loadTasks().catch(err => console.error('刷新任务失败:', err));
};
eel.expose(reloadTasks);

window.showTaskDialogFromHotkey = function() {
    showTaskDialog();
};
eel.expose(showTaskDialogFromHotkey);

function showLoadingIndicator() {
    const container = document.getElementById('taskListContainer');
    if (container) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">正在初始化服务...</div>';
    }
    setTimeout(() => {
        if (!servicesReadyCalled) {
            const c = document.getElementById('taskListContainer');
            if (c) c.innerHTML = '<div style="text-align: center; padding: 40px; color: #e55;">服务初始化超时，请重启应用</div>';
        }
    }, 15000);
}

function hideLoadingIndicator() {
    // loadAllData 会自动替换内容
}

// ===== 事件监听 =====
function setupEventListeners() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal && !modal.classList.contains('modal-reminder')) {
                modal.classList.remove('show');
            }
        });
    });

    document.addEventListener('contextmenu', (e) => {
        const taskItem = e.target.closest('.task-item, .permanent-item, .recurring-item');
        if (taskItem) {
            e.preventDefault();
            showContextMenu(e, taskItem);
        }
    });

    document.addEventListener('click', () => {
        document.getElementById('contextMenu').style.display = 'none';
    });
}

// ===== 筛选切换 =====
function filterTasks(filter) {
    state.currentFilter = filter;

    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-filter="${filter}"]`).classList.add('active');

    loadTasks();
}

// ===== 加载所有数据 =====
async function loadAllData() {
    await Promise.all([loadPermanentTasks(), loadTasks()]);
}

// ===== 加载任务 =====
async function loadTasks() {
    try {
        if (state.currentFilter === 'all' || state.currentFilter === 'today') {
            const tasks = await eel.get_all_tasks()();
            state.tasks = tasks;
            renderTaskList();
        } else if (state.currentFilter === 'recurring') {
            const tasks = await eel.get_all_recurring_tasks()();
            state.recurringTasks = tasks;
            renderRecurringList();
        }
    } catch (error) {
        console.error('加载任务失败:', error);
    }
}

// ===== 渲染任务列表 =====
function renderTaskList() {
    const container = document.getElementById('taskListContainer');

    let uncompleted, completed;

    if (state.currentFilter === 'all') {
        uncompleted = state.tasks.filter(t => t.status === 0 && !t.recurring_id);
        completed = state.tasks.filter(t => t.status === 1 && !t.recurring_id);
    } else if (state.currentFilter === 'today') {
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);

        uncompleted = state.tasks.filter(t => {
            if (t.status !== 0) return false;
            if (t.due_time && new Date(t.due_time) >= todayStart && new Date(t.due_time) <= todayEnd) return true;
            if (t.remind_time && new Date(t.remind_time) >= todayStart && new Date(t.remind_time) <= todayEnd) return true;
            return false;
        });

        completed = state.tasks.filter(t => {
            if (t.status !== 1) return false;
            if (t.completed_at && new Date(t.completed_at) >= todayStart && new Date(t.completed_at) <= todayEnd) return true;
            if (t.due_time && new Date(t.due_time) >= todayStart && new Date(t.due_time) <= todayEnd) return true;
            if (t.remind_time && new Date(t.remind_time) >= todayStart && new Date(t.remind_time) <= todayEnd) return true;
            return false;
        });
    } else {
        uncompleted = state.tasks.filter(t => t.status === 0);
        completed = state.tasks.filter(t => t.status === 1);
    }

    const sortTasks = tasks => tasks.sort((a, b) => {
        if (!a.remind_time) return 1;
        if (!b.remind_time) return -1;
        return new Date(a.remind_time) - new Date(b.remind_time);
    });

    sortTasks(uncompleted);
    sortTasks(completed);

    let html = '';

    if (uncompleted.length > 0) {
        html += `
            <div class="task-group">
                <div class="task-group-header" onclick="toggleTaskGroup('uncompleted', event)">
                    <span class="group-icon" id="uncompleted-icon">▼</span>
                    <span>📋 未完成 （${uncompleted.length}）</span>
                </div>
                <div class="task-group-content" id="uncompleted-content">
                    ${uncompleted.map(task => renderTaskItem(task)).join('')}
                </div>
            </div>
        `;
    }

    if (completed.length > 0) {
        html += `
            <div class="task-group">
                <div class="task-group-header" onclick="toggleTaskGroup('completed', event)">
                    <span class="group-icon collapsed" id="completed-icon">▼</span>
                    <span>✅ 已完成 （${completed.length}）</span>
                </div>
                <div class="task-group-content collapsed" id="completed-content">
                    ${completed.map(task => renderTaskItem(task)).join('')}
                </div>
            </div>
        `;
    }

    if (uncompleted.length === 0 && completed.length === 0) {
        html = '<div class="empty-state"><div class="icon">📋</div><p>暂无任务</p></div>';
    }

    container.innerHTML = html;
}

// ===== 渲染单个任务项 =====
function renderTaskItem(task) {
    const isCompleted = task.status === 1;
    return `
        <div class="task-item ${isCompleted ? 'completed' : ''}"
             data-task-id="${task.id}"
             ondblclick="editTask(${task.id})"
             onclick="selectTaskItem(event)"
             oncontextmenu="return false;">
            <div class="task-title-col">
                <div class="task-checkbox ${isCompleted ? 'checked' : ''}"
                     onclick="toggleTaskStatus(${task.id}, event)"></div>
                <span class="task-title-text">${escapeHtml(task.title)}</span>
            </div>
            <div class="task-time-col">
                ${task.remind_time ? formatDateTime(task.remind_time) : ''}
            </div>
            <div class="task-status-col">
                ${isCompleted ? '已完成' : '未完成'}
            </div>
        </div>
    `;
}

function selectTaskItem(event) {
    document.querySelectorAll('.task-item').forEach(item => item.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

function toggleTaskGroup(groupName, event) {
    const icon = document.getElementById(`${groupName}-icon`);
    const content = document.getElementById(`${groupName}-content`);
    const header = event.currentTarget;

    icon.classList.toggle('collapsed');
    content.classList.toggle('collapsed');

    if (state.selectedGroupHeader) state.selectedGroupHeader.classList.remove('selected');
    header.classList.add('selected');
    state.selectedGroupHeader = header;
}

async function toggleTaskStatus(taskId, event) {
    event.stopPropagation();
    try {
        const result = await eel.toggle_task_status(taskId)();
        if (result.success) await loadTasks();
    } catch (error) {
        console.error('切换任务状态失败:', error);
    }
}

// ===== 加载常驻任务 =====
async function loadPermanentTasks() {
    try {
        const tasks = await eel.get_all_permanent_tasks()();
        state.permanentTasks = tasks;
        renderPermanentTasks();
    } catch (error) {
        console.error('加载常驻任务失败:', error);
    }
}

function renderPermanentTasks() {
    const container = document.getElementById('permanentList');

    if (state.permanentTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无常驻任务</p></div>';
        return;
    }

    container.innerHTML = state.permanentTasks.map(task => `
        <div class="permanent-item"
             data-task-id="${task.id}"
             ondblclick="editPermanentTask(${task.id})"
             oncontextmenu="return false;"
             onclick="selectPermanentItem(event)">
            <div class="permanent-item-title">${escapeHtml(task.title)}</div>
            ${task.description ? `<div class="permanent-item-desc">${escapeHtml(task.description)}</div>` : ''}
            ${task.tags ? `
                <div class="permanent-item-tags">
                    ${task.tags.split(',').map(tag =>
                        `<span class="permanent-tag">${escapeHtml(tag.trim())}</span>`
                    ).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

function selectPermanentItem(event) {
    document.querySelectorAll('.permanent-item').forEach(item => item.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

// ===== 渲染循环任务列表 =====
function renderRecurringList() {
    const container = document.getElementById('taskListContainer');

    if (state.recurringTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🔄</div><p>暂无循环任务</p></div>';
        return;
    }

    const typeLabels = { 'daily': '每交易日', 'weekly': '每周', 'monthly': '每月' };

    container.innerHTML = state.recurringTasks.map(task => {
        const typeLabel = typeLabels[task.recur_type] || '未知';
        const timePart = task.remind_time ? task.remind_time.substring(0, 5) : '';

        return `
            <div class="recurring-item"
                 data-task-id="${task.id}"
                 ondblclick="editRecurringTask(${task.id})"
                 oncontextmenu="return false;"
                 onclick="selectRecurringItem(event)">
                <div class="recurring-row">
                    <div class="recurring-type-badge">${typeLabel}</div>
                    <div class="recurring-title">${escapeHtml(task.title)}</div>
                    <div class="recurring-time">${timePart}</div>
                </div>
            </div>
        `;
    }).join('');
}

function selectRecurringItem(event) {
    document.querySelectorAll('.recurring-item').forEach(item => item.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

// ===== 任务对话框 =====
function showTaskDialog(taskId = null) {
    const modal = document.getElementById('taskModal');
    const form = document.getElementById('taskForm');
    const title = document.getElementById('taskModalTitle');
    const statusGroup = document.getElementById('taskStatusGroup');

    form.reset();
    state.editingTask = taskId;

    if (taskId) {
        title.textContent = '编辑任务';
        statusGroup.style.display = 'block';
        const task = state.tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('taskTitle').value = task.title;
            document.getElementById('taskDesc').value = task.description || '';
            document.getElementById('taskStartTime').value = formatDateTimeInput(task.start_time);
            document.getElementById('taskDueTime').value = formatDateTimeInput(task.due_time);
            document.getElementById('taskStatus').value = task.status;
            document.getElementById('taskTags').value = task.tags ? task.tags.join(',') : '';
        }
    } else {
        title.textContent = '新建任务';
        statusGroup.style.display = 'none';
        const now = new Date();
        document.getElementById('taskStartTime').value = formatDateTimeInput(now.toISOString());
        const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
        document.getElementById('taskDueTime').value = formatDateTimeInput(oneHourLater.toISOString());
    }

    modal.classList.add('show');
}

function closeTaskDialog() {
    document.getElementById('taskModal').classList.remove('show');
    state.editingTask = null;
}

async function saveTask(event) {
    event.preventDefault();

    const dueTimeVal = document.getElementById('taskDueTime').value;
    if (dueTimeVal) {
        const remindDate = dueTimeVal.substring(0, 10);
        const tradeCheck = await eel.check_trade_day(remindDate)();
        if (!tradeCheck.is_trade_day) {
            alert(`提醒日期 ${remindDate} 不是交易日，请选择交易日`);
            return;
        }
    }

    const taskData = {
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDesc').value,
        start_time: document.getElementById('taskStartTime').value,
        due_time: dueTimeVal,
        remind_time: dueTimeVal,
        tags: document.getElementById('taskTags').value.split(',').map(t => t.trim()).filter(t => t)
    };

    if (state.editingTask) {
        taskData.status = parseInt(document.getElementById('taskStatus').value);
    }

    try {
        const result = state.editingTask
            ? await eel.update_task(state.editingTask, taskData)()
            : await eel.create_task(taskData)();

        if (result.success) {
            closeTaskDialog();
            await loadTasks();
        } else {
            alert(result.message || '保存失败');
        }
    } catch (error) {
        console.error('保存任务失败:', error);
        alert('保存失败');
    }
}

function editTask(taskId) { showTaskDialog(taskId); }

async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗?')) return;
    try {
        const result = await eel.delete_task(taskId)();
        if (result.success) await loadTasks();
        else alert(result.message || '删除失败');
    } catch (error) {
        console.error('删除任务失败:', error);
        alert('删除失败');
    }
}

// ===== 循环任务对话框 =====
function showRecurringDialog(taskId = null) {
    const modal = document.getElementById('recurringModal');
    const form = document.getElementById('recurringForm');
    const title = document.getElementById('recurringModalTitle');

    form.reset();
    state.editingRecurring = taskId;

    if (taskId) {
        title.textContent = '编辑循环任务';
        const task = state.recurringTasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('recurringTitle').value = task.title;
            document.getElementById('recurringDesc').value = task.description || '';
            document.getElementById('recurringRemindTime').value = task.remind_time || '09:00';
            document.getElementById('recurringType').value = task.recur_type;
            if (task.end_date) {
                document.getElementById('hasEndDate').checked = true;
                document.getElementById('recurringEndDate').value = formatDateInput(task.end_date);
                toggleEndDate();
            }
            document.getElementById('recurringTags').value = task.tags ? task.tags.join(',') : '';
            onRecurringTypeChange();
            setTimeout(() => {
                if (task.recur_days) {
                    task.recur_days.forEach(day => {
                        const checkbox = document.querySelector(`#recurringDaysCheckboxes input[value="${day}"]`);
                        if (checkbox) checkbox.checked = true;
                    });
                }
            }, 0);
        }
    } else {
        title.textContent = '新建循环任务';
        onRecurringTypeChange();
    }

    modal.classList.add('show');
}

function closeRecurringDialog() {
    document.getElementById('recurringModal').classList.remove('show');
    state.editingRecurring = null;
}

function onRecurringTypeChange() {
    const type = document.getElementById('recurringType').value;
    const daysGroup = document.getElementById('recurringDaysGroup');
    const daysCheckboxes = document.getElementById('recurringDaysCheckboxes');

    if (type === 'daily') {
        daysGroup.style.display = 'none';
    } else {
        daysGroup.style.display = 'block';

        if (type === 'weekly') {
            // value 使用 0-6，与 Python weekday() 一致
            const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
            daysCheckboxes.innerHTML = weekdays.map((day, i) => `
                <label>
                    <input type="checkbox" value="${i}" name="recurDays">
                    ${day}
                </label>
            `).join('');
        } else if (type === 'monthly') {
            const days = Array.from({length: 31}, (_, i) => i + 1);
            daysCheckboxes.innerHTML = days.map(day => `
                <label>
                    <input type="checkbox" value="${day}" name="recurDays">
                    ${day}号
                </label>
            `).join('');
        }
    }
}

function toggleEndDate() {
    const checked = document.getElementById('hasEndDate').checked;
    document.getElementById('endDateGroup').style.display = checked ? 'block' : 'none';
}

async function saveRecurringTask(event) {
    event.preventDefault();

    const type = document.getElementById('recurringType').value;
    const recurDays = Array.from(
        document.querySelectorAll('#recurringDaysCheckboxes input:checked')
    ).map(cb => parseInt(cb.value));

    const taskData = {
        title: document.getElementById('recurringTitle').value,
        description: document.getElementById('recurringDesc').value,
        remind_time: document.getElementById('recurringRemindTime').value + ':00' || null,
        recur_type: type,
        recur_days: type === 'daily' ? [] : recurDays,
        end_date: document.getElementById('hasEndDate').checked
            ? document.getElementById('recurringEndDate').value : null,
        tags: document.getElementById('recurringTags').value.split(',').map(t => t.trim()).filter(t => t)
    };

    try {
        const result = state.editingRecurring
            ? await eel.update_recurring_task(state.editingRecurring, taskData)()
            : await eel.create_recurring_task(taskData)();

        if (result.success) {
            closeRecurringDialog();
            if (state.currentFilter === 'recurring') await loadTasks();
        } else {
            alert(result.message || '保存失败');
        }
    } catch (error) {
        console.error('保存循环任务失败:', error);
        alert('保存失败');
    }
}

function editRecurringTask(taskId) { showRecurringDialog(taskId); }

async function deleteRecurringTask(taskId) {
    if (!confirm('确定要删除这个循环任务吗？已生成的任务实例不会被删除。')) return;
    try {
        const result = await eel.delete_recurring_task(taskId)();
        if (result.success) await loadTasks();
        else alert(result.message || '删除失败');
    } catch (error) {
        console.error('删除循环任务失败:', error);
        alert('删除失败');
    }
}

// ===== 常驻任务对话框 =====
function showPermanentDialog(taskId = null) {
    const modal = document.getElementById('permanentModal');
    const form = document.getElementById('permanentForm');
    const title = document.getElementById('permanentModalTitle');

    form.reset();
    state.editingPermanent = taskId;

    if (taskId) {
        title.textContent = '编辑常驻任务';
        const task = state.permanentTasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('permanentTitle').value = task.title;
            document.getElementById('permanentDesc').value = task.description || '';
            document.getElementById('permanentTags').value = task.tags || '';
        }
    } else {
        title.textContent = '新建常驻任务';
    }

    modal.classList.add('show');
}

function closePermanentDialog() {
    document.getElementById('permanentModal').classList.remove('show');
    state.editingPermanent = null;
}

async function savePermanentTask(event) {
    event.preventDefault();

    const taskData = {
        title: document.getElementById('permanentTitle').value,
        description: document.getElementById('permanentDesc').value,
        tags: document.getElementById('permanentTags').value
    };

    try {
        const result = state.editingPermanent
            ? await eel.update_permanent_task(state.editingPermanent, taskData)()
            : await eel.create_permanent_task(taskData)();

        if (result.success) {
            closePermanentDialog();
            await loadPermanentTasks();
        } else {
            alert(result.message || '保存失败');
        }
    } catch (error) {
        console.error('保存常驻任务失败:', error);
        alert('保存失败');
    }
}

function editPermanentTask(taskId) { showPermanentDialog(taskId); }

async function deletePermanentTask(taskId) {
    if (!confirm('确定要删除这个常驻任务吗?')) return;
    try {
        const result = await eel.delete_permanent_task(taskId)();
        if (result.success) await loadPermanentTasks();
        else alert(result.message || '删除失败');
    } catch (error) {
        console.error('删除常驻任务失败:', error);
        alert('删除失败');
    }
}

// ===== 提醒对话框 =====
function showReminderDialog(taskId, taskTitle = '') {
    loadTasks().then(() => {
        const task = state.tasks.find(t => t.id === taskId);
        if (!task) return;

        state.reminderTask = task;
        document.getElementById('reminderTaskTitle').textContent = task.title;
        document.getElementById('reminderTaskDesc').textContent = task.description || '无描述';
        document.getElementById('reminderModal').classList.add('show');

        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTKJ0fPEcikGJ37C7+ONQQ4XZrjr77FXFg1No+LyvmwcBzaL0vPFcikGJ3/C7+OOTQ8WWLP');
            audio.volume = 0.3;
            audio.play().catch(() => {});
        } catch (e) {}
    });
}

function closeReminderDialog() {
    // 提醒弹窗必须选择操作，不允许直接关闭
}

async function completeReminderTask() {
    if (!state.reminderTask) return;
    try {
        const result = await Promise.race([
            eel.toggle_task_status(state.reminderTask.id)(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('操作超时')), 5000))
        ]);

        if (!result || !result.success) {
            alert(result?.message || '操作失败，请稍后重试');
            return;
        }

        await eel.dismiss_reminder()();
        document.getElementById('reminderModal').classList.remove('show');
        state.reminderTask = null;
        await loadTasks();
    } catch (error) {
        console.error('完成任务失败:', error);
        alert('完成任务失败: ' + error.message);
    }
}

async function snoozeReminder(minutes) {
    if (!state.reminderTask) return;
    try {
        const result = await Promise.race([
            eel.snooze_reminder(state.reminderTask.id, minutes)(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('操作超时')), 5000))
        ]);

        if (!result || !result.success) {
            alert(result?.message || '操作失败，请稍后重试');
            return;
        }

        await eel.dismiss_reminder()();
        document.getElementById('reminderModal').classList.remove('show');
        state.reminderTask = null;
        await loadTasks();
    } catch (error) {
        console.error('延迟提醒失败:', error);
        alert('延迟提醒失败: ' + error.message);
    }
}

async function snoozeCustom() {
    const input = document.getElementById('customSnoozeMinutes');
    const minutes = parseInt(input.value);
    if (!minutes || minutes < 1 || minutes > 1440) {
        alert('请输入 1-1440 之间的分钟数');
        return;
    }
    await snoozeReminder(minutes);
    input.value = '';
}

// ===== 右键菜单 =====
function showContextMenu(event, element) {
    const menu = document.getElementById('contextMenu');
    const items = document.getElementById('contextMenuItems');
    const taskId = parseInt(element.dataset.taskId);

    let menuHtml = '';
    if (element.classList.contains('permanent-item')) {
        menuHtml = `
            <li onclick="editPermanentTask(${taskId})">编辑</li>
            <li onclick="deletePermanentTask(${taskId})">删除</li>
        `;
    } else if (element.classList.contains('recurring-item')) {
        menuHtml = `
            <li onclick="editRecurringTask(${taskId})">编辑</li>
            <li onclick="deleteRecurringTask(${taskId})">删除</li>
        `;
    } else {
        menuHtml = `
            <li onclick="editTask(${taskId})">编辑</li>
            <li onclick="deleteTask(${taskId})">删除</li>
        `;
    }

    items.innerHTML = menuHtml;
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    menu.style.display = 'block';
}

// ===== 工具函数 =====
function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const isTomorrow = date.toDateString() === new Date(now.getTime() + 86400000).toDateString();
    const time = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    if (isToday) return `今天 ${time}`;
    if (isTomorrow) return `明天 ${time}`;
    return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatDateTimeInput(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatDateInput(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
