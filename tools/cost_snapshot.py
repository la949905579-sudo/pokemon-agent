#!/usr/bin/env python3
"""每合同成本快照（合同 C3 §6③ / TEAM §三·十二）：`--contract <id>` 生成 `.pilot/<id>/cost.json`。

口径：
- `windowTotal` = `token_report.mjs --json` 的 `days[].totalTokens` 求和（窗口内总量）；
- 基线取 `.pilot/cost-before.json` 的 `pilotBaseline.baselinePerBatch`（缺则 `--baseline` 给文件或数字）；
- `delta` = windowTotal − `before.pilotBaseline.windowTotal`；
- `batches` = `docs/BATCHES.md` 中含「合同:<id>」的数据行数（须 ≥1）；
- `perBatch` = round(delta / batches)；`threshold` = round(baselinePerBatch × 0.85)；
- 另写 `byRole`（直接取 report.roles）+ `contract` / `generatedAt` / `batches`。

用法：
    python3 tools/cost_snapshot.py --contract C3 [--since 2026-11-13]
    python3 tools/cost_snapshot.py --contract C3 --report /tmp/report.json --baseline /tmp/before.json --out /tmp/cost.json

窗口口径：`--since` 缺省时自动取基线文件里的 `since`（现为 `2026-11-13`），保证 windowTotal
与基线同窗口（PILOT §六「同一 since」）；否则默认全量窗口会把窗口前的天也计进 delta。
默认跑 `node tools/token_report.mjs --json`（只读本地会话日志，不走网络）；写文件前不联网。
核心计算是纯函数 `compute_cost(report, before, cid, batches)`，窗口起点是纯函数
`report_since(before, cli_since)`，测试可离线喂 fixture。
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = timezone(timedelta(hours=8))
DEFAULT_BASELINE = os.path.join(".pilot", "cost-before.json")
COST_FIELDS = ("windowTotal", "baselinePerBatch", "delta", "perBatch", "threshold")


def window_total(report):
    """窗口总量 = days[].totalTokens 之和（不看 totals，避免口径混用）。"""
    days = (report or {}).get("days") or []
    total = 0
    for d in days:
        total += int((d or {}).get("totalTokens") or 0)
    return total


def baseline_per_batch(before):
    """取 before.pilotBaseline.baselinePerBatch；缺/非法抛 ValueError。"""
    pb = (before or {}).get("pilotBaseline") if isinstance(before, dict) else None
    val = pb.get("baselinePerBatch") if isinstance(pb, dict) else None
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("缺 baseline：before.pilotBaseline.baselinePerBatch")
    return int(val)


def compute_cost(report, before, cid, batches):
    """纯函数：token_report --json + cost-before.json → cost.json 内容（5 字段 + byRole）。"""
    if not isinstance(report, dict):
        raise ValueError("report 必须是对象")
    baseline = baseline_per_batch(before)
    if isinstance(batches, bool) or not isinstance(batches, int) or batches < 1:
        raise ValueError("batches 须为 ≥1 的整数（BATCHES 没有「合同:%s」行）" % cid)
    total = window_total(report)
    before_total = int(((before.get("pilotBaseline") or {}).get("windowTotal")) or 0)
    delta = total - before_total
    return {
        "contract": str(cid),
        "windowTotal": total,
        "baselinePerBatch": baseline,
        "delta": delta,
        "batches": batches,
        "perBatch": round(delta / batches),
        "threshold": round(baseline * 0.85),
        "byRole": list((report or {}).get("roles") or []),
    }


def count_batches(text, cid):
    """BATCHES 中含「合同:<id>」的数据行数（跳过表头/模板/分隔行）。"""
    pat = re.compile(r"合同[:：]\s*%s(?!\d)" % re.escape(str(cid)))
    n = 0
    for line in (text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or cells[0] in ("批次", "") or cells[0].startswith("<"):
            continue
        if set(s) <= set("| :-"):
            continue
        if pat.search(s):
            n += 1
    return n


def load_baseline(value):
    """--baseline：存在的文件 → 读 JSON；纯数字 → 只给 baselinePerBatch（windowTotal 按 0）。"""
    value = str(value)
    if os.path.isfile(value):
        with open(value, encoding="utf-8") as f:
            return json.load(f)
    try:
        num = int(value)
    except (TypeError, ValueError):
        raise ValueError("基线不存在也不是数字：%s" % value)
    return {"pilotBaseline": {"windowTotal": 0, "baselinePerBatch": num}}


def report_since(before, cli_since=None):
    """窗口起点：CLI 给了 --since 用 CLI；否则取基线文件里的 since（与基线同窗口，PILOT §六）。

    缺省/非法（非 YYYY-MM-DD）返回 None（token_report 按全量窗口）；纯数字基线没有 since。
    """
    if cli_since:
        return cli_since
    value = (before or {}).get("since") if isinstance(before, dict) else None
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    return None


def run_report(since=None):
    """跑 node tools/token_report.mjs --json（只读本地会话日志，不联网）。"""
    cmd = ["node", os.path.join(ROOT, "tools", "token_report.mjs"), "--json"]
    if since:
        cmd += ["--since", since]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError("token_report 失败（exit %d）：%s" % (r.returncode, (r.stderr or "").strip()[-200:]))
    out = r.stdout.strip()
    start = out.find("{")
    if start < 0:
        raise RuntimeError("token_report 没输出 JSON")
    return json.loads(out[start:])


def load_report(path, since=None):
    if path:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return run_report(since)


def write_cost(cost, out_path):
    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cost, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="cost_snapshot.py",
        description="每合同成本快照：读 token_report --json + cost-before 基线，"
                    "写 .pilot/<id>/cost.json（windowTotal/baselinePerBatch/delta/perBatch/threshold + byRole）。",
    )
    ap.add_argument("--contract", required=True, metavar="ID", help="合同号（如 C3）")
    ap.add_argument("--since", default=None, metavar="YYYY-MM-DD", help="token 统计窗口起点（可选）")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, metavar="PATH|N",
                    help="基线文件（默认 .pilot/cost-before.json）或 baselinePerBatch 数字")
    ap.add_argument("--report", default=None, metavar="PATH",
                    help="离线 report JSON（默认跑 node tools/token_report.mjs --json）")
    ap.add_argument("--out", default=None, metavar="PATH", help="默认 .pilot/<id>/cost.json")
    ap.add_argument("--dry-run", action="store_true", help="只打印 JSON，不写文件")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    batches_text = ""
    batches_path = os.path.join(ROOT, "docs", "BATCHES.md")
    try:
        with open(batches_path, encoding="utf-8") as f:
            batches_text = f.read()
        before = load_baseline(args.baseline)
        since = report_since(before, args.since)
        report = load_report(args.report, since)
        batches = count_batches(batches_text, args.contract)
        cost = compute_cost(report, before, args.contract, batches)
    except Exception as e:
        print("FAIL %s" % e)
        return 2
    cost["since"] = since
    cost["generatedAt"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M（Asia/Shanghai）")
    if args.dry_run:
        print(json.dumps(cost, ensure_ascii=False, indent=2))
        return 0
    out = args.out or os.path.join(".pilot", args.contract, "cost.json")
    write_cost(cost, out)
    print("已写入 %s（windowTotal=%d / delta=%d / perBatch=%d / threshold=%d / batches=%d）"
          % (out, cost["windowTotal"], cost["delta"], cost["perBatch"],
             cost["threshold"], cost["batches"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
