#!/bin/bash
# 一键还原日记数据
cd "$(dirname "$0")"
echo "正在还原日记数据..."
curl -s -X POST 'http://127.0.0.1:5000/api/import/markdown?mode=overwrite' -F 'file=@data/_safe_backup.md' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'还原完成：新增 {d[\"created\"]} 条日记')"
echo "如果上面报错，请先启动服务器：bash start.sh"
