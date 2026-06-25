"""实习日记 Web 应用 — Flask 入口"""

import os
import sys
from flask import Flask
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
    from routes.migrate import migrate_bp
    from routes.io import io_bp
    from routes.notes import notes_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(entries_bp, url_prefix='/api')
    app.register_blueprint(photos_bp, url_prefix='/api')
    app.register_blueprint(reminders_bp, url_prefix='/api')
    app.register_blueprint(migrate_bp, url_prefix='/api')
    app.register_blueprint(io_bp, url_prefix='/api')
    app.register_blueprint(notes_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    # 首次运行初始化数据库
    if not os.path.exists(os.path.join(DATA_DIR, 'diary.db')):
        init_db()

    app = create_app()
    print("\n📔 实习日记应用已启动！")
    print("   打开浏览器访问: http://localhost:5000\n")
    app.run(debug=DEBUG, host='127.0.0.1', port=5000)
