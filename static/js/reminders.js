/* === 提醒面板组件 === */

const RemindersView = {
    async show() {
        AppState.currentEntryDate = null;
        showView('reminders');

        const container = document.getElementById('view-reminders');
        container.innerHTML = '<p style="text-align:center;padding:40px;color:var(--color-text-muted);">加载中...</p>';

        try {
            const reminders = await API.getReminders();
            this._render(reminders);
        } catch (e) {
            container.innerHTML = `<p style="text-align:center;padding:40px;color:var(--color-danger);">加载失败：${e.message}</p>`;
        }
    },

    _render(reminders) {
        const container = document.getElementById('view-reminders');

        if (reminders.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:60px 20px;color:var(--color-text-muted);">
                    <div style="font-size:48px;margin-bottom:16px;">🔔</div>
                    <p>还没有提醒事项</p>
                    <p style="font-size:13px;margin-top:8px;">点击下方按钮创建第一个提醒</p>
                </div>
                <div style="text-align:center;">
                    <button class="btn btn-primary" id="btn-add-reminder">➕ 添加提醒</button>
                </div>
            `;
        } else {
            const active = reminders.filter(r => !r.is_completed);
            const completed = reminders.filter(r => r.is_completed);

            let html = `
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                    <h2 style="font-size:20px;font-weight:700;">⏰ 提醒列表</h2>
                    <button class="btn btn-primary btn-sm" id="btn-add-reminder">➕ 添加提醒</button>
                </div>
            `;

            // 活跃提醒
            if (active.length > 0) {
                html += '<div style="margin-bottom:24px;">';
                html += '<h3 style="font-size:14px;color:var(--color-text-muted);margin-bottom:12px;">进行中</h3>';
                for (const r of active) {
                    html += this._reminderCard(r);
                }
                html += '</div>';
            } else {
                html += '<p style="color:var(--color-text-muted);text-align:center;padding:20px;">没有活跃提醒</p>';
            }

            // 已完成
            if (completed.length > 0) {
                html += '<h3 style="font-size:14px;color:var(--color-text-muted);margin-bottom:12px;">已完成</h3>';
                for (const r of completed) {
                    html += this._reminderCard(r);
                }
            }

            container.innerHTML = html;
        }

        this._bindEvents();
    },

    _reminderCard(r) {
        const remindDate = new Date(r.remind_at);
        const dateStr = `${remindDate.getMonth() + 1}月${remindDate.getDate()}日 ${String(remindDate.getHours()).padStart(2, '0')}:${String(remindDate.getMinutes()).padStart(2, '0')}`;
        const isOverdue = !r.is_completed && !r.is_dismissed && remindDate < new Date();
        const recurringLabel = r.is_recurring
            ? { daily: '每天', weekly: '每周', monthly: '每月' }[r.recurring_rule] || '重复'
            : '';

        return `
            <div class="reminder-card ${r.is_completed ? 'completed' : ''} ${isOverdue ? 'overdue' : ''}"
                 style="background:var(--color-surface);border:1px solid ${isOverdue ? 'var(--color-danger)' : 'var(--color-border)'};border-radius:var(--radius);padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px;${r.is_completed ? 'opacity:0.5;' : ''}">
                <div style="font-size:24px;flex-shrink:0;">
                    ${isOverdue ? '🔴' : r.is_completed ? '✅' : '⏰'}
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:15px;">${this._escapeHtml(r.title)}</div>
                    ${r.description ? `<div style="font-size:13px;color:var(--color-text-muted);margin-top:2px;">${this._escapeHtml(r.description)}</div>` : ''}
                    <div style="font-size:12px;color:var(--color-text-muted);margin-top:4px;">
                        ${dateStr}
                        ${recurringLabel ? ` · ${recurringLabel}` : ''}
                        ${r.entry_date ? ` · <a href="javascript:openEntry('${r.entry_date}')" style="color:var(--color-primary);">查看日记</a>` : ''}
                    </div>
                </div>
                <div style="display:flex;gap:4px;flex-shrink:0;">
                    ${!r.is_completed ? `
                        <button class="btn btn-sm btn-outline edit-reminder-btn" data-id="${r.id}">编辑</button>
                        <button class="btn btn-sm btn-outline dismiss-btn" data-id="${r.id}">忽略</button>
                        <button class="btn btn-sm btn-primary complete-btn" data-id="${r.id}">完成</button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger delete-reminder-btn" data-id="${r.id}">删除</button>
                </div>
            </div>
        `;
    },

    _bindEvents() {
        // 添加提醒按钮
        const addBtn = document.getElementById('btn-add-reminder');
        if (addBtn) {
            addBtn.addEventListener('click', () => this._showForm());
        }

        // 编辑按钮
        document.querySelectorAll('.edit-reminder-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.dataset.id);
                const reminders = await API.getReminders();
                const r = reminders.find(r => r.id === id);
                if (r) this._showForm(r);
            });
        });

        // 完成按钮
        document.querySelectorAll('.complete-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.dataset.id);
                try {
                    await API.updateReminder(id, { is_completed: 1 });
                    showToast('提醒已完成', 'success');
                    this.show();
                    updateReminderBadge();
                } catch (err) {
                    showToast('操作失败：' + err.message, 'error');
                }
            });
        });

        // 忽略按钮
        document.querySelectorAll('.dismiss-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.dataset.id);
                try {
                    await API.dismissReminder(id);
                    showToast('已忽略');
                    this.show();
                    updateReminderBadge();
                } catch (err) {
                    showToast('操作失败：' + err.message, 'error');
                }
            });
        });

        // 删除按钮
        document.querySelectorAll('.delete-reminder-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.dataset.id);
                const confirmed = await showConfirm('确定要删除这个提醒吗？');
                if (confirmed) {
                    try {
                        await API.deleteReminder(id);
                        showToast('提醒已删除');
                        this.show();
                        updateReminderBadge();
                    } catch (err) {
                        showToast('删除失败：' + err.message, 'error');
                    }
                }
            });
        });
    },

    _showForm(existing) {
        const isEdit = !!existing;
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';

        const now = new Date();
        const defaultTime = new Date(now);
        defaultTime.setDate(defaultTime.getDate() + 1);

        const remindAt = existing ? existing.remind_at : defaultTime.toISOString().slice(0, 16);
        const remindDate = remindAt.slice(0, 10);
        const remindTime = remindAt.slice(0, 16);

        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <span class="modal-title">${isEdit ? '✏️ 编辑提醒' : '➕ 添加提醒'}</span>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="form-group">
                    <label class="label">标题</label>
                    <input class="input" id="remind-title" placeholder="例如：开会"
                           value="${this._escapeHtml(existing ? existing.title : '')}">
                </div>
                <div class="form-group">
                    <label class="label">描述（可选）</label>
                    <input class="input" id="remind-desc" placeholder="补充说明"
                           value="${this._escapeHtml(existing ? existing.description : '')}">
                </div>
                <div class="form-group">
                    <label class="label">提醒时间</label>
                    <input class="input" type="datetime-local" id="remind-time" value="${remindTime}"${isEdit ? '' : ` min="${now.toISOString().slice(0, 16)}"`}>
                </div>
                <div class="form-group">
                    <label class="label">关联日记日期（可选）</label>
                    <input class="input" type="date" id="remind-entry-date"
                           value="${this._escapeHtml(existing ? existing.entry_date : '')}">
                </div>
                <div class="form-group">
                    <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                        <input type="checkbox" id="remind-recurring"
                               ${existing && existing.is_recurring ? 'checked' : ''}>
                        重复提醒
                    </label>
                    <select class="input" id="remind-recurring-rule"
                            style="margin-top:8px;${existing && existing.is_recurring ? '' : 'display:none;'}">
                        <option value="daily" ${existing && existing.recurring_rule === 'daily' ? 'selected' : ''}>每天</option>
                        <option value="weekly" ${existing && existing.recurring_rule === 'weekly' ? 'selected' : ''}>每周</option>
                        <option value="monthly" ${existing && existing.recurring_rule === 'monthly' ? 'selected' : ''}>每月</option>
                    </select>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline cancel-btn">取消</button>
                    <button class="btn btn-primary save-btn">${isEdit ? '更新' : '保存'}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 事件
        document.getElementById('remind-recurring').addEventListener('change', function() {
            document.getElementById('remind-recurring-rule').style.display = this.checked ? 'block' : 'none';
        });

        overlay.querySelector('.modal-close').addEventListener('click', () => overlay.remove());
        overlay.querySelector('.cancel-btn').addEventListener('click', () => overlay.remove());
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        overlay.querySelector('.save-btn').addEventListener('click', async () => {
            const title = document.getElementById('remind-title').value.trim();
            const remindAtVal = document.getElementById('remind-time').value;

            if (!title) {
                showToast('请输入标题', 'error');
                return;
            }
            if (!remindAtVal) {
                showToast('请选择提醒时间', 'error');
                return;
            }

            const data = {
                title,
                description: document.getElementById('remind-desc').value.trim(),
                remind_at: remindAtVal,
                entry_date: document.getElementById('remind-entry-date').value || '',
                is_recurring: document.getElementById('remind-recurring').checked,
                recurring_rule: document.getElementById('remind-recurring').checked
                    ? document.getElementById('remind-recurring-rule').value : '',
            };

            try {
                if (isEdit) {
                    await API.updateReminder(existing.id, data);
                    showToast('提醒已更新', 'success');
                } else {
                    await API.createReminder(data);
                    showToast('提醒已创建', 'success');
                    requestNotificationPermission();
                }
                overlay.remove();
                this.show();
                updateReminderBadge();
            } catch (err) {
                showToast((isEdit ? '更新' : '创建') + '失败：' + err.message, 'error');
            }
        });
    },

    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
