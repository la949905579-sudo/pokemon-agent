#!/usr/bin/env python3
"""构建与 CI 度量：从远端 build-* tag 与 GitHub Actions 记录生成 docs/METRICS.md。

解决两个问题：
1. 一个 build tag 可能覆盖多个提交（CI 按推送 tip 打 tag），只看 tag 名会误判
   “某些提交没有构建”。本脚本把每个 tag 展开成它实际包含的提交列表，并列出
   尚未被任何 tag 覆盖的提交（构建覆盖可核）。
2. CI 首次通过率没人统计，T4 触发条件形同虚设。本脚本按“每个推送 tip 的第一次
   Action 结论”算首过率，写进文档，供 `docs/AUDIT.md` T4 每周自动判定。

用法：
    python3 tools/metrics.py              # 生成 docs/METRICS.md
    python3 tools/metrics.py --check      # 只打印摘要，不写文件
    python3 tools/metrics.py --offline    # 不查 GitHub API（CI 数据标“未知”）

数据来源：
- 远端 tag：`git ls-remote --tags origin`（远端是唯一真源，本地可能有历史重写残留）
- 提交：本地仓库（tag 指向的 commit 必须已在本地）
- CI：GitHub Actions 公共 API（无 token，只读；受 60 次/小时限制）
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com/repos/la949905579-sudo/pokemon-agent"
OUT = os.path.join(ROOT, "docs", "METRICS.md")
TZ = timezone(timedelta(hours=8))  # 手机时区 Asia/Shanghai


def sh(*args, check=False):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"命令失败：{' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pokemon-agent-metrics"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fmt_ts(ts):
    return datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M")


class BuildTag:
    def __init__(self, name, sha, ts, subject):
        self.name = name
        self.sha = sha
        self.ts = ts
        self.subject = subject
        self.commits = []      # [(short, ts, subject, touches_native)]
        self.ci_first = None   # True / False / None（未知）

    @property
    def short(self):
        return self.name[len("build-"):][:7]


def remote_build_tags():
    """远端 build-* tag → 提交 sha。用 ^{} 解引用附注 tag；一次性拿到全量，避免逐 tag 请求。"""
    out = sh("git", "ls-remote", "--tags", "origin")
    tags, peeled = {}, {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        name = ref[len("refs/tags/"):]
        if not name.startswith("build-"):
            continue
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            tags[name] = sha
    tags.update(peeled)
    result = []
    for name, sha in tags.items():
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            continue
        if sh("git", "cat-file", "-t", sha).strip() != "commit":
            continue
        ts = int(sh("git", "log", "-1", "--format=%ct", sha).strip() or 0)
        subject = sh("git", "log", "-1", "--format=%s", sha).strip()
        result.append(BuildTag(name, sha, ts, subject))
    return sorted(result, key=lambda t: (t.ts, t.name))


def touches_native(sha):
    files = sh("git", "show", "--name-only", "--format=", sha).splitlines()
    return any(f.startswith("native-emu/") for f in files)


def fill_commits(tags):
    """按时间顺序把每个 tag 相对前一个 tag 新增的提交填进 tag.commits。

    CI 按推送 tip 打 tag；一次推送里的多个提交会被同一个 tag 覆盖，这里把它们显式列出来。
    重复指向同一提交的 tag（重跑/重推）标 0 个新提交。
    """
    seen = []
    for t in tags:
        if not seen:
            # 首个 tag 的推送基线不可知（历史重写后第一次推送），不展开，避免把全仓库都算进去
            seen.append(t.sha)
            continue
        out = sh("git", "rev-list", "--reverse", t.sha, "--not", *seen)
        shas = [s for s in out.splitlines() if s]
        for s in shas:
            t.commits.append((s[:7], int(sh("git", "log", "-1", "--format=%ct", s).strip()),
                              sh("git", "log", "-1", "--format=%s", s).strip()[:60],
                              touches_native(s)))
        seen.append(t.sha)


def uncovered_commits(tags):
    """还没被任何 build tag 覆盖的提交（最后一个 tag 之后到 HEAD）。"""
    if not tags:
        return []
    args = ["rev-list", "--reverse", "HEAD", "--not", *[t.sha for t in tags]]
    out = sh("git", *args)
    rows = []
    for s in out.splitlines():
        if not s:
            continue
        rows.append((s[:7], int(sh("git", "log", "-1", "--format=%ct", s).strip()),
                     sh("git", "log", "-1", "--format=%s", s).strip()[:60],
                     touches_native(s)))
    return rows


def fetch_runs():
    """GitHub Actions 全部运行记录；失败返回 None（网络或限流）。"""
    runs, page = [], 1
    try:
        while True:
            data = get_json(f"{API}/actions/runs?per_page=100&page={page}")
            batch = data.get("workflow_runs", [])
            runs += batch
            if len(batch) < 100 or len(runs) >= data.get("total_count", 0):
                break
            page += 1
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"⚠ 取 CI 数据失败（{e}），CI 指标标“未知”", file=sys.stderr)
        return None
    return runs


def ci_stats(runs):
    """按推送 tip 分组，取每个 tip 的第一次 Action 结论算首过率。"""
    if runs is None:
        return None
    by_sha = {}
    for r in sorted(runs, key=lambda x: x["created_at"]):
        by_sha.setdefault(r["head_sha"], []).append(r)
    tips = []
    for sha, rs in by_sha.items():
        first = rs[0]
        tips.append({
            "sha": sha,
            "first": first["conclusion"],
            "attempts": len(rs),
            "created": first["created_at"],
            "event": first.get("event", ""),
        })
    tips.sort(key=lambda x: x["created"])
    ok = sum(1 for t in tips if t["first"] == "success")
    recent = tips[-20:]
    ok_recent = sum(1 for t in recent if t["first"] == "success")
    return {
        "tips": tips,
        "total": len(tips),
        "ok": ok,
        "rate": ok / len(tips) if tips else 0,
        "recent_total": len(recent),
        "recent_ok": ok_recent,
        "recent_rate": ok_recent / len(recent) if recent else 0,
        "runs": len(runs),
        "retries": len(runs) - len(tips),
        "by_sha": by_sha,
    }


def annotate_ci(tags, stats):
    """给 tag 标“首次构建是否首过”。

    优先按 tag 指向的提交 sha 匹配；历史重写后 tag 名里可能还是旧 sha，
    所以再按 tag 名里的 7 位 sha 兜底匹配（tag 名就是 CI 当时的推送 tip）。
    """
    if not stats:
        return
    by_prefix = {}
    for sha, rs in stats["by_sha"].items():
        by_prefix.setdefault(sha[:7], rs)
    for t in tags:
        suffix = t.name[len("build-"):]
        rs = stats["by_sha"].get(t.sha) or by_prefix.get(suffix[:7])
        if not rs:
            continue
        first = sorted(rs, key=lambda x: x["created_at"])[0]["conclusion"]
        t.ci_first = first == "success"


def incidents():
    path = os.path.join(ROOT, "docs", "INCIDENTS.md")
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return 0, 0
    entries = re.findall(r"^## (INC-\d+[^\n]*)", text, re.M)
    relapse = [e for e in entries if "复发" in e]
    return len(entries), len(relapse)


def pct(x):
    return f"{x:.1%}"


def build_doc(tags, uncovered, stats, inc_total, inc_relapse, offline):
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    head = sh("git", "rev-parse", "--short", "HEAD").strip()
    lines = [
        "# 构建与 CI 度量（METRICS）",
        "",
        "> 由 `tools/metrics.py` 生成，**不要手改**。重新生成：`python3 tools/metrics.py`。",
        "> 目的：让「哪些提交被构建过」「CI 首过率多少」可核，而不是看 tag 名猜。",
        "",
        f"- 生成时间：{now}（Asia/Shanghai）",
        f"- HEAD：`{head}`",
        "- 数据源：远端 `build-*` tag（`git ls-remote --tags origin`）+ GitHub Actions 公共 API + `docs/INCIDENTS.md`",
        "",
        "## 一、CI 首次通过率（T4 判据）",
        "",
    ]
    if offline or not stats:
        lines += ["**未知**：本次未取到 GitHub Actions 数据（`--offline` 或网络/限流失败）。", ""]
    else:
        lines += [
            "定义：以**推送 tip** 为单位，取该 tip 第一次 Action 的结论；首次即 success 记为“首过”。",
            "（一个 tip 可能对应一次推送里的多个提交——CI 按推送 tip 跑。）",
            "",
            "| 口径 | 首过 / 总数 | 首过率 | 备注 |",
            "|---|---|---|---|",
            f"| 全量（{stats['total']} 个推送 tip） | {stats['ok']} / {stats['total']} | {pct(stats['rate'])} | 含早期 workflow 未加 paths 过滤时的 docs 推送 |",
            f"| 最近 20 个 tip | {stats['recent_ok']} / {stats['recent_total']} | {pct(stats['recent_rate'])} | 判断当前趋势用这个 |",
            "",
            f"- 总运行次数 {stats['runs']}，其中重试/重复运行 {stats['retries']} 次。",
            f"- T4 阈值：全量首过率 < 70% → 启动审查。当前 {pct(stats['rate'])}，"
            f"**{'需要启动' if stats['rate'] < 0.7 else '未触发'}**。",
            "",
        ]

    lines += [
        "## 二、build tag → 包含的提交（构建覆盖）",
        "",
        "CI 按**推送 tip** 打 tag：一次推送推了多个提交时，只有 tip 有 tag。",
        "下表把每个 tag 展开成它实际覆盖的提交，解决“某个提交没有独立 tag = 没构建”的误判。",
        "",
        "| tag | 目标提交 | 时间 | 覆盖提交数 | 覆盖的提交（从旧到新） | 首次构建 |",
        "|---|---|---|---|---|---|",
    ]
    for i, t in enumerate(tags):
        if t.commits:
            commits = "；".join(f"`{c[0]}`" for c in t.commits)
        elif i == 0:
            commits = "（首个 tag，推送基线不可知）"
        else:
            commits = "（同一提交重复构建，无新提交）"
        if len(commits) > 120:
            commits = commits[:117] + "…"
        first = {True: "首过", False: "重试后过", None: "未知"}[t.ci_first]
        lines.append(
            f"| `{t.name}` | `{t.sha[:7]}` | {fmt_ts(t.ts)} | {len(t.commits)} | {commits} | {first} |"
        )
    per_tag = [len(t.commits) for t in tags]
    multi = sum(1 for n in per_tag if n > 1)
    lines += [
        "",
        f"- **单 tag 覆盖多提交的证据**：{len(tags)} 个 build tag 中，{multi} 个覆盖 ≥2 个提交"
        f"（最多 {max(per_tag) if per_tag else 0} 个）。所以“提交数 > tag 数”不等于漏构建。",
        "",
        "## 三、构建覆盖缺口（tag 之后未构建的提交）",
        "",
    ]
    if uncovered:
        native = [c for c in uncovered if c[3]]
        lines += [f"最后一个 build tag 之后还有 **{len(uncovered)}** 个提交未构建：", ""]
        lines += ["| 提交 | 时间 | 说明 | 触及 `native-emu/**` |", "|---|---|---|---|"]
        for s, ts, subj, nat in uncovered:
            lines.append(f"| `{s}` | {fmt_ts(ts)} | {subj} | {'⚠ 是' if nat else '否'} |")
        lines += [
            "",
            ("**构建覆盖完整**：未构建的提交都不触及 `native-emu/**`，不影响 APK。"
             if not native else
             f"**⚠ 覆盖缺口 {len(native)} 个**：有触及 `native-emu/**` 的提交未构建，需要推送触发 CI。"),
            "",
        ]
    else:
        lines += ["所有提交都在某个 build tag 的覆盖范围内。", ""]
    lines += [
        "## 四、事故与复发率",
        "",
        "定义：复发率 = `docs/INCIDENTS.md` 中标题标注「（复发）」的条目数 / 事故总数。",
        f"当前：事故 **{inc_total}** 条，标注复发的 **{inc_relapse}** 条。",
        "",
    ]
    if inc_relapse == 0:
        lines += [
            "> 注意：这是**登记口径**的数字。2026-11-12 首次审查已口头判定 INC-003 复发，",
            "> 但事故库没有打标记，所以脚本读到 0。T4 想靠它自动判定，前提是复发条目",
            "> 必须在标题里写「（复发）」——这是本指标的已知局限，已记入 2026-11-12 整改。",
            "",
        ]
    stale = local_stale_tags(tags)
    lines += [
        "## 五、已知局限",
        "",
        "- CI 首过率只算“推送 tip 的第一次 Action”，不含本机测试结果；",
        "  文档类推送在 workflow 加 paths 过滤前也会触发构建，早期数据偏噪。",
        "- 无 token 访问 API 限 60 次/小时；脚本失败时 CI 一栏标“未知”，不会编数字。",
    ]
    if stale:
        lines += [
            f"- 本地还有 {len(stale)} 个远端已删除的 `build-*` tag（历史重写遗留），"
            "本表以远端为准；清理：`git fetch --prune-tags`。",
        ]
    lines += ["", "## 六、怎么用", "", "```bash",
              "python3 tools/metrics.py            # 重新生成本文件",
              "python3 tools/metrics.py --check    # 只看摘要（每周 T4 判定用）",
              "python3 tools/metrics.py --offline  # 没网时只算 tag/覆盖",
              "```", ""]
    return "\n".join(lines)


def local_stale_tags(remote_tags):
    local = {t for t in sh("git", "tag", "-l", "build-*").splitlines() if t}
    remote = {t.name for t in remote_tags}
    return sorted(local - remote)


def main():
    offline = "--offline" in sys.argv
    check = "--check" in sys.argv

    tags = remote_build_tags()
    if not tags:
        print("没有找到远端 build-* tag；先确认能连 origin", file=sys.stderr)
        return 1
    for t in tags:
        if subprocess.run(["git", "cat-file", "-e", f"{t.sha}^{{commit}}"], cwd=ROOT,
                          capture_output=True).returncode != 0:
            print(f"⚠ tag {t.name} 指向的提交 {t.sha[:7]} 不在本地，先 git fetch", file=sys.stderr)
    fill_commits(tags)
    uncovered = uncovered_commits(tags)
    stats = None if offline else ci_stats(fetch_runs())
    annotate_ci(tags, stats)
    inc_total, inc_relapse = incidents()

    stale = local_stale_tags(tags)
    print(f"远端 build tag：{len(tags)} 个；未构建提交：{len(uncovered)} 个"
          f"（其中触及 native-emu 的 {sum(1 for c in uncovered if c[3])} 个）")
    if stale:
        print(f"本地残留远端已删 tag：{len(stale)} 个（以远端为准）")
    if stats:
        print(f"CI 首过率：{stats['ok']}/{stats['total']} = {pct(stats['rate'])}"
              f"（最近 20 个 tip：{pct(stats['recent_rate'])}）")
    else:
        print("CI 首过率：未知（offline 或网络失败）")
    print(f"事故：{inc_total} 条，标注复发 {inc_relapse} 条")

    doc = build_doc(tags, uncovered, stats, inc_total, inc_relapse, offline)
    if not check:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(doc.rstrip() + "\n")
        print(f"已写入 {os.path.relpath(OUT, ROOT)}")

    # T4 判定：首过率 < 70% 或 复发率 > 0 → exit 1（供 cron/脚本判红）
    red = []
    if stats and stats["rate"] < 0.7:
        red.append(f"CI 首过率 {pct(stats['rate'])} < 70%")
    if inc_relapse > 0:
        red.append(f"复发 {inc_relapse} 条")
    if check and red:
        print("T4 红：" + "；".join(red))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
