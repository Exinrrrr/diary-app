#!/bin/bash
cd "$(dirname "$0")"

# 检查 Python
if ! python3 --version &>/dev/null; then
    echo "❌ 没有找到 Python3，请先安装。"
    echo "   打开终端运行：xcode-select --install"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 首次运行，正在配置环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask Pillow markdown
    echo "✅ 环境配置完成"
else
    source venv/bin/activate
fi

# 初始化数据库
if [ ! -f "data/diary.db" ]; then
    python3 -c "
import os, sqlite3
os.makedirs('data', exist_ok=True)
db = sqlite3.connect('data/diary.db')
with open('database/schema.sql') as f:
    db.executescript(f.read())
db.close()
print('✅ 数据库已初始化')
"
fi

# 启动
python3 app.py &
sleep 2
open http://localhost:5000
wait
