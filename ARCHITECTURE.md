# 架构与执行流程（2026-11-09 23:30 快照）

> 本文件由当前代码实际 import 关系整理，不是设计稿；与 README 有出入的地方以这里为准。

## 一、文件系统

```
/root/workspace
├── 核心链路
│   ├── memory.py          UDP 读内存（127.0.0.1:55355）
│   ├── ra.py              UDP 按键（127.0.0.1:55400，含三重松开保护）
│   ├── addresses.py       地址表（唯一真源，全部实测）
│   ├── state.py           状态：坐标/战斗/回合/光标/队伍/束缚/snapshot
│   ├── terrain.py         地图：通行/草地/NPC/换图检测（gMapHeader）
│   ├── bdata.py           数据：招式/属性/克制/队伍解密/my_mon
│   ├── info.py            信息层：scene() + 一致性快照 + 扩展钩子
│   ├── intent.py          指令层：AI/用户目标（拖回合/不击杀/脱战/限定招）
│   ├── decision.py        决策门面（显式导出）
│   ├── decision_battle.py 出招/换人/首发/威胁评估
│   ├── decision_map.py    转身/走路/草里降频
│   ├── action.py          执行层：按键封装、光标、出招、换人
│   ├── switch.py          换人 + 出场槽位（species 驱动）
│   ├── watchdog.py        看门狗 + 等回合结束
│   ├── battle_loop.py     战斗主循环（可传 on_round 观测）
│   ├── pathfind.py        同图寻路 + 遇敌自动打（travel/goto）
│   ├── encounter.py       找草/遇敌
│   ├── nav.py             BFS（转弯惩罚）
│   └── auto_battle.py     兼容门面（battle_loop 的旧入口）
│
├── 入口 / 工具
│   ├── farm.py            自动练级（场数/目标等级/时限/血线）
│   ├── train.py           练级 + 回合观测
│   ├── intent_demo.py     实机演示：注入指令看决策变化
│   ├── probe.py           Recorder：订阅 on_round → JSONL + 汇总
│   ├── probe_enemy.py     定向用非攻击招逼敌方出招
│   ├── move_probe.py      10Hz 采样战斗结构原始字节
│   ├── api_server.py      HTTP API（127.0.0.1:8081，动作+任务）
│   ├── state_server.py    下屏网页（127.0.0.1:8080）
│   ├── mapdraw.py         单地图可视化
│   ├── map_coords.py      全局地图坐标（BFS 推算偏移）
│   ├── map_links.py       地图连接记录
│   ├── map_links_vis.py   连接图可视化
│   ├── track_route.py     记录手动坐标轨迹
│   ├── log.py             日志（控制台 + logs/game-*.log）
│   └── run_tests.py       一键跑 test_*.py
│
├── 实验 / 未接入主链路
│   └── bridge.py + handlers.py   注册制中间层（只有 test_bridge 在用）
│
├── 测试（20 个文件）
│   ├── test_action / test_info / test_decision / test_moves / test_battle_loop
│   ├── test_pathfind / test_travel / test_avoid_grass / test_runlen
│   ├── test_switch / test_switch2 / test_cursor / test_lead / test_turns
│   └── test_guard / test_loop / test_bridge / test_extension / test_probe / test_turn
│
├── 文档
│   ├── ARCHITECTURE.md    本文件
│   ├── README.md          架构/模块/扩展（部分停留在设计稿）
│   ├── NOTES.md           地址表/实测/踩坑
│   ├── HANDOFF.md         会话交接
│   └── PORTING.md         移植说明
│
├── 数据
│   ├── maps/*.json        单地图缓存
│   ├── logs/rounds-*.jsonl  回合观测
│   ├── logs/move_trace-*.jsonl  旧采集（对照用）
│   ├── map_links.json     地图连接
│   └── map_cache.txt      最近地图缓存
│
└── legacy/                旧实验脚本归档（别引用）
```

## 二、分层

```
        入口：farm.py / train.py / intent_demo.py / api_server.py / state_server.py
                              │
        指令：intent.py（目标注入 + 生命周期 + 护栏 + 审计）
                              │
        协调：battle_loop.py  pathfind.py  encounter.py
          │                     │
        决策：decision.py ── decision_battle.py / decision_map.py
          │                     │
        执行：action.py ── switch.py ── watchdog.py
          │                     │
        信息：info.py ── state.py ── terrain.py ── bdata.py
                              │
        底层：memory.py (读内存)        ra.py (按键)
                │                        │
        UDP 55355 READ_CORE_MEMORY   UDP 55400 press
```

依赖原则：信息层只读；决策层纯函数（可离线测）；执行层只按键。
已知例外：`action.py` ↔ `switch.py` 有循环引用（历史遗留，功能正常）。

## 三、执行流程 A：自动练级（farm.py）

```
farm.farm()
 ├─ 读等级/血线（bdata.my_mon）
 ├─ encounter.find_encounter()
 │    └─ terrain(找草) → nav(BFS) → action.walk → ra.press
 ├─ battle_loop.battle_loop(on_round=Recorder)
 │    ├─ info.scene()                  场景：map/battle_main/party_option/...
 │    ├─ switch.active_slot()          读 0x02023BE4 species（唯一真源）
 │    ├─ bdata.my_mon / enemy_info     我方 4 招 + PP、敌方 species/HP
 │    ├─ intent.effective(me, foe)      指令过护栏/排序
 │    ├─ decision.choose_move(..., intents=)  纯逻辑评分
 │    ├─ action.open_move_menu/use_move
 │    │    └─ ra.press → UDP 55400
 │    ├─ watchdog.wait_round_end       等 turn 回 1，动画按 A
 │    └─ on_round(rec)                 回合观测
 │         └─ probe.Recorder → logs/rounds-*.jsonl
 └─ 汇总（PP 差反推实际出招 vs 决策 idx）
```

## 四、执行流程 B：单场战斗内部

```
turn/光标 ──► info.scene()
   map                → 返回
   battle_intro       → advance_dialog（按 A）
   battle_main        → 选招 → use_move
   battle_moves       → use_move
   party / party_option → 换人 / 濒死换人 → ensure_active
   choice             → choose_option(0)（是）
   anim               → 等或按 A
```

## 五、内存与按键

| 通道 | 方式 | 用途 |
|---|---|---|
| 读内存 | UDP `READ_CORE_MEMORY <addr> <n>` @55355 | 所有状态 |
| 按键 | UDP `press` @55400 | 方向/A/B/start 等 |

关键地址（详见 NOTES.md）：

| 地址 | 含义 |
|---|---|
| `0x02036E48/4A` | 坐标（地块 = 坐标 - 7） |
| `0x02024018` | 战斗标志（0 = 地图） |
| `0x02023E82` | 回合（1 主菜单/2 招式/4 动画/0 开场） |
| `0x02023BE4` | 我方 BattlePokemon（+0 species，+0x0C 4 招，+0x22 束缚，+0x4C status1） |
| `0x02023C3C` | 敌方 BattlePokemon（同上，+0x0C 敌方 4 招） |
| `0x02024284` | 队伍数据（100B/只） |
| `0x02036DFC` | gMapHeader 指针（换图立即变） |
| `0x02023D4C` / `0x02023DC4` | 最近行动招式 / 我方本回合招式 |

## 六、测试与验证

- `python3 run_tests.py`：20 个文件全离线（mock 内存/按键）
- 实机验证链：`train.py 1 180`（单场观测）→ `farm.py N 20`
- 数据回归：`test_moves.py` 锁定 26 条招式 + 8 个物种属性
- 观测产物：`logs/rounds-*.jsonl`，`probe.Recorder.summary()` 给一致性

## 七、已知问题（按优先级）

1. `bridge.py`/`handlers.py` 是场景裁剪（信息流），未接入主链路；AI 指令流由 `intent.py` 承担 → README 需修
2. `action.py` ↔ `switch.py` 循环依赖
3. 威胁评估目前只写日志，未进决策；intent 的 prioritize 还没和威胁评估联动
4. 室内地图靠 `OFF_X/OFF_Y=7` 换算，换图瞬间坐标可能短暂是旧值
