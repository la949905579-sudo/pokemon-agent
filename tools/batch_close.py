#!/usr/bin/env python3
"""台账收尾检查 + BATCHES 行草稿（简化流程 v1.2，TEAM §三·十一）。
用法：python3 tools/batch_close.py --batch "<批次名>" [--contract C3] [--regen] [--run-tests] [--dry-run]
检查：BATCHES 末行「待复核/推送前 ⏳」/ 合同 accepted + contract_check / FILES --check=0 /
test_results 与 tests/ 文件数一致（--run-tests 才实跑）；输出 BATCHES 行草稿（7 列，含「合同:<id>」备注位）
+ 待办提醒。默认 dry-run 只打印；--regen 显式重生成 FILES/METRICS（唯一写动作）；BATCHES/HANDOFF 从不代写。
exit：0 全过 / 1 有 FAIL / 2 用法或仓库错误。
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=8))

def sh(repo, *args, timeout=60):
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

def run_py(repo, script, args=(), timeout=300, root=False):
    """跑仓库脚本，返回 (exit码|None, 输出末行|SKIP 说明)。"""
    path = os.path.join(repo, script if root else os.path.join("tools", script))
    if not os.path.isfile(path):
        return None, f"SKIP 无 {script}"
    try:
        r = subprocess.run([sys.executable, path, *args], cwd=repo, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 1, "FAIL 超时"
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()]
    return r.returncode, (lines[-1].strip() if lines else "")

def last_batch_row(text):
    """BATCHES 最后一条数据行 → 单元格列表；没有数据行返回 None。"""
    rows = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if r.strip("|").split("|")[0].strip() not in ("批次", "")]
    rows = [r for r in rows if set(r) - set("| :-")]
    return [c.strip() for c in rows[-1].strip("|").split("|")] if rows else None

def check_batches(repo):
    try:
        text = open(os.path.join(repo, "docs", "BATCHES.md"), encoding="utf-8").read()
    except OSError:
        return False, "FAIL 缺 docs/BATCHES.md"
    row = last_batch_row(text)
    if row is None:
        return False, "FAIL BATCHES 无数据行（本批行未追加）"
    raw = "|".join(row)
    if re.search(r"待[^|]*(复核|考官|CI|真机)", raw) and "⏳" in raw:
        return True, f"末行「{row[0]}」含待复核 + 推送前 ⏳"
    return False, f"FAIL 末行缺「待复核/推送前 ⏳」：{row[0]}"

def check_contract(repo, cid):
    spath = os.path.join(repo, ".pilot", cid, "status.json")
    if not os.path.isfile(spath):
        return False, f"FAIL 缺 .pilot/{cid}/status.json（运行态缺失）"
    st = read_json(spath) or {}
    if st.get("state") != "accepted":
        return False, f"FAIL 合同 {cid} 未 accepted（state={st.get('state')}）"
    cands = glob.glob(os.path.join(repo, "docs", "contracts", f"{cid}-*.md"))
    if not cands:
        return False, f"FAIL 缺 docs/contracts/{cid}-*.md"
    rc, out = run_py(repo, "contract_check.py", ["--contract", cands[0], "--status", spath, "--repo", repo])
    if rc is None:
        return None, f"SKIP 无 contract_check（人工核合同 {cid}）"
    return rc == 0, (f"合同 {cid} accepted，contract_check 通过" if rc == 0 else f"FAIL contract_check：{out}")

def check_files(repo):
    rc, out = run_py(repo, "gen_files_index.py", ["--check"])
    if rc is None:
        return None, "SKIP 无 gen_files_index（人工核 FILES）"
    return rc == 0, ("FILES --check = 0 ✓" if rc == 0 else f"FAIL FILES --check = {rc}：{out}")

def check_test_results(repo, run_tests):
    data = read_json(os.path.join(repo, "tools", "test_results.json"))
    if data is None:
        return False, "FAIL 缺 tools/test_results.json"
    rec = (data.get("python") or {}).get("tests")
    files = len(glob.glob(os.path.join(repo, "tests", "test_*.py")))
    if run_tests:
        rc, out = run_py(repo, "run_tests.py", [], timeout=600, root=True)
        return rc == 0, (f"实跑通过（{out}）；记录 python={rec}" if rc == 0 else f"FAIL 实跑未过：{out}")
    if rec == files:
        return True, f"python={rec} 与 tests/ 下 {files} 个测试文件一致（实跑加 --run-tests）"
    return False, f"FAIL python={rec} ≠ tests/ 下 {files} 个：先跑 run_tests.py 再同步 test_results"

def batch_draft(repo, batch, cid):
    """BATCHES 行草稿：7 列，含「合同:<id>」备注位。"""
    _, head, _ = sh(repo, "log", "-1", "--pretty=%h %s")
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    note = (f"合同:{cid}；" if cid else "") + "《授权留痕/来源/成本快照》"
    cols = [batch, today, f"《本批内容一句话》（含 docs/tools 计数）", "docs=`<hash>`；tools=`<hash>`（以 git log 为准）",
            "待复核（考官）", "提交前 ✅ 推送前 ⏳（等考官，不 push）", note]
    return "| " + " | ".join(cols) + " |"

def main(argv=None):
    ap = argparse.ArgumentParser(description="台账收尾检查 + BATCHES 行草稿")
    ap.add_argument("--batch", required=True, help="批次名（如「简化流程-v1.2」）")
    ap.add_argument("--contract", default=None, help="合同号（如 C3），给则校验运行态")
    ap.add_argument("--regen", action="store_true", help="重生成 FILES/METRICS（唯一写动作）")
    ap.add_argument("--run-tests", action="store_true", help="实跑 run_tests.py 并核数字")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写（默认）")
    a = ap.parse_args(argv)
    rc, out, _ = sh(os.getcwd(), "rev-parse", "--show-toplevel")
    repo = out if rc == 0 and out else None
    if not repo:
        print("FAIL git 不可用 / 不在仓库里")
        return 2
    write = a.regen and not a.dry_run
    checks = [("BATCHES", *check_batches(repo))]
    if a.contract:
        checks.append(("合同", *check_contract(repo, a.contract)))
    checks += [("FILES", *check_files(repo)), ("测试记录", *check_test_results(repo, a.run_tests))]
    print(f"== 台账收尾检查：{a.batch}（{'dry-run：只打印' if not write else 'regen：写生成物'}）==")
    failed = 0
    for name, ok, msg in checks:
        print(("✓" if ok else ("SKIP" if ok is None else "✗")) + f" {name}: {msg}")
        if ok is False:
            failed += 1
    if write:
        for script, label in (("gen_files_index.py", "FILES"), ("metrics.py", "METRICS（联网，慢）")):
            rc, out = run_py(repo, script, [], timeout=600)
            print(("✓" if rc == 0 else ("SKIP" if rc is None else "✗")) + f" 重生成 {label}: {out}")
    else:
        print("i 未重生成（加 --regen 写 FILES + METRICS；dry-run 下不写任何文件）")
    print("\nBATCHES 行草稿（7 列；粘贴前补内容 / 提交号 / 授权留痕）：")
    print(batch_draft(repo, a.batch, a.contract))
    print("\n待办提醒：")
    print("  1. 粘贴草稿 → precommit_check.sh --scope <路径> 提交；一次写对，禁止同批 amend")
    print("  2. HANDOFF：批次收尾 / 交接前按 §二 更新（测试数引用 test_results，不写死）")
    print("  3. METRICS 重生成 + 成本快照 .pilot/<id>/cost.json（合同批）")
    print("  4. 考官三查 → 通过后 precommit_check.sh --push（需 --examiner-ok）")
    print(f"\n结论：{'检查全过' if not failed else f'{failed} 项 FAIL（先修再提交）'}")
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
