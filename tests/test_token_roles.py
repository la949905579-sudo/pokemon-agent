#!/usr/bin/env python3
"""tools/token_report.mjs 职位归因（ROLE_PATTERNS / --roles）离线测试 —— 合同 C7 §6②。

覆盖（合同 C7 §7.1 M4 / §7.2）：
  1. --roles JSON：11 个规范角色齐全，且与 tools/write_scopes.json 同集；
  2. 旧名兼容映射：统筹主持·执行主管→代理人、独立督导·审查员·成本管理员→审计督导、
     builder→工匠、steward→助理、verifier→考官（含英文实例名）；
  3. 「取最靠左命中」规则不变（同 label 多职位词看谁先出现）；
  4. 有 descriptor 但无职位词→「未知职位」；无 descriptor→「主会话（未标注职位）」；
  5. 同 fixture「映射前后 totals 相等」：改分组不改总量（byRole 合计 = windowTotal）。

纯离线：不读真实 sessions 目录（fixture 经 TOKEN_REPORT_SESSIONS_ROOT 指到 tempdir）、
不联网、不写业务文件（落盘一律 tempfile）。
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "tools", "token_report.mjs")
SCOPES = os.path.join(ROOT, "tools", "write_scopes.json")
NODE = "node"
TZ = ZoneInfo("Asia/Shanghai")

# 11 规范角色（与 tools/write_scopes.json / docs/TEAM.md §一 同集，顺序同 ROLE_PATTERNS）
CANONICAL = [
    "代理人", "承包商", "审计督导", "组织规划", "策略顾问", "真机执行",
    "助理", "工匠", "考官", "分工规划员", "结构规划员",
]
NEW_ROLES = ["代理人", "承包商", "审计督导", "真机执行", "分工规划员", "结构规划员"]

# 合同 C7 §6① 旧名兼容映射（旧名 → 规范角色）
OLD_TO_NEW = {
    "统筹主持": "代理人",
    "执行主管": "代理人",
    "独立督导": "审计督导",
    "审查员": "审计督导",
    "成本管理员": "审计督导",
    "builder": "工匠",
    "steward": "助理",
    "verifier": "考官",
}

# 改前（旧 9 角色表，git a9604b8 的 ROLE_PATTERNS）——只在本测试内用于「映射前后 totals 相等」
OLD_PATTERNS = [
    ("统筹主持", ["统筹主持", "主持"]),
    ("助理", ["助理", "执行主管", "steward"]),
    ("工匠", ["工匠", "builder"]),
    ("考官", ["考官", "验证员", "verifier"]),
    ("独立督导", ["独立督导", "督导"]),
    ("审查员", ["审查员"]),
    ("成本管理员", ["成本管理员"]),
    ("组织规划", ["组织规划", "组织架构师", "architect"]),
    ("策略顾问", ["策略顾问", "advisor"]),
]


def sh(cmd, env=None):
    """跑子命令，返回 stdout（失败抛 RuntimeError 带 stderr）。"""
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                       cwd=ROOT, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[:2]} exit {r.returncode}: {(r.stderr or r.stdout)[-500:]}")
    return r.stdout


def roles_json():
    """--roles 输出（JSON：规范角色 → 匹配词）。"""
    return json.loads(sh([NODE, REPORT, "--roles", "--json"]))


def role_of(labels):
    """调 token_report.mjs 导出的 roleFromLabel（不扫 sessions），批量返回职位名。"""
    code = (
        "import { roleFromLabel } from %s;"
        "const labels = JSON.parse(process.argv[1]);"
        "console.log(JSON.stringify(labels.map(roleFromLabel)));"
    ) % json.dumps(Path(REPORT).as_uri())
    out = sh([NODE, "--input-type=module", "-e", code, json.dumps(labels, ensure_ascii=False)])
    return json.loads(out)


def old_role(label):
    """改前归因（测试内副本）：与旧代码同规则（取最靠左、同位置按表序）。"""
    if not label:
        return "主会话（未标注职位）"
    low = label.lower()
    best = None
    for idx, (role, pats) in enumerate(OLD_PATTERNS):
        for p in pats:
            pos = low.find(p.lower())
            if pos < 0:
                continue
            if best is None or pos < best[0] or (pos == best[0] and idx < best[1]):
                best = (pos, idx, role)
    return best[2] if best else "未知职位"


# 离线 fixture 写入器：在 tempdir 里生成 zstd 压缩的 session.v4.jsonl.zstd（不碰真实 sessions）
WRITER = r"""
import fs from "node:fs";
import zlib from "node:zlib";
const [, root, specJson] = process.argv;  // node -e 时 argv[1] 起才是参数
const spec = JSON.parse(specJson);
for (const item of spec) {
  const dir = root + "/--fixture-ws--/" + item.sid;
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(dir + "/session.v4.jsonl.zstd",
    zlib.zstdCompressSync(Buffer.from(item.text, "utf8")));
}
"""


def ms(y, m, d, hh=10):
    return int(datetime(y, m, d, hh, 0, tzinfo=TZ).timestamp() * 1000)


def usage_line(ts, total, extra=None):
    u = {"inputTokens": total // 2, "outputTokens": total // 10,
         "cacheReadTokens": total // 3, "cacheWriteTokens": 0, "totalTokens": total}
    if extra:
        u.update(extra)
    return {"type": "assistant/message", "time": ts, "data": {"usage": u}}


def descriptor_line(label):
    return {"type": "subagent/descriptor", "data": {"version": 3, "label": label}}


# fixture：窗口 2026-11-14 内 4 个会话（含 1 个窗口前 usage 验证 --since 裁剪）
FIXTURE = [
    # 承包商：窗口内 1115 + 窗口前 999（窗口前不计入）
    ("sess-contractor", "承包商：C7 映射测试", [usage_line(ms(2026, 11, 14), 1115),
                                                usage_line(ms(2026, 11, 13), 999)]),
    # 考官：窗口内 2000
    ("sess-examiner", "C7 考官：复核可发布", [usage_line(ms(2026, 11, 14, 11), 2000)]),
    # 主会话：无 descriptor，窗口内 3000
    ("sess-main", None, [usage_line(ms(2026, 11, 14, 12), 3000)]),
    # 遗留无职位词 label：窗口内 500 → 未知职位
    ("sess-legacy", "落盘合同制试点最小集", [usage_line(ms(2026, 11, 14, 13), 500)]),
]
FIXTURE_WINDOW_TOTAL = 1115 + 2000 + 3000 + 500  # 6615


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_roles_11(tmp):
    """--roles：11 规范角色齐全（含 6 个新角色），且与 write_scopes.json 同集。"""
    roles = roles_json()
    problems = []
    if list(roles.keys()) != CANONICAL:
        problems.append(f"角色名/顺序不符：{list(roles.keys())}")
    missing_new = [r for r in NEW_ROLES if r not in roles]
    if missing_new:
        problems.append(f"缺新角色：{missing_new}")
    for name, pats in roles.items():
        if not isinstance(pats, list) or not pats or not all(
                isinstance(p, str) and p.strip() for p in pats):
            problems.append(f"{name} 匹配词非法：{pats!r}")
    with open(SCOPES, encoding="utf-8") as f:
        scopes = json.load(f)["roles"]
    if set(roles) != set(scopes):
        problems.append(f"与 write_scopes 不同集：{sorted(set(roles) ^ set(scopes))}")
    return not problems, "；".join(problems) or f"11 角色齐全且与 write_scopes 同集（{len(roles)}）"


@case
def case_old_names(tmp):
    """旧名兼容映射：旧名出现在且仅出现在对应规范角色的匹配词里（历史会话归属不丢）。"""
    roles = roles_json()
    problems = []
    for old, new in OLD_TO_NEW.items():
        owners = [r for r, pats in roles.items() if old in pats]
        if owners != [new]:
            problems.append(f"{old}→{new} 实际 {owners}")
    # 旧名兼容后仍保留的别名（不丢历史归属）
    for alias, new in (("督导", "审计督导"), ("验证员", "考官"),
                       ("组织架构师", "组织规划")):
        if alias not in roles.get(new, []):
            problems.append(f"兼容别名 {alias} 未在 {new}")
    return not problems, "；".join(problems) or f"{len(OLD_TO_NEW)} 个旧名全部落到规范角色"


@case
def case_label_mapping(tmp):
    """真实历史 label → 规范角色（旧名 / 英文实例名 / 历史描述词）。"""
    labels = [
        "统筹主持：调度", "执行主管（steward）：调度、构建、推送、文档",
        "A 队执行主管：协调 F2、跑测试", "B 队审查员：按 AUDIT.md 做窗口审查",
        "B 队成本管理员：跑 token 统计", "第三方流程审查（中文名：督导），一次性",
        "builder：改 native-emu", "steward：写文档", "verifier：复核",
        "proxy：写合同", "contractor：执行合同", "supervisor：审计",
        "architect：组织设计", "advisor：参谋", "device：真机取证",
        "assistant：台账", "artisan：改代码", "examiner：复核",
        "role-planner：分工", "struct-planner：结构",
    ]
    want = [
        "代理人", "代理人", "代理人", "审计督导", "审计督导", "审计督导",
        "工匠", "助理", "考官", "代理人", "承包商", "审计督导",
        "组织规划", "策略顾问", "真机执行", "助理", "工匠", "考官",
        "分工规划员", "结构规划员",
    ]
    got = role_of(labels)
    problems = [f"{lab[:20]!r}: 期望 {w} 实际 {g}"
                for lab, w, g in zip(labels, want, got) if w != g]
    return not problems, "；".join(problems) or f"{len(labels)} 条 label 归因正确"


@case
def case_leftmost(tmp):
    """「取最靠左命中」不变：多职位词按出现位置优先，而非表序/角色序。"""
    labels = [
        "A 队工匠：F2 招式实现（先只读准备，等执行主管派活）",   # 工匠 在 执行主管 左
        "执行主管：等工匠交活",                                 # 执行主管 在 工匠 左
        "C5 考官：复核（docs/roles/a/examiner.md）",            # 考官 在 examiner 左
        "实现与修复 native-emu 代码（中文名：工匠，带 shell 权限）",
    ]
    want = ["工匠", "代理人", "考官", "工匠"]
    got = role_of(labels)
    problems = [f"{lab[:24]!r}: 期望 {w} 实际 {g}"
                for lab, w, g in zip(labels, want, got) if w != g]
    return not problems, "；".join(problems) or "取最靠左命中规则未变"


@case
def case_unknown_and_main(tmp):
    """有 descriptor 无职位词→未知职位；无 descriptor→主会话（未标注职位）。"""
    labels = ["落盘合同制试点最小集", "DSH 跨会话能力调研", None]
    got = role_of(labels)
    want = ["未知职位", "未知职位", "主会话（未标注职位）"]
    problems = [f"{lab!r}: 期望 {w} 实际 {g}"
                for lab, w, g in zip(labels, want, got) if w != g]
    return not problems, "；".join(problems) or "未知 label 不猜、主会话不猜"


@case
def case_fixture_totals_invariant(tmp):
    """同 fixture 映射前后 totals 相等：只改分组、不改总量（byRole 合计 = windowTotal）。"""
    spec = []
    for sid, label, lines in FIXTURE:
        records = ([descriptor_line(label)] if label is not None else []) + lines
        text = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
        spec.append({"sid": sid, "text": text})
    sh([NODE, "-e", WRITER, tmp, json.dumps(spec, ensure_ascii=False)])
    env = dict(os.environ)
    env["TOKEN_REPORT_SESSIONS_ROOT"] = tmp
    report = json.loads(sh([NODE, REPORT, "--json", "--since", "2026-11-14"], env=env))

    window = report["totals"]["totalTokens"]
    new_buckets = {r["role"]: r["totalTokens"] for r in report["roles"]}
    new_total = sum(new_buckets.values())
    # 「映射前后」：同一 fixture 用旧表（测试内副本）重新分组，总量必须相等
    old_buckets = {}
    for _sid, label, lines in FIXTURE:
        for ln in lines:
            if ln["time"] < ms(2026, 11, 14):
                continue
            old_buckets[old_role(label)] = old_buckets.get(old_role(label), 0) + \
                ln["data"]["usage"]["totalTokens"]
    old_total = sum(old_buckets.values())

    problems = []
    if window != FIXTURE_WINDOW_TOTAL:
        problems.append(f"windowTotal {window} != 期望 {FIXTURE_WINDOW_TOTAL}（--since 裁剪错）")
    if new_total != window:
        problems.append(f"byRole 合计 {new_total} != windowTotal {window}（分组丢了总量）")
    if old_total != new_total:
        problems.append(f"映射前后总量不等：旧 {old_total} / 新 {new_total}")
    want_new = {"承包商": 1115, "考官": 2000, "主会话（未标注职位）": 3000, "未知职位": 500}
    if new_buckets != want_new:
        problems.append(f"新分组不符：{new_buckets} != {want_new}")
    if old_buckets == new_buckets:
        problems.append("fixture 未体现分组变化（旧/新分组相同，测试无效）")
    if any(r["sessions"] < 1 for r in report["roles"]):
        problems.append("存在 0 会话角色")
    return not problems, "；".join(problems) or (
        f"fixture windowTotal={window}；旧分组 {old_total} / 新分组 {new_total}（相等）；"
        f"新 byRole={new_buckets}")


def main():
    failed = 0
    for fn in CASES:
        try:
            with tempfile.TemporaryDirectory(prefix="c7-roles-") as tmp:
                ok, out = fn(tmp)
        except Exception as e:  # noqa: BLE001
            ok, out = False, f"异常：{e}"
        print(f"{'PASS' if ok else 'FAIL'}  {fn.__name__}")
        if not ok:
            failed += 1
            print(out[-800:])
    if failed:
        print(f"\n失败 {failed}/{len(CASES)}")
        return 1
    print("\n全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
