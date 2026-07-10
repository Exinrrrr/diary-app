/* === 工具函数 === */

/** 格式化日期为 YYYY-MM-DD */
function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

/** 格式化日期为中文显示 */
function formatDateCN(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const y = d.getFullYear();
    const m = d.getMonth() + 1;
    const day = d.getDate();
    const w = weekdays[d.getDay()];
    return `${y}年${m}月${day}日 · 星期${w}`;
}

/** 解析 YYYY-MM-DD 为 Date 对象 */
function parseDate(dateStr) {
    return new Date(dateStr + 'T00:00:00');
}

/** 获取今天的日期字符串 */
function todayStr() {
    return formatDate(new Date());
}

/** 获取当前月份信息 */
function getMonthInfo(year, month) {
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startDayOfWeek = firstDay.getDay(); // 0=Sun
    const daysInMonth = lastDay.getDate();
    // 日历显示从周一开始，转换：周日=6，周一=0...
    const startOffset = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;
    return { firstDay, lastDay, startOffset, daysInMonth };
}

/** Toast 通知 */
function showToast(message, type = '') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

/** 确认对话框 */
function showConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.innerHTML = `
            <div class="confirm-box">
                <p>${message}</p>
                <div class="confirm-buttons">
                    <button class="btn btn-outline" data-action="cancel">取消</button>
                    <button class="btn btn-danger" data-action="confirm">确认</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action === 'confirm') {
                overlay.remove();
                resolve(true);
            } else if (action === 'cancel' || e.target === overlay) {
                overlay.remove();
                resolve(false);
            }
        });
    });
}

/** Debounce */
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/** HTML 转义（全项目公用） */
function escHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/** 统一绑定弹窗关闭事件 */
function bindModalClose(overlay, closeFn) {
    const closeBtn = overlay.querySelector('.modal-close');
    const cancelBtn = overlay.querySelector('.cancel-btn');
    if (closeBtn) closeBtn.addEventListener('click', closeFn);
    if (cancelBtn) cancelBtn.addEventListener('click', closeFn);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeFn(); });
}

/** 提取文本片段 */
function extractSnippet(text, query, before = 30, after = 50) {
    if (!text || !query) return '';
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx < 0) return '';
    const start = Math.max(0, idx - before);
    const end = Math.min(text.length, idx + query.length + after);
    return (start > 0 ? '...' : '') + text.slice(start, end) + (end < text.length ? '...' : '');
}
