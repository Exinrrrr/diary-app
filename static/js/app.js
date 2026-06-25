/* === 应用主控制器 === */

const AppState = {
    currentView: 'welcome',     // 'welcome' | 'entry' | 'reminders'
    currentEntryDate: null,     // '2026-06-22'
    currentMonth: {
        year: new Date().getFullYear(),
        month: new Date().getMonth() + 1,
    },
    editing: false,
    reminderCount: 0,
    entriesCache: {},           // { '2026-06-22': { ... } }
};

/** 切换视图 */
function showView(viewName) {
    AppState.currentView = viewName;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.add('active');
    }
}

/** 打开某一天的日记 */
async function openEntry(date) {
    AppState.currentEntryDate = date;
    AppState.editing = false;
    showView('entry');
    await EntryView.render(date);
    CalendarView.highlightDate(date);
}

/** 打开编辑某一天的日记 */
async function editEntry(date) {
    AppState.currentEntryDate = date;
    AppState.editing = true;
    showView('entry');
    await EntryView.renderEdit(date);
    CalendarView.highlightDate(date);
}

/** 打开新建日记 */
async function newEntry(date) {
    AppState.currentEntryDate = date;
    AppState.editing = true;
    showView('entry');
    await EntryView.renderEdit(date);
    CalendarView.highlightDate(date);
}

/** 回到欢迎页 / 日历 */
function goHome() {
    AppState.currentEntryDate = null;
    AppState.editing = false;
    showView('welcome');
    CalendarView.highlightDate(null);
}

/** 更新提醒角标 */
async function updateReminderBadge() {
    try {
        const due = await API.getDueReminders();
        const count = due.length;
        AppState.reminderCount = count;

        const badge = document.getElementById('reminder-badge');
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
            // 如果之前是0，加脉冲动画
            if (AppState._prevReminderCount === 0) {
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 400);
            }
        } else {
            badge.classList.add('hidden');
        }
        AppState._prevReminderCount = count;

        // 浏览器桌面通知
        if (count > 0 && Notification.permission === 'granted') {
            const latest = due[0];
            new Notification('📔 实习日记提醒', {
                body: latest.title,
                icon: '/static/img/placeholder.svg',
            });
        }
    } catch (e) {
        // 静默失败
    }
}

/** 请求通知权限 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

/* === 快速记录对话框 === */

/** 从文本中检测日期 */
function detectDateFromText(text) {
    const today = new Date();

    // 今天
    if (/今天/.test(text)) return todayStr();

    // 昨天
    if (/昨天/.test(text)) {
        const d = new Date(today);
        d.setDate(d.getDate() - 1);
        return formatDate(d);
    }

    // 明天
    if (/明天/.test(text)) {
        const d = new Date(today);
        d.setDate(d.getDate() + 1);
        return formatDate(d);
    }

    // 前天
    if (/前天/.test(text)) {
        const d = new Date(today);
        d.setDate(d.getDate() - 2);
        return formatDate(d);
    }

    // 后天
    if (/后天/.test(text)) {
        const d = new Date(today);
        d.setDate(d.getDate() + 2);
        return formatDate(d);
    }

    // 具体日期: "6月22日" 或 "06月22日" 或 "6.22" 或 "6/22"
    const match = text.match(/(\d{1,2})[月.\-/](\d{1,2})[日]?/);
    if (match) {
        const month = parseInt(match[1]);
        const day = parseInt(match[2]);
        const year = today.getFullYear();
        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    // 默认：今天
    return todayStr();
}

/** 打开快速记录对话框 */
function openQuickRecord() {
    const modal = document.getElementById('quick-record-modal');
    const input = document.getElementById('quick-record-input');
    const dateInput = document.getElementById('quick-record-date');
    const preview = document.getElementById('quick-record-preview');
    const saveBtn = document.getElementById('quick-record-save');

    // 默认日期为今天
    dateInput.value = todayStr();

    // 清空
    input.value = '';
    preview.classList.add('hidden');
    preview.textContent = '';
    saveBtn.classList.add('hidden');

    modal.classList.remove('hidden');
    input.focus();
}

/** 关闭快速记录对话框 */
function closeQuickRecord() {
    document.getElementById('quick-record-modal').classList.add('hidden');
}

/* === 初始化应用 === */
async function initApp() {
    // 渲染日历
    await CalendarView.render();

    // 按钮事件
    // 快速记录按钮
    document.getElementById('btn-quick-record').addEventListener('click', openQuickRecord);

    // === 导出按钮 + 下拉菜单 ===
    const btnExport = document.getElementById('btn-export');
    const exportDropdown = document.getElementById('export-dropdown');

    btnExport.addEventListener('click', (e) => {
        e.stopPropagation();
        exportDropdown.classList.toggle('hidden');
    });

    // 点击其他地方关闭下拉
    document.addEventListener('click', () => {
        exportDropdown.classList.add('hidden');
    });

    exportDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // 导出选项
    exportDropdown.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', async () => {
            exportDropdown.classList.add('hidden');
            const action = item.dataset.action;
            let url, filename;
            if (action === 'export-backup') {
                url = '/api/export/backup';
                filename = `diary_backup_${todayStr()}.zip`;
            } else {
                url = '/api/export/markdown';
                filename = `diary_export_${todayStr()}.md`;
            }
            try {
                showToast('正在导出...');
                const res = await fetch(url);
                if (!res.ok) throw new Error('导出失败');
                const blob = await res.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(a.href);
                showToast('导出完成', 'success');
            } catch (e) {
                showToast('导出失败：' + e.message, 'error');
            }
        });
    });

    // === 导入按钮 ===
    const importFileInput = document.getElementById('import-file-input');

    importFileInput.addEventListener('change', () => {
        const file = importFileInput.files[0];
        if (!file) return;
        showImportModeDialog(file);
        importFileInput.value = '';
    });

    function showImportModeDialog(file) {
        const isZip = file.name.toLowerCase().endsWith('.zip');
        const isMd = file.name.toLowerCase().endsWith('.md');
        const apiPath = isMd ? '/api/import/markdown' : '/api/import';
        const typeLabel = isZip ? '📦 完整备份 (.zip)' : isMd ? '📄 日记文档 (.md)' : '❓ 未知格式';
        const typeNote = isMd ? '<p style="font-size:12px;color:var(--color-accent);margin-top:4px;">💡 .md 导入不会清空照片，仅更新日记文本内容</p>' : '';

        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal" style="max-width:420px;">
                <div class="modal-header">
                    <span class="modal-title">📥 导入日记</span>
                    <button class="modal-close">&times;</button>
                </div>
                <p style="margin-bottom:4px;font-size:14px;color:var(--color-text-secondary);">
                    文件：<strong>${file.name}</strong>
                </p>
                <p style="margin-bottom:12px;font-size:12px;color:var(--color-text-muted);">
                    类型：${typeLabel}
                </p>
                ${typeNote}
                <div style="display:flex;flex-direction:column;gap:8px;margin-top:12px;">
                    <button class="btn btn-danger btn-full" id="mode-overwrite">
                        🔴 覆盖所有内容
                    </button>
                    <button class="btn btn-primary btn-full" id="mode-merge">
                        🟢 在原有基础上更新
                    </button>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline close-btn">取消</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        function close() { overlay.remove(); }

        async function doImport(mode) {
            close();
            showToast('正在导入...');
            try {
                const fd = new FormData();
                fd.append('file', file);
                const res = await fetch(apiPath + '?mode=' + mode, { method: 'POST', body: fd });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({ error: '请求失败' }));
                    throw new Error(err.error || res.statusText);
                }
                const result = await res.json();
                const total = result.created + result.merged;
                if (total === 0) {
                    showToast('没有需要更新的内容', 'success');
                } else {
                    showToast(`导入完成！新增 ${result.created} 条，合并 ${result.merged} 条`, 'success');
                }
                await CalendarView.render();
                if (AppState.currentView === 'entry') goHome();
            } catch (err) {
                showToast('导入失败：' + err.message, 'error');
            }
        }

        document.getElementById('mode-overwrite').addEventListener('click', async () => {
            const ok = await showConfirm('⚠️ 覆盖模式将清空所有内容，确定继续？');
            if (ok) await doImport('overwrite');
        });
        document.getElementById('mode-merge').addEventListener('click', () => doImport('merge'));

        overlay.querySelector('.modal-close').addEventListener('click', close);
        overlay.querySelector('.close-btn').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    }

    // 快速记录对话框事件
    const quickModal = document.getElementById('quick-record-modal');
    const quickInput = document.getElementById('quick-record-input');
    const quickDate = document.getElementById('quick-record-date');
    const quickPreview = document.getElementById('quick-record-preview');
    const quickSave = document.getElementById('quick-record-save');
    let quickFormattedMd = '';

    // 关闭按钮
    document.getElementById('quick-record-close').addEventListener('click', closeQuickRecord);
    document.getElementById('quick-record-cancel').addEventListener('click', closeQuickRecord);
    quickModal.addEventListener('click', (e) => {
        if (e.target === quickModal) closeQuickRecord();
    });

    // 输入时自动检测日期
    quickInput.addEventListener('input', () => {
        const detected = detectDateFromText(quickInput.value);
        if (detected) quickDate.value = detected;
    });

    // 预览排版
    document.getElementById('quick-record-format').addEventListener('click', async () => {
        const rawText = quickInput.value.trim();
        if (!rawText) {
            showToast('请先输入行程内容', 'error');
            return;
        }
        try {
            const result = await API.autoFormat(rawText);
            quickFormattedMd = result.formatted_md;
            quickPreview.textContent = result.formatted_md;
            quickPreview.classList.remove('hidden');
            quickSave.classList.remove('hidden');
        } catch (err) {
            showToast('排版失败：' + err.message, 'error');
        }
    });

    // 保存日记
    quickSave.addEventListener('click', async () => {
        const date = quickDate.value;
        if (!date) {
            showToast('请选择日期', 'error');
            return;
        }
        try {
            await API.updateEntry(date, {
                content_md: quickFormattedMd,
                title: '',
                mood: '',
            });
            showToast(`已保存到 ${formatDateCN(date)}`, 'success');
            closeQuickRecord();
            await CalendarView.render();
            // 如果当前打开的正是这个日期，刷新显示
            if (AppState.currentEntryDate === date && AppState.currentView === 'entry') {
                await EntryView.render(date);
            }
        } catch (err) {
            showToast('保存失败：' + err.message, 'error');
        }
    });

    // 快捷键 Ctrl+Shift+N 打开快速记录
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
            e.preventDefault();
            openQuickRecord();
        }
    });

    document.getElementById('btn-new-entry').addEventListener('click', () => {
        newEntry(todayStr());
    });

    document.getElementById('btn-reminders').addEventListener('click', () => {
        RemindersView.show();
    });

    // 更新按钮
    document.getElementById('btn-update').addEventListener('click', async () => {
        showToast('正在检查更新...');
        try {
            const checkRes = await fetch('/api/update/check', { method: 'POST' });
            const checkData = await checkRes.json();
            if (!checkData.has_update) {
                showToast('已是最新版本 ✨', 'success');
                return;
            }
            const confirmed = await showConfirm(checkData.message + '，是否拉取更新？\n更新后需刷新页面生效');
            if (!confirmed) return;
            const pullRes = await fetch('/api/update/pull', { method: 'POST' });
            const pullData = await pullRes.json();
            if (pullData.success) {
                showToast('更新完成！请刷新页面', 'success');
            } else {
                showToast('更新失败：' + pullData.message, 'error');
            }
        } catch (e) {
            showToast('更新失败：' + e.message, 'error');
        }
    });

    document.getElementById('btn-notes').addEventListener('click', () => {
        NotesView.show();
    });

    document.getElementById('btn-reminder-panel').addEventListener('click', () => {
        RemindersView.show();
    });

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            newEntry(todayStr());
        }
        if (e.key === 'Escape') {
            // 优先关闭快速记录对话框
            const quickModal = document.getElementById('quick-record-modal');
            if (quickModal && !quickModal.classList.contains('hidden')) {
                closeQuickRecord();
                return;
            }
            const lightbox = document.getElementById('lightbox');
            if (!lightbox.classList.contains('hidden')) {
                lightbox.classList.add('hidden');
                return;
            }
            if (AppState.currentView === 'entry') {
                goHome();
            }
            if (AppState.currentView === 'reminders' || AppState.currentView === 'notes') {
                goHome();
            }
        }
    });

    // 灯箱关闭
    document.getElementById('lightbox').addEventListener('click', (e) => {
        if (e.target.classList.contains('lightbox') || e.target.classList.contains('lightbox-close')) {
            document.getElementById('lightbox').classList.add('hidden');
        }
    });

    // 提醒轮询（每 30 秒）
    requestNotificationPermission();
    updateReminderBadge();
    setInterval(updateReminderBadge, 30000);
}

// 启动
document.addEventListener('DOMContentLoaded', initApp);
