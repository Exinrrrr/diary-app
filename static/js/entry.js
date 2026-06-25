/* === 日记详情 / 编辑组件 === */

const EntryView = {
    _currentData: null,  // 当前加载的条目数据

    /** 渲染阅读模式 */
    async render(date) {
        const container = document.getElementById('view-entry');
        container.innerHTML = '<div class="entry-container"><p style="text-align:center;color:var(--color-text-muted);padding:40px;">加载中...</p></div>';

        let data;
        try {
            data = await API.getEntry(date);
        } catch (e) {
            container.innerHTML = `<div class="entry-container"><p style="text-align:center;color:var(--color-danger);padding:40px;">加载失败：${e.message}</p></div>`;
            return;
        }

        if (!data) {
            // 日记不存在，直接进入编辑模式
            this.renderEdit(date);
            return;
        }

        this._currentData = data;

        const photosHtml = this._renderPhotos(data.photos || [], false);
        const moodHtml = data.mood ? `<span class="entry-mood">${data.mood}</span>` : '';

        container.innerHTML = `
            <div class="entry-container">
                <div class="entry-header">
                    <div class="entry-date">${formatDateCN(date)}</div>
                    <div class="entry-title">${this._escapeHtml(data.title || '无标题')}</div>
                    <div class="entry-meta">
                        <span>${data.word_count || 0} 字</span>
                        ${moodHtml}
                    </div>
                </div>

                <div class="entry-content">
                    ${this._mdToHtml(data.content_md || '')}
                </div>

                ${photosHtml}

                <div class="entry-actions">
                    <div class="entry-actions-left">
                        <button class="btn btn-outline btn-sm" onclick="goHome()">← 返回日历</button>
                    </div>
                    <div class="entry-actions-right">
                        <button class="btn btn-primary" id="btn-edit-entry">✏️ 编辑</button>
                        <button class="btn btn-danger btn-sm" id="btn-delete-entry">🗑️ 删除</button>
                    </div>
                </div>
            </div>
        `;

        // 绑定事件
        document.getElementById('btn-edit-entry').addEventListener('click', () => {
            editEntry(date);
        });
        document.getElementById('btn-delete-entry').addEventListener('click', async () => {
            const confirmed = await showConfirm(`确定要删除 ${formatDateCN(date)} 的日记吗？\n照片也会一并删除，此操作不可撤销。`);
            if (confirmed) {
                try {
                    await API.deleteEntry(date);
                    showToast('日记已删除', 'success');
                    goHome();
                    await CalendarView.render();
                } catch (e) {
                    showToast('删除失败：' + e.message, 'error');
                }
            }
        });

        // 照片灯箱
        document.querySelectorAll('.photo-card:not(.photo-upload)').forEach(card => {
            card.addEventListener('click', () => {
                const img = card.querySelector('img');
                if (img) {
                    const lightbox = document.getElementById('lightbox');
                    document.getElementById('lightbox-img').src = img.dataset.full || img.src;
                    document.getElementById('lightbox-caption').textContent = img.alt || '';
                    lightbox.classList.remove('hidden');
                }
            });
        });
    },

    /** 渲染编辑模式 */
    async renderEdit(date) {
        const container = document.getElementById('view-entry');
        container.innerHTML = '<div class="entry-container"><p style="text-align:center;color:var(--color-text-muted);padding:40px;">加载中...</p></div>';

        let data = null;
        try {
            data = await API.getEntry(date);
        } catch (e) {
            // 日记不存在，正常
        }

        this._currentData = data;

        const title = data ? data.title : '';
        const contentMd = data ? data.content_md : '';
        const mood = data ? data.mood : '';
        const photos = data ? (data.photos || []) : [];

        const photosHtml = this._renderPhotos(photos, true);

        container.innerHTML = `
            <div class="entry-container">
                <div class="entry-header">
                    <div class="entry-date">${formatDateCN(date)}</div>
                    <input type="text" class="entry-title-input" id="edit-title"
                           value="${this._escapeHtml(title)}" placeholder="日记标题（可选）">
                    <div class="mood-selector">
                        ${['😊','😌','😐','😢','💪','🎉'].map(m => `
                            <button class="mood-btn ${mood === m ? 'selected' : ''}" data-mood="${m}">${m}</button>
                        `).join('')}
                    </div>
                </div>

                <!-- 格式化工具栏 -->
                <div class="editor-toolbar">
                    <button class="toolbar-btn" data-action="bold" title="加粗">B</button>
                    <button class="toolbar-btn" data-action="heading" title="标题">H2</button>
                    <button class="toolbar-btn" data-action="list" title="列表">•</button>
                    <button class="toolbar-btn" data-action="hr" title="分隔线">—</button>
                    <button class="toolbar-btn" data-action="auto-format" title="自动格式化" style="margin-left:auto;background:var(--color-accent-light);border-color:var(--color-accent);color:var(--color-accent);">✨ 自动排版</button>
                </div>

                <textarea class="entry-editor" id="edit-content" placeholder="在这里写日记...&#10;&#10;可以用 Markdown 语法：&#10;- 列表项&#10;**加粗**&#10;## 标题">${this._escapeHtml(contentMd)}</textarea>

                ${photosHtml}

                <!-- 照片上传区 -->
                <div class="upload-zone" id="upload-zone">
                    <div class="upload-icon">📷</div>
                    <p>拖拽或点击上传照片（支持 JPG/PNG/GIF/WebP，单张不超过 20MB）</p>
                    <input type="file" id="photo-input" accept="image/*" multiple hidden>
                </div>

                <!-- 自动格式化面板（默认隐藏） -->
                <div class="auto-format-panel hidden" id="auto-format-panel">
                    <h3>✨ 自动排版</h3>
                    <p style="font-size:13px;color:var(--color-text-muted);margin-bottom:10px;">
                        将原始行程贴入下方，系统会自动按早/中/晚分组并配上 emoji
                    </p>
                    <textarea class="auto-format-input" id="auto-format-input"
                              placeholder="例如：&#10;早上去社区参观&#10;下午开会讨论了项目进展&#10;午饭吃了食堂&#10;晚上和李老师讨论了报告"></textarea>
                    <div style="display:flex;gap:8px;margin-top:10px;">
                        <button class="btn btn-primary" id="btn-do-format">🪄 开始排版</button>
                        <button class="btn btn-outline" id="btn-cancel-format">取消</button>
                    </div>
                    <div class="auto-format-preview hidden" id="auto-format-preview"></div>
                    <button class="btn btn-outline hidden" id="btn-apply-format" style="margin-top:10px;">
                        ✅ 应用排版结果
                    </button>
                </div>

                <div class="entry-actions">
                    <div class="entry-actions-left">
                        <button class="btn btn-outline btn-sm" onclick="goHome()">← 返回</button>
                    </div>
                    <div class="entry-actions-right">
                        <button class="btn btn-primary" id="btn-save-entry">💾 保存</button>
                    </div>
                </div>
            </div>
        `;

        this._bindEditEvents(date);
    },

    /** 绑定编辑模式事件 */
    _bindEditEvents(date) {
        // 心情选择
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
            });
        });

        // 工具栏
        document.querySelectorAll('.toolbar-btn[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const textarea = document.getElementById('edit-content');
                if (action === 'auto-format') {
                    document.getElementById('auto-format-panel').classList.remove('hidden');
                    return;
                }
                this._insertMarkdown(textarea, action);
            });
        });

        // 照片上传
        const uploadZone = document.getElementById('upload-zone');
        const photoInput = document.getElementById('photo-input');

        uploadZone.addEventListener('click', () => photoInput.click());
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            this._uploadPhotos(date, e.dataTransfer.files);
        });
        photoInput.addEventListener('change', () => {
            if (photoInput.files.length > 0) {
                this._uploadPhotos(date, photoInput.files);
                photoInput.value = '';
            }
        });

        // 删除已有照片
        document.querySelectorAll('.photo-remove').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const photoId = parseInt(btn.dataset.photoId);
                try {
                    await API.deletePhoto(photoId);
                    showToast('照片已删除');
                    this.renderEdit(date);
                } catch (err) {
                    showToast('删除失败：' + err.message, 'error');
                }
            });
        });

        // 自动格式化
        document.getElementById('btn-do-format').addEventListener('click', async () => {
            const rawText = document.getElementById('auto-format-input').value.trim();
            if (!rawText) {
                showToast('请先输入行程内容', 'error');
                return;
            }
            try {
                const result = await API.autoFormat(rawText);
                const preview = document.getElementById('auto-format-preview');
                preview.textContent = result.formatted_md;
                preview.classList.remove('hidden');
                document.getElementById('btn-apply-format').classList.remove('hidden');
                this._formatResult = result.formatted_md;
            } catch (err) {
                showToast('格式化失败：' + err.message, 'error');
            }
        });

        document.getElementById('btn-cancel-format').addEventListener('click', () => {
            document.getElementById('auto-format-panel').classList.add('hidden');
            document.getElementById('auto-format-preview').classList.add('hidden');
            document.getElementById('btn-apply-format').classList.add('hidden');
            document.getElementById('auto-format-input').value = '';
            this._formatResult = null;
        });

        document.getElementById('btn-apply-format').addEventListener('click', () => {
            if (this._formatResult) {
                document.getElementById('edit-content').value = this._formatResult;
                document.getElementById('auto-format-panel').classList.add('hidden');
                document.getElementById('auto-format-preview').classList.add('hidden');
                document.getElementById('btn-apply-format').classList.add('hidden');
                this._formatResult = null;
                showToast('排版结果已应用，可继续编辑后保存', 'success');
            }
        });

        // 保存
        document.getElementById('btn-save-entry').addEventListener('click', async () => {
            const title = document.getElementById('edit-title').value.trim();
            const contentMd = document.getElementById('edit-content').value;
            const moodBtn = document.querySelector('.mood-btn.selected');
            const mood = moodBtn ? moodBtn.dataset.mood : '';

            try {
                await API.updateEntry(date, {
                    title,
                    content_md: contentMd,
                    mood,
                });
                showToast('日记已保存', 'success');
                AppState.editing = false;
                await CalendarView.render();
                this.render(date);
            } catch (err) {
                showToast('保存失败：' + err.message, 'error');
            }
        });
    },

    /** 上传照片 */
    async _uploadPhotos(date, files) {
        showToast('正在上传照片...');
        try {
            const result = await API.uploadPhotos(date, files);
            showToast(`已上传 ${result.length} 张照片`, 'success');
            await CalendarView.render();
            this.renderEdit(date);
        } catch (err) {
            showToast('上传失败：' + err.message, 'error');
        }
    },

    /** 渲染照片画廊 */
    _renderPhotos(photos, editable) {
        if (!photos || photos.length === 0) {
            return '';
        }
        let html = '<div class="photo-gallery">';
        for (const photo of photos) {
            html += `
                <div class="photo-card">
                    <img src="/api/photos/${AppState.currentEntryDate}/${photo.thumb_filename}"
                         data-full="/api/photos/${AppState.currentEntryDate}/${photo.filename}"
                         alt="${this._escapeHtml(photo.original_name || '')}"
                         loading="lazy">
                    ${editable ? `<button class="photo-remove" data-photo-id="${photo.id}">×</button>` : ''}
                </div>
            `;
        }
        html += '</div>';
        return html;
    },

    /** 插入 Markdown 语法 */
    _insertMarkdown(textarea, action) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const selected = text.substring(start, end);

        let replacement = '';
        switch (action) {
            case 'bold':
                replacement = `**${selected || '加粗文字'}**`;
                break;
            case 'heading':
                replacement = `\n## ${selected || '标题'}\n`;
                break;
            case 'list':
                replacement = selected
                    ? selected.split('\n').map(l => `- ${l}`).join('\n')
                    : `- 列表项`;
                break;
            case 'hr':
                replacement = '\n---\n';
                break;
        }

        textarea.value = text.substring(0, start) + replacement + text.substring(end);
        textarea.focus();
        const newPos = start + replacement.length;
        textarea.setSelectionRange(newPos, newPos);
    },

    /** 简单 Markdown → HTML 转换 */
    _mdToHtml(md) {
        if (!md) return '<p style="color:var(--color-text-muted);">暂无内容</p>';

        let html = md;

        // 转义 HTML
        html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // 水平线
        html = html.replace(/^---$/gm, '<hr>');

        // 标题
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

        // 粗体
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // 斜体
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // 无序列表
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // 段落（连续的非空行）
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';

        // 清理空段落
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p>(\s*<h[23]>)/g, '$1');
        html = html.replace(/(<\/h[23]>)\s*<\/p>/g, '$1');
        html = html.replace(/<p>(\s*<hr>\s*)<\/p>/g, '$1');
        html = html.replace(/<p>(\s*<ul>)/g, '$1');
        html = html.replace(/(<\/ul>)\s*<\/p>/g, '$1');

        return html;
    },

    /** HTML 转义 */
    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
