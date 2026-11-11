#!/usr/bin/env python3
"""把最新一次 CI 构建的 APK 发布到 GitHub Releases（供 App 内 OTA 检查）。

用法：
    GITHUB_TOKEN=xxx python3 publish_release.py [tag]
"""
import json
import os
import subprocess
import sys
import urllib.request

OWNER, REPO = "la949905579-sudo", "pokemon-agent"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"


def api(path, method="GET", data=None, raw=None, ctype=None):
    url = API + path
    body = None
    headers = {"Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json"}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    if raw is not None:
        body = raw
        headers["Content-Type"] = ctype or "application/octet-stream"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or "{}")


def latest_run_artifact():
    runs = api(f"/repos/{OWNER}/{REPO}/actions/runs?per_page=1")["workflow_runs"]
    run = runs[0]
    arts = api(f"/repos/{OWNER}/{REPO}/actions/runs/{run['id']}/artifacts")["artifacts"]
    if not arts:
        raise Exception("没有 artifact")
    return run["head_sha"][:7], arts[0]["id"]


def download_apk(aid, out="/tmp/release.apk"):
    url = f"{API}/repos/{OWNER}/{REPO}/actions/artifacts/{aid}/zip"
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r, open("/tmp/a.zip", "wb") as f:
        f.write(r.read())
    subprocess.run(["unzip", "-o", "-q", "/tmp/a.zip", "-d", "/tmp/apkout"], check=True)
    apk = os.path.join("/tmp/apkout", "app-debug.apk")
    if not os.path.exists(apk):
        raise SystemExit("解压后没有 app-debug.apk")
    os.replace(apk, out)
    return out


def main():
    if not TOKEN:
        raise SystemExit("需要 GITHUB_TOKEN")
    apk_local = "/sdcard/Download/DSH-Go/app-debug.apk"
    try:
        sha, aid = latest_run_artifact()
        tag = sys.argv[1] if len(sys.argv) > 1 else "build-" + sha
        apk = download_apk(aid)
    except Exception as e:
        print("artifact 获取失败(%s)，改用本地 APK" % e)
        sha = "local"
        tag = sys.argv[1] if len(sys.argv) > 1 else "local-build"
        apk = "/tmp/release.apk"
        import shutil
        shutil.copy(apk_local, apk)
    size = os.path.getsize(apk)
    print(f"commit {sha}, apk {size} bytes, tag {tag}")

    # 已存在同 tag 的 release 就跳过创建
    try:
        rel = api(f"/repos/{OWNER}/{REPO}/releases/tags/{tag}")
        print("release 已存在:", rel["id"])
    except Exception:
        rel = api(f"/repos/{OWNER}/{REPO}/releases", "POST", {
            "tag_name": tag, "name": "NativeEmu " + tag,
            "body": f"自动发布：commit {sha}", "draft": False, "prerelease": False,
        })
        print("release 创建:", rel["id"])

    # 删除同名 asset 后上传
    for a in rel.get("assets", []):
        if a["name"] == "app-debug.apk":
            api(f"/repos/{OWNER}/{REPO}/releases/assets/{a['id']}", "DELETE")
    up_url = f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{rel['id']}/assets?name=app-debug.apk"
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-H", "Authorization: token " + TOKEN,
        "-H", "Content-Type: application/vnd.android.package-archive",
        "--data-binary", "@" + apk, up_url,
    ], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise SystemExit("上传失败: " + r.stderr[:200])
    info = json.loads(r.stdout or "{}")
    print("上传完成:", info.get("browser_download_url", r.stdout[:120]))


if __name__ == "__main__":
    main()
