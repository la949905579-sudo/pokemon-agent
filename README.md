# pokemon-agent

Android 上的 GBA 宝可梦模拟器 + 自动化。
- `native-emu/`：Android App（Kotlin / Jetpack Compose / mGBA C++ 核心，JNI）
- 根目录 `.py`：Python 旧自动化层（**冻结**：保留但不新增功能）
- `tests/`：Python 离线测试（旧层）；`native-emu/app/src/test`：Kotlin 单测
- `docs/`：`TASKS.md`（任务）、`HANDOFF.md`（换会话先读）、`ARCH.md`（架构）、`CHANGELOG.md`、`archive/`（旧文档，只读）

## 构建 / 测试
```bash
cd native-emu
gradle :app:testDebugUnitTest --console=plain 2>&1 | tail -30   # Kotlin 单测
gradle :app:assembleDebug --console=plain 2>&1 | tail -20       # APK（签名见 app/keystore-info.txt）
python3 run_tests.py                                            # Python 旧层测试（冻结期只保证不坏）
```

## 发布
push 到 `master` 且改动 `native-emu/**` → GitHub Actions 构建 `build-<sha>` Release → App 内 OTA 更新。

## 规则 / 流程
见 `AGENTS.md`（开发循环、验证、红线）。旧治理文档在 `docs/archive/2026-11/`。
