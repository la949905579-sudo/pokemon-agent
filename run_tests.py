#!/usr/bin/env python3
"""一键跑全部离线测试。

用法：
    python3 run_tests.py            # 全部
    python3 run_tests.py battle     # 只跑名字含 battle 的
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(glob.glob(f"{ROOT}/tests/test_*.py"))
    if pat:
        files = [f for f in files if pat in f]
    if not files:
        print("没有匹配的测试")
        return 1

    # 测试文件在 tests/ 下；模块已收编到 pyplatform/：
    # 子进程 cwd 固定在 ROOT，把 ROOT/pyplatform 与 ROOT 放进 PYTHONPATH，保证 import 可用。
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "pyplatform") + os.pathsep + ROOT + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    failed = []
    for f in files:
        name = f.rsplit("/", 1)[-1]
        try:
            r = subprocess.run([sys.executable, f], capture_output=True,
                               text=True, timeout=120, cwd=ROOT, env=env)
            ok = r.returncode == 0 and "全部通过" in r.stdout
        except subprocess.TimeoutExpired:
            ok, r = False, None
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed.append((name, r))

    print(f"\n{len(files) - len(failed)}/{len(files)} 通过")
    if failed:
        for name, r in failed:
            print(f"\n--- {name} ---")
            if r:
                print((r.stdout or "")[-800:])
                print((r.stderr or "")[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
