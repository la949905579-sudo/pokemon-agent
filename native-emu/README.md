# NativeEmu（Android 工程）

自研双屏 GBA 模拟器：上屏跑 mGBA，下屏是控制台，通过 TCP 桥给 Python 自动化用。

## 结构

```
native-emu/
├── app/
│   ├── build.gradle.kts        # 固定 debug 签名 + BuildConfig(GIT_SHA/BUILD_TIME)
│   ├── keystore.jks            # 固定签名（本地，已 gitignore；口令见 keystore-info.txt）
│   └── src/main/
│       ├── AndroidManifest.xml # 权限：存储/前台服务/安装包
│       ├── cpp/
│       │   ├── CMakeLists.txt  # mGBA 子目录 + 宏全对齐（关键！）
│       │   ├── emu_core.cpp    # mGBA 生命周期：init/runFrame/save/load/内存
│       │   ├── emu_core.h
│       │   └── emu_jni.cpp     # JNI 层（含 ABGR→ARGB 像素转换）
│       └── java/com/dsh/emu/
│           ├── MainActivity.kt # Compose UI + EmuView(SurfaceView)
│           ├── EmuCore.kt      # native 声明 + 按键掩码
│           ├── BridgeServer.kt # TCP :55401
│           ├── EmuService.kt   # 前台保活 + WakeLock
│           ├── Updater.kt      # GitHub Releases OTA
│           └── UiState.kt      # 外部推送的状态
└── tools/
    ├── patch_mgba.py           # 给 mGBA 插调试日志（CI 用）
    └── bridge_client.py        # 桥客户端示例
```

## 签名（2026-11-12 起）

- 密钥库**不在仓库里**：CI 从 Actions secret `ANDROID_KEYSTORE_B64` 解码，
  口令来自 `STORE_PASSWORD` / `KEY_PASSWORD`，别名固定 `emu`。
- 本地开发想构建：把 keystore 放到 `native-emu/app/keystore.jks`（已被 .gitignore 忽略），
  并 `export STORE_PASSWORD=... KEY_PASSWORD=...`。
- **签名已轮换过**：旧包的签名无法覆盖升级，换机/重装必须卸载旧版。
- 构建成功会自动发 Release（`build-<sha>`），OTA 的更新源就是它，不需要 PAT。

## 构建

**分工**：Kotlin 编译 + 单测可以在本机跑；**APK/NDK 必须走 CI**（NDK 的 clang 是 x86_64，proot 下 qemu 嵌套 exec 不可用）。

### 本机跑 Kotlin 单测（2026-11-12 实测可用）

```bash
mkdir -p /root/android-emu-local
ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2   # 必须叫 aapt2
cd /root/workspace/native-emu
export PATH=/opt/gradle-8.9/bin:$PATH
gradle :app:testDebugUnitTest --no-daemon --console=plain \
  -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2
```

- 首次要联网拉 junit/hamcrest（之后可加 `--offline`）；首次约 2 分钟，热跑约 1 分钟
- `local.properties` 需 `sdk.dir=/root/android-sdk`（已 gitignore）
- 依赖两块本机资源（不在仓库里，换机要重建）：`/opt/aapt2-x86_64/aapt2` 与 `/opt/amd64-root/`

```bash
# 推送即触发 .github/workflows/build-native-emu.yml
git push
# 产物：Actions → build-apk →  artifact app-debug
```

## 调试

- 运行日志写在 `/sdcard/Download/emu_native.log`（`init: xxx` 步骤）
- 服务日志 `/sdcard/Download/service.log`
- 桥日志 `/sdcard/Download/bridge.log`

## 关键坑（改代码前必读）

1. **emu 与 libmgba 的编译宏必须完全一致**，否则 `struct mCore` 布局错位，`core->init` 读到垃圾指针（表现为初始化随机崩溃）
2. **初始化顺序**：`mCoreConfigInit` → `mCoreCreate` → `mCoreInitConfig` → `core->init` → `setVideoBuffer` → `loadROM` → `reset`
3. **无 BIOS 要 `opts.skipBios = true`**，否则 CPU 从空 BIOS 区执行会崩
4. **像素是 RGB565（16 位）**，JNI 里按 `BYTES_PER_PIXEL` 转 ARGB；32 位模式是 ABGR 不是 ARGB
5. **存档 API 参数是内存缓冲区**，不是 `VFile*`（传错会堆溢出）
6. `mCoreFind` 偶尔返回未初始化 core，加载要重试
