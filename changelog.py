"""从 git log 生成 CHANGELOG 草稿（按 commit 前缀归类）。

用法：
  python3 changelog.py            # 全部历史
  python3 changelog.py <since>    # 只看 since..HEAD，如 v2026.11.09-1
"""
import collections
import subprocess
import sys

PREFIX = {
    "feat": "新增", "fix": "修复", "refactor": "变更",
    "docs": "文档", "test": "测试", "perf": "性能", "chore": "杂项",
}


def commits(since=None):
    cmd = ["git", "log", "--pretty=format:%h\x1f%s"]
    if since:
        cmd.append(f"{since}..HEAD")
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        if "\x1f" not in line:
            continue
        h, s = line.split("\x1f", 1)
        rows.append((h, s))
    return rows


def classify(subject):
    for p, cat in PREFIX.items():
        if subject.startswith(p + ":") or subject.startswith(p + "："):
            return cat, subject.split(":", 1)[-1].strip()
    return "其他（历史）", subject


def draft(since=None):
    groups = collections.OrderedDict()
    for h, s in commits(since):
        cat, text = classify(s)
        groups.setdefault(cat, []).append((h, text))
    out = ["## 草稿（未发布）", ""]
    for cat, items in groups.items():
        out.append(f"### {cat}")
        out.extend(f"- {t} ({h})" for h, t in items)
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(draft(sys.argv[1] if len(sys.argv) > 1 else None))
