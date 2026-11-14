"""统一日志：JSONL 单一流（机器）+ 控制台文本（人）。

文件：logs/run-YYYYMMDD.jsonl，每条：
  {"ts": "...", "session": "043201", "level": "info",
   "mod": "action", "event": "walk", "data": {"dir": "left", "n": 3}}

用法不变：
  log.info("action", "walk", dir="left", n=3)
  log.error("battle", "stuck", reason="timeout")
查询：python3 logq.py --mod switch --event 换人

规范：
  mod   模块名（action/switch/battle/pathfind/probe/...）
  event 动词或事件名；错误统一以 ERROR: 开头
  data  扁平字段优先；嵌套只用于 party/foe 这类结构化快照
"""
import json
import os
import threading
import time

LOG_DIR = "/root/workspace/logs"
KEEP_DAYS = 7
_level = 1
_lock = threading.Lock()
_session = os.environ.get("DSH_SESSION") or time.strftime("%H%M%S")
_fp = {"day": None, "fh": None}


def set_level(level):
    global _level
    _level = level


def session(sid=None):
    """设置/读取会话 id（默认进程启动时间）。"""
    global _session
    if sid:
        _session = sid
    return _session


def _path(day):
    return os.path.join(LOG_DIR, f"run-{day}.jsonl")


def _cleanup():
    try:
        cutoff = time.time() - KEEP_DAYS * 86400
        for fn in os.listdir(LOG_DIR):
            if fn.startswith("run-") and fn.endswith(".jsonl"):
                p = os.path.join(LOG_DIR, fn)
                if os.path.getmtime(p) < cutoff:
                    os.remove(p)
    except Exception:
        pass


def _open(day):
    if _fp["day"] == day and _fp["fh"]:
        return _fp["fh"]
    os.makedirs(LOG_DIR, exist_ok=True)
    if _fp["fh"]:
        try:
            _fp["fh"].close()
        except Exception:
            pass
    _fp["fh"] = open(_path(day), "a", encoding="utf-8")
    _fp["day"] = day
    _cleanup()
    return _fp["fh"]


def _fmt(mod, event, kw):
    ts = time.strftime("%H:%M:%S")
    parts = []
    for k, v in kw.items():
        if isinstance(v, (dict, list, tuple)):
            try:
                v = json.dumps(v, ensure_ascii=False)
            except Exception:
                v = str(v)
        parts.append(f"{k}={v}")
    return f"[{ts}] {mod:<10} {event:<14} " + " ".join(parts)


def _write(level, mod, event, kw):
    now = time.time()
    ts = (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
          + f".{int(now * 1000) % 1000:03d}")
    rec = {"ts": ts, "session": _session, "level": level,
           "mod": mod, "event": event, "data": kw}
    with _lock:
        try:
            fh = _open(time.strftime("%Y%m%d"))
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
        except Exception:
            pass
    print(_fmt(mod, event, kw), flush=True)


def info(mod, event, **kw):
    if _level >= 1:
        _write("info", mod, event, kw)


def debug(mod, event, **kw):
    if _level >= 2:
        _write("debug", mod, event, kw)


def error(mod, event, **kw):
    _write("error", mod, event, kw)
