#!/bin/bash
# 后台常驻状态推送（下屏显示 + 自动战斗页）
# 用法：bash start_push.sh         启动
#       bash start_push.sh stop    停止
cd /root/workspace || exit 1

if [ "$1" = "stop" ]; then
    pkill -f "run_game.py" 2>/dev/null
    echo "已停止"
    exit 0
fi

pkill -f "run_game.py" 2>/dev/null
sleep 1
(setsid env EMU_BACKEND=native python3 -u pyplatform/run_game.py pokemon_firered > /tmp/push.log 2>&1 < /dev/null &)
echo "已启动 (pid $!)，日志 /tmp/push.log"
