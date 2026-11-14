"""最小 AI 闭环：观察 state -> 下指令 -> 触发战斗 -> 读效果。

用法：python3 ai_agent.py [prolong|no_kill|flee] [场数]
前提：api_server.py 已在 8081 运行（同进程驱动战斗，指令可见）。
"""
import http.client
import json
import sys

HOST, PORT = "127.0.0.1", 8081


def call(method, path, body=None, timeout=240):
    c = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    c.request(method, path,
              body=json.dumps(body) if body is not None else None,
              headers={"Content-Type": "application/json"})
    r = c.getresponse()
    return json.loads(r.read())


def main(kind="prolong", battles=1):
    st = call("GET", "/api/state")["state"]
    print("观察:", {k: st.get(k) for k in ("scene", "battle", "pos")}, flush=True)
    call("POST", "/api/intent/clear", {})
    r = call("POST", "/api/intent", {"kind": kind, "ttl": 5, "source": "ai"})
    print("注入:", kind, "->", r.get("id"), flush=True)
    res = call("POST", "/api/task", {"name": "farm", "args": {"battles": battles}})
    print("战斗:", {k: res.get(k) for k in ("ok", "battles")}, flush=True)
    fb = call("GET", "/api/intent")
    print("回读:", fb.get("last_battle"), flush=True)
    print("audit:", [a.get("event") for a in fb.get("audit") or []][-4:], flush=True)


if __name__ == "__main__":
    k = sys.argv[1] if len(sys.argv) > 1 else "prolong"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    main(k, n)
