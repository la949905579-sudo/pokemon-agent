# pokemon-agent

Android 上的 GBA 宝可梦模拟器 + 自动化。
- `native-emu/`：Android App（Kotlin / Jetpack Compose / mGBA C++ 核心，JNI）
- `pyplatform/`：Python 旧自动化层（**冻结**：保留但不新增功能；数据在 `games/pokemon_firered/`）
- `tests/`：Python 离线测试（旧层）；`native-emu/app/src/test`：Kotlin 单测
- `docs/`：`TASKS.md`（任务）、`HANDOFF.md`（换会话先读）、`ARCH.md`（架构）、`CHANGELOG.md`、`archive/`（旧文档，只读）

## 构建 / 测试
```bash
# Kotlin 单测（本机可跑；aapt2 经 qemu wrapper，见 native-emu/README）
ln -sfn /root/workspace/native-emu/tools/aapt2-wrapper /root/android-emu-local/aapt2
cd native-emu
/opt/gradle-8.9/bin/gradle :app:testDebugUnitTest --no-daemon --console=plain \
  -Pandroid.aapt2FromMavenOverride=/root/android-emu-local/aapt2 2>&1 | tail -30

# APK / NDK 必须走 CI（push 触发），本机无法编译
python3 run_tests.py   # Python 旧层测试（冻结期只保证不坏）
```

## 发布
push 到 `master` 且改动 `native-emu/**` → GitHub Actions 构建 `build-<sha>` Release → App 内 OTA 更新。

## 规则 / 流程
见 `AGENTS.md`（开发循环、验证、红线）。旧治理文档在 `docs/archive/2026-11/`。
