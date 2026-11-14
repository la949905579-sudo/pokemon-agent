#!/usr/bin/env python3
"""tools/batch_facts.py / tools/batch_close.py 的离线测试（tempfile + 假 git 仓库，不写业务文件）。"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.join(ROOT, "tools", "batch_facts.py")
CLOSE = os.path.join(ROOT, "tools", "batch_close.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
PENDING_ROW = ("| 测试批 | 2026-11-14 | 测试内容 | docs=`abc`；tools=`def` | "
               "待复核（考官） | 提交前 ✅ 推送前 ⏳ | 授权留痕 |")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FACTS_MOD = load("batch_facts", FACTS)
CLOSE_MOD = load("batch_close", CLOSE)


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


def make_repo(tmp, batch_row=PENDING_ROW):
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    run_git(repo, "init", "-q")
    rows = ["# 批次台账", "", "| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |",
            "|---|---|---|---|---|---|---|"]
    if batch_row:
        rows.append(batch_row)
    write(os.path.join(repo, "docs", "BATCHES.md"), "\n".join(rows) + "\n")
    write(os.path.join(repo, "tools", "test_results.json"),
          json.dumps({"python": {"tests": 1, "result": "PASS"},
                      "kotlin": {"tests": 2, "result": "PASS"}}))
    write(os.path.join(repo, "tests", "test_demo.py"), "print('全部通过')\n")
    commit_all(repo, "base: 初始")
    return repo


def snapshot(repo):
    out = {}
    for dirpath, dirnames, filenames in os.walk(repo):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            p = os.path.join(dirpath, name)
            with open(p, "rb") as f:
                out[os.path.relpath(p, repo)] = f.read()
    return out


def run_script(script, cwd, *args):
    r = subprocess.run([sys.executable, script, *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_facts_fields(tmp):
    repo = make_repo(tmp)
    rc, out = run_script(FACTS, tmp, "--repo", repo)
    ok = (rc == 0 and "HEAD" in out and "base: 初始" in out
          and "工作树" in out and "干净" in out and "SKIP 无 origin/master" in out)
    return ok, out


@case
def case_facts_fail_continue(tmp):
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    run_git(repo, "init", "-q")
    write(os.path.join(repo, "x.txt"), "x\n")
    commit_all(repo, "only")
    rc, out = run_script(FACTS, tmp, "--repo", repo)
    return rc == 0 and "FAIL" in out and "BATCHES" in out, out


@case
def case_facts_not_repo(tmp):
    rc, out = run_script(FACTS, tmp, "--repo", tmp)
    return rc == 2 and "FAIL" in out, out


@case
def case_pure_last_batch_row(tmp):
    text = "\n".join(["| 批次 | 日期 | 内容 | 提交号 | 考官结论 | 门禁 | 备注 |",
                      "|---|---|---|---|---|---|---|", PENDING_ROW])
    row = FACTS_MOD.last_batch_row(text)
    empty = FACTS_MOD.last_batch_row("| 批次 | 日期 | 内容 |\n|---|---|---|\n")
    return (row is not None and len(row) == 7 and row[0] == "测试批" and empty is None), f"row={row}"


@case
def case_pure_parse_results(tmp):
    got = FACTS_MOD.parse_test_results({"python": {"tests": 31, "result": "PASS（31/31）"},
                                        "kotlin": {"tests": 115, "result": "PASS"}})
    miss = FACTS_MOD.parse_test_results(None)
    ok = (got["python"].startswith("31 例") and got["kotlin"].startswith("115 例")
          and miss["python"] == "无数据" and miss["kotlin"] == "无数据")
    return ok, f"{got} / {miss}"


@case
def case_close_dry_run_no_write(tmp):
    repo = make_repo(tmp)
    before = snapshot(repo)
    rc, out = run_script(CLOSE, repo, "--batch", "测试批", "--dry-run")
    after = snapshot(repo)
    ok = rc == 0 and before == after and "BATCHES 行草稿" in out and "检查全过" in out
    return ok, out + f"\nrc={rc} 变更文件={[k for k in after if before.get(k) != after[k]]}"


@case
def case_close_missing_batch_row(tmp):
    repo = make_repo(tmp, batch_row=None)
    rc, out = run_script(CLOSE, repo, "--batch", "测试批")
    return rc == 1 and "FAIL" in out and "BATCHES" in out, out


@case
def case_close_contract_not_accepted(tmp):
    repo = make_repo(tmp)
    write(os.path.join(repo, ".pilot", "C3", "status.json"),
          json.dumps({"contract": "C3", "state": "claimed", "base": "x"}))
    rc, out = run_script(CLOSE, repo, "--batch", "测试批", "--contract", "C3")
    return rc == 1 and "未 accepted" in out, out


@case
def case_close_contract_missing(tmp):
    repo = make_repo(tmp)
    rc, out = run_script(CLOSE, repo, "--batch", "测试批", "--contract", "C3")
    return rc == 1 and "status.json" in out, out


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
