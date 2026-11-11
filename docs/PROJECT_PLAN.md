# 项目规划：从「一个游戏的自动化」到「一个模拟器平台 + 多个游戏插件」

> 2026-11-11 规划。当前状态：Pokemon 火红自动化已跑通；NativeEmu（自研双屏 GBA 模拟器）P0 完成。

---

## 一、愿景

```
        ┌──────────────────────────────────────┐
        │  NativeEmu（模拟器平台，与游戏无关）   │
        │  mGBA 内核 · 双屏渲染 · 触屏按键      │
        │  存档 · TCP 桥 :55401 · OTA 更新      │
        └───────────────┬──────────────────────┘
                        │  read/write/press/frame/status
        ┌───────────────┴──────────────────────┐
        │  游戏插件层（每个游戏一个目录）        │
        │  ┌─────────────┐  ┌─────────────┐    │
        │  │ pokemon_fr  │  │ 未来：其他   │    │
        │  │ 地址表·决策  │  │ 游戏插件     │    │
        │  └─────────────┘  └─────────────┘    │
        └──────────────────────────────────────┘
```

**原则**：平台层永远不知道「Pokemon」；游戏层只关心「这个游戏的内存和操作」。

---

## 二、三层职责

### 1. 平台层（Platform）
与具体游戏无关，跨游戏复用：

| 模块 | 职责 | 现状 |
|---|---|---|
| `native-emu/` | Android App：渲染/按键/存档/OTA | ✅ |
| `emu_bridge.py` | Python 侧 TCP 客户端（rd/wr/press/frame） | ✅ |
| `push_status.py` | 状态推送（下屏显示） | ✅ 需插件化 |
| 下屏 UI | 小地图/菜单/日志/按键 | ✅ |

### 2. 游戏插件层（Game Plugin）
每个游戏一个目录，实现统一接口：

```
games/<game_id>/
├── plugin.py        # 入口：实现 GamePlugin
├── memory_map.py    # 内存地址表（结构化）
├── state.py         # 解码游戏状态（场景/坐标/队伍/战斗）
├── decision.py      # 决策（状态 -> 按键序列）
└── README.md        # 这个游戏的说明
```

### 3. 自动化层（Automation）
通用调度：循环「读状态 → 决策 → 执行 → 推送状态」。

```
runner.py            # 通用主循环（与游戏无关）
```

---

## 三、游戏插件接口（契约）

```python
class GamePlugin(Protocol):
    game_id: str                 # "pokemon_firered"
    display_name: str            # "口袋妖怪 火红"

    def attach(self, bridge) -> None:
        """注入平台桥（rd/wr/press/frame）。"""

    def status(self) -> dict:
        """返回下屏要显示的状态（map/x/y/team/battle/log）。"""

    def decide(self) -> list[str]:
        """返回下一步要按的键（如 ["UP", "A"]），空表示等待。"""

    def on_event(self, event: str) -> None:
        """平台事件（存档/读档/战斗开始等），可选。"""
```

**平台只认这个接口**；具体游戏怎么读内存、怎么决策，平台不关心。

---

## 四、目录规划（迁移目标）

```
/root/workspace/
├── platform/                 # 平台通用（从现有模块抽取）
│   ├── bridge.py             # TCP 客户端（emu_bridge 改名）
│   ├── runner.py             # 通用循环
│   └── status_push.py        # 状态推送
├── games/
│   ├── _template/            # 新游戏模板（复制即用）
│   └── pokemon_firered/      # 现有 Pokemon 项目迁入
│       ├── plugin.py
│       ├── memory_map.py     # ← addresses.py
│       ├── state.py          # ← state.py/info.py
│       ├── decision.py       # ← decision*.py
│       └── ...
├── native-emu/               # Android App（不变）
├── tests/                    # 离线测试（不变）
└── docs/                     # 文档（README/NATIVE_EMU/PROJECT_PLAN...）
```

**迁移顺序**（每步都可独立验证）：
1. 建 `platform/` + `games/pokemon_firered/`
2. 把 `addresses.py` → `games/pokemon_firered/memory_map.py`（纯移动 + import 修正）
3. `info.py`/`state.py` 的**游戏专用部分**挪进插件，通用部分留平台
4. `runner.py` 包装现有 `battle_loop`/`farm` 的主循环
5. 测试全绿 + 实机跑一次（AGENTS.md 规则 4）

---

## 五、路线图

### P0 · 平台跑通（✅ 已完成）
- NativeEmu 双屏 + 存档 + 按键
- TCP 桥 + Python 客户端
- 后台常驻 + OTA

### P1 · 插件化（✅ 2026-11-11 完成）
- [x] 抽出 `GamePlugin` 接口 + `_template`（`framework/game_plugin.py`）
- [x] Pokemon 插件 `games/pokemon_firered/`（包装现有 info/state，零改动）
- [x] `framework/runner.py` 通用主循环 + `framework/loader.py` + `run_game.py`
- [x] 测试 28/28
- **用法**：`EMU_BACKEND=native python3 run_game.py pokemon_firered`

### P2 · 第二个游戏（约 1-2 周）
- [ ] 选一个结构简单的游戏（候选：黄金太阳、火焰纹章、星之卡比）
- [ ] 只用插件接口实现（不改平台代码）
- **验收**：新游戏下屏能显示状态，能做最简单的自动操作

### P3 · 平台增强
- [ ] 下屏战斗页自动切换
- [ ] 联机（GBA link cable）
- [ ] 加速 / 按键映射自定义

---

## 六、关键决策记录

| 决策 | 结论 | 理由 |
|---|---|---|
| 游戏知识放哪 | **游戏插件层** | 平台保持通用，加游戏不改平台 |
| 状态怎么显示 | **插件推送 JSON** | App 不知道游戏地址，保持通用 |
| 插件接口 | **鸭子类型 Protocol** | Python 简单，不强制继承 |
| 第二个游戏选谁 | 结构越简单越好 | 验证插件接口，不是做完整自动化 |

---

## 七、风险

1. **不同游戏内存结构差异大**（RPG/战棋/动作）→ 接口要留 `raw()` 逃生口
2. **插件化迁移可能破坏现有功能** → 每步跑测试 + 实机
3. **下屏 UI 是平台层**，游戏要定制显示需要**扩展点**（如自定义 Tab），别做死
