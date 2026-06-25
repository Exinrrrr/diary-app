/* === 后端 API 调用封装 === */

const API = {
    // ===== 日记 =====

    /** 获取某月的日记列表 */
    async getEntries(year, month) {
        const res = await fetch(`/api/entries?year=${year}&month=${month}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 获取某一天的日记 */
    async getEntry(date) {
        const res = await fetch(`/api/entries/${date}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 创建日记 */
    async createEntry(date, data = {}) {
        const res = await fetch('/api/entries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, ...data }),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 更新日记 */
    async updateEntry(date, data) {
        const res = await fetch(`/api/entries/${date}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 删除日记 */
    async deleteEntry(date) {
        const res = await fetch(`/api/entries/${date}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 自动格式化 */
    async autoFormat(rawText) {
        const res = await fetch('/api/entries/auto-format', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ raw_text: rawText }),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // ===== 照片 =====

    /** 上传照片 */
    async uploadPhotos(date, files) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('photos', file);
        }
        const res = await fetch(`/api/photos/upload/${date}`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 删除照片 */
    async deletePhoto(photoId) {
        const res = await fetch(`/api/photos/${photoId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // ===== 提醒 =====

    /** 获取所有提醒 */
    async getReminders(status = '') {
        const params = status ? `?status=${status}` : '';
        const res = await fetch(`/api/reminders${params}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 获取到期提醒 */
    async getDueReminders() {
        const res = await fetch('/api/reminders/due');
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 创建提醒 */
    async createReminder(data) {
        const res = await fetch('/api/reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 更新提醒 */
    async updateReminder(id, data) {
        const res = await fetch(`/api/reminders/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 删除提醒 */
    async deleteReminder(id) {
        const res = await fetch(`/api/reminders/${id}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    /** 忽略提醒 */
    async dismissReminder(id) {
        const res = await fetch(`/api/reminders/${id}/dismiss`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // ===== 迁移 =====

    /** 导入旧日记 */
    async migrateDiary() {
        const res = await fetch('/api/migrate', {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
};
