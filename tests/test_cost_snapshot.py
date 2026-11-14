#!/usr/bin/env python3
"""tools/cost_snapshot.py 的离线测试（fixture 喂字节/对象，不联网、不碰真实 .pilot）。"""
import importlib.util
import os

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


if __name__ == "__main__":
    for fn in (test_full_fields_and_two_batches, test_by_role_passthrough,
               test_count_batches_from_rows, test_report_since_from_baseline,
               test_missing_baseline_raises, test_zero_batches_raises):
        fn()
    print("全部通过")
