"""外部 API：给 AI / 简易程序提供「观察 + 操作」接口。

端口默认 8081（下屏服务是 8080，互不影响）。

接口：
  GET  /api/state        当前状态（场景/坐标/队伍/敌人/菜单/turn/地图）
  GET  /api/actions      可用动作列表
  POST /api/act          动作原语 {name, args}
  POST /api/task         高层任务 {name, args}

动作执行是同步的：请求会等动作完成再返回结果。
"""
import sys, json, time, threading, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, "/root/workspace")
import state, info, bdata, terrain

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
_lock = threading.Lock()


# ---------------- 状态 ----------------

def read_party():
    d = state.rd(0x02024284, 600, retries=1)
    if not d or len(d) < 600:
        return []
    out = []
    for i in range(6):
        o = i * 100
        lv = d[o + 0x54]
        hp, mhp = struct.unpack_from("<HH", d, o + 0x56)
        pid = struct.unpack_from("<I", d, o)[0]
        if pid:
            out.append({"slot": i, "lv": lv, "hp": hp, "mhp": mhp})
    return out


def get_state():
    p = state.coords()
    s = state.snapshot()
    d = {
        "scene": info.scene(),
        "pos": {"x": p[0] - 7, "y": p[1] - 7} if p else None,
        "raw": {"x": p[0], "y": p[1]} if p else None,
        "battle": s["battle"],
        "dialog": s["dialog"],
        "choice": s["choice"],
        "turn": s["turn"],
        "party": read_party(),
        "mode": s["mode"],
    }
    try:
        a, w, h, _ = terrain.load()
        d["map"] = {"id": hex(a) if a else None, "w": w, "h": h}
    except Exception:
        d["map"] = None
    if s["battle"]:
        e = bdata.enemy_info()
        if e:
            d["enemy"] = {"lv": e["lv"], "hp": e["hp"], "mhp": e["mhp"],
                          "species": e["species"], "types": list(e["types"])}
        me = bdata.my_mon(0)
        if me:
            d["me"] = {"lv": me["lv"], "hp": me["hp"], "mhp": me["mhp"],
                       "species": me["species"], "types": list(me["types"]),
                       "moves": me["moves"], "pp": me["pp"]}
    return d


# ---------------- 地图视野 ----------------

TILE_WALK, TILE_WALL, TILE_GRASS, TILE_NPC, TILE_OUT = ".", "#", "G", "N", "?"


def get_view(radius=2):
    """玩家周围 (2r+1)x(2r+1) 的格子类型图。

    '.' 可走  '#' 墙  'G' 草  'N' NPC  '?' 地图外
    """
    p = state.coords()
    if not p:
        return None
    a, w, h, vals = terrain.load()
    if not vals:
        return None
    tx, ty = p[0] - 7, p[1] - 7
    npcs = terrain.npc_tiles()
    grid = []
    for dy in range(-radius, radius + 1):
        row = []
        for dx in range(-radius, radius + 1):
            x, y = tx + dx, ty + dy
            if not (0 <= x < w and 0 <= y < h):
                row.append(TILE_OUT)
            elif (x, y) in npcs and (dx or dy):
                row.append(TILE_NPC)
            elif not terrain.walkable(vals, w, x, y):
                row.append(TILE_WALL)
            elif terrain.is_grass(vals, w, x, y):
                row.append(TILE_GRASS)
            else:
                row.append(TILE_WALK)
        grid.append(row)
    return {
        "radius": radius,
        "origin": {"x": tx, "y": ty},
        "tiles": grid,
        "legend": {".": "可走", "#": "墙", "G": "草地", "N": "NPC", "?": "地图外"},
    }


# ---------------- 动作原语 ----------------

def act_press(args):
    from ra import press
    press(args.get("key", "a"), float(args.get("duration", 0.25)))
    return {"ok": True}


def act_walk(args):
    import action
    direction = args.get("direction", "down")
    steps = int(args.get("steps", 1))
    moved = action.walk(direction, steps)
    return {"ok": True, "moved": moved}


def act_goto(args):
    import pathfind
    x = int(args["x"]); y = int(args["y"])
    r = pathfind.goto(x, y, max_segs=int(args.get("max_segs", 60)))
    return {"ok": r is True, "result": str(r)}


def act_travel(args):
    import pathfind
    x = int(args["x"]); y = int(args["y"])
    r = pathfind.travel(x, y)
    return {"ok": r in ("ok", "warped"), "result": str(r)}


def act_fight(args):
    import auto_battle
    res = auto_battle.battle_loop(max_rounds=int(args.get("rounds", 12)))
    return {"ok": True, "result": res}


def act_switch(args):
    import switch
    slot = int(args["slot"])
    pos = switch._cursor_for_slot(slot)
    if pos is None:
        return {"ok": False, "error": "slot 无效"}
    ok = switch._pick_and_switch(slot, False, "api")
    return {"ok": ok}


def act_flee(args):
    import action
    action.run_away()
    time.sleep(0.8)
    return {"ok": True}


def act_heal(args):
    """在精灵中心柜台治疗。"""
    import action
    for _ in range(3):
        action.tap_a()
        time.sleep(1.0)
    time.sleep(2.0)
    for _ in range(5):
        if not state.in_dialog():
            break
        action.tap_b()
        time.sleep(0.7)
    return {"ok": True, "party": read_party()}


ACTIONS = {
    "press": act_press,
    "walk": act_walk,
    "goto": act_goto,
    "travel": act_travel,
    "fight": act_fight,
    "switch": act_switch,
    "flee": act_flee,
    "heal": act_heal,
}


# ---------------- 高层任务 ----------------

def task_goto_center(args):
    """回最近的精灵中心（当前实现：枯叶市）。"""
    import pathfind
    r = pathfind.travel(15, 8)
    return {"ok": True, "result": str(r)}


def task_farm(args):
    """练级：遇敌 N 场。"""
    import encounter, auto_battle
    n = int(args.get("battles", 3))
    done = 0
    for _ in range(n):
        if not encounter.find_encounter(max_steps=30):
            break
        auto_battle.battle_loop()
        done += 1
    return {"ok": True, "battles": done}


TASKS = {
    "goto_center": task_goto_center,
    "farm": task_farm,
}


# ---------------- HTTP ----------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _stream(self):
        """SSE：状态变化时推送。客户端断开就退出。"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last = None
        try:
            while True:
                s = get_state()
                key = (s["scene"], s.get("pos"), s.get("turn"),
                       tuple((p["hp"] for p in s["party"])),
                       (s.get("enemy") or {}).get("hp"))
                if key != last:
                    payload = json.dumps(s, ensure_ascii=False)
                    self.wfile.write(f"data: {payload}\n\n".encode())
                    self.wfile.flush()
                    last = key
                time.sleep(0.2)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/stream":
            self._stream()
            return
        if path == "/api/state":
            try:
                self._send(200, {"ok": True, "state": get_state()})
            except Exception as e:
                self._send(500, {"ok": False, "error": str(e)})
            return
        if path == "/api/view":
            try:
                r = int(urlparse(self.path).query.split("radius=")[-1]) if "radius=" in self.path else 2
            except Exception:
                r = 2
            self._send(200, {"ok": True, "view": get_view(max(1, min(r, 10)))})
            return
        if path == "/api/actions":
            self._send(200, {"ok": True, "actions": sorted(ACTIONS),
                             "tasks": sorted(TASKS)})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            req = {}
        name = req.get("name")
        args = req.get("args") or {}

        if path == "/api/act":
            fn = ACTIONS.get(name)
        elif path == "/api/task":
            fn = TASKS.get(name)
        else:
            self._send(404, {"ok": False, "error": "not found"})
            return

        if not fn:
            self._send(200, {"ok": False, "error": f"未知动作: {name}"})
            return
        if not _lock.acquire(blocking=False):
            self._send(200, {"ok": False, "error": "busy", "reason": "上一个动作还没完成"})
            return
        try:
            result = fn(args)
            self._send(200, result)
        except Exception as e:
            self._send(500, {"ok": False, "error": str(e)})
        finally:
            _lock.release()


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"external api on http://127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
