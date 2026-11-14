# ARCH（架构与选型）

## 组成
- **Android App `native-emu/`**：Kotlin + Jetpack Compose；mGBA 核心（C/C++，`app/src/main/cpp` + `third_party/mgba`）经 JNI 调用。
- **应用内逻辑 `app/src/main/java/com/dsh/emu/`**：`EmuCore`（FFI / 帧循环 / 按键注入）、`BridgeServer`（TCP 桥，供旧 Python 层）、`UiState` / `Updater`（OTA）、`ui/`（下屏各页、`EmuView` 渲染、按键/地图/战斗页）、`game/`（Kotlin 决策层：`Addresses` / `GameState` / `BattleDecider` / `SwitchDecider` / `MapWalker` / `MapLinks` / `CrossMapPathfinder` / `MoveCaster` 等）。
- **资源**：`assets/`（13 张地图、`map_links.json`、招式/宝可梦名表）；地图数据源在 `maps/`（仓库根，旧 Python 侧）。
- **Python 旧层（冻结）**：根目录 `.py`（`info/bridge/decision_*/action/nav/pathfind/...`）+ `tests/` 离线测试 + `tools/emu_probe.py`。**不新增功能**；新逻辑一律进 Kotlin。
- **CI / 发布**：`.github/workflows/build-native-emu.yml`（push `native-emu/**` → 单测 + assembleDebug → master 上发 `build-<sha>` Release → App OTA）。

## 语言政策
- **Kotlin**：App UI、应用内自动化、点击映射、测试（JUnit）——新功能唯一语言。
- **C/C++**：仅 mGBA 核心与既有 JNI；不新写业务逻辑。
- **Python**：冻结；只允许离线一次性脚本（数据生成）与旧层维护。
- **不引入** Rust / 新语言 / CV-OCR 重方案；交互用固定热区表 + 状态回读。

## 关键约定
- 内存地址只在 `game/Addresses.kt`（Kotlin 侧）与 `addresses.py`（旧）维护，**实测过才加**；位标志只用验证过的位。
- 点击/自动操作一律 **fail-closed**：前置状态不满足不按键、不重试。
- 真机验证优先（装 APK → 截图/状态取证），单测覆盖纯函数（坐标映射、路径、解码）。
- 危险区（FFI / 地址 / 签名 / OTA / 删除 / 迁移）改动需 1 次 fresh 复核。

## 构建环境（本机）
`/opt/gradle-8.9` ｜ `/root/android-sdk`（platform 34 / build-tools 34 / cmake 3.22.1 / ndk 27.0.12077973）｜ JDK 17 ｜ mGBA 已 clone 到 `native-emu/third_party/mgba`。
