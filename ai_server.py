"""接收 RetroArch AI 服务的请求（端口 4404），记录内容并返回占位翻译。"""
import sys, json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 4404
ROOT = "/root/workspace"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n) if n else b""
        ctype = self.headers.get("Content-Type", "")
        stamp = int(time.time())
        fn = f"{ROOT}/ai_req_{stamp}.bin"
        with open(fn, "wb") as f:
            f.write(body)
        print(f"POST {self.path} ctype={ctype} len={n} -> {fn}", flush=True)
        # 尝试解析 JSON / 表单
        preview = ""
        try:
            preview = body[:300].decode("utf-8", "replace")
        except Exception:
            preview = repr(body[:100])
        print("  body head:", preview, flush=True)
        resp = json.dumps({"translation": "（测试翻译）"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"ai capture server on {PORT}", flush=True)
    srv.serve_forever()
