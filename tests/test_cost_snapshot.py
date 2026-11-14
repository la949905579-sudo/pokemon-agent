#!/usr/bin/env python3
"""tools/cost_snapshot.py 的离线测试（fixture 喂字节/对象，不联网、不碰真实 .pilot）。

覆盖：`--contract` 的 5 字段计算（compute_cost）+ `--before` 的 4 字段计算
（compute_before，合同 C4 §6①）、窗口批次数解析、以及 `--before` 产物作 `--contract` 基线。
"""
import importlib.util
import os
import tempfile
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, "tools", "cost_snapshot.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = load("cost_snapshot", SNAP)

# token_report --json 的报告形状（只留本工具用到的字段；totals 故意给干扰值）
REPORT = {
    "days": [
        {"day": "2026-11-13", "inputTokens": 1000, "totalTokens": 120_000_000},
        {"day": "2026-11-14", "inputTokens": 500, "totalTokens": 80_000_000},
    ],
    "roles": [
        {"role": "助理", "sessions": 2, "totalTokens": 150_000_000},
        {"role": "考官", "sessions": 1, "totalTokens": 50_000_000},
    ],
    "totals": {"totalTokens": 999, "inputTokens": 1500},  # 口径：windowTotal 只看 days
}
BEFORE = {"pilotBaseline": {"windowTotal": 100_000_000, "batches": 9,
                            "baselinePerBatch": 67_474_076}}


def test_full_fields_and_two_batches():
    """5 字段齐全 + 数值正确：windowTotal=days 求和、delta、按 2 批折算、threshold=×0.85。"""
    cost = MOD.compute_cost(REPORT, BEFORE, "C3", 2)
    for k in ("windowTotal", "baselinePerBatch", "delta", "perBatch", "threshold"):
        assert k in cost, k
    assert cost["contract"] == "C3"
    assert cost["batches"] == 2
    assert cost["windowTotal"] == 200_000_000, cost["windowTotal"]
    assert cost["baselinePerBatch"] == 67_474_076, cost["baselinePerBatch"]
    assert cost["delta"] == 100_000_000, cost["delta"]       # 200M − 100M
    assert cost["perBatch"] == 50_000_000, cost["perBatch"]  # 100M / 2 批
    assert cost["threshold"] == 57_352_965, cost["threshold"]  # round(67,474,076 × 0.85)


def test_by_role_passthrough():
    """byRole 直接取 report.roles（内容透传，不是聚合重算）。"""
    cost = MOD.compute_cost(REPORT, BEFORE, "C3", 1)
    assert cost["byRole"] == REPORT["roles"], cost["byRole"]
    assert [r["role"] for r in cost["byRole"]] == ["助理", "考官"]


def test_count_batches_from_rows():
    """只数含「合同:<id>」的数据行：跳过表头/分隔/模板，兼容全角冒号。"""
    text = "\n".join([
        "| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |",
        "|---|---|---|---|---|---|---|",
        "| <编号> | YYYY-MM-DD | <一句话> | `<hash>` | 可发布 / 不可发布 | 提交前 ✅ 推送前 ✅ | 合同:C3 |",
        "| A | 2026-11-13 | x | `1` | 待复核 | 提交前 ✅ | 合同:C3；授权留痕 |",
        "| B | 2026-11-14 | y | `2` | 待复核 | 提交前 ✅ | 合同：C3（全角） |",
        "| C | 2026-11-14 | z | `3` | 待复核 | 提交前 ✅ | 合同:C4 |",
        "| D | 2026-11-14 | w | `4` | 待复核 | 提交前 ✅ | 无合同号 |",
    ])
    assert MOD.count_batches(text, "C3") == 2, MOD.count_batches(text, "C3")
    assert MOD.count_batches(text, "C4") == 1, MOD.count_batches(text, "C4")
    assert MOD.count_batches("", "C3") == 0


def test_report_since_from_baseline():
    """--since 缺省 → 取基线文件 since（与基线同窗口）；CLI 优先；非法值忽略。"""
    assert MOD.report_since({"since": "2026-11-13"}, None) == "2026-11-13"
    assert MOD.report_since({"since": "2026-11-13"}, "2026-11-14") == "2026-11-14"
    assert MOD.report_since({}, None) is None
    assert MOD.report_since(None, None) is None
    assert MOD.report_since({"since": "not-a-date"}, None) is None


def test_missing_baseline_raises():
    """缺 pilotBaseline.baselinePerBatch → ValueError（不得静默按 0 算）。"""
    for before in ({}, {"pilotBaseline": {}}, {"pilotBaseline": {"windowTotal": 1}}, None):
        try:
            MOD.compute_cost(REPORT, before, "C3", 1)
        except ValueError:
            continue
        raise AssertionError("缺基线应抛 ValueError：%r" % (before,))


def test_zero_batches_raises():
    """0 批（BATCHES 没本批行）→ ValueError，不写 cost.json。"""
    for n in (0, -1, True):
        try:
            MOD.compute_cost(REPORT, BEFORE, "C3", n)
        except ValueError:
            continue
        raise AssertionError("batches=%r 应抛 ValueError" % (n,))


def test_compute_before_fields_and_math():
    """--before 四字段齐全：baselinePerBatch=窗口总量÷批次数、threshold=×0.85（与 C4 手动快照同口径复算）。"""
    base = MOD.compute_before(REPORT, "C5", 4, "2026-11-14")
    for k in ("windowTotal", "batches", "baselinePerBatch", "threshold"):
        assert k in base, k
    assert base["id"] == "C5" and base["since"] == "2026-11-14"
    assert base["windowTotal"] == 200_000_000, base["windowTotal"]     # 只看 days[].totalTokens
    assert base["batches"] == 4
    assert base["baselinePerBatch"] == 50_000_000                     # 200M / 4
    assert base["threshold"] == 42_500_000                            # round(50M × 0.85)
    # 样本复算：C4 手动快照 117,604,016 ÷ 5 批 → 23,520,803 / 阈值 19,992,683
    c4 = {"days": [{"totalTokens": 117_604_016}]}
    b4 = MOD.compute_before(c4, "C4", 5, "2026-11-14")
    assert b4["baselinePerBatch"] == 23_520_803, b4["baselinePerBatch"]
    assert b4["threshold"] == 19_992_683, b4["threshold"]


def test_compute_before_rejects_bad_input():
    """--before：0 批 / 缺 since → ValueError（基线不得静默按 0 算）。"""
    for n in (0, -1, True):
        try:
            MOD.compute_before(REPORT, "C5", n, "2026-11-14")
        except ValueError:
            continue
        raise AssertionError("batches=%r 应抛 ValueError" % (n,))
    try:
        MOD.compute_before(REPORT, "C5", 2, None)
    except ValueError:
        pass
    else:
        raise AssertionError("缺 since 应抛 ValueError")


def test_count_window_batches_since_and_exclude():
    """窗口批次数：只数日期 ≥ since 的数据行；模板/表头/分隔行不计；可排除本批「合同:<id>」行。"""
    text = "\n".join([
        "| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |",
        "|---|---|---|---|---|---|---|",
        "| <编号> | YYYY-MM-DD | <一句话> | `<hash>` | 待复核 | 提交前 ✅ | 合同:C5 |",
        "| A | 2026-11-13 | 前一日 | `1` | 待复核 | 提交前 ✅ | 合同:C1 |",
        "| B | 2026-11-14 | x | `2` | 待复核 | 提交前 ✅ | 合同:C2 |",
        "| C | 2026-11-14 | y | `3` | 待复核 | 提交前 ✅ | 合同:C3 |",
        "| 本批 | 2026-11-14 | 本批行 | `<hash>` | 待复核 | 提交前 ✅ | 合同:C5 |",
    ])
    assert MOD.count_window_batches(text, "2026-11-14") == 3, MOD.count_window_batches(text, "2026-11-14")
    assert MOD.count_window_batches(text, "2026-11-14", exclude_cid="C5") == 2
    assert MOD.count_window_batches(text, "2026-11-13") == 4
    assert MOD.count_window_batches("", "2026-11-14") == 0


def test_before_output_usable_as_contract_baseline():
    """--before 产出的顶层基线可直接喂 --contract：delta 用顶层 windowTotal，不要求 pilotBaseline 嵌套。"""
    before = {"id": "C4", "since": "2026-11-14", "windowTotal": 100_000_000,
              "batches": 5, "baselinePerBatch": 20_000_000, "threshold": 17_000_000}
    cost = MOD.compute_cost(REPORT, before, "C4", 1)
    assert cost["baselinePerBatch"] == 20_000_000
    assert cost["delta"] == 100_000_000        # 200M − 100M（顶层 windowTotal）
    assert cost["perBatch"] == 100_000_000
    assert cost["threshold"] == 17_000_000     # round(20M × 0.85)
    assert MOD.report_since(before) == "2026-11-14"


def test_defaults_pick_contract_baseline():
    """--before 缺省窗口起点=当天；--contract 缺省基线优先 .pilot/<id>/cost-before.json，退旧全局基线。"""
    assert MOD.default_since(datetime(2026, 11, 14, 9, 30)) == "2026-11-14"
    with tempfile.TemporaryDirectory() as tmp:
        assert MOD.baseline_for("C5", tmp) == os.path.join(tmp, ".pilot", "cost-before.json")
        os.makedirs(os.path.join(tmp, ".pilot", "C5"))
        with open(os.path.join(tmp, ".pilot", "C5", "cost-before.json"), "w", encoding="utf-8") as f:
            f.write("{}\n")
        assert MOD.baseline_for("C5", tmp) == os.path.join(tmp, ".pilot", "C5", "cost-before.json")


if __name__ == "__main__":
    for fn in (test_full_fields_and_two_batches, test_by_role_passthrough,
               test_count_batches_from_rows, test_report_since_from_baseline,
               test_missing_baseline_raises, test_zero_batches_raises,
               test_compute_before_fields_and_math, test_compute_before_rejects_bad_input,
               test_count_window_batches_since_and_exclude,
               test_before_output_usable_as_contract_baseline,
               test_defaults_pick_contract_baseline):
        fn()
    print("全部通过")
