# 原生双屏 GBA 模拟器 · 项目规划（NATIVE_EMU）

> 目标：把 mGBA 内核封装进自研 Android 程序，上屏游戏、下屏接自动化项目。
> 本文是 P0 任务清单 + 接口契约草案。代码将放在 `native-emu/` 子目录。

---

## 当前状态（2026-11-11）

P0 已跑通并在手机上实测：

- 双屏 1:1（上屏 240×160 游戏、下屏 Compose 控制台）
- ROM 加载（自动扫描 `/sdcard/rom/gba` 等）、存档/读档
- 触屏按键（多指、按住高亮）
- 60fps 限帧、RGB565→ARGB 正确渲染
- **TCP 桥 :55401**：`read` / `write` / `press` / `frame` / `status`
- 后台常驻（前台服务 + WakeLock + 电池无限制），后台帧持续推进
- 固定签名 + App 内 OTA（MENU → 更新，显示版本/构建时间/更新说明）

入口：`NATIVE_EMU_TODO.md`（待办）· `native-emu/`（工程）· `emu_bridge.py`（Python 客户端）

## 一、范围与边界

**做**：
- 原生 Android App（Kotlin + Compose + NDK）
- 内嵌 mGBA 内核（原始 C 库，非 libretro 外壳）
- 上屏 SurfaceView 渲染，下屏 Compose 面板
- JNI 暴露：内存读写、按键注入、帧步进、速度、即时存档
- localhost TCP 桥，供 proot 里的 Python 自动化使用

**不做（P0）**：
- 金手指/联机/录像/云存档
- 多机种（只做 GBA）
- 下屏完整自动化 UI（P1 才做）

---

## 二、技术选型

| 项 | 选择 | 理由 |
|---|---|---|
| 内核 | mGBA（libmgba，MPL 2.0） | C API 最全：`readMemory/writeMemory/setKeys/saveState/step` |
| 渲染 | SurfaceView + Bitmap（P0） | 简单；P1 再评估 GLES |
| 语言 | Kotlin + Compose | 下屏 UI 快 |
| 构建 | Gradle + CMake + NDK | mGBA 官方 CMake 支持 ANDROID |
| ABI | arm64-v8a（P0 单 ABI） | 手机主流，先减半工作量 |
| 音频 | P0 关闭 | 降低同步难度 |
| BIOS | 内置开源 BIOS（Normmatt，MIT）或用户自备 | 合法性与可用性 |

---

## 二半、决策记录（2026-11-11，已确认）

| 决策 | 结论 | 备注 |
|---|---|---|
| BIOS | **P0 不用 BIOS**（mGBA 里是 Optional，有内置兜底）；P1 加“设置里自备 BIOS” | 开源 BIOS 暂不内置 |
| ABI | **只做 arm64-v8a** | 不做 PC/x86_64 调试 |
| 音频 | **P0 关闭**，保留空回调接口；P1 再接 AAudio/Oboe | 先跑通画面 |

## 三、P0 任务清单（验收制）

> **历史计划，已全部完成**（2026-11-12 复核）。当前进度与待办以 `NATIVE_EMU_TODO.md` 为准；
> 本节保留当初的验收标准，方便回看。


### P0-1 编译链（2-3 天）
- [x] 拉 mGBA 源码（tag 稳定版），确认 `-DBUILD_...` 选项
- [x] NDK arm64 编译出 `libmgba.so`（先关 png/zlib/ffmpeg 等可选依赖）
- [x] 写 `CMakeLists.txt` 接入 Gradle `externalNativeBuild`
- [x] 验收：`nm -D libmgba.so` 能看到 `mCoreInit` 等符号；APK 装进手机不崩

### P0-2 最小 JNI（1-2 天）
- [x] JNI 层实现 `init/start/pause/stop/runFrame/setKeys`
- [x] 验收：logcat 打印帧号持续增长，CPU 占用正常

### P0-3 上屏渲染（2-3 天）
- [x] `runFrame` 后从 mGBA 取 240×160 帧缓冲（RGB565→ARGB8888）
- [x] 渲染线程 → Bitmap → SurfaceView（或 `lockCanvas`）
- [x] 验收：画面流畅（≥50fps），无撕裂/绿屏

### P0-4 触屏按键（1-2 天）
- [x] 虚拟 D-pad + A/B + Start/Select（Compose 覆盖层）
- [x] 触摸状态 → 按键位掩码 → `setKeys`
- [x] 验收：能玩到游戏标题、能移动

### P0-5 存档/加载（1 天，P2 前先用）
- [x] `saveState()/loadState()` 走 JNI
- [x] 验收：存档再读档，进度一致

### P0-6 冒烟（0.5 天）
- [x] 加载 ROM 玩 10 分钟不崩、不丢帧
- [x] 记录帧率/内存/电量基线

**合计约 8-12 天（单人）。**

---

## 四、接口契约草案

### 4.1 JNI（Kotlin `EmuCore` ←→ C）

```kotlin
object EmuCore {
    external fun init(romPath: String, biosPath: String): Boolean
    external fun start(): Boolean
    external fun pause()
    external fun resume()
    external fun stop()

    external fun runFrame(): Long          // 跑一帧，返回帧号
    external fun setSurface(surface: Surface)

    external fun setKeys(mask: Int)        // 见位掩码
    external fun readMemory(addr: Int, len: Int): ByteArray?
    external fun writeMemory(addr: Int, data: ByteArray): Boolean

    external fun saveState(): ByteArray?
    external fun loadState(data: ByteArray): Boolean
    external fun setSpeed(num: Int, den: Int)  // 1/1 正常；4/1 快进
    external fun frameCount(): Long
}
```

**按键位掩码**（与 GBA 一致）：
```
A=1<<0  B=1<<1  Select=1<<2  Start=1<<3
Right=1<<4  Left=1<<5  Up=1<<6  Down=1<<7
R=1<<8  L=1<<9
```

### 4.2 TCP 协议（Python ↔ App，默认端口 55401）

每行一个 JSON（NDJSON），请求-响应 + 事件推送。

**请求**
```json
{"id":1,"op":"read","addr":8426116,"len":100}
{"id":2,"op":"keys","mask":8,"frames":1}
{"id":3,"op":"step","frames":1}
{"id":4,"op":"speed","num":4,"den":1}
{"id":5,"op":"save"}
{"id":6,"op":"load","data":"<base64>"}
{"id":7,"op":"snapshot"}
```

**响应**
```json
{"id":1,"ok":true,"data":"<hex>"}
{"id":2,"ok":true}
{"id":3,"ok":true,"frame":123456}
{"id":5,"ok":true,"data":"<base64>"}
```

**事件推送**（可选，App → Python）
```json
{"ev":"frame","frame":123456}
{"ev":"scene","scene":"battle_main"}
```

**约定**
- `read` 的 `data` 用 hex（与现有 Python `memory.rd` 返回 bytes 对应）
- `keys` 的 `frames` 表示持续帧数（0=保持直到下次 keys）
- 单连接、串行请求（P0），P2 再加并发/订阅

### 4.3 下屏快照格式（App 内部 + 可推给 Python）

```json
{
  "frame": 123456,
  "scene": "battle_main",
  "battle": true,
  "coords": [8, 8],
  "tile": [1, 1],
  "party": [
    {"slot": 0, "species": 4, "lv": 10, "hp": 29, "mhp": 29, "status": 0}
  ],
  "enemy": {"species": 16, "lv": 5, "hp": 20, "mhp": 20},
  "speed": 1.0,
  "fps": 59.7
}
```

- 下屏 UI 只读快照 + 发 `keys/step/speed` 指令
- Python 优先直接 `read` 内存（兼容现有代码），快照只给 UI 用

---

## 四半、开发环境（本机已装好，2026-11-11）

| 组件 | 路径 / 版本 |
|---|---|
| JDK | `/usr/lib/jvm/java-17-openjdk-arm64`（17.0.21） |
| Android SDK | `/root/android-sdk`（platform 34 / build-tools 34.0.0 / platform-tools） |
| NDK | `/root/android-sdk/ndk/27.0.12077973` |
| Gradle | `/opt/gradle-8.9`（未生成 wrapper，命令用绝对路径） |
| mGBA 源码 | `native-emu/third_party/mgba`（已 clone，已 .gitignore） |

构建命令：
```bash
cd native-emu
export ANDROID_SDK_ROOT=/root/android-sdk ANDROID_HOME=/root/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
/opt/gradle-8.9/bin/gradle :app:assembleDebug --no-daemon
```

## 构建与发布（2026-11-11 实测流程）

**本地完整构建不可行**：手机是 arm64 + proot，NDK 的 clang/aapt2 是 x86_64（qemu 嵌套 exec 不可用）。
**用 GitHub Actions 构建**（x86_64 runner）：

```bash
# 1) 推送触发（paths: native-emu/**）
git push

# 2) 下载产物（需要 GITHUB_TOKEN）
curl -L -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/actions/artifacts/<id>/zip" -o apk.zip
unzip -o apk.zip -d /sdcard/Download/DSH-Go/

# 3) 发布到 Releases（App 内 OTA 的更新源）
GITHUB_TOKEN=xxx python3 publish_release.py build-<sha>
```

**OTA 链路**：`publish_release.py` → GitHub Releases（说明取 git 提交信息）
→ App 的「MENU → 更新」检查 `releases/latest` → 下载（带 UA + APK 头校验）→ 系统安装器。

> 签名固定在 `native-emu/app/keystore.jks`，口令存在同目录 `keystore-info.txt`（已被 gitignore）。
> 换签名会导致 `INSTALL_FAILED_UPDATE_INCOMPATIBLE`。

## TCP 桥协议（:55401，行协议）

| 命令 | 返回 | 说明 |
|---|---|---|
| `ping` | `pong` | 探活 |
| `read <addrHex> <len>` | `ok <hexBytes>` | 读内存（地址如 `202c000`） |
| `write <addrHex> <hex>` | `ok` | 写内存 |
| `press <mask> <ms>` | `ok` | 按键（A=1 B=2 SELECT=4 START=8 RIGHT=16 LEFT=32 UP=64 DOWN=128 R=256 L=512） |
| `frame` | `ok <n>` | 当前帧计数 |
| `status <json>` | `ok` | 外部推送下屏状态（map/x/y/team/battle） |

Python 客户端：`emu_bridge.py`（rd/wr/press/frame/ping）。

## 五、目录结构建议

```
native-emu/
├── app/                      # Android 模块
│   ├── src/main/java/.../    # Kotlin（EmuCore、UI）
│   ├── src/main/cpp/         # JNI 胶水
│   └── CMakeLists.txt
├── third_party/mgba/         # mGBA 源码（submodule 或拷贝）
├── tools/                    # 编译脚本、BIOS 准备
└── docs/PROJECT_PLAN.md      # 分层与契约
```

---

## 六、风险与对策

| 风险 | 对策 |
|---|---|
| NDK 编译 mGBA 依赖冲突 | 先只开 `-DBUILD_STATIC=OFF -DBUILD_QT=OFF`，逐步开依赖 |
| 音频同步爆炸 | P0 直接关音频 |
| 渲染绿屏/撕裂 | 先 Bitmap 同步渲染，P1 再 GLES |
| Python 桥延迟 | P0 串行请求；P2 加帧事件订阅 |
| BIOS 合法性 | 用 MIT 开源 BIOS 或强制用户自备 |
| 双屏内存占用 | 下屏 Compose 10Hz 刷新，上屏独立线程 |

---

## 七、下一步

1. 决定 P0 从哪个 mGBA tag 开始（建议最新稳定版）
2. 我先把 `native-emu/` 骨架（Gradle + CMake + 空 JNI）建起来
3. 跑通 P0-1 编译链，再逐项验收
