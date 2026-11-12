#!/usr/bin/env python3
"""扫描 Kotlin 里 mutableStateOf 的写点/读点是否配对（INC-006 的固化）。

背景：下屏提示文案 `statusText` 只写不读，整轮会话里用户看不到任何操作反馈，
因为没有任何测试或检查覆盖 UI 状态绑定。本脚本把这条固化成一个可跑的检查：
每个 `mutableStateOf` 声明的变量，只要存在写入点，就必须存在读取点。

支持两种写法：
    val statusText = mutableStateOf("")                    # 通过 .value 读写
    var tabPage by remember { mutableStateOf<Page?>(null) } # 直接读写

用法：
    python3 tools/check_ui_state.py            # 检查 native-emu/app/src/main/java
    python3 tools/check_ui_state.py --dir <源码目录>
    python3 tools/check_ui_state.py --self-test  # 用内置样例自测检查逻辑

退出码：0 = 没有“只写不读”的状态；1 = 有（需要修）；2 = 用法/环境错误。
抑制：在声明行（或上一行）加 `// ui-state-ok` 可跳过该变量（写清理由）。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(ROOT, "native-emu", "app", "src", "main", "java")

# 声明：val/var NAME [ : 类型 ] = mutableStateOf(  或  val/var NAME by [remember {] mutableStateOf(
RE_DIRECT = re.compile(
    r"\b(?:val|var)\s+(\w+)\s*(?::\s*[^=\n]+)?=\s*(?:remember\s*(?:\([^)]*\))?\s*\{\s*)?mutableStateOf\b"
)
RE_DELEGATE = re.compile(
    r"\b(?:val|var)\s+(\w+)\s+by\s+(?:remember\s*(?:\([^)]*\))?\s*\{\s*)?mutableStateOf\b"
)
ASSIGN_OPS = r"(?:=(?!=)|\+=|-=|\*=|/=|%=|\+\+|--)"
RE_READ_VALUE = re.compile(r"\.value(?!\s*" + ASSIGN_OPS + r")")
RE_WRITE_VALUE = re.compile(r"\.value\s*" + ASSIGN_OPS)


def strip_comments(src):
    """去掉 // 与 /* */ 注释，保留字符串内容与行号（换行保留）。"""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            # 跳过字符串（含转义），原样保留
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
        elif c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            if j == -1:
                break
            out.append("\n" * src.count("\n", i, j + 2))
            i = j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def scan_text(text):
    """返回 [(变量名, 风格, 读次数, 写次数, 行号)]。"""
    clean = strip_comments(text)
    lines = clean.splitlines()
    decls = []  # (name, style, line_no)
    for i, line in enumerate(lines, 1):
        for m in RE_DIRECT.finditer(line):
            decls.append((m.group(1), "direct", i))
        for m in RE_DELEGATE.finditer(line):
            decls.append((m.group(1), "delegate", i))
    result = []
    seen = set()
    for name, style, line_no in decls:
        key = (name, line_no)
        if key in seen:
            continue
        seen.add(key)
        # 抑制标记
        ctx = lines[line_no - 1] + (lines[line_no - 2] if line_no >= 2 else "")
        if "ui-state-ok" in ctx:
            continue
        reads = writes = 0
        pat = re.compile(r"\b" + re.escape(name) + r"\b")
        for m in pat.finditer(clean):
            # 跳过声明本身
            if clean.count("\n", 0, m.start()) + 1 == line_no:
                continue
            tail = clean[m.end():m.end() + 12]
            if style == "direct":
                if tail.lstrip().startswith(".value") or m.group(0) == name and tail.lstrip().startswith(".value"):
                    seg = clean[m.end():m.end() + 16]
                    if re.match(r"\.value\s*" + ASSIGN_OPS, seg):
                        writes += 1
                    else:
                        reads += 1
                else:
                    # 把 State 对象本身传出去，也算读取（下游会 .value）
                    reads += 1
            else:
                seg = clean[m.start():m.start() + len(name) + 4]
                if re.match(re.escape(name) + r"\s*" + ASSIGN_OPS, seg) or \
                        re.match(re.escape(name) + r"\s*\+\+", seg) or \
                        re.match(re.escape(name) + r"\s*--", seg):
                    writes += 1
                else:
                    reads += 1
        result.append((name, style, reads, writes, line_no))
    return result


def check_file(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    return scan_text(text)


def report(files):
    errors, warns, total = [], [], 0
    for path, rows in files:
        rel = os.path.relpath(path, ROOT)
        for name, style, reads, writes, line in rows:
            total += 1
            if writes > 0 and reads == 0:
                errors.append((rel, line, name, style, reads, writes))
            elif reads == 0 and writes == 0:
                warns.append((rel, line, name, style, "未使用（无读无写）", ""))
            elif writes == 0:
                warns.append((rel, line, name, style, f"只读：读 {reads} 次、没有写入点", ""))
    print(f"扫描 {len(files)} 个 Kotlin 文件，发现 {total} 个 mutableStateOf 状态。")
    print()
    if errors:
        print("未配对（只写不读，用户看不到变化 —— INC-006 类）：")
        for rel, line, name, style, reads, writes in errors:
            print(f"  ✗ {rel}:{line}  {name}（{style}）：读 {reads} / 写 {writes}")
        print()
    if warns:
        print("提示（不是错误，确认是否有意为之）：")
        for rel, line, name, style, msg, _ in warns:
            print(f"  ! {rel}:{line}  {name}（{style}）：{msg}")
        print()
    if not errors and not warns:
        print("所有 mutableStateOf 的读写点都配对。")
    if errors:
        print(f"结论：{len(errors)} 个状态只写不读，需要补读取点或删除。")
        return 1
    print("结论：通过。")
    return 0


def self_test():
    cases = [
        # 只写不读 → 应该报错
        ('val statusText = mutableStateOf("")\nfun f() { statusText.value = "x" }\n', "direct", 0, 1),
        # 有读有写 → 通过
        ('val statusText = mutableStateOf("")\nfun f() { statusText.value = "x"; println(statusText.value) }\n', "direct", 1, 1),
        # 委托写法：只写不读
        ('var page by remember { mutableStateOf(0) }\nfun f() { page = 1 }\n', "delegate", 0, 1),
        # 委托写法：有读有写
        ('var page by remember { mutableStateOf(0) }\nfun f() { page = 1; println(page) }\n', "delegate", 1, 1),
        # 注释里的名字不算读
        ('val s = mutableStateOf("")\n// s 注释\nfun f() { s.value = "x" }\n', "direct", 0, 1),
        # 抑制标记
        ('val s = mutableStateOf("") // ui-state-ok 给外部渲染\nfun f() { s.value = "x" }\n', None, 0, 0),
    ]
    bad = 0
    for i, (src, style, exp_reads, exp_writes) in enumerate(cases, 1):
        rows = [r for r in scan_text(src)]
        if style is None:
            ok = not rows
            got = "被抑制" if ok else rows
        else:
            ok = len(rows) == 1 and rows[0][2] == exp_reads and rows[0][3] == exp_writes
            got = rows
        print(f"{'PASS' if ok else 'FAIL'}  用例{i}：期望 读{exp_reads}/写{exp_writes}，实际 {got}")
        bad += 0 if ok else 1
    print(f"\n自测 {len(cases) - bad}/{len(cases)} 通过")
    return 0 if bad == 0 else 1


def main():
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test()
    src_dir = DEFAULT_DIR
    if "--dir" in args:
        src_dir = args[args.index("--dir") + 1]
    if not os.path.isdir(src_dir):
        print(f"目录不存在：{src_dir}", file=sys.stderr)
        return 2
    files = []
    for base, _, names in os.walk(src_dir):
        for n in sorted(names):
            if n.endswith(".kt"):
                p = os.path.join(base, n)
                files.append((p, check_file(p)))
    return report(files)


if __name__ == "__main__":
    sys.exit(main())
