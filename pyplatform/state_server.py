"""本地状态服务：给网页「下屏」提供数据与动作接口。

用法：python3 state_server.py [端口]
浏览器打开 http://127.0.0.1:8080
"""
import sys, json, time, threading, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, "/root/workspace")
import state, bdata, info, terrain

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = "/root/workspace/web"

# 正在执行的动作（避免重入）
_busy = {"name": None, "since": 0}



import socket as _sock

def fast_rd(addr, n, timeout=0.35):
    """短超时的内存读取（游戏不在前台时快速失败）。"""
    try:
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0)); s.settimeout(timeout)
        s.sendto(f"READ_CORE_MEMORY {addr:x} {n}".encode(), ("127.0.0.1", 55355))
        r = s.recvfrom(16384)[0].split()
        s.close()
        if len(r) > 2:
            return bytes(int(x, 16) for x in r[2:])
    except Exception:
        pass
    return b""

def read_party():
    d = fast_rd(0x02024284, 600)
    if not d or len(d) < 600:
        return []
    out = []
    for i in range(6):
        o = i * 100
        lv = d[o + 0x54]
        hp, mhp = struct.unpack_from("<HH", d, o + 0x56)
        pid = struct.unpack_from("<I", d, o)[0]
        species = 0
        if pid:
            out.append({"slot": i, "lv": lv, "hp": hp, "mhp": mhp, "species": species})
    return out


def party_detail():
    """带招式/属性的队伍详情（较慢，二级页面用）。"""
    out = []
    for i in range(6):
        m = bdata.my_mon(i)
        if m:
            out.append(m)
    return out


def current_state():
    """用短超时直接读，游戏不在前台时也能快速返回。"""
    p = fast_rd(0x02036e48, 4)
    x = y = None
    if len(p) == 4:
        x, y = struct.unpack_from("<hh", p, 0)
    b = fast_rd(0x02024018, 1)
    dg = fast_rd(0x03000F9C, 1)
    t = fast_rd(0x02023E82, 2)
    m = fast_rd(0x02036DFC, 4)
    battle = bool(b and b[0])
    dialog = bool(dg and dg[0] == 1)
    turn = t[0] if t else None
    choice = bool(battle and turn == 1 and t and len(t) > 1 and t[1] == 0)
    if not battle:
        scene = "map"
    elif turn == 0:
        scene = "battle_intro"
    elif turn == 4:
        scene = "anim"
    elif choice:
        scene = "choice"
    else:
        scene = "battle"
    d = {
        "ok": True,
        "scene": scene,
        "x": (x - 7) if x is not None else None,
        "y": (y - 7) if y is not None else None,
        "battle": battle,
        "dialog": dialog,
        "choice": choice,
        "party": read_party(),
        "map": hex(struct.unpack_from("<I", m, 0)[0]) if len(m) == 4 else None,
        "busy": _busy["name"],
    }
    if battle:
        e = bdata.enemy_info()
        if e:
            d["enemy"] = {"lv": e["lv"], "hp": e["hp"], "mhp": e["mhp"],
                          "species": e["species"], "types": e["types"]}
        me = bdata.my_mon(0)
        if me:
            d["me"] = {"lv": me["lv"], "hp": me["hp"], "mhp": me["mhp"],
                       "species": me["species"], "types": me["types"],
                       "moves": me["moves"], "pp": me["pp"]}
            try:
                idx, why = bdata.choose_move(me, e["types"] if e else ())
                d["suggest"] = {"idx": idx, "why": why}
            except Exception:
                pass
    return d


def run_action(name, fn):
    def wrapper():
        _busy["name"] = name
        _busy["since"] = time.time()
        try:
            fn()
        except Exception as e:
            print("action error", name, e, flush=True)
        finally:
            _busy["name"] = None
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    return t


ACTIONS = {}


def action(name):
    def deco(fn):
        ACTIONS[name] = fn
        return fn
    return deco


@action("encounter")
def _enc(args=None):
    import encounter
    encounter.find_encounter(max_steps=40)


@action("auto_battle")
def _auto(args=None):
    import auto_battle
    auto_battle.battle_loop(max_rounds=12)


@action("heal")
def _heal(args=None):
    import pathfind, time as t2
    from ra import press
    pathfind.goto(7, 4)
    for _ in range(3):
        press("a", 0.25); t2.sleep(1.0)
    for _ in range(4):
        if not state.in_dialog():
            break
        press("b", 0.25); t2.sleep(0.7)


@action("goto")
def _goto(args=None):
    import pathfind
    gx, gy = int(args["x"]), int(args["y"])
    pathfind.goto(gx, gy)


@action("move")
def _move(args=None):
    """走一步（方向由 args 给）。"""
    from ra import press
    d = args.get("dir", "down")
    press(d, 0.15)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            try:
                with open(f"{ROOT}/index.html", "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except Exception as e:
                self._send(500, str(e), "text/plain")
            return
        if path == "/api/state":
            self._send(200, json.dumps(current_state(), ensure_ascii=False))
            return
        if path == "/api/party":
            self._send(200, json.dumps({"party": party_detail()}, ensure_ascii=False))
            return
        if path == "/api/moves":
            e = bdata.enemy_info()
            me = bdata.my_mon(0)
            moves = []
            if me:
                for mid, pp in zip(me["moves"], me["pp"]):
                    info_m = bdata.MOVES.get(mid)
                    if not info_m:
                        continue
                    name, typ, power = info_m
                    eff = 1.0
                    if e:
                        for et in e["types"]:
                            eff *= bdata.TYPE_CHART.get((typ, et), 1.0)
                    moves.append({"name": name, "type": typ, "power": power,
                                  "pp": pp, "eff": round(eff, 2)})
            self._send(200, json.dumps({"moves": moves, "enemy": e}, ensure_ascii=False))
            return
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/action":
            self._send(404, "not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode() if n else "{}"
        try:
            req = json.loads(body)
        except Exception:
            req = {}
        name = req.get("name")
        if _busy["name"]:
            self._send(200, json.dumps({"ok": False, "busy": _busy["name"]}))
            return
        fn = ACTIONS.get(name)
        if not fn:
            self._send(200, json.dumps({"ok": False, "error": "unknown action"}))
            return
        run_action(name, lambda: fn(req.get("args") or {}))
        self._send(200, json.dumps({"ok": True, "started": name}, ensure_ascii=False))


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"state server on http://127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
