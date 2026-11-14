#!/usr/bin/env python3
"""tools/metrics.py 的离线测试（C9）：CI 数据源固定标签 + live / cache 两分支。

纯离线：不联网（`get_json` 用假函数替换）、不读实机、不写业务文件；缓存一律写 tempdir。
覆盖：`data_source_label()` 映射（live / cache(<fetchedAt>) / offline / 未知）+
`fetch_runs()` live 分支（写临时缓存）+ cache 分支（读临时假缓存，限流兜底）。
"""
import importlib.util
import json
import os
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "tools", "metrics.py")


def load():
    spec = importlib.util.spec_from_file_location("metrics_mod", METRICS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def case_label_mapping(tmp):
    """数据源标签纯函数：live / cache(<fetchedAt>) / offline / 未知 四分支。"""
    m = load()
    got = {
        "live": m.data_source_label("live"),
        "cache": m.data_source_label("cache(2026-11-14 14:11)"),
        "offline": m.data_source_label(None, offline=True),
        "none": m.data_source_label(None),
    }
    ok = (got["live"] == "live"
          and got["cache"] == "cache(2026-11-14 14:11)"
          and "offline" in got["offline"] and "未知" in got["none"])
    return ok, f"got={got}"


@case
def case_fetch_live(tmp):
    """live 分支：get_json 返回假运行记录 → source=live，并写临时缓存（不联网）。"""
    m = load()
    cache = os.path.join(tmp, "cache.json")
    m.CACHE = cache
    m.get_json = lambda url: {"workflow_runs": [{"id": 1}], "total_count": 1}
    runs, source = m.fetch_runs()
    ok = (source == "live" and runs == [{"id": 1}] and os.path.isfile(cache)
          and json.load(open(cache, encoding="utf-8")).get("runs") == [{"id": 1}])
    return ok, f"source={source} runs={runs} cache_exists={os.path.isfile(cache)}"


@case
def case_fetch_cache(tmp):
    """cache 分支：get_json 抛 URLError（限流/断网）→ 读临时假缓存，source=cache(<fetchedAt>)。"""
    m = load()
    cache = os.path.join(tmp, "cache.json")
    with open(cache, "w", encoding="utf-8") as f:
        json.dump({"fetchedAt": "2026-11-14 14:11", "runs": [{"id": 7}]}, f)
    m.CACHE = cache

    def boom(url):
        raise urllib.error.URLError("blocked in offline test")

    m.get_json = boom
    runs, source = m.fetch_runs()
    ok = source == "cache(2026-11-14 14:11)" and runs == [{"id": 7}]
    return ok, f"source={source} runs={runs}"


@case
def case_fetch_no_cache(tmp):
    """无缓存兜底：get_json 失败且无缓存文件 → (None, None)，不抛异常。"""
    m = load()
    m.CACHE = os.path.join(tmp, "missing.json")

    def boom(url):
        raise TimeoutError("offline")

    m.get_json = boom
    runs, source = m.fetch_runs()
    return runs is None and source is None, f"runs={runs} source={source}"


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
