#!/usr/bin/env python3
"""tools/contract_close.py 的离线测试（tempfile + 假 git 仓库，不读真实 .pilot、不写业务文件）。"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOSE = os.path.join(ROOT, "tools", "contract_close.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t",
       "-c", "commit.gpgsign=false"]

CONTRACT = """# C4 合同收尾测试

> 状态机：open → claimed → green → accepted

## 1–2 合同号 / 类型：C4 ｜ 功能型

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
- 允许：`tests/**`
- 不允许：`native-emu/**`

## 9 禁止项
- 无

## 10 变更规则
- 见合同

## 11 回执
- `.pilot/<id>/result.md`
"""

COST = {
    "contract": "C4", "windowTotal": 132_645_667, "baselinePerBatch": 23_520_803,
    "delta": 15_041_651, "batches": 1, "perBatch": 15_041_651, "threshold": 19_992_683,
}


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
    """最小假仓库：base 提交 + 一个范围内提交 + accepted 运行态 + cost.json。"""
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    run_git(repo, "init", "-q")
    contract = os.path.join(repo, "docs", "contracts", "C4-test.md")
    write(contract, CONTRACT)
    write(os.path.join(repo, "docs", "BATCHES.md"),
          "# 批次\n\n| 批 | 内容 |\n|---|---|\n| C4 | 合同:C4 收尾测试 |\n")
    base = commit_all(repo, "base")
    write(os.path.join(repo, "tests", "x.py"), "x = 1\n")
    commit = commit_all(repo, "in-scope")
    status = {
        "id": "C4",
        "state": "accepted",
        "base": base,
        "claimedAt": "2026-11-14 11:30 (Asia/Shanghai)",
        "session": "session-test",
        "attempts": 1,
        "commit": commit,
        "accepted": {"by": "A", "verdict": "accepted", "at": "2026-11-14 12:00"},
        "result": ".pilot/C4/result.md",
    }
    status_path = os.path.join(repo, ".pilot", "C4", "status.json")
    write(status_path, json.dumps(status, ensure_ascii=False, indent=2))
    write(os.path.join(repo, ".pilot", "C4", "result.md"), "session: t ｜ 状态: green\n行2\n行3\n")
    write(os.path.join(repo, ".pilot", "C4", "cost.json"),
          json.dumps(COST, ensure_ascii=False, indent=2))
    return repo, contract, status_path


def close(repo, cid="C4"):
    r = subprocess.run([sys.executable, CLOSE, cid, "--repo", repo],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def edit_json(path, mutate):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    mutate(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_pass(tmp):
    """accepted + contract_check 通过 + BATCHES 合同行 + cost 双判据 → exit 0，四段草稿齐全。"""
    repo, _, _ = make_repo(tmp)
    rc, out = close(repo)
    ok = (rc == 0 and "BATCHES 追记行草稿" in out and "HANDOFF 摘要行草稿" in out
          and "METRICS 重生成提示" in out and "双判据 ✓" in out and "检查全过" in out)
    return ok, out


@case
def case_not_accepted(tmp):
    """claimed 态（未 accepted）→ accepted 校验记 SKIP、exit 0，仍打印预览草稿（提交前预跑不阻断）。"""
    repo, _, status = make_repo(tmp)
    edit_json(status, lambda d: d.update(state="claimed"))
    rc, out = close(repo)
    ok = (rc == 0 and "SKIP status" in out and "未 accepted" in out
          and "BATCHES 追记行草稿" in out and "预览" in out and "检查全过" in out)
    return ok, out


@case
def case_contract_check_fail(tmp):
    """accepted 但 base..commit 改了范围外文件 → contract_check FAIL → exit 1。"""
    repo, _, status = make_repo(tmp)
    write(os.path.join(repo, "forbidden.txt"), "x\n")
    out_commit = commit_all(repo, "out-of-scope")
    edit_json(status, lambda d: d.update(commit=out_commit))
    rc, out = close(repo)
    return rc != 0 and "contract_check FAIL" in out and "写入范围" in out, out


@case
def case_cost_missing(tmp):
    """accepted 但 cost.json 未取 → 只提示（SKIP），不算 FAIL、exit 0。"""
    repo, _, _ = make_repo(tmp)
    os.remove(os.path.join(repo, ".pilot", "C4", "cost.json"))
    rc, out = close(repo)
    return rc == 0 and "SKIP cost" in out and "不算失败" in out, out


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
