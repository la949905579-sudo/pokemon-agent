"""查询统一日志 logs/run-*.jsonl。

示例：
  python3 logq.py --mod switch
  python3 logq.py --event 换人 --limit 20
  python3 logq.py --grep got=2 --json
"""
import argparse
import glob
import json
import os
import sys

LOG_DIR = "/root/workspace/logs"


def load(day=None, directory=None):
    d = directory or LOG_DIR
    pattern = f"run-{day}.jsonl" if day else "run-*.jsonl"
    for fn in sorted(glob.glob(os.path.join(d, pattern))):
        with open(fn, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def match(rec, args):
    if args.mod and rec.get("mod") != args.mod:
        return False
    if args.event and args.event not in (rec.get("event") or ""):
        return False
    if args.level and rec.get("level") != args.level:
        return False
    if args.since and (rec.get("ts") or "") < args.since:
        return False
    if args.grep:
        blob = json.dumps(rec, ensure_ascii=False)
        if args.grep not in blob:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod")
    ap.add_argument("--event")
    ap.add_argument("--level")
    ap.add_argument("--since", help="ISO 前缀，如 2026-11-10T04")
    ap.add_argument("--grep")
    ap.add_argument("--day")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    rows = [r for r in load(args.day) if match(r, args)]
    rows = rows[-args.limit:]
    for r in rows:
        if args.as_json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            data = " ".join(f"{k}={v}" for k, v in (r.get("data") or {}).items())
            print(f"{r.get('ts')} {r.get('mod'):<10} {r.get('event'):<16} {data}")
    print(f"--- {len(rows)} 条", file=sys.stderr)


if __name__ == "__main__":
    main()
