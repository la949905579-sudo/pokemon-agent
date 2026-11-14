#!/usr/bin/env python3
"""精简事实快照（TEAM §三·十一）：HEAD/工作树/未推送/最近 3 提交/test_results/索引/合同/BATCHES。
用法：python3 tools/batch_facts.py [--repo <根>] [--full]；--full 才跑 metrics --check（联网耗时）；单项失败标 FAIL 但继续，仅 git 不可用 exit 2，其余 exit 0。
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

def sh(repo, *args, timeout=20):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)

def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

def run_py(repo, script, args=(), timeout=180):
    """跑仓库 tools/ 下脚本，返回 (exit码|None, 输出末行|SKIP 说明)。"""
    path = os.path.join(repo, "tools", script)
    if not os.path.isfile(path):
        return None, f"SKIP 无 tools/{script}"
    try:
        r = subprocess.run([sys.executable, path, *args], cwd=repo, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 1, "FAIL 超时"
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()]
    return r.returncode, (lines[-1].strip() if lines else "")

def parse_test_results(data):
    """test_results → {"python": "31 例 PASS", "kotlin": "115 例 PASS"}；缺项“无数据”。"""
    out = {}
    for key in ("python", "kotlin"):
        blk = (data or {}).get(key) or {}
        n, res = blk.get("tests"), blk.get("result") or ""
        out[key] = f"{n} 例 {res}".strip() if n is not None else "无数据"
    return out

def last_batch_row(text):
    """BATCHES 最后一条数据行 → 单元格列表；没有数据行返回 None。"""
    rows = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if r.strip("|").split("|")[0].strip() not in ("批次", "")]
    rows = [r for r in rows if set(r) - set("| :-")]
    return [c.strip() for c in rows[-1].strip("|").split("|")] if rows else None

CLOSE_NOTE_MARK = "合同收尾追记"


def last_close_note(text):
    """BATCHES 最后一条 `> 合同收尾追记…` 行 → {cid, accepted, push, raw}；无则 None。

    追记行是接受 / 推送后的权威摘要（C5 起），优先于末表行「待复核/⏳」旧态。
    """
    raw = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(">") and CLOSE_NOTE_MARK in s:
            raw = s
    if raw is None:
        return None
    m = re.search(r"合同收尾追记（\s*(C\d+)[，,]", raw)
    pm = re.search(r"已\s*push（origin/master=([0-9a-f]{7,40})）", raw)
    return {"cid": m.group(1) if m else None,
            "accepted": "accepted" in raw,
            "push": pm.group(1) if pm else None,
            "raw": raw}


def summarize_close_note(note):
    """追记 dict → 摘要行（accepted / 已 push / 待 push）；None → None。"""
    if not note:
        return None
    bits = ["追记（%s）" % note["cid"]] if note.get("cid") else ["追记"]
    bits.append("accepted" if note.get("accepted") else "未标 accepted")
    if note.get("push"):
        bits.append("已 push（origin/master=%s）" % note["push"][:7])
    elif re.search(r"待\s*push|未\s*push", note.get("raw") or ""):
        bits.append("待 push")
    return "｜".join(bits)


def summarize_contracts(repo):
    """扫 .pilot/*/status.json → ["C1 accepted", ...]。"""
    out = []
    for path in sorted(glob.glob(os.path.join(repo, ".pilot", "*", "status.json"))):
        st = read_json(path) or {}
        cid = st.get("id") or st.get("contract") or os.path.basename(os.path.dirname(path))
        out.append(f"{cid} {st.get('state') or '?'}")
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(description="精简事实快照")
    ap.add_argument("--repo", default=None, help="仓库根（默认 git toplevel）")
    ap.add_argument("--full", action="store_true", help="追加 metrics --check（联网、耗时）")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo) if a.repo else None
    if repo is None:
        rc, out, _ = sh(os.getcwd(), "rev-parse", "--show-toplevel")
        repo = out if rc == 0 and out else None
    if not repo or sh(repo, "rev-parse", "--git-dir")[0] != 0:
        print("FAIL git 不可用 / 不是 git 仓库")
        return 2
    print(f"== 事实快照 {repo} ==")
    rc, head, _ = sh(repo, "log", "-1", "--pretty=%h %s")
    print(f"HEAD      : {head or 'FAIL git log 失败'}")
    rc, short, _ = sh(repo, "status", "--short")
    dirty = len([ln for ln in short.splitlines() if ln.strip()])
    print("工作树    : " + ("FAIL git status 失败" if rc else ("干净" if not dirty else f"{dirty} 处未提交改动")))
    ref = "origin/master" if sh(repo, "rev-parse", "--verify", "--quiet", "origin/master")[0] == 0 else None
    if ref is None:
        rc, up, _ = sh(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        ref = up if rc == 0 and up else None
    if ref:
        rc, n, _ = sh(repo, "rev-list", "--count", f"{ref}..HEAD")
        print(f"未推送    : {ref}..HEAD = {n if rc == 0 else 'FAIL'}" + (" ✓" if rc == 0 and n == "0" else ""))
    else:
        print("未推送    : SKIP 无 origin/master / upstream")
    rc, log, _ = sh(repo, "log", "-3", "--pretty=%h %s")
    print("最近提交  :")
    for ln in (log.splitlines() if rc == 0 else []):
        print(f"  {ln}")
    data = read_json(os.path.join(repo, "tools", "test_results.json"))
    summ = parse_test_results(data)
    tail = "" if data is not None else "（FAIL 缺 tools/test_results.json）"
    print(f"python    : {summ['python']}{tail}")
    print(f"kotlin    : {summ['kotlin']}{tail}")
    rc, out = run_py(repo, "gen_files_index.py", ["--check"])
    print("索引      : " + (out if rc is None else ("FILES --check = 0 ✓" if rc == 0 else f"FAIL FILES --check = {rc}（{out}）")))
    cs = summarize_contracts(repo)
    print("合同      : " + (" · ".join(cs) if cs else "无 .pilot/*/status.json"))
    try:
        btext = open(os.path.join(repo, "docs", "BATCHES.md"), encoding="utf-8").read()
    except OSError:
        btext = ""
    note = last_close_note(btext)
    row = last_batch_row(btext)
    note_summary = summarize_close_note(note)
    if note_summary:
        print(f"BATCHES   : {note_summary}")
    elif row is None:
        print("BATCHES   : FAIL 无 docs/BATCHES.md 或末行")
    else:
        print(f"BATCHES   : 考官={(row[4] if len(row) > 4 else '?')[:18]}｜门禁={(row[5] if len(row) > 5 else '?')[:22]}")
    if a.full:
        rc, out = run_py(repo, "metrics.py", ["--check"], timeout=180)
        print("METRICS   : " + (out if rc is None else ("--check exit 0 ✓" if rc == 0 else f"FAIL --check exit {rc}（{out}）")))
    else:
        print("METRICS   : SKIP（--full 才跑，默认跳过耗时项）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
