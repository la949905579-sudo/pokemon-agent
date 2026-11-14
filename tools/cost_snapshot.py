#!/usr/bin/env python3
"""每合同成本快照（合同 C3 §6③ / C4 §6①；TEAM §三·十 / §三·十二）。

两种模式：
- `--contract <id>`：生成 `.pilot/<id>/cost.json`（accepted 后取），字段
  `windowTotal` / `baselinePerBatch` / `delta` / `perBatch` / `threshold` + `byRole`；
- `--before <id>`：开工前成本基线，写 `.pilot/<id>/cost-before.json`，字段
  `windowTotal` / `batches` / `baselinePerBatch` / `threshold`（口径见合同 §7.4 / TEAM §三·十）。

口径：
- `windowTotal` = `token_report.mjs --json` 的 `days[].totalTokens` 求和（窗口内总量）；
- `--before`：`batches` = `docs/BATCHES.md` 中日期落在窗口内（≥`since`）的数据行数（排除本批 `<id>` 行），
  `baselinePerBatch` = round(windowTotal / batches)，`threshold` = round(baselinePerBatch × 0.85)；
- `--contract`：基线取 `--baseline`（缺省优先 `.pilot/<id>/cost-before.json`，退旧 `.pilot/cost-before.json`）
  的 `baselinePerBatch`（兼容 `pilotBaseline` 嵌套与 `--before` 产出的顶层字段）；
  `delta` = windowTotal − 基线 `windowTotal`；`batches` = `docs/BATCHES.md` 中含「合同:<id>」的数据行数（须 ≥1）；
  `perBatch` = round(delta / batches)；`threshold` = round(baselinePerBatch × 0.85)；
- 另写 `byRole`（直接取 report.roles）+ `contract` / `generatedAt` / `batches`。

用法：
    python3 tools/cost_snapshot.py --contract C3 [--since 2026-11-13]
    python3 tools/cost_snapshot.py --before C5 [--since 2026-11-14]
    python3 tools/cost_snapshot.py --contract C3 --report /tmp/report.json --baseline /tmp/before.json --out /tmp/cost.json
    python3 tools/cost_snapshot.py --before C5 --report /tmp/report.json --dry-run

窗口口径：`--contract` 的 `--since` 缺省时自动取基线文件里的 `since`（现为 `2026-11-13`），保证 windowTotal
与基线同窗口（PILOT §六「同一 since」）；否则默认全量窗口会把窗口前的天也计进 delta。
`--before` 的窗口起点缺省取当天（Asia/Shanghai）：基线 = 开工当日窗口 ÷ 窗口内批次数（不含本批），
与 A 手动落 C4 基线的口径一致（TEAM §三·十 / 合同 §7.4）。
默认跑 `node tools/token_report.mjs --json`（只读本地会话日志，不走网络）；写文件前不联网。
核心计算是纯函数 `compute_cost(report, before, cid, batches)` 与 `compute_before(report, cid, batches, since)`，
窗口起点是纯函数 `report_since(before, cli_since)`，测试可离线喂 fixture。
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
BEFORE_FIELDS = ("windowTotal", "batches", "baselinePerBatch", "threshold")
THRESHOLD_RATIO = 0.85          # 双判据阈值：基线 × 0.85（TEAM §三·十 / 合同 §7.4）
DAY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def window_total(report):
    """窗口总量 = days[].totalTokens 之和（不看 totals，避免口径混用）。"""
    days = (report or {}).get("days") or []
    total = 0
    for d in days:
        total += int((d or {}).get("totalTokens") or 0)
    return total


def baseline_per_batch(before):
    """取 before.pilotBaseline.baselinePerBatch；兼容 `--before` 产出的顶层 baselinePerBatch。缺/非法抛 ValueError。"""
    if not isinstance(before, dict):
        raise ValueError("缺 baseline：before.pilotBaseline.baselinePerBatch")
    pb = before.get("pilotBaseline")
    val = pb.get("baselinePerBatch") if isinstance(pb, dict) else None
    if val is None:
        val = before.get("baselinePerBatch")   # cost_snapshot --before 产出的顶层字段
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("缺 baseline：before.pilotBaseline.baselinePerBatch")
    return int(val)


def before_window_total(before):
    """基线侧窗口总量：优先 pilotBaseline.windowTotal（旧全局基线），否则顶层 windowTotal（--before 产出）。"""
    if not isinstance(before, dict):
        return 0
    pb = before.get("pilotBaseline")
    if isinstance(pb, dict) and pb.get("windowTotal") is not None:
        return int(pb.get("windowTotal") or 0)
    return int(before.get("windowTotal") or 0)


def compute_cost(report, before, cid, batches):
    """纯函数：token_report --json + cost-before.json → cost.json 内容（5 字段 + byRole）。"""
    if not isinstance(report, dict):
        raise ValueError("report 必须是对象")
    baseline = baseline_per_batch(before)
    if isinstance(batches, bool) or not isinstance(batches, int) or batches < 1:
        raise ValueError("batches 须为 ≥1 的整数（BATCHES 没有「合同:%s」行）" % cid)
    total = window_total(report)
    delta = total - before_window_total(before)
    return {
        "contract": str(cid),
        "windowTotal": total,
        "baselinePerBatch": baseline,
        "delta": delta,
        "batches": batches,
        "perBatch": round(delta / batches),
        "threshold": round(baseline * THRESHOLD_RATIO),
        "byRole": list((report or {}).get("roles") or []),
    }


def compute_before(report, cid, batches, since):
    """纯函数：report + 窗口内批次数 → cost-before.json 内容（§6①：windowTotal/batches/baselinePerBatch/threshold）。"""
    if not isinstance(report, dict):
        raise ValueError("report 必须是对象")
    if isinstance(batches, bool) or not isinstance(batches, int) or batches < 1:
        raise ValueError("batches 须为 ≥1 的整数（窗口内没有 BATCHES 数据行，算不出基线）")
    if not since:
        raise ValueError("缺 since（窗口起点，YYYY-MM-DD）")
    total = window_total(report)
    baseline = round(total / batches)
    return {
        "id": str(cid),
        "since": since,
        "windowTotal": total,
        "batches": batches,
        "baselinePerBatch": baseline,
        "threshold": round(baseline * THRESHOLD_RATIO),
    }


def batch_rows(text):
    """BATCHES 数据行 → 单元格列表（跳过表头 / 分隔 / 模板行）。"""
    rows = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or cells[0] in ("批次", "") or cells[0].startswith("<"):
            continue
        if set(s) <= set("| :-"):
            continue
        rows.append(cells)
    return rows


def count_batches(text, cid):
    """BATCHES 中含「合同:<id>」的数据行数（跳过表头/模板/分隔行）。"""
    pat = re.compile(r"合同[:：]\s*%s(?!\d)" % re.escape(str(cid)))
    return sum(1 for cells in batch_rows(text) if pat.search("|".join(cells)))


def count_window_batches(text, since, exclude_cid=None):
    """窗口内批次数：日期列（第 2 列）≥ since 的数据行，排除「合同:<exclude_cid>」本批行（§7.4 不含本批）。"""
    if not since:
        raise ValueError("缺 since（窗口起点，YYYY-MM-DD）")
    n = 0
    for cells in batch_rows(text):
        m = DAY_RE.match(cells[1]) if len(cells) > 1 else None
        if not m or m.group(1) < since:
            continue
        if exclude_cid and re.search(r"合同[:：]\s*%s(?!\d)" % re.escape(str(exclude_cid)),
                                     "|".join(cells)):
            continue
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


def default_since(now=None):
    """--before 的窗口起点缺省值：当天（Asia/Shanghai，开工日）。"""
    return (now or datetime.now(TZ)).strftime("%Y-%m-%d")


def baseline_for(cid, root=ROOT):
    """--contract 的缺省基线：优先 .pilot/<id>/cost-before.json（--before 产出），否则旧全局基线。"""
    per_contract = os.path.join(root, ".pilot", str(cid), "cost-before.json")
    if os.path.isfile(per_contract):
        return per_contract
    return os.path.join(root, DEFAULT_BASELINE)


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
        description="每合同成本快照：--contract 读 token_report --json + cost-before 基线，"
                    "写 .pilot/<id>/cost.json（windowTotal/baselinePerBatch/delta/perBatch/threshold + byRole）；"
                    "--before 写 .pilot/<id>/cost-before.json（windowTotal/batches/baselinePerBatch/threshold）。",
        epilog="示例：python3 tools/cost_snapshot.py --before C5 ｜ "
               "python3 tools/cost_snapshot.py --contract C4",
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--contract", metavar="ID", help="合同号（如 C3）：生成 .pilot/<id>/cost.json")
    group.add_argument("--before", metavar="ID",
                       help="合同号（如 C5）：开工前基线 → .pilot/<id>/cost-before.json（C5 起成本门禁读它）")
    ap.add_argument("--since", default=None, metavar="YYYY-MM-DD",
                    help="token 统计窗口起点（可选；--before 缺省当天）")
    ap.add_argument("--baseline", default=None, metavar="PATH|N",
                    help="--contract 的基线：默认优先 .pilot/<id>/cost-before.json，退 .pilot/cost-before.json")
    ap.add_argument("--report", default=None, metavar="PATH",
                    help="离线 report JSON（默认跑 node tools/token_report.mjs --json）")
    ap.add_argument("--out", default=None, metavar="PATH",
                    help="默认 .pilot/<id>/cost.json（--before 时为 cost-before.json）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 JSON，不写文件")
    return ap


def write_contract(args, batches_text):
    """--contract 模式：accepted 后成本快照 → .pilot/<id>/cost.json。"""
    baseline = args.baseline if args.baseline is not None else baseline_for(args.contract)
    before = load_baseline(baseline)
    since = report_since(before, args.since)
    report = load_report(args.report, since)
    batches = count_batches(batches_text, args.contract)
    cost = compute_cost(report, before, args.contract, batches)
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


def write_before(args, batches_text):
    """--before 模式：开工前成本基线 → .pilot/<id>/cost-before.json。"""
    since = args.since or default_since()
    report = load_report(args.report, since)
    batches = count_window_batches(batches_text, since, exclude_cid=args.before)
    base = compute_before(report, args.before, batches, since)
    base["generatedAt"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M（Asia/Shanghai）")
    base["method"] = "TEAM §三·十 / 合同 §7.4：开工前当日窗口实测 ÷ 窗口内批次数（不含本批）"
    base["window"] = "token_report --since %s" % since
    if args.dry_run:
        print(json.dumps(base, ensure_ascii=False, indent=2))
        return 0
    out = args.out or os.path.join(".pilot", args.before, "cost-before.json")
    write_cost(base, out)
    print("已写入 %s（windowTotal=%d / batches=%d / baselinePerBatch=%d / threshold=%d）"
          % (out, base["windowTotal"], base["batches"], base["baselinePerBatch"], base["threshold"]))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    batches_text = ""
    batches_path = os.path.join(ROOT, "docs", "BATCHES.md")
    try:
        with open(batches_path, encoding="utf-8") as f:
            batches_text = f.read()
        if args.before:
            return write_before(args, batches_text)
        return write_contract(args, batches_text)
    except Exception as e:
        print("FAIL %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
