#!/usr/bin/env python3
"""tools/write_scopes.json 与 docs/TEAM.md §一 编制的离线一致性测试。

纯离线：只读仓库内两个文件（JSON / TEAM 文本），不联网、不读实机、不写任何业务文件
（需要落盘一律 tempfile，本文件无写动作）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = os.path.join(ROOT, "tools", "write_scopes.json")
TEAM = os.path.join(ROOT, "docs", "TEAM.md")

# C5 新编制：旧 4 角色已删除（write_scopes 内不得残留，TEAM 里标「停设」的历史行不回改）
LEGACY_ROLES = ("统筹主持", "独立督导", "审查员", "成本管理员")
LEGACY_ALIASES = ("lead", "audit-lead", "auditor", "audit-cost")

# 关键角色 → (首个 aliases, 期望 paths)；逐条对照 docs/TEAM.md §一 1.1/1.2
REQUIRED = {
    "代理人": (["proxy"], ["docs/contracts/**"]),
    "承包商": (["contractor"], []),
    "审计督导": (["supervisor"], []),
    "组织规划": (["architect"], [
        "docs/TEAM.md", "docs/roles/README.md", "docs/README.md",
        "docs/roles/a/**", "docs/roles/org/**", "docs/PROJECT_PLAN.md",
        "docs/WORKPLAN.md", "docs/STRUCTURE.md", "docs/org/**"]),
    "策略顾问": (["advisor"], []),
    "真机执行": (["device"], []),
    "助理": (["assistant"], [
        "tools/**", "docs/generated/**", "docs/HANDOFF.md", "docs/HANDOVER.md",
        "docs/BATCHES.md", "docs/NATIVE_EMU_TODO.md", "docs/history/CHANGELOG.md"]),
    "工匠": (["artisan"], ["native-emu/**", "tests/**"]),
    "考官": (["examiner"], []),
    "分工规划员": (["role-planner"], ["docs/org/**"]),
    "结构规划员": (["struct-planner"], ["docs/org/**"]),
}


def load_scopes():
    with open(SCOPES, encoding="utf-8") as f:
        return json.load(f)


def read_team():
    with open(TEAM, encoding="utf-8") as f:
        return f.read()


def team_section(team_text):
    """取 TEAM §一「编制」正文（到 §二 前），用于逐条对照。"""
    start = team_text.index("## 一、编制")
    end = team_text.index("## 二、")
    return team_text[start:end]


def paths_format_ok(paths):
    """paths 字段格式校验：list[str]，非空项、不含空格与花括号（合同 §8 禁 {a,b}），
    且形如精确路径 / 目录前缀（/ 结尾、/** 结尾）/* 通配。"""
    if not isinstance(paths, list):
        return False, "paths 不是 list"
    for p in paths:
        if not isinstance(p, str) or not p.strip() or p != p.strip():
            return False, "paths 含空项/非字符串/首尾空格：%r" % (p,)
        if any(c in p for c in " {}"):
            return False, "path 含空格或花括号（合同 §8 禁用 {a,b}）：%r" % p
        if p == "*":
            continue
        if not (p.endswith("/") or p.endswith("/**") or any(c in p for c in "*?[")):
            if "\\" in p or p.startswith("/"):
                return False, "path 不是相对路径/合法通配：%r" % p
    return True, "ok"


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_json_valid(tmp):
    """JSON 合法：可解析、顶层对象、roles 为对象且非空、source 指向 TEAM §一。"""
    data = load_scopes()
    ok = (isinstance(data, dict) and isinstance(data.get("roles"), dict)
          and len(data["roles"]) > 0 and "TEAM.md" in str(data.get("source", "")))
    return ok, f"roles={len(data.get('roles') or {})} source={data.get('source')}"


@case
def case_no_legacy_names(tmp):
    """无旧名：旧 4 角色键与旧英文实例名（lead/audit-lead/auditor/audit-cost）都不在表内。"""
    roles = load_scopes()["roles"]
    bad_keys = [r for r in LEGACY_ROLES if r in roles]
    bad_aliases = [a for r in roles.values() for a in r.get("aliases", [])
                   if a in LEGACY_ALIASES]
    return not bad_keys and not bad_aliases, f"bad_keys={bad_keys} bad_aliases={bad_aliases}"


@case
def case_required_roles_aliases_paths(tmp):
    """关键角色 + aliases + paths 齐；paths 字段格式合法；alias 全局唯一（成本归因）。"""
    roles = load_scopes()["roles"]
    problems = []
    for name, (aliases, paths) in REQUIRED.items():
        role = roles.get(name)
        if not isinstance(role, dict):
            problems.append("缺角色 %s" % name)
            continue
        if not isinstance(role.get("aliases"), list) or role["aliases"][:len(aliases)] != aliases:
            problems.append("%s aliases 不符：%r" % (name, role.get("aliases")))
        if role.get("paths") != paths:
            problems.append("%s paths 不符：%r" % (name, role.get("paths")))
        if not role.get("note"):
            problems.append("%s 缺 note" % name)
        ok, msg = paths_format_ok(role.get("paths"))
        if not ok:
            problems.append("%s %s" % (name, msg))
    all_aliases = [a for r in roles.values() for a in r.get("aliases", [])]
    dup = sorted({a for a in all_aliases if all_aliases.count(a) > 1})
    if dup:
        problems.append("alias 重复：%r" % dup)
    return not problems, "；".join(problems) or "11 角色逐条一致"


@case
def case_team_consistency(tmp):
    """与 docs/TEAM.md §一 逐条对照：每个角色名与首个 alias 都出现在 §一 编制表。"""
    section = team_section(read_team())
    roles = load_scopes()["roles"]
    missing = []
    for name, (aliases, _) in REQUIRED.items():
        if name not in section:
            missing.append("TEAM §一 缺角色名 %s" % name)
        if aliases and aliases[0] not in section:
            missing.append("TEAM §一 缺实例名 %s" % aliases[0])
    return not missing, "；".join(missing) or "TEAM §一 ↔ write_scopes 一致"


def main():
    failed = 0
    for fn in CASES:
        try:
            ok, out = fn(None)
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
