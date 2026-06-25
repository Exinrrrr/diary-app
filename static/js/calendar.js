/* === 日历组件 === */

const CalendarView = {
    entries: {},   // { '2026-06-22': { has_photos, ... } }

    async render() {
        const container = document.getElementById('calendar-container');
        const { year, month } = AppState.currentMonth;
        const info = getMonthInfo(year, month);

        // 加载当月条目
        try {
            const entries = await API.getEntries(year, month);
            this.entries = {};
            for (const e of entries) {
                this.entries[e.date] = e;
            }
        } catch (e) {
            this.entries = {};
        }

        // 星期头
        const weekdays = ['一', '二', '三', '四', '五', '六', '日'];

        let html = `
            <div class="calendar-header">
                <span class="calendar-month">${year}年${month}月</span>
                <div class="calendar-nav">
                    <button id="cal-prev" title="上月">◀</button>
                    <button id="cal-today" class="calendar-today-btn">今天</button>
                    <button id="cal-next" title="下月">▶</button>
                </div>
            </div>
            <div class="calendar-weekdays">
                ${weekdays.map(d => `<span>${d}</span>`).join('')}
            </div>
            <div class="calendar-grid">
        `;

        // 填充前面空白格
        for (let i = 0; i < info.startOffset; i++) {
            html += '<div class="calendar-cell other-month"></div>';
        }

        // 日期格
        const today = todayStr();
        for (let day = 1; day <= info.daysInMonth; day++) {
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isToday = dateStr === today;
            const isSelected = dateStr === AppState.currentEntryDate;
            const hasEntry = dateStr in this.entries;
            const hasPhotos = hasEntry && this.entries[dateStr].has_photos;

            let cellClass = 'calendar-cell';
            if (isToday) cellClass += ' today';
            if (isSelected) cellClass += ' selected';
            if (hasEntry) cellClass += ' has-entry';

            html += `
                <div class="${cellClass}" data-date="${dateStr}">
                    <span class="cell-day">${day}</span>
                    <div class="cell-indicators">
                        ${hasEntry ? '<span class="cell-dot"></span>' : ''}
                        ${hasPhotos ? '<span class="cell-dot photo"></span>' : ''}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;

        // 绑定事件
        this.bindEvents();
    },

    bindEvents() {
        // 日期点击
        document.querySelectorAll('.calendar-cell[data-date]').forEach(cell => {
            cell.addEventListener('click', () => {
                const date = cell.dataset.date;
                if (date in this.entries) {
                    openEntry(date);
                } else {
                    newEntry(date);
                }
            });
        });

        // 导航
        document.getElementById('cal-prev').addEventListener('click', () => {
            if (AppState.currentMonth.month === 1) {
                AppState.currentMonth.month = 12;
                AppState.currentMonth.year--;
            } else {
                AppState.currentMonth.month--;
            }
            this.render();
        });

        document.getElementById('cal-next').addEventListener('click', () => {
            if (AppState.currentMonth.month === 12) {
                AppState.currentMonth.month = 1;
                AppState.currentMonth.year++;
            } else {
                AppState.currentMonth.month++;
            }
            this.render();
        });

        document.getElementById('cal-today').addEventListener('click', () => {
            const today = new Date();
            AppState.currentMonth.year = today.getFullYear();
            AppState.currentMonth.month = today.getMonth() + 1;
            this.render();
        });
    },

    highlightDate(date) {
        AppState.currentEntryDate = date;
        document.querySelectorAll('.calendar-cell.selected').forEach(c => c.classList.remove('selected'));
        if (date) {
            const cell = document.querySelector(`.calendar-cell[data-date="${date}"]`);
            if (cell) cell.classList.add('selected');
        }
    },
};
