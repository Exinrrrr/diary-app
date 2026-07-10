"""实习日记 Web 应用 — Flask 入口"""

import os
import sys
import subprocess
from flask import Flask, jsonify, request, redirect, session, render_template
from config import SECRET_KEY, DEBUG, DATA_DIR, ENTRIES_DIR, PHOTOS_DIR
from database.db import init_db, close_db, get_db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DATA_DIR'] = DATA_DIR
    app.config['ENTRIES_DIR'] = ENTRIES_DIR
    app.config['PHOTOS_DIR'] = PHOTOS_DIR

    # 确保数据目录存在
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)

    # 注册数据库清理
    app.teardown_appcontext(close_db)

    # 密码锁
    PASSWORD = '610223'

    @app.before_request
    def check_lock():
        path = request.path
        if path.startswith('/static/') or path == '/lock' or path.startswith('/api/auth/'):
            return
        if not session.get('unlocked'):
            return redirect('/lock')

    @app.route('/lock', methods=['GET'])
    def lock_page():
        return render_template('lock.html')

    @app.route('/api/auth/unlock', methods=['POST'])
    def unlock():
        data = request.get_json()
        if data and data.get('password') == PASSWORD:
            session['unlocked'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '密码错误'}), 401

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'success': True})

    @app.route('/api/auth/ip', methods=['GET'])
    def get_ip():
        import subprocess
        try:
            ip = subprocess.check_output(['ipconfig', 'getifaddr', 'en0'], text=True).strip()
            return jsonify({'ip': ip, 'url': f'http://{ip}:8080'})
        except:
            return jsonify({'ip': None})

    # 搜索 API
    @app.route('/api/search')
    def search():
        q = request.args.get('q', '').strip()
        if not q or len(q) < 1:
            return jsonify([])

        from database.db import get_db
        db = get_db()
        results = []
        like = f'%{q}%'
        seen = set()

        def snippet(content, query):
            if not content: return ''
            idx = content.lower().find(query.lower())
            if idx < 0: return ''
            start = max(0, idx - 30)
            end = min(len(content), idx + len(query) + 50)
            s = content[start:end]
            return ('...' if start > 0 else '') + s + ('...' if end < len(content) else '')

        # 搜索日记标题
        for e in db.execute("SELECT id, date, title FROM entries WHERE title LIKE ? ORDER BY date DESC LIMIT 20", (like,)).fetchall():
            if e['id'] in seen: continue
            seen.add(e['id'])
            md_path = os.path.join(ENTRIES_DIR, f"{e['date']}.md")
            content = ''
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f: content = f.read()
            results.append({'type': 'diary', 'id': e['id'], 'date': e['date'], 'title': e['title'] or '无标题', 'snippet': snippet(content, q)})

        # 搜索日记文件内容
        if os.path.isdir(ENTRIES_DIR):
            for fname in os.listdir(ENTRIES_DIR):
                if not fname.endswith('.md'): continue
                date = fname.replace('.md', '')
                if date in seen: continue
                md_path = os.path.join(ENTRIES_DIR, fname)
                try:
                    with open(md_path, 'r', encoding='utf-8') as f: content = f.read()
                    if q.lower() not in content.lower(): continue
                    entry = db.execute("SELECT id, title FROM entries WHERE date=?", (date,)).fetchone()
                    eid = entry['id'] if entry else None
                    seen.add(eid)
                    results.append({'type': 'diary', 'id': eid, 'date': date, 'title': entry['title'] if entry else '无标题', 'snippet': snippet(content, q)})
                except: pass

        # 搜索笔记
        for n in db.execute("SELECT n.id, n.title, n.content_md, n.project_id, p.name as project FROM notes n LEFT JOIN projects p ON p.id=n.project_id WHERE n.title LIKE ? OR n.content_md LIKE ? ORDER BY n.updated_at DESC LIMIT 10", (like, like)).fetchall():
            results.append({'type': 'note', 'id': n['id'], 'project_id': n['project_id'], 'title': n['title'] or '无标题', 'project': n['project'] or '', 'snippet': snippet(n['content_md'], q)})

        return jsonify(results[:30])

    # 注册路由
    from routes.pages import pages_bp
    from routes.entries import entries_bp
    from routes.photos import photos_bp
    from routes.reminders import reminders_bp
    from routes.io import io_bp
    from routes.notes import notes_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(entries_bp, url_prefix='/api')
    app.register_blueprint(photos_bp, url_prefix='/api')
    app.register_blueprint(reminders_bp, url_prefix='/api')
    app.register_blueprint(io_bp, url_prefix='/api')
    app.register_blueprint(notes_bp, url_prefix='/api')

    # 更新按钮 API：检查是否有新版本
    @app.route('/api/update/check', methods=['POST'])
    def check_update():
        try:
            import os
            base = os.path.dirname(os.path.abspath(__file__))
            # fetch 获取远程信息
            subprocess.run(['git', 'fetch'], cwd=base, capture_output=True, text=True, timeout=15)
            # 比较本地和远程
            behind = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD..origin/main'],
                cwd=base, capture_output=True, text=True, timeout=10
            )
            count = int(behind.stdout.strip())
            if count == 0:
                return jsonify({'has_update': False, 'message': '已是最新版本'})
            else:
                return jsonify({'has_update': True, 'message': f'发现 {count} 个新提交'})
        except Exception as e:
            return jsonify({'has_update': False, 'message': f'检查失败：{e}'}), 500

    # 更新按钮 API：执行更新
    @app.route('/api/update/pull', methods=['POST'])
    def pull_update():
        try:
            import os
            result = subprocess.run(
                ['git', 'pull'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                output = result.stdout.strip() or '已更新'
                return jsonify({'success': True, 'message': output})
            else:
                return jsonify({'success': False, 'message': result.stderr.strip() or '更新失败'}), 500
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'message': '更新超时，请检查网络'}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    return app

if __name__ == '__main__':
    # 首次运行初始化数据库
    if not os.path.exists(os.path.join(DATA_DIR, 'diary.db')):
        init_db()

    app = create_app()
    print("\n📔 实习日记应用已启动！")
    print("   打开浏览器访问: http://localhost:8080\n")
    app.run(debug=DEBUG, host='0.0.0.0', port=8080)
