#!/usr/bin/env python3
"""生成 docs/FILES.md：仓库里每个被跟踪文件的用途索引。

目的：交接时任何一个文件都能在文档里查到「它是干什么的、属于哪一层、要不要留」。

用法：
    python3 tools/gen_files_index.py           # 重新生成 docs/FILES.md
    python3 tools/gen_files_index.py --check   # 只检查，有未描述的文件就退出码 1
"""
import ast
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 需要人工说明的文件（自动提取不出来或容易误导）
OVERRIDES = {
    "action.py": ("平台", "只负责按方向键/确认键的执行层，不含决策"),
    "addresses.py": ("平台", "火红内存地址表（唯一真源，别在别处硬编码地址）"),
    "ai_agent.py": ("平台", "外部 AI 接入口（实验）"),
    "api_server.py": ("平台", "HTTP 指令接口：/api/intent 等"),
    "battle_loop.py": ("平台", "战斗主循环：读状态→决策→按键→回写日志"),
    "bdata.py": ("平台", "战斗数据解码（双方精灵、招式、血量）"),
    "bridge.py": ("平台", "注册制中间层（未接入主链路）"),
    "handlers.py": ("平台", "注册制中间层（未接入主链路）"),
    "emu_bridge.py": ("平台", "NativeEmu TCP 桥客户端（rd/wr/press/frame）"),
    "INCIDENTS.md": ("文档", "事故复盘库（现象/根因/固化改动）"),
    "publish_release.py": ("构建", "把 CI 产物发布到 GitHub Release（OTA 更新源）"),
    "push_status.py": ("平台", "把状态推给模拟器下屏（:55401 status 命令）"),
    "run_game.py": ("平台", "插件化入口：EMU_BACKEND=native python3 run_game.py <game_id>"),
    "run_tests.py": ("测试", "一键跑全部离线测试（按 test_*.py 文件计数）"),
    "start_push.sh": ("平台", "后台常驻的状态推送脚本（setsid，支持 stop）"),
    "memory.py": ("平台", "内存读写的统一入口（按 EMU_BACKEND 分派 RetroArch / NativeEmu）"),
    "ra.py": ("平台", "RetroArch UDP 通道（读内存 :55355、按键 :55400）"),
    "keystore.jks": ("构建", "固定签名私钥库（⚠ 已在公开仓库暴露，见 HANDOFF 安全债）"),
    "BattlePage.kt": ("界面", "战斗页：双方血条 + 招式列表"),
    "Tabs.kt": ("界面", "右侧竖排 Tab 与 Page 枚举"),
    "Theme.kt": ("界面", "下屏配色常量"),
    "MainActivity.kt": ("界面", "Compose 主界面：双屏、Tab、按键页、小地图（已超 500 行，待拆）"),
    "BridgeServer.kt": ("桥", "TCP :55401 服务端（read/write/press/frame/status）"),
    "EmuCore.kt": ("内核", "JNI 声明与按键位掩码"),
    "EmuService.kt": ("内核", "前台服务 + WakeLock 保活"),
    "Updater.kt": ("桥", "GitHub Releases OTA：检查、下载、校验、拉起安装器"),
    "UiState.kt": ("界面", "下屏状态模型（Python 推送的 JSON 落到这里）"),
    "GameState.kt": ("游戏", "读内存解码场景/坐标/队伍/敌方信息（Kotlin 版）"),
    "BattleDecider.kt": ("游戏", "战斗决策（选招/换人评分）"),
    "SwitchDecider.kt": ("游戏", "换人决策"),
    "MapWalker.kt": ("游戏", "同图 BFS 寻路，输出方向序列"),
    "PartyCrypto.kt": ("游戏", "队伍数据解密（PortablePokemon）"),
    "Species.kt": ("游戏", "关东 1-151 中文名表"),
    "Memo.kt": ("游戏", "内存读取的小封装（u8/u16/块读）"),
    "GameData.kt": ("游戏", "静态数据：属性表、招式表"),
    "Addresses.kt": ("游戏", "Kotlin 侧地址表（对应 addresses.py）"),
    "emu_core.cpp": ("内核", "mGBA 生命周期：init/runFrame/save/load/内存"),
    "emu_jni.cpp": ("内核", "JNI 胶水 + RGB565→ARGB 像素转换"),
    ".gitignore": ("构建", "忽略规则：缓存、构建产物、运行日志"),
    "games/_template/__init__.py": ("插件", "新游戏插件模板包"),
    "games/pokemon_firered/__init__.py": ("插件", "火红插件包入口"),
    "native-emu/.gitignore": ("构建", "忽略 third_party 与构建产物"),
    "native-emu/app/build.gradle.kts": ("构建", "Android 模块构建：固定签名 + BuildConfig(GIT_SHA/BUILD_TIME)"),
    "native-emu/app/src/main/AndroidManifest.xml": ("构建", "权限（存储/前台服务/安装包）与组件声明"),
    "native-emu/app/src/main/cpp/CMakeLists.txt": ("构建", "mGBA 子目录 + 编译宏（必须与 libmgba 完全一致）"),
    "native-emu/app/src/main/cpp/emu_core.h": ("内核", "内核 C 接口声明（emu_core.cpp 的头文件）"),
    "native-emu/app/src/main/res/xml/file_paths.xml": ("构建", "FileProvider 路径（OTA 安装 APK 用）"),
    "native-emu/build.gradle.kts": ("构建", "Gradle 根构建脚本"),
    "native-emu/gradle.properties": ("构建", "Gradle 参数（JVM 内存等）"),
    "native-emu/settings.gradle.kts": ("构建", "模块声明（:app）"),
    "native-emu/tools/aapt2-wrapper": ("构建", "aapt2 包装脚本（arm64 主机上的 x86_64 工具链绕行）"),
    "native-emu/tools/aapt2_wrapper.c": ("构建", "aapt2 包装器源码"),
    "native-emu/tools/build.sh": ("构建", "本地构建脚本（本机必然失败，仅作记录）"),
    "native-emu/tools/cmake_wrapper.c": ("构建", "CMake 包装器源码"),
    "native-emu/tools/setup-sdk.sh": ("构建", "安装 Android SDK / NDK / Gradle"),
    "web/index.html": ("其他", "网页入口（状态面板，用途待确认）"),
}

# 这些目录/后缀按类别说明，不逐个展开
SKIP_PREFIX = ("native-emu/third_party/",)
LOG_RE = re.compile(r"\.(log)$")
DEBUG_RESIDUE = set()


def git_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f and not f.startswith(SKIP_PREFIX)]


def py_doc(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
        doc = ast.get_docstring(tree) or ""
        return doc.strip().splitlines()[0].strip() if doc.strip() else ""
    except Exception:
        return ""


def kt_doc(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r"/\*\*(.*?)\*/", txt, re.S)
    if m:
        line = [l.strip(" *") for l in m.group(1).splitlines() if l.strip(" *")]
        if line:
            return line[0]
    m = re.search(r"^(?:class|object|fun)\s+\w+", txt, re.M)
    return m.group(0) if m else ""


def md_title(path):
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def describe(f):
    name = os.path.basename(f)
    if f in OVERRIDES:
        return OVERRIDES[f]
    if name in OVERRIDES:
        return OVERRIDES[name]
    ext = os.path.splitext(f)[1]
    p = os.path.join(ROOT, f)
    if ext == ".py":
        if name.startswith("test_"):
            return ("测试", f"离线测试：{name[5:-3]}")
        d = py_doc(p)
        return ("平台", d or "")
    if ext == ".mjs":
        txt = open(p, encoding="utf-8", errors="ignore").read()
        m = re.search(r"/\*\*(.*?)\*/", txt, re.S)
        if m:
            line = [l.strip(" *") for l in m.group(1).splitlines() if l.strip(" *")]
            if line:
                return ("工具", line[0])
        return ("工具", "")
    if ext == ".kt":
        return ("界面" if "res/" in f else "游戏", kt_doc(p))
    if ext == ".md":
        return ("文档", md_title(p))
    if ext in (".json", ".bin"):
        return ("数据", "数据/样例文件")
    if ext in (".yml", ".yaml"):
        return ("构建", "CI / 工具配置")
    if ext in (".sh", ".c", ".kts", ".xml", ".properties", ".jks"):
        return ("构建", "")
    if LOG_RE.search(f) or name in DEBUG_RESIDUE:
        return ("残留", "调试日志/转储，建议清理")
    return ("其他", "")


def layer_of(f):
    if f.startswith("docs/"):
        return "文档"
    if f.startswith(".github/"):
        return "构建"
    if f.startswith("native-emu/app/src/main/cpp/"):
        return "内核"
    if f.startswith("native-emu/app/src/main/java"):
        if "/game/" in f:
            return "游戏"
        base = os.path.basename(f)
        if base in ("BridgeServer.kt", "Updater.kt"):
            return "桥"
        if base == "MainActivity.kt":
            return "界面"
        return "内核"
    if f.startswith("native-emu/app/src/test"):
        return "测试"
    if f.startswith("native-emu/"):
        return "构建"
    if f.startswith("framework/") or f.startswith("games/"):
        return "插件"
    if f.startswith("maps/") or f.startswith("battles/") or f.startswith("dialogs/"):
        return "数据"
    if f.startswith("tools/"):
        return "工具"
    if f.startswith("test_"):
        return "测试"
    if f.endswith(".py"):
        return "平台"
    return "其他"


def main():
    check = "--check" in sys.argv
    files = git_files()
    rows, missing = [], []
    for f in files:
        if f == "docs/FILES.md":
            continue
        layer, desc = describe(f)
        if not desc:
            missing.append(f)
            desc = "⚠ 未描述"
        status = "待清理" if (f in DEBUG_RESIDUE or LOG_RE.search(f)) else "保留"
        rows.append((layer, f, desc, status))

    rows.sort(key=lambda r: (r[0], r[1]))
    lines = ["# 文件索引", "",
             "> 由 `tools/gen_files_index.py` 生成，**不要手改**。新增/删除文件后重跑：",
             "> `python3 tools/gen_files_index.py`；CI 或交接前用 `--check` 确认没有未描述的文件。", ""]
    cur = None
    for layer, f, desc, status in rows:
        if layer != cur:
            cur = layer
            lines += ["", f"## {layer}", "", "| 文件 | 用途 | 状态 |", "|---|---|---|"]
        lines.append(f"| `{f}` | {desc} | {status} |")
    lines += ["", f"> 共 {len(rows)} 个文件（不含 `native-emu/third_party/` 第三方源码）。", ""]

    if missing:
        print("未描述的文件（请补 docstring 或加进 OVERRIDES）：")
        for m in missing:
            print("  -", m)

    if check:
        return 1 if missing else 0

    open(os.path.join(ROOT, "docs/FILES.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"已写入 docs/FILES.md（{len(rows)} 个文件，{len(missing)} 个未描述）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
