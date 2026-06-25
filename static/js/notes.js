/* === 工作笔记组件 === */

const NotesView = {
    _projects: [],
    _selectedProjectId: null,
    _notes: [],

    async show() {
        AppState.currentView = 'notes';
        AppState.currentEntryDate = null;
        this._selectedProjectId = null;
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById('view-notes').classList.add('active');
        await this._loadProjects();
        this._render();
    },

    async _loadProjects() {
        try {
            const res = await fetch('/api/projects');
            this._projects = await res.json();
        } catch (e) {
            this._projects = [];
        }
    },

    async _loadNotes(projectId) {
        try {
            const res = await fetch(`/api/projects/${projectId}/notes`);
            this._notes = await res.json();
        } catch (e) {
            this._notes = [];
        }
    },

    _render() {
        const container = document.getElementById('view-notes');
        const hasProjects = this._projects.length > 0;

        let html = '<div class="notes-layout">';

        // 左侧项目列表
        html += '<div class="notes-sidebar">';
        html += '<div class="notes-sidebar-header">';
        html += '<h3>📋 项目</h3>';
        html += '<button class="btn btn-sm btn-primary" id="btn-add-project">+ 新建</button>';
        html += '</div>';
        html += '<div class="notes-project-list">';
        if (hasProjects) {
            for (const p of this._projects) {
                const selected = p.id === this._selectedProjectId ? 'selected' : '';
                html += `
                    <div class="notes-project-item ${selected}" data-project-id="${p.id}">
                        <span class="notes-project-name">${escHtml(p.name)}</span>
                        <span class="notes-project-count">${p.note_count || 0}</span>
                    </div>
                `;
            }
        } else {
            html += '<p class="notes-empty">暂无项目，点击上方按钮创建</p>';
        }
        html += '</div>';
        html += '</div>';

        // 右侧内容区
        html += '<div class="notes-content">';
        if (this._selectedProjectId) {
            const project = this._projects.find(p => p.id === this._selectedProjectId);
            html += `
                <div class="notes-content-header">
                    <h2>${escHtml(project ? project.name : '')}</h2>
                    <div style="display:flex;gap:6px;">
                        <button class="btn btn-sm btn-outline" id="btn-edit-project">✏️ 编辑项目</button>
                        <button class="btn btn-sm btn-primary" id="btn-add-note">+ 新笔记</button>
                    </div>
                </div>
            `;
            html += '<div class="notes-list">';
            if (this._notes.length > 0) {
                for (const n of this._notes) {
                    const t = n.title || '无标题';
                    html += `
                        <div class="notes-card" data-note-id="${n.id}">
                            <div class="notes-card-body">
                                <div class="notes-card-title">${escHtml(t)}</div>
                                <div class="notes-card-preview">${escHtml(this._preview(n.content_md))}</div>
                            </div>
                            <span class="notes-card-time">${this._timeStr(n.updated_at)}</span>
                        </div>
                    `;
                }
            } else {
                html += '<p class="notes-empty">暂无笔记，点击"新笔记"创建</p>';
            }
            html += '</div>';
        } else {
            html += '<div class="notes-welcome"><span>📋</span><p>选择一个项目查看笔记</p></div>';
        }
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
        this._bindEvents();
    },

    _bindEvents() {
        // 新建项目
        const addBtn = document.getElementById('btn-add-project');
        if (addBtn) {
            addBtn.addEventListener('click', () => this._showProjectForm());
        }

        // 项目点击
        document.querySelectorAll('.notes-project-item').forEach(item => {
            item.addEventListener('click', async () => {
                this._selectedProjectId = parseInt(item.dataset.projectId);
                await this._loadNotes(this._selectedProjectId);
                this._render();
            });
        });

        // 新建笔记
        const addNoteBtn = document.getElementById('btn-add-note');
        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', () => this._showNoteForm());
        }

        // 编辑项目
        const editProjectBtn = document.getElementById('btn-edit-project');
        if (editProjectBtn) {
            editProjectBtn.addEventListener('click', () => {
                const p = this._projects.find(p => p.id === this._selectedProjectId);
                if (p) this._showProjectForm(p);
            });
        }

        // 笔记点击
        document.querySelectorAll('.notes-card').forEach(card => {
            card.addEventListener('click', () => {
                const noteId = parseInt(card.dataset.noteId);
                const note = this._notes.find(n => n.id === noteId);
                if (note) this._showNoteForm(note);
            });
        });
    },

    _showProjectForm(existing) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal" style="max-width:420px;">
                <div class="modal-header">
                    <span class="modal-title">${existing ? '✏️ 编辑项目' : '➕ 新建项目'}</span>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="form-group">
                    <label class="label">项目名称</label>
                    <input class="input" id="project-name" value="${escHtml(existing ? existing.name : '')}" placeholder="例如：街道办工作">
                </div>
                <div class="form-group">
                    <label class="label">描述（可选）</label>
                    <input class="input" id="project-desc" value="${escHtml(existing ? existing.description : '')}" placeholder="简短描述">
                </div>
                <div class="modal-footer">
                    ${existing ? '<button class="btn btn-danger btn-sm" id="btn-delete-project">🗑️ 删除项目</button>' : ''}
                    <button class="btn btn-outline cancel-btn">取消</button>
                    <button class="btn btn-primary save-btn">${existing ? '更新' : '创建'}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        function close() { overlay.remove(); }

        overlay.querySelector('.modal-close').addEventListener('click', close);
        overlay.querySelector('.cancel-btn').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        overlay.querySelector('.save-btn').addEventListener('click', async () => {
            const name = document.getElementById('project-name').value.trim();
            if (!name) { showToast('请输入项目名称', 'error'); return; }
            const desc = document.getElementById('project-desc').value.trim();
            try {
                if (existing) {
                    await fetch(`/api/projects/${existing.id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, description: desc }),
                    });
                } else {
                    const res = await fetch('/api/projects', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, description: desc }),
                    });
                    const created = await res.json();
                    existing = created;  // 用于后续选中
                }
                close();
                showToast(existing ? '项目已更新' : '项目已创建', 'success');
                await this._loadProjects();
                this._selectedProjectId = existing.id;
                await this._loadNotes(this._selectedProjectId);
                this._render();
            } catch (e) {
                showToast('操作失败', 'error');
            }
        });

        const deleteBtn = document.getElementById('btn-delete-project');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                const ok = await showConfirm('删除项目将同时删除其下所有笔记，确定？');
                if (!ok) return;
                try {
                    await fetch(`/api/projects/${existing.id}`, { method: 'DELETE' });
                    close();
                    showToast('项目已删除', 'success');
                    this._selectedProjectId = null;
                    await this._loadProjects();
                    this._render();
                } catch (e) {
                    showToast('删除失败', 'error');
                }
            });
        }
    },

    _showNoteForm(note) {
        const isNew = !note;
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal" style="max-width:600px;">
                <div class="modal-header">
                    <span class="modal-title">${isNew ? '➕ 新建笔记' : '✏️ 编辑笔记'}</span>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="form-group">
                    <input class="input" id="note-title" value="${escHtml(note ? note.title : '')}" placeholder="笔记标题" style="font-size:18px;font-weight:600;">
                </div>
                <div class="form-group">
                    <textarea class="textarea" id="note-content" placeholder="写笔记...&#10;&#10;支持 Markdown 语法" style="min-height:280px;">${escHtml(note ? note.content_md : '')}</textarea>
                </div>
                <div class="modal-footer">
                    ${!isNew ? '<button class="btn btn-danger btn-sm" id="btn-delete-note">🗑️ 删除</button>' : ''}
                    <button class="btn btn-outline cancel-btn">取消</button>
                    <button class="btn btn-primary save-btn">${isNew ? '创建' : '保存'}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        function close() { overlay.remove(); }

        overlay.querySelector('.modal-close').addEventListener('click', close);
        overlay.querySelector('.cancel-btn').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        overlay.querySelector('.save-btn').addEventListener('click', async () => {
            const title = document.getElementById('note-title').value.trim();
            const content = document.getElementById('note-content').value;
            try {
                if (isNew) {
                    await fetch(`/api/projects/${this._selectedProjectId}/notes`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, content_md: content }),
                    });
                } else {
                    await fetch(`/api/notes/${note.id}`, {
                        method: 'PUT', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, content_md: content }),
                    });
                }
                close();
                showToast(isNew ? '笔记已创建' : '笔记已保存', 'success');
                await this._loadNotes(this._selectedProjectId);
                this._render();
            } catch (e) {
                showToast('操作失败', 'error');
            }
        });

        const deleteNoteBtn = document.getElementById('btn-delete-note');
        if (deleteNoteBtn) {
            deleteNoteBtn.addEventListener('click', async () => {
                const ok = await showConfirm('确定删除这条笔记？');
                if (!ok) return;
                try {
                    const res = await fetch(`/api/notes/${note.id}`, { method: 'DELETE' });
                    if (!res.ok) throw new Error('删除失败');
                    close();
                    showToast('笔记已删除', 'success');
                    await Promise.all([this._loadProjects(), this._loadNotes(this._selectedProjectId)]);
                    this._render();
                } catch (e) {
                    showToast('删除失败：' + e.message, 'error');
                }
            });
        }
    },

    _preview(md) {
        if (!md) return '（空）';
        return md.replace(/[#*`>\-\[\]]/g, '').substring(0, 80) || '（空）';
    },

    _timeStr(ts) {
        try { return ts ? ts.slice(0, 10) : ''; } catch (e) { return ''; }
    },

};
