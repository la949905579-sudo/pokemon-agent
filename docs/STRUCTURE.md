# 项目结构规范（STRUCTURE）

> 目标：改一个功能时只动一两个文件，不牵一发动全身。
> 配套：`docs/generated/FILES.md`（每个文件是什么）、`OBSERVABILITY.md`（日志规范）。

## 一、现状的三个问题

1. **根目录平铺**：40+ 个 `.py` 混在一起，平台通用代码和火红专用代码没有边界。
2. **单文件过大**：`native-emu/.../MainActivity.kt` 已 830 行，界面、逻辑、按键、小地图全在一个文件里。
3. **调试残留入库**：`*.log`、`faint*.txt`、`mapcap*.log` 等 11 个文件被提交进仓库（见 `docs/generated/FILES.md` 标「待清理」的条目）。

## 二、目标结构

```
/root/workspace/
├── platform/                 # 与游戏无关：桥、内存、日志、状态推送、任务循环
│   ├── bridge.py             # ← emu_bridge.py / ra.py 的统一入口
│   ├── memory.py             # ← memory.py（保留）
│   ├── log.py                # ← log.py / logq.py
│   └── runner.py             # ← framework/runner.py
├── games/
│   ├── _template/            # 新游戏模板（复制即用）
│   └── pokemon_firered/      # ← addresses.py / info.py / decision*.py / battle_loop.py ...
│       ├── memory_map.py     # ← addresses.py
│       ├── decode.py         # ← info.py / state.py / bdata.py
│       ├── decide.py         # ← decision*.py
│       ├── plugin.py         # 实现 GamePlugin
│       ├── maps/             # ← 根目录 maps/（地图数据，2026-11-13 定）
│       ├── battles/          # ← 根目录 battles/（战斗数据）
│       └── dialogs/          # ← 根目录 dialogs/（对话数据）
├── tools/                    # 开发工具（gen_files_index.py 等）
├── tests/                    # ← test_*.py（全收；命名不变，只挪位置）
├── native-emu/
│   └── app/src/main/java/com/dsh/emu/
│       ├── core/             # ← EmuCore.kt / EmuService.kt
│       ├── bridge/           # ← BridgeServer.kt / Updater.kt
│       ├── game/             # 已就位（GameState / BattleDecider / MapWalker ...）
│       └── ui/               # ← MainActivity.kt 拆成 Screen/Panels/Keypad
├── docs/
└── web/                      # 用途待确认，确认前不动
```

## 三、依赖规则（硬性）

1. **单向依赖**：`games → platform`、`ui → game → core`。平台层**永远不 import 具体游戏**。
2. **游戏之间零耦合**：`games/A` 不许 import `games/B`。
3. **无环**：任何 `import` 环都算违规，考官（examiner）有权直接打回。
4. **UI 不碰内存**：Compose 层只消费 `GameState` 暴露的数据，不直接 `Memo.u16(...)`。

## 四、文件规范

| 项 | 规则 |
|---|---|
| 单文件长度 | Python ≤ 400 行；Kotlin Composable 文件 ≤ 500 行，超过必须拆 |
| 命名 | Python 模块 `snake_case`；Kotlin 文件 `PascalCase`（与主类型同名）；测试 `test_<模块>.py` |
| 一文件一职责 | 文件名要能预测内容；出现「以及」「顺便」就该拆 |
| 新增模块三件套 | ①单测 ②归属层（platform/games/ui/core）③`docs/generated/FILES.md` 里能查到 |
| 数据文件 | 运行期产物（`*.log`、转储）一律不进仓库，写进 `.gitignore` |

## 五、迁移分期（只搬不改，每步可回滚）

- **P0 规范**（本文档 + `docs/generated/FILES.md` + `OBSERVABILITY.md`）——已完成 2026-11-12
- **P1 Python 侧**（2026-11-13 重建后启动，**等 F 批发布**）：`test_*.py` 全收进 `tests/`；
  `maps/` `battles/` `dialogs/` 并入 `games/pokemon_firered/`；根目录 `.py` 收编进 `platform/`。
  按「移动 + 修 import」迁移，每步跑 `run_tests.py`
- **P2 Kotlin 侧**：拆 `MainActivity.kt`；只能靠 CI 验证，一次只拆一个页面
- **P3 固化**：考官增加边界检查；独立督导检查是否按分期执行

**每期的验收标准（四连，缺一不算完成）**：旧路径 grep=0 → `run_tests.py` 全过 → 无 import 环 →
索引 `--check`=0；涉及模拟器时再加**真机冒烟**。

## 六、边界检查怎么落地

考官（examiner）的清单里加三条（不用新角色）：

1. 新代码属于哪一层？有没有跨层 import？
2. 有没有引入循环依赖？（`python3 -c "import <模块>"` 或静态 grep）
3. 改动的文件是否超过长度上限？超了是拆分计划还是就这样？

独立督导（B 队）则只看流程：迁移有没有夹带行为变更、有没有跳过测试。
