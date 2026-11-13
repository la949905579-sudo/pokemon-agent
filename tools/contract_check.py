#!/usr/bin/env python3
"""合同制机械校验（TEAM §三·十）：合同 spec + 运行态 status.json。

用法：
    python3 tools/contract_check.py --contract docs/contracts/C1-tests-consolidation.md \
        --status .pilot/C1/status.json [--repo <仓库根>]

校验项：必填标题 / 合同 ≤60 行 / status 字段与状态机 / base 是合法提交 /
result.md ≤10 行 / accepted 时 BATCHES 含「合同:<id>」且 base..commit 改动落在
合同「写入范围」（豁免 .pilot/**）。
退出码：0 全部通过；1 有阻断；2 用法错误。
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

REQUIRED_HEADINGS = ("合同号", "类型", "事实快照", "基线提交", "背景与目标",
                     "任务清单", "验收", "写入范围", "禁止项", "变更规则", "回执")
STATES = ("open", "claimed", "green", "blocked", "accepted")
MAX_CONTRACT_LINES = 60
MAX_RESULT_LINES = 10
EXEMPT = (".pilot/",)


def sh(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def read_text(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def contract_headings(text, errs):
    heads = [ln.strip() for ln in text.splitlines() if ln.lstrip().startswith("#")]
    for kw in REQUIRED_HEADINGS:
        if not any(kw in h for h in heads):
            errs.append(f"合同缺少必填标题：{kw}")


def contract_scope(text):
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#") and "写入范围" in ln:
            start = i + 1
            break
    if start is None:
        return []
    pats = []
    for ln in lines[start:]:
        if ln.lstrip().startswith("## "):
            break
        if "允许" not in ln or "不允许" in ln:
            continue
        pats += re.findall(r"`([^`]+)`", ln)
    return [p for p in pats if p]


def in_scope(path, patterns):
    for p in patterns:
        if p.endswith("/**"):
            if path.startswith(p[:-2]):
                return True
        elif any(c in p for c in "*?["):
            if fnmatch.fnmatch(path, p):
                return True
        elif path == p or path.startswith(p.rstrip("/") + "/"):
            return True
    return False


def legal_commit(repo, sha):
    if not sha or not isinstance(sha, str):
        return False
    rc, _, _ = sh(repo, "cat-file", "-e", f"{sha}^{{commit}}")
    return rc == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="合同制机械校验")
    ap.add_argument("--contract", required=True, help="合同 spec 路径")
    ap.add_argument("--status", required=True, help=".pilot/<id>/status.json 路径")
    ap.add_argument("--repo", default=None, help="仓库根（默认 git toplevel）")
    a = ap.parse_args(argv)

    repo = a.repo
    if repo is None:
        rc, out, _ = sh(os.getcwd(), "rev-parse", "--show-toplevel")
        repo = out if rc == 0 and out else os.getcwd()

    if not os.path.isfile(a.contract):
        print(f"FAIL 合同不存在：{a.contract}")
        return 1
    if not os.path.isfile(a.status):
        print(f"FAIL status 不存在：{a.status}")
        return 1

    errs = []
    text = read_text(a.contract)
    c_lines = len(text.splitlines())
    if c_lines > MAX_CONTRACT_LINES:
        errs.append(f"合同超行数：{c_lines} 行 > 上限 {MAX_CONTRACT_LINES}")
    contract_headings(text, errs)
    patterns = contract_scope(text)
    if not patterns:
        errs.append("合同「写入范围」未解析到允许路径")

    try:
        st = json.loads(read_text(a.status))
    except json.JSONDecodeError as e:
        print(f"FAIL status 不是合法 JSON：{e}")
        return 1
    if not isinstance(st, dict):
        print("FAIL status 顶层必须是对象")
        return 1

    state = st.get("state")
    if state not in STATES:
        errs.append(f"status.state 非法：{state!r}（应属 {'/'.join(STATES)}）")
    cid = st.get("id") or st.get("contract") or ""
    if not cid:
        m = re.match(r"(C\d+)", os.path.basename(a.contract))
        cid = m.group(1) if m else os.path.basename(a.contract)

    if not st.get("base"):
        errs.append("status 缺 base（开工前 git rev-parse HEAD）")
    elif not legal_commit(repo, st["base"]):
        errs.append(f"status.base 不是合法提交：{st['base']}")
    if state != "open":
        for k in ("claimedAt", "session"):
            if not st.get(k):
                errs.append(f"status 缺 {k}（state={state}）")
    if state in ("green", "blocked", "accepted"):
        commit = st.get("commit")
        if not commit:
            errs.append(f"status 缺 commit（state={state}）")
        elif not legal_commit(repo, commit):
            errs.append(f"status.commit 不是合法提交：{commit}")
    if state == "accepted":
        acc = st.get("accepted") or st.get("acceptance")
        if not isinstance(acc, dict):
            errs.append("status 缺 accepted 验收记录（state=accepted）")
        else:
            for k in ("by", "verdict"):
                if not acc.get(k):
                    errs.append(f"accepted 验收记录缺 {k}")

    result = st.get("result") or os.path.join(os.path.dirname(a.status), "result.md")
    rpath = result if os.path.isabs(result) else os.path.join(repo, result)
    if os.path.isfile(rpath):
        r_lines = len(read_text(rpath).splitlines())
        if r_lines > MAX_RESULT_LINES:
            errs.append(f"result 超行数：{r_lines} 行 > 上限 {MAX_RESULT_LINES}")
    elif state == "accepted":
        errs.append(f"accepted 但 result 回执不存在：{rpath}")

    if state == "accepted":
        batches = os.path.join(repo, "docs", "BATCHES.md")
        btxt = read_text(batches) if os.path.isfile(batches) else ""
        if ("合同:" + cid) not in btxt and ("合同：" + cid) not in btxt:
            errs.append(f"BATCHES 缺「合同:{cid}」行（accepted 要求）")
        commit = st.get("commit")
        if st.get("base") and commit:
            rc, out, _ = sh(repo, "diff", "--name-only", f"{st['base']}..{commit}")
            if rc != 0:
                errs.append(f"git diff {st['base']}..{commit} 失败")
            else:
                bad = [p for p in out.splitlines()
                       if p and not p.startswith(EXEMPT) and not in_scope(p, patterns)]
                if bad:
                    errs.append(f"改动超出合同写入范围：{', '.join(bad[:5])}")

    print(f"合同：{a.contract}（{c_lines} 行）｜ id={cid} ｜ state={state}")
    for e in errs:
        print(f"  ✗ {e}")
    if errs:
        print(f"结论：阻断 {len(errs)} 条")
        return 1
    print("结论：通过（合同 / status / result / BATCHES / 写入范围）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
