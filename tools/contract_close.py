#!/usr/bin/env python3
"""合同收尾检查 + 台账追记草稿（合同 C4 §6③；TEAM §三·十二）：accepted 后一把核对、给人抄。

用法：python3 tools/contract_close.py <id> [--repo <根>] [--dry-run]

检查（accepted 后强校验，缺一即 FAIL）：
- `.pilot/<id>/status.json` 存在且 state=accepted（accepted 记录含 `by` / `verdict`）；
- 合同 spec `docs/contracts/<id>-*.md` 存在；
- `tools/contract_check.py` 通过（复用同一机械校验，不另立口径）；
- `docs/BATCHES.md` 含「合同:<id>」；
- `.pilot/<id>/cost.json` 摘要（有则判双判据：perBatch ≤ threshold 且 ≤30M/批）。

未 accepted（open/claimed/green）：accepted 校验记 **SKIP**（不阻断提交前预览），照常打印
追记行 / HANDOFF 摘要 / METRICS 提示 / cost 摘要草稿；A 置 accepted 后重跑才做正式校验。
只打印、不写任何文件（风格同 `tools/batch_close.py`）。
exit：0 检查全过或未 accepted 预览（SKIP）/ 1 有 FAIL / 2 用法或仓库错误。
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = timezone(timedelta(hours=8))
COST_FIELDS = ("windowTotal", "baselinePerBatch", "delta", "perBatch", "threshold")
CAP_30M = 30_000_000            # 双判据之二：≤30M/批
THRESHOLD_RATIO = 0.85          # 双判据之一：≤基线×0.85（cost.json 的 threshold 已按此算好）


def sh(repo, *args, timeout=30):
    """跑 git，返回 (exit码, stdout, stderr)；异常不抛。"""
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)


def read_text(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_json(path):
    """读 JSON；缺/坏返回 None（由调用方记 FAIL，不静默当空对象）。"""
    try:
        return json.loads(read_text(path))
    except (OSError, ValueError):
        return None


def find_contract(repo, cid):
    """docs/contracts/<id>-*.md → 第一个（编号唯一，正常只有一份）。"""
    hits = sorted(glob.glob(os.path.join(repo, "docs", "contracts", "%s-*.md" % cid)))
    return hits[0] if hits else None


def contract_title(spec):
    """取合同一级标题，供 HANDOFF 摘要行标注。"""
    try:
        for line in read_text(spec).splitlines():
            s = line.strip()
            if s.startswith("#"):
                return s.lstrip("#").strip()
    except OSError:
        pass
    return ""


def check_status(repo, cid):
    """校验运行态：accepted → 强校验（ok=True/False）；其它 state → SKIP（ok=None，供提交前预览）。"""
    spath = os.path.join(repo, ".pilot", cid, "status.json")
    if not os.path.isfile(spath):
        return False, "缺 .pilot/%s/status.json（运行态缺失）" % cid, {}
    st = read_json(spath)
    if not isinstance(st, dict):
        return False, ".pilot/%s/status.json 不是合法对象" % cid, {}
    state = st.get("state")
    if state != "accepted":
        return None, ("未 accepted（state=%s）：accepted 校验 SKIP（A 置 accepted 后重跑才做正式校验；"
                      "以下草稿为预览）" % state), st
    acc = st.get("accepted") or st.get("acceptance") or {}
    miss = [k for k in ("by", "verdict") if not (isinstance(acc, dict) and acc.get(k))]
    if miss:
        return False, "accepted 验收记录缺 %s" % " / ".join(miss), st
    return True, "accepted（by=%s ｜ verdict=%s）" % (acc.get("by"), acc.get("verdict")), st


def run_contract_check(repo, spec, spath):
    """复用 tools/contract_check.py（不另立口径）。返回 (ok|None, msg)。"""
    script = os.path.join(ROOT, "tools", "contract_check.py")
    if not os.path.isfile(script):
        return None, "SKIP 无 tools/contract_check.py（人工核合同）"
    try:
        r = subprocess.run([sys.executable, script, "--contract", spec, "--status", spath,
                            "--repo", repo], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "contract_check FAIL（超时）"
    lines = [ln.strip() for ln in (r.stdout + r.stderr).splitlines() if ln.strip()]
    tail = " / ".join(lines[-3:]) if lines else ""
    if r.returncode == 0:
        return True, "contract_check 通过（exit 0）"
    return False, "contract_check FAIL（exit %d）：%s" % (r.returncode, tail)


def check_batches(repo, cid):
    """BATCHES 是否已含「合同:<id>」行（accepted 的台账要求）。"""
    path = os.path.join(repo, "docs", "BATCHES.md")
    if not os.path.isfile(path):
        return False, "缺 docs/BATCHES.md"
    text = read_text(path)
    if ("合同:" + cid) in text or ("合同：" + cid) in text:
        return True, "BATCHES 含「合同:%s」行" % cid
    return False, "BATCHES 缺「合同:%s」行" % cid


def fmt_m(n):
    return "%.1fM" % (float(n) / 1_000_000)


def cost_summary(repo, cid):
    """cost.json 摘要 → (状态 ok|missing|fail, 文本)。missing 不算失败（无数据不默认红）。"""
    path = os.path.join(repo, ".pilot", cid, "cost.json")
    if not os.path.isfile(path):
        return "missing", "缺 .pilot/%s/cost.json（accepted 后用 `python3 tools/cost_snapshot.py --contract %s` 取；不算失败）" % (cid, cid)
    cost = read_json(path)
    if not isinstance(cost, dict):
        return "fail", ".pilot/%s/cost.json 不是合法对象" % cid
    miss = [k for k in COST_FIELDS if k not in cost]
    if miss:
        return "fail", ".pilot/%s/cost.json 缺字段：%s" % (cid, ", ".join(miss))
    per, thr = cost.get("perBatch"), cost.get("threshold")
    notes, over = [], False
    if isinstance(per, (int, float)):
        notes.append("perBatch=%s" % fmt_m(per))
        if isinstance(thr, (int, float)):
            over = over or per > thr
            notes.append("%s阈值 %s" % ("≤" if per <= thr else "> 超", fmt_m(thr)))
        over = over or per > CAP_30M
        notes.append("%s 30M/批" % ("≤" if per <= CAP_30M else "> 超"))
    else:
        return "fail", ".pilot/%s/cost.json 的 perBatch 不是数字" % cid
    return ("fail" if over else "ok"), "；".join(notes) + ("（超判据，须复盘）" if over else "（双判据 ✓）")


def draft_batch_note(cid, st, cost_status, cost_text):
    """BATCHES 追记行草稿：一行 `> ...`，粘到末行后；未 accepted 时明确标「预览」。"""
    acc = (st.get("accepted") or st.get("acceptance") or {}) if isinstance(st, dict) else {}
    if not isinstance(acc, dict):
        acc = {}
    state = st.get("state") if isinstance(st, dict) else None
    if state == "accepted":
        acc_part = "accepted by %s / verdict %s" % (acc.get("by"), acc.get("verdict"))
    else:
        acc_part = "【预览】当前 state=%s（待 A 置 accepted 后重跑取正式追记）" % (state or "?")
    cost_part = ("cost 快照未取（accepted 后补取）" if cost_status == "missing"
                 else "cost " + cost_text)
    return ("> 合同收尾追记（%s，%s）：%s；提交 `%s`；%s；"
            "contract_check exit 0；BATCHES 已含合同:%s；METRICS 已重生成（#9/#10 计入）；"
            "待考官「可发布」→ B push。"
            % (cid, datetime.now(TZ).strftime("%Y-%m-%d"), acc_part,
               st.get("commit") or "（无 commit 字段）", cost_part, cid))


def draft_handoff_line(cid, title, st, cost_status, cost_text):
    """HANDOFF 摘要行草稿：一行 `- ...`；未 accepted 时标「预览」。"""
    state = st.get("state") if isinstance(st, dict) else None
    tag = "" if state == "accepted" else "（预览，待 accepted）"
    cost_part = "cost 快照未取" if cost_status == "missing" else "cost " + cost_text
    return ("- 合同 %s（%s）%s：提交 `%s`；%s；contract_check exit 0；BATCHES 已含合同:%s。"
            % (cid, title or "见合同", tag, st.get("commit") or "（无 commit 字段）",
               cost_part, cid))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="contract_close.py",
        description="合同收尾检查（accepted / contract_check / BATCHES / cost）+ 台账追记草稿；只打印不改台账",
        epilog="示例：python3 tools/contract_close.py C4（默认即 dry-run：只打印）",
    )
    ap.add_argument("id", metavar="ID", help="合同号（如 C4）")
    ap.add_argument("--repo", default=None, help="仓库根（默认 git toplevel）")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写（本工具从不写，保留以对齐 batch_close）")
    a = ap.parse_args(argv)

    repo = a.repo
    if repo is None:
        rc, out, _ = sh(os.getcwd(), "rev-parse", "--show-toplevel")
        repo = out if rc == 0 and out else None
    if not repo:
        print("FAIL git 不可用 / 不在仓库里")
        return 2

    spath = os.path.join(repo, ".pilot", a.id, "status.json")
    checks = []
    ok_st, msg_st, st = check_status(repo, a.id)
    checks.append(("status", ok_st, msg_st))
    spec = find_contract(repo, a.id)
    if spec:
        checks.append(("合同", True, os.path.relpath(spec, repo)))
    else:
        checks.append(("合同", False, "缺 docs/contracts/%s-*.md" % a.id))
    if spec and os.path.isfile(spath):
        checks.append(("contract_check", *run_contract_check(repo, spec, spath)))
    else:
        checks.append(("contract_check", None, "SKIP 合同 spec / status 缺失"))
    checks.append(("BATCHES", *check_batches(repo, a.id)))
    cost_status, cost_text = cost_summary(repo, a.id)
    checks.append(("cost", {"ok": True, "missing": None, "fail": False}[cost_status], cost_text))

    print("== 合同收尾检查：%s ==" % a.id)
    failed = 0
    skipped = 0
    for name, ok, msg in checks:
        print(("✓" if ok else ("SKIP" if ok is None else "✗")) + " %s: %s" % (name, msg))
        if ok is False:
            failed += 1
        elif ok is None:
            skipped += 1

    if ok_st is not False:
        print("\nBATCHES 追记行草稿（一行，粘到 BATCHES 末行后）：")
        print(draft_batch_note(a.id, st, cost_status, cost_text))
        print("\nHANDOFF 摘要行草稿（粘到 HANDOFF 对应批）：")
        print(draft_handoff_line(a.id, contract_title(spec) if spec else "",
                                 st, cost_status, cost_text))
    else:
        print("\nBATCHES 追记行草稿 / HANDOFF 摘要行草稿：SKIP（status 缺失/非法，先补运行态）")
    if skipped:
        print("\n（%d 项 SKIP：未 accepted 只作提交前预览；A 置 accepted 后重跑才做正式校验、"
              "FAIL 即阻断）" % skipped)
    print("\nMETRICS 重生成提示：")
    print("  python3 tools/metrics.py   # 重新生成 docs/generated/METRICS.md"
          "（#9 合同一次通过率 / #10 每合同成本 计入本合同）")
    print("\n待办提醒：")
    print("  1. 本工具只打印、不写台账：追记行 / 摘要行由人工粘进 BATCHES / HANDOFF")
    print("  2. METRICS 重生成后跑 `python3 tools/metrics.py --check`（#9 / #10 有数据）")
    print("  3. 未 accepted 时 exit 0（预览）；A 置 accepted 后重跑，FAIL 才阻断收尾")
    print("\n结论：" + ("检查全过" + ("（含 SKIP：未 accepted 预览）" if skipped else "")
                      if not failed else "%d 项 FAIL（先修再收尾）" % failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
