# 可观测性规范（OBSERVABILITY）

> 目标：出问题时能在 5 分钟内定位到「哪一层、哪个环节、什么参数」，而不是靠猜。
> 反例：OTA 下载卡在 0%，因为没有进度和错误码日志，只能手动重装绕过去。

## 一、格式（一行一个事件）

```
2026-11-12T05:30:12Z INFO  bridge.conn  connect port=55401 ok=true
2026-11-12T05:31:03Z ERROR ota.download stage=fetch code=EAI_AGAIN attempt=2
```

- 时间用 ISO8601（本地时区可读为准）；级别固定 5 档：`ERROR/WARN/INFO/DEBUG/TRACE`。
- 第 3 列是**事件名**（`模块.动作`），后面全是 `key=value`。
- 禁止只打一句人话；关键字段必须结构化，方便 `grep` 和统计。

## 二、必须打日志的关键节点

| 层 | 节点 | 必带字段 |
|---|---|---|
| 启动 | 初始化各阶段、ROM 加载、BIOS 选择 | `stage` `ok` `ms` `rom` |
| 内核 | `init` / `runFrame` 异常、帧率掉档 | `frame` `fps` `err` |
| 桥 | 连接、断开、命令收发失败 | `port` `cmd` `ok` `err` |
| 游戏 | 战斗开始/结束、决策选择、按键执行 | `turn` `choice` `keys` `ms` |
| 推送 | 状态推送成功/失败 | `bytes` `ok` `err` |
| 网络 | OTA 检查、下载进度、校验、安装回调 | `stage` `pct` `code` `sha` |

原则：**凡是「可能卡住或失败」的地方，都要有一条带错误码的日志。**

## 三、级别与开关

- 生产默认 `INFO`；排查时用开关切到 `DEBUG`，**不要靠改代码加日志再重新构建**。
- `ERROR` 只用于「功能真的坏了」；`WARN` 用于「降级但还能用」（如推送数据缺失、沿用上次值）。

## 四、纪律

1. **异常不许吞**：`catch` 里至少要记一条 `ERROR`，带上下文和堆栈。
2. **带上下文**：哪个函数、什么参数、前后状态。只写「失败了」等于没写。
3. **限流与轮转**：单文件上限（如 5 MB，超出滚动为 `<name>.1`，例如 `ota.log.1`）；高频路径（每帧）只许 `TRACE` 且默认关闭。
4. **隐私**：不记 token、账号、完整文件路径中的用户名；内存地址可以记。
5. **别把日志当调试器**：临时日志用完删，别以 `// debug` 形式留在主干。

## 五、现有设施（沿用，不重写）

| 位置 | 现状 |
|---|---|
| Python | `log.py`（写日志）/ `logq.py`（查询）；`logs/intent.json` 等 |
| Kotlin/C++ | 统一走 `Nlog`（`native-emu/.../Nlog.kt`）：写 `/sdcard/Download/emu_native.log`，格式 `ISO8601 LEVEL event k=v`，5MB 滚动 `.1`，异步写、失败降级 logcat。覆盖：桥（bridge.conn/bridge.cmd）、帧循环（emu.frame.*）、Growth（growth.rom）、MapData（map.assets/map.parse/map.fallback）。`service.log` 仍是服务自己的简单日志 |
| CI | GitHub Actions 日志；失败时先看 `e: file:///…` 行 |

## 六、落地状态（2026-11-12 更新）

1. [x] 按第二节的表补结构化日志（统一格式）：
   - OTA：检查/下载进度/校验/安装 → `ota.log`（`aa126e0`）
   - 桥与帧循环：`bridge.conn` / `bridge.cmd` / `emu.frame.*` → `emu_native.log`（`8082f89`、`fdbf448`）
   - Growth / MapData：`growth.rom` / `map.assets` / `map.parse` / `map.fallback`（批次 C）
2. [x] OTA 补 `pct` / `code` 日志（同上 `aa126e0`）。
3. [ ] 设置页「日志级别」开关（`INFO`/`DEBUG`）：`Nlog.minLevel` 已支持，缺 UI 开关；
   记为待办（见 `NATIVE_EMU_TODO.md`）。

**旧文件说明**：`/sdcard/Download/bridge.log` 自 2026-11-12 起不再写入（桥日志并入 `emu_native.log`），
历史文件可留作对照；`ota.log` / `service.log` 仍各自独立。

验收：制造一次失败（如断网触发 OTA），日志里能直接看到失败阶段和错误码。
