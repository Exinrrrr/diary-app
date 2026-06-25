"""实习日记 Web 应用 — Flask 入口"""

import os
import sys
import subprocess
from flask import Flask, jsonify
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
    print("   打开浏览器访问: http://localhost:5000\n")
    app.run(debug=DEBUG, host='127.0.0.1', port=5000)
