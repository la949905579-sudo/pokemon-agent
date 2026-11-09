"""统一日志：所有模块通过这里记录操作，便于回溯和迭代。

用法：
    import log
    log.info("action", "walk", dir="left", n=3, moved=2)
    log.debug("decision", "choose_move", idx=0, why="电光一闪")

输出：
    - 控制台（stdout）
    - 文件 /root/workspace/logs/game.log（按天滚动）

级别：
    0 = 关闭
    1 = info（关键动作，默认）
    2 = debug（详细数据）
"""
import os, sys, time, json

LOG_DIR = "/root/workspace/logs"
_level = 1


def set_level(level):
    global _level
    _level = level


def _fmt(mod, event, **kw):
    ts = time.strftime("%H:%M:%S")
    parts = []
    for k, v in kw.items():
        if isinstance(v, (dict, list, tuple)):
            try:
                v = json.dumps(v, ensure_ascii=False)
            except Exception:
                v = str(v)
        parts.append(f"{k}={v}")
    body = " ".join(parts)
    return f"[{ts}] {mod:<10} {event:<14} {body}"


def _emit(line):
    print(line, flush=True)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        fn = os.path.join(LOG_DIR, time.strftime("game-%Y%m%d.log"))
        with open(fn, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def info(mod, event, **kw):
    if _level >= 1:
        _emit(_fmt(mod, event, **kw))


def debug(mod, event, **kw):
    if _level >= 2:
        _emit(_fmt(mod, event, **kw))


def error(mod, event, **kw):
    _emit(_fmt(mod, "ERROR:" + event, **kw))
