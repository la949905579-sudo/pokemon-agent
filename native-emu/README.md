# NativeEmu（Android 工程）

自研双屏 GBA 模拟器：上屏跑 mGBA，下屏是控制台，通过 TCP 桥给 Python 自动化用。

## 结构

```
native-emu/
├── app/
│   ├── build.gradle.kts        # 固定 debug 签名 + BuildConfig(GIT_SHA/BUILD_TIME)
│   ├── keystore.jks            # 固定签名（口令 emu123456），保证能覆盖安装
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

**必须用 CI**（x86_64 runner）：本地 arm64 + proot 无法跑 NDK 的 x86_64 工具链（qemu 嵌套 exec 不可用）。

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
