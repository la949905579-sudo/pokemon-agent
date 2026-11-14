#!/usr/bin/env python3
"""tools/contract_check.py 的离线测试（tempfile + 假 git 仓库，不写业务文件）。"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(ROOT, "tools", "contract_check.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t",
       "-c", "commit.gpgsign=false"]

CONTRACT = """# C1 测试合同

> 状态机：open → claimed → green → accepted

## 1–2 合同号 / 类型：C1 ｜ 机械型

## 3 事实快照
- HEAD：`x`

## 4 基线提交
- 见 status.base

## 5 背景与目标
- 目标

## 6 任务清单（WBS）
- ① 做

## 7 验收
- M1 命令

## 8 写入范围
- 允许：`tests/**`、`bdata.py`
- 不允许：`native-emu/**`

## 9 禁止项
- 无

## 10 变更规则
- 见合同

## 11 回执
- `.pilot/<id>/result.md`
"""


def run_git(repo, *args):
    r = subprocess.run(GIT + ["-C", repo, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {args} 失败：{r.stderr}")
    return r.stdout.strip()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def commit_all(repo, msg):
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", msg)
    return run_git(repo, "rev-parse", "HEAD")


def make_repo(tmp):
    """建一个最小的假仓库：base 提交 + 一个范围内提交。"""
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    run_git(repo, "init", "-q")
    contract = os.path.join(repo, "docs", "contracts", "C1-test.md")
    write(contract, CONTRACT)
    write(os.path.join(repo, "docs", "BATCHES.md"),
          "# 批次\n\n| 批 | 内容 |\n|---|---|\n| C1 | 合同:C1 试点 |\n")
    base = commit_all(repo, "base")
    write(os.path.join(repo, "tests", "x.py"), "x = 1\n")
    commit = commit_all(repo, "in-scope")
    status = {
        "contract": "C1",
        "state": "accepted",
        "base": base,
        "claimedAt": "2026-11-14 00:00 (Asia/Shanghai)",
        "session": "session-test",
        "commit": commit,
        "accepted": {"by": "A", "verdict": "accepted", "at": "2026-11-14 01:00", "spotCheck": "M1"},
        "result": ".pilot/C1/result.md",
    }
    status_path = os.path.join(repo, ".pilot", "C1", "status.json")
    write(status_path, json.dumps(status, ensure_ascii=False, indent=2))
    write(os.path.join(repo, ".pilot", "C1", "result.md"), "session: t ｜ 状态: green\n行2\n行3\n")
    return repo, contract, status_path, base, commit


def check(repo, contract, status):
    r = subprocess.run([sys.executable, CHECKER, "--contract", contract,
                        "--status", status, "--repo", repo],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def edit_json(path, mutate):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    mutate(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def to_claimed(d):
    """accepted → claimed（去掉 accepted 记录与 commit，保留 base/claimedAt/session）。"""
    d["state"] = "claimed"
    d.pop("accepted", None)
    d.pop("commit", None)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_pass(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    rc, out = check(repo, contract, status)
    return rc == 0, out


@case
def case_attempts_invalid(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, lambda d: d.update(attempts=0))
    rc, out = check(repo, contract, status)
    return rc != 0 and "attempts" in out, out


@case
def case_cost_missing_fields(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    write(os.path.join(repo, ".pilot", "C1", "cost.json"),
          json.dumps({"perBatch": 1000000}, ensure_ascii=False))
    rc, out = check(repo, contract, status)
    return rc != 0 and "cost.json" in out and "windowTotal" in out, out


@case
def case_missing_field(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, lambda d: d.pop("session"))
    rc, out = check(repo, contract, status)
    return rc != 0 and "session" in out, out


@case
def case_contract_too_long(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    with open(contract, "a", encoding="utf-8") as f:
        f.write("\n".join(f"- 填充 {i}" for i in range(30)) + "\n")
    rc, out = check(repo, contract, status)
    return rc != 0 and "上限" in out, out


@case
def case_accepted_missing(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, lambda d: (d.pop("accepted"), d.pop("commit")))
    rc, out = check(repo, contract, status)
    return rc != 0 and "accepted" in out and "commit" in out, out


@case
def case_accepted_missing_by_verdict(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, lambda d: d.update(accepted={"at": "2026-11-14"}))
    rc, out = check(repo, contract, status)
    return rc != 0 and "缺 by" in out and "缺 verdict" in out, out


@case
def case_out_of_scope(tmp):
    repo, contract, status, base, _ = make_repo(tmp)
    write(os.path.join(repo, "forbidden.txt"), "x\n")
    out_commit = commit_all(repo, "out-of-scope")
    edit_json(status, lambda d: d.update(commit=out_commit))
    rc, out = check(repo, contract, status)
    return rc != 0 and "写入范围" in out, out


@case
def case_result_too_long(tmp):
    repo, contract, status, _, _ = make_repo(tmp)
    write(os.path.join(repo, ".pilot", "C1", "result.md"),
          "\n".join(f"行 {i}" for i in range(11)) + "\n")
    rc, out = check(repo, contract, status)
    return rc != 0 and "result" in out, out


@case
def case_claimed_missing_cost_before(tmp):
    """claimed 缺 .pilot/<id>/cost-before.json → 只警告（C4 批），exit 0，提示 C5 起阻断。"""
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, to_claimed)
    rc, out = check(repo, contract, status)
    return rc == 0 and "cost-before" in out and "C5 起阻断" in out, out


@case
def case_claimed_with_cost_before(tmp):
    """claimed 已有开工前基线 → 无 cost-before 警告，仍 exit 0。"""
    repo, contract, status, _, _ = make_repo(tmp)
    edit_json(status, to_claimed)
    write(os.path.join(repo, ".pilot", "C1", "cost-before.json"),
          json.dumps({"windowTotal": 100, "batches": 1, "baselinePerBatch": 100, "threshold": 85}))
    rc, out = check(repo, contract, status)
    return rc == 0 and "cost-before" not in out, out


def main():
    failed = 0
    for fn in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            try:
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
