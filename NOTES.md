# 叶绿内存（实测）

| 用途 | 地址 | 说明 |
|---|---|---|
| 坐标 | 0x02036E48 / 0x02036E4A | 地块 = 坐标 - 7 |
| 战斗 | 0x02024018 | 0=地图 |
| 对话框 | 0x03000F9C | 菜单打开时也是 1 |
| **玩家回合** | **0x02023E82** | 1=主菜单/强制换人，2=子菜单，4=动画/结算/地图，0=开场 |
| 主菜单光标 | 0x02023FF8 | 0=战斗 1=背包 2=宝可梦 3=逃跑；子菜单里保留"从哪打开" |
| 招式光标 | 0x02023FFC | 0=左上 1=右上 2=左下 3=右下 |
| 队伍光标 | 0x0203B0A9 | 0-5=第1-6只；主菜单=7；**强制换人时也是 0-5** |
| 背包光标 | 0x0203AD08 | 道具列表 0 起 |
| 队伍数据 | 0x02024284 | 100B/只：等级 +0x54，HP +0x56/maxHP +0x58 |
| 我方招式 | 队伍 +0x20 | PID^OTID 解密，PID%24 取 A 结构，前 8B=4 招式；G 结构首 u16=species |
| 敌方摘要 | 0x02024080 | +0 等级，+2 HP，+4 maxHP（无 species/招式） |
| **敌方 species** | **0x02023C3C** | 敌方 BattlePokemon +0（u16）；turn=0/1 实测稳定：16 波波 / 52 喵喵 / 69 喇叭芽 |
| ~~敌方 species~~ | ~~0x020244DE~~ | **不可用**：主菜单/换人界面会变成我方场上（实测读到 15/22/32） |
| 地图 | 扫 EWRAM 唯一候选 | 返回地图数组地址+宽高（**仅作回退**，慢约 4s） |
| **gMapHeader 指针** | **0x02036DFC** | 换图后值立刻变（室内 0x82d5970 / 室外 0x82e1514 实测）；+0=layout，+4/+8=tileset。terrain.py 首选它判换图 |
| **朝向** | **0x02036E38+0x18** | 低字节：0x11=下 0x22=上 0x33=左 0x44=右 |
| NPC | 0x02036E38 | 0x24/个（玩家是第 0 个） |

## 判断逻辑
- 地图：`in_battle()==0`（注意地图上 E82 也是 4）
- 主菜单：E82=1 且 B0A9=7
- 强制换人：E82=1 且 B0A9<=5
- 子菜单：E82=2，看 0x02023FF8 残留：0=招式 1=背包 2=换人

## 经验
- **按键时长（二次实测，以这个为准）**：
  - `0.06s`：**只转身、不走格**（用于调整朝向）
  - 长按时长与格数（实测）：`0.09s→1`、`0.18s→1`、`0.27s→2`、`0.36s→3`，近似 `0.06 + 0.09×格数`
  - **室外长距离实测**（枯叶市 25 格直路）：9 格、12 格往返全部精确，坐标零误差
  - `0.09s`：**稳定走 1 格**（逐格走用这个）
  - `0.10s`：不稳定（有时 0 格）
  - `0.12s`：偶尔串成 2 格（长按段会多走）
  - **A/B 键至少 0.25s**（0.15s 游戏不识别）
  - `action.walk` 已改为**逐格短按 + 坐标校正 + 超走回退**。
- 换图必重扫（terrain.py 用 0x02036DFC 判断，进门瞬间切到新图，不再靠坐标剧变）
- 水面碰撞=0 但高度层不同（岸 3/水 1），BFS 必须查高度
- 消息要按 B 跳（advance_b）
- **菜单里按住会连发**：0.3s 能跳 2 格，选宝可梦必须 0.08s 单步 + 每步读光标
- **队伍菜单布局（截图实测）**：左边是当前出场的精灵（光标 **0**），右边一列是队伍里除它以外的其余 5 只（光标 **1..5**，按队伍顺序）。所以**光标号 ≠ 队伍槽位**，必须换算 `_cursor_for_slot(slot, active)`，否则会选错人。
- **出场规则**：战斗开始时游戏按队伍顺序自动派第一只有 HP 的，不弹菜单。
- **濒死流程（实测）**：场上精灵倒下 → 对话框「XX 被打倒了！」（等按 A）→ 按 A 后可能弹 **「要使用下一只宝可梦吗？」是/否** → 选「是」进队伍换人界面。
  - 选项框标志（**已验证 2 次**）：`0x02023E83` 弹窗时 =0，主菜单 =1（`E82=01 xx`）。`snapshot()['mode']=='choice'` 表示当前有选项菜单（是/否 或 放出/概况/取消）。
  - **`turn=2` = 二级菜单**（放出/概况/取消）：换人时必须按到 `turn=4`（换人动画）才算成功；用 `turn != 1` 判断会把二级菜单误当成已推进。
  - 濒死换人时左侧是倒下的那只，光标默认在它上面；要先移到右侧健康的那只再按 A。
  - **倒下后每次只按一次 A 就采集**：连按会跳过弹窗（踩过坑）。
- **战斗中换人 = 交换位置**（实测 3 次核对通过）：界面上「左边当前出场」与「右边选中的」互换，右侧顺序立刻变。真实队伍数组 0x02024284 不变，战斗内部另有一份顺序（战斗结束重置）。
  - 用 `party_order()` **在内存中**维护（不落盘）：`order[0]`=左边当前出场，`order[1..5]`=右侧 5 只；换人后交换 `order[0]` 与选中位置；新战斗开场 `reset_party_order()`。
  - `_cursor_for_slot()` = `order.index(slot)`，光标号就是 order 下标。
  - 换人后必须等动画走完（约 2-4 秒）再打开菜单核对，动画中打开会读到旧数据。
  - **内存里没有明文顺序数组**：扫过全 EWRAM，只有 7 处 `[0,1,2,3,4,5]` 常量、换人后不变；战斗队伍数据是加密的（0x020244C0 附近只有当前上场那只有明文 species）。所以顺序只能在进程内跟踪，新进程按队伍顺序重新初始化。
- **不要用 0x020244DE 判断场上**：菜单打开时它会变成「光标所指」的宝可梦。场上槽位统一用 `party_order()[0]`。
- 战斗换人流程：队伍列表 → A → 「放出/概况/取消」→ A 选「放出」=换上场；列表底部「取消」光标=7
- **强制换人后可能弹「放出/概况/取消」**：选中后看 `turn`——变 4 = 直接上场（不许再按 A，否则落到列表触发交换）；仍为 1 = 弹了二级菜单，要再按一次 A。不能按场景假设。
- menu_kind：队伍列表一定 FF8==2；只看 B0A9<=5 会把主菜单误判成换人界面
- RetroArch 后台读不到，先 open
- 少用全量 EWRAM 扫描，日常用 qstate.py
- **卡键**：`timeout` 强杀 python 会停在「按下」和「松开」之间，角色一直走、其它键像失灵，且方向看起来像反的。ra.py 已有 try/finally + atexit + SIGTERM 三重松开；再遇到先 `release_all()`
- 精灵中心流程：门口 (15,8) 往上走到 (15,5) 自动进门 → 室内柜台 (7,4) → 按 A 三次治疗 → 按 B 关对话

## 战斗模块（bdata.py / auto_battle.py / encounter.py）
- 选招：PP=0 跳过；按 威力×克制 排序（敌方 species 未知时克制=×1）
- 换人 choose_switch：优先有克制招式且等级>=敌方-5；否则选等级最高且不被克制
- 强制换人 / 手动换人（do_switch）都用这套策略
- 遇敌：先判断草地，不在则 BFS 走到最近草格；九宫格有草优先朝草走；草地内不连续同方向
- 属性表 SPECIES_TYPES 只收了常见种类，缺的补

## 架构（三层，迁移中）

- **info.py 信息层**：`scene()` 返回场景（map / battle_intro / battle_main / battle_moves / battle_submenu / party / party_option / choice / anim），`context()` 附带光标。只读内存，不决策不按键。已实测 + 9 个映射测试。
- **decision.py 决策层**：`choose_move` / `choose_switch` / `should_switch`，纯逻辑、零 IO，可离线测试。目前是 bdata 策略的收拢层。
- **action.py 执行层**：`tap_a` / `tap_b` / `move_cursor_to` / `wait_until`，只执行动作，不判断场景。
- **现状**：三层已打通。`battle_loop` 现在是薄协调层：`scene → decision → action`，实测打完一整场。
- 已迁移：换人（action.pick_and_switch）、选招（action.use_move）、对话推进、选项选择；策略（choose_move/choose_switch）全在 decision。
- 已迁移寻路：`pathfind.walk_segment` 只调 `action.walk`；避草/段长决策在 `decision.grass_tiles / clear_run / run_limit`。`pathfind.goto/travel` 保留为协调层。
- 实测：`battle_loop` 打完整场（胜负正确）、`travel` 避草 4.2s 出城（warped）。

### 转身的分层（实测通过）

流程：**想移动 -> 决策层拉朝向 -> 判断 -> 一致直接走；不一致先 turn 再 walk**

- **info.facing()**：读当前朝向（up/down/left/right）
- **decision.need_turn(direction, facing)**：True 表示需要先转身（读不到朝向时返回 False）
- **action.turn(direction)**：只转身，按 0.06（实测不走格）
- **action.walk(direction, steps)**：**只移动**，不负责转身；**时长驱动**：一次长按 `0.06 + 0.09×steps`，再按坐标微调（少了补按、多了反向退）
- 协调：`if decision.need_turn(d, info.facing()): action.turn(d)` 然后 `action.walk(d, n)`
- 实测：朝向 up 走 down -> 先转身再走 1 格；朝向 down 走 up 3 格 -> 先转身再走 3 格，位移全部精确

### 扩展接口（接入新操作的标准路径）

- **信息层**：`info.register_scene(name, detector, priority=0)` —— 新界面先注册检测器跑通，稳定后再固化进 `scene()` 内置分支；`unregister_scene(name)` 撤销。
- **决策层**：`decision.set_move_strategy(fn)` / `set_switch_strategy(fn)` —— 换策略/换招逻辑可插拔，传 `None` 恢复默认。
- **执行层**：新动作先写成 `action.py` 的函数（单步、可测），通过后再接入协调层。
- 流程：**注册/临时实现 → 离线测试 → 实战验证 → 固化**。
- 迁移顺序：action 抽按键 → decision 抽策略 → battle_loop 变薄协调层 → 寻路/遇敌同样处理。


## 5 号道路 / 精灵中心（实测）

- **5 号道路**地图 `0x82df30c`（48×40）
- **精灵中心入口**：站在 **(22,20) 往上走一格**即进门；室内布局 `0x82d5844`（15×10，与枯叶市共用），进门点在 (7,8)，柜台 (7,4)
- 提醒：这块地图的碰撞数据与实际**多处不符**（数据说墙、实际能走），靠 metatile 猜门不可靠，要以实际走位为准


## 地图汇总（实测，2026-11-09）

| 地图 | 地址 | 尺寸 | 关键位置 / 连接 |
|---|---|---|---|
| 枯叶市 | `0x82e0614` | 48×40 | 精灵中心门口 (15,8)，往上到 (15,5) 进门；北边界 (24,0) 出界 → 6 号道路 |
| 精灵中心（室内，通用布局） | `0x82d5844` | 15×10 | 进门点 (7,8)，柜台 (7,4)，按 A 治疗 |
| 6 号道路 | `0x82e9260` | 24×40 | 南边界出界 → 枯叶市；北边 (19,16) 往上 → 入口房间 A |
| 入口房间 A | `0x83192f0` | 13×10 | **(7,4) 往左 → 地下通道**；(3,7) 往下 → 5 号道路；南门 (6,8) ← 6 号道路 |
| 地下通道 | `0x831989c` | 8×63 | 连接房间 A：(7,4) 左进 / (4,3) 右出（双向） |
| 5 号道路 | `0x82e833c` | 48×40 | 北边界出界 → 华蓝市（有草，遇敌区） |
| **被偷的房间**（原入口房间 B） | `0x831a3a0` | 10×9 | 华蓝市 (31,8) 往下 / (30,12) 往上；5 号道路 (31,8) 往下也能进 |
| 华蓝市 | `0x82df30c` | 48×40 | **精灵中心入口 (22,20) 往上**（(22,19) metatile 98） |

### 门是通用图块（实测验证）

- **精灵中心门 = metatile 98**：枯叶市 (15,6)、华蓝市 (22,19) 都是 98
- **道馆门 = metatile 347**：华蓝市道馆门 (31,21)（之前误记 346，那是左边的 (30,21)），走上去进入道馆室内 `0x82d5cbc`（17×20）
- **门的辅助特征**：地面 elev=3 → 门格 elev=0（高差 3），门格 coll=1、上方连排是建筑图块（330/339/347 等）
- **单向坎（ledge）= metatile 176**（华蓝市 (11,16) 实测）：elev=0、coll=1，**只能从上往下跳，不能从下往上走**；这一带整片都是这个功能。
  - 区分：门是「走上去换图」，ledge 是「跳下去只变坐标」；elev/coll 一样，要靠 metatile 或实际行为区分
- 判定门 = 建筑正面 + 与地面高差 3 + 下方是道路(8/9/16/17)
- 门前：上方一格是建筑正面（90/82 等），下方一格是道路（8/9）
- 所有精灵中心长得一样，同一套建筑 tileset 下 98 就是门
- 注意：不同地图 tileset 不同时，98 未必是门，只在同套 tileset 内通用
- 踩坑：`0x0586–0x059f`（390–415）是装饰不是门；这张图碰撞数据和实际**多处不符**，以实际走位为准


## 招式表数据（踩坑）

- `MOVES` 表有手抄错误：曾经把 **31** 写成「咬住」（恶 60），实际 31 = **乱击**（虫 15），咬住 = **44**
- 症状：选招总是第 1 招、伤害不对
- 验证方法：**截图游戏内招式菜单**和 `MOVES` 表对照（招式名/属性/PP 都要对）
- 当前已知正确：31 乱击(虫15)、40 毒针(毒15)、41 双针(虫25)、44 咬住(恶60)、98 电光一闪(一般40)


## 健壮性（P0，已实现）

- **读一致性**：`info.consistent_snapshot()` —— 读前后对比坐标/回合，防「读到一半游戏状态变了」
- **看门狗**：`auto_battle._watchdog()` —— 连续 12 轮「场景+双方血量」无变化就按 A，再 3 轮按 B
- 测试：`test_guard.py`


## 执行闭环（已实现）

- `action.use_move()`：按 A 后检查 `turn` 是否从 2 变化，**没变就是没出招**（不靠 HP）
- `auto_battle.wait_round_end()`：等 `turn` 回到 1 或战斗结束；期间动画/结算按 A 推进
- **不用真实时间**，只数轮询次数 —— 加速/不加速都适用
- 出招失败会自动重试一次，仍失败交给看门狗
- 实测：turn 2→4（出招 0.06s）、4→0→1（回合完成）


## 中间层 bridge（已落地，注册制）

- `bridge.py`：核心只有 **注册表 + 裁剪 + 分发**，不含任何具体场景
- `handlers.py`：各场景的处理器（battle/map/dialog/choice），**一个新功能 = 一个函数 + 一行注册**
- `handlers.InfoSource`：把 info 模块包装成 `get(key)` 给 bridge 用
- 增删功能：`register_scene(name, fields, handler)` / `unregister_scene(name)`
- 测试：`test_bridge.py`（含插件场景注册/注销）
- 现有 `battle_loop` 暂不切换，保持稳定；新功能优先走 bridge


## 决策层模块化（已拆分）

- `decision.py`：**门面**（19 行），统一导出旧接口，保持兼容
- `decision_battle.py`：战斗决策（出招/换人/选首发/克制）
- `decision_map.py`：地图决策（转身/走路/草里降频）
- `handlers.py`：每个场景只 import 自己需要的模块
- 由 bridge 根据场景激活对应模块


## 代码整理（已完成）

- 23 个死代码文件已移到 `legacy/`（确认无引用后）
- 新增 `run_tests.py` 一键跑全部测试：`python3 run_tests.py [关键字]`
- 当前核心模块 16 个，导入冒烟测试全过
- 剩余可优化：`auto_battle.py`(379) / `state.py`(272) 偏大，可再拆


## state 拆分（已完成）

- `memory.py`：UDP 内存读写基础（`rd` + HOST/PORT）
- `addresses.py`：地址表（全部实测地址集中一处）
- `state.py`：状态函数（256 行，接口不变，旧代码零改动）


## auto_battle 拆分（已完成）

- `switch.py`：换人（队伍顺序 / 光标映射 / 换人动作）
- `watchdog.py`：看门狗 + 等回合完成
- `battle_loop.py`：战斗主循环
- `auto_battle.py`：门面（11 行，旧接口兼容）


## 走路速度优化（2026-11-09 实测）

- **按住 B 跑步**：`action.walk()` 里同时按住 B 键（设备 id 0），实测 **0.21s/格**（步行 0.45s）
- **转弯等待**：转身 0.06s + 等待 0.05s（原 0.15s）
- **地图数据缓存**：`terrain.load()` 同地图不重读（省 1920 字节 UDP/次）
- **转弯惩罚寻路**：`nav.bfs_turns()`，转弯 +1.6 成本，复杂地图少转弯
- 实测：枯叶市街道 12 格 = 2.46s，20 格路线 20s → 11.3s


## 外部 API（已实现，端口 8081）

- `GET /api/state`：完整状态（场景/坐标/队伍/敌人/地图）
- `GET /api/view?radius=N`：地图视野（周围格子矩阵：. # G N ?）
- `GET /api/stream`：SSE 状态推送（变化即推）
- `POST /api/act`：动作原语（press/walk/goto/travel/fight/switch/flee/heal）
- `POST /api/task`：高层任务（goto_center/farm）
- 动作互斥（同一时间只能执行一个）


## 换首发 bug 修复（2026-11-09）

- 根因：选「宝可梦」后**直接是「替换/概况/取消」界面**（状态判定 `party_option`），不是 `PARTY`
- 修复：`switch_from_main` 接受 `PARTY_OPTION`；删掉会退出菜单的 `tap_b`
- 实测：选项界面方向键仍能移动队伍光标；A×2 完成换人（turn→4）
- 已恢复 `_lead_enabled = True`


## 换人被拒兜底（2026-11-09）

- 束缚类招式（紧束/缠绕/火焰旋涡等）会让换人失败
- `switch._switch_blocked`：换人失败后本场不再尝试，避免死循环
- `battle_loop`：检测到 blocked 就退出队伍菜单继续打
- 失败时自动关闭残留对话


## 战斗状态检测（2026-11-09 实测）

- **我方战斗数据结构**：`0x02023BE4`（species 在 +0x00，大针蜂=15）
- **状态字段 status1**：`0x02023BE4/0x02023C3C + 0x4C`（1 字节）
  - 位定义：低 3 位=睡眠回合(0x07)、中毒 0x08、灼伤 0x10、冰冻 0x20、**麻痹 0x40**、剧毒 0x80
  - 实测：睡眠时 1 → 醒来 0；敌方被皮卡丘静电麻痹时 = 64(0x40)
  - 接口：`state.status_flags(slot)` / `info.battle_status(slot)` / `info.paralyzed(slot)`
  - slot 0 = 我方场上，1 = 敌方场上
- **束缚（已确认）**：`+0x22` 的 bit 8（0x100）
  - 无束缚 = 3；束缚中 = 258（0x102）
  - 实测：束缚时换人失败 + 游戏提示「无法被交换下场」
  - 接口：`state.trapped()` / `info.trapped()`（战斗外返回 False，防残留数据）
- OSD 状态行会显示 `[睡眠]`


## 特殊可互动图块（2026-11-09）

- **小树苗**：metatile 317（不可走，需要用「居合斩」砍掉）
- 华蓝市 (27,32) 附近有小树苗挡路（去道馆的近路）


- **华蓝道馆**：地图 0x82d5cbc（17×20），入口在华蓝市 (31,22) 往上

## 待办
1. ~~重新定位敌方 species~~ ✅ 改用 0x02023C3C（实测 16/52/69 稳定）
   ~~换人交换隐患~~ ✅ 强制换人单次 A（实测队伍顺序未变）
2. **强制换人的 menu_kind 判据**：已用 `probe_menu()` 方向键试探，实战走通过；可再多验证
3. 敌方招式表地址（可选）
3. ~~存档/回中心补血流程~~ ✅ 已跑通（见经验）

## 模块（统一入口 pkmn.py，from pkmn import *）

**状态 state.py**：**snapshot()** / coords / in_battle / in_dialog / turn_state / menu_kind / cursor / player_facing / party / wait_turn
- **snapshot()**：统一轻量状态检测，只读 4 处内存（约 40-80ms），返回 `{mode, battle, dialog, turn, x, y}`；`mode` = `map` / `battle` / `battle_dialog`。所有动作前用它当守卫。

**战斗 bdata.py**：MOVES / TYPE_CHART / SPECIES_TYPES / my_mon(slot) / enemy_info / choose_move(mon,types) / choose_switch(types,lv) / move_effect

**战斗流程 auto_battle.py**：advance_b（B 跳对话）/ move_to（光标定位）/ do_switch（手动换人）/ handle_force_switch（强制换人）/ battle_loop / active_slot

**遇敌 encounter.py**：ensure_grass / nearest_grass / step_in_grass / find_encounter / is_grass_here / tile_pos

**移动 pathfind.py + move.py**：goto(x,y)（BFS+长按+障碍学习+**战斗检测**）/ travel(x,y)（遇敌自动打再继续走）/ walk_segment / move(dir,n)（朝向感知）
- 障碍学习：某段没走够 n 格 → 把挡路那格记进 `_blocked`，之后 BFS 绕开；黑名单堵死路时自动清空重试；**战斗中不学**；到达目标清空。离线回归测试 `test_pathfind.py`（不碰游戏，mock 版）。
- **战斗检测**：`goto` 返回 `True` / `"battle"` / `"dialog"` / `False`；每 `CHECKPOINT=6` 格查一次 `snapshot()`，遇敌或 NPC 对话立即停。
- **段长动态**：沿路径算「到第一格草的距离」——草前一律长段（≤`MAX_RUN=40`），**进草那一段起**才降到 `MAX_RUN_GRASS=6`，离开草后又恢复长段。测试 `test_runlen.py`。
- **travel(x,y)**：遇敌 → `battle_loop()` → 打完继续赶路。返回 `ok` / **`warped`（途中换图，目标坐标失效）** / `fail` / `battle_stuck` / `too_many_battles`。换图用 gMapHeader 指针检测（实测走出边界返回 warped）。
- `nav.goto` 也会在遇敌时返回 `"battle"`。测试 `test_travel.py`。
- **避开草地**：`goto/travel` 的 `avoid_grass=True`（默认开）。只有草地刷野怪，赶路优先绕开；绕不开或目标本身是草格时自动回退允许穿草。实测 (13,10) 从 33 格踩 9 草 → 41 格 0 草。测试 `test_avoid_grass.py`。

**组合示例**：
```
from pkmn import *
if find_encounter(): battle_loop()
goto(26,11); move('up',3)
do_switch()          # 按克制/等级策略换人
```

其他：qstate.py 状态行 / nav.py 逐格导航 / run3.py 连打 N 场

**按键 ra.py**：press(name, dur)（含 try/finally 松开）/ send(bid,state) / release_all()（退出/异常自动调用）/ IDS 方向键映射（已实测：up=4 down=5 left=6 right=7 顺序正确，按 0.25s≈2 格）

## 后续补充（2026-11-09 深夜）

### 束缚判据（+0x22，2026-11-09 修正）
- **可靠判据只有 bit8（0x100）**：258 = 0x102 实测换人被拒（形态 A，Wrap 类）
- 旧的 bit2/3 判据已废弃：皮卡丘实测 `+0x22 = 1037（0x040D）` 时**换人正常**，低 4 位就是 0x0D，说明低位会误判（高位 0x400 出现时含义不同，未完全定位）
- 现状：`state.trapped()` = `v & 0x100`；万一真被拒，由 `switch._switch_blocked` 兜底（换人失败后本场不再换）
- 副作用曾导致：皮卡丘（全变化招）在场时误判束缚 → 跳过所有换人 → 卡在无效出招

### 固定跨图路线（实测通过）
- `route_5_to_6()`：5号道路 → 车站 → 通道顶部 → 车站 → 6号道路
- `route_6_to_5()`：6号道路 → 车站 → 通道底部 → 车站 → 5号道路
- 车站复用：通道上/下门对应 5号/6号道路，出口取决于来源
- 通用跨图寻路（travel_map）不可靠，已删除

### 全局地图坐标（map_coords.py）
- 从连接表 BFS 推算每张地图的全局偏移
- `to_global(map, x, y)` / `to_local` / `map_at`
- 验证：6号道路 (12,39) 和 枯叶市 (24,2) 全局坐标相同（23,97）

### 战斗流程修复（重要）
- 换人界面（turn=4 + 队伍光标）→ 判定 party_option，不是 anim
- 濒死换人：界面顺序 = 原始槽位（0-5），不是 party_order；排除当前 active
- 敌方 0 血 → 按 A 推进（换下一只），上限 8 次防死循环
- 睡眠/冰冻：正常出招（游戏会跳过），不要干等

### 行走/遇敌
- 硬编码路线比通用跨图寻路可靠
- 打完战斗立刻走离草地（防原地连续遇敌）

## 出招内存（2026-11-09 练级实测）

### 地址（已并入 addresses.py）
- **我方场上 BattlePokemon** `0x02023BE4`（结构 **0x58** 字节）：
  - `+0x00` species（实测 大针蜂 15 / 卡咪龟 8 / 大嘴雀 22）
  - `+0x0C` **4 个招式 id（u16）**，与队伍数据解密结果一致
  - `+0x22` 束缚、`+0x4C` status1（原有）
- **敌方场上 BattlePokemon** `0x02023C3C`（= 我方 +0x58）：`+0x00` species，`+0x0C` 4 招
- **`0x02023D4C`**：最近一次行动的招式（敌我共用，敌方出手会覆盖）
- **`0x02023DC4`**：我方本回合使用的招式（敌方行动后仍保留我方值）
- 队伍 PP：`bdata.my_mon()` 解密后 `att[8:12]`，**战斗内实时写回**（出招后 -1），可用 PP 差反推实际招式

### 决策一致性（12 回合，0 不一致）
- 方法：出招前记 4 招 PP → 回合结束看哪招 -1 = 实际出招 → 对比 `decision.choose_move` 的 idx
- 结果：12/12 一致；出招瞬间 D4C 也等于该招 id
- 校验：大针蜂 `[31,116,40,41]`、卡咪龟 `[55,39,145,44]` 与队伍解密完全一致

### 敌方出招采集
- 敌方招式表 = `0x02023C3C + 0x0C`：波波 `[33,28,16,98]`、喇叭芽 `[22,74,35,79]`、喵喵 `[10,45,44,0]`（0 = 空位）
- 实际出手：波波 28 瞪眼 / 16 起风 / 33 撞击（都在其表内）
- 采法：回合内 60-80ms 采样 D4C，出现「不在我方招式表」的 id 即敌方出手

### 采集工具
- `move_probe.py`：10Hz 采样战斗结构原始字节
- `train_probe.py`：练级 + monkeypatch battle_loop，记录决策/PP/D4C（`logs/move_trace-*.jsonl`）
- `probe_enemy.py`：定向用非攻击招逼敌方出招（`logs/enemy_trace-*.jsonl`）

### 出场槽位：species 驱动（2026-11-09 重构）
- 现象：濒死/强制换人后 `active_slot()` 指向倒下的那只，决策读错招式表。实测代码以为 #2 大嘴雀在用「啄」，实际场上 species=8（卡咪龟）打的是水枪 55
- 根因：同一件事有两套映射——濒死界面光标按原始槽位，正常队伍菜单按 `order` 下标，且濒死分支漏更新 order
- 重构：`active_slot()` 以 **`0x02023BE4+0` 的场上 species 为唯一依据**（0.6s 缓存，换人后 `invalidate_field()` 强制重读）；`party_order()` 每次调用都校正 `order[0]`；order 只负责右侧顺序和光标映射，战斗外用 order 兜底
- 效果：换人路径漏更新 order 也会被自动修正（练级复验：18 回合 0 次槽位不同步）
- 测试：`test_switch.py` F/G/H（ensure_active）+ I/J（缓存/无内存兜底）

### 无攻击招卡死（2026-11-09）
- 症状：场上精灵全是变化招（如皮卡丘 影分身/叫声/摇尾巴/电磁波）或 PP 耗尽 → 一直「默认第一招」，打不动，battle_loop 跑满 25 轮 timeout
- 修复：`decision.has_attack_move()` + battle_loop 优先换一只有攻击招的队友（排除自己）；换人失败则本场不再尝试
- 测试：`test_decision.py` F

### 招式表修正（对照实测 id）
- `28` = 撒沙（地面 0）——原误写「挖洞 80」；挖洞是 `91`
- `35` = 缠绕（一般 15）——原误写「摇尾巴 0」
- 补：`10` 抓、`16` 起风、`79` 睡眠粉、`91` 挖洞

## 工程化（2026-11-09 深夜）

### 可观测性
- `battle_loop(on_round=cb)`：每回合格子（决策 idx、4 招、PP、D4C、敌方 species/招式表、slot_ok）
- `probe.Recorder`：订阅回调写 `logs/rounds-*.jsonl`，`summary()` 用 PP 差反推实际出招
- `train.py`：练级 + 观测；`farm.py`：目标等级/场数/时间上限的自动练级
- 旧的 `train_probe.py` / `move_probe.py` 已归档到 legacy；定向抓敌方出招仍可用 `probe_enemy.py`

### 威胁评估（只用于日志，未接入决策）
- `decision.threat_score(enemy_moves, my_types)`：敌方招式表里「威力×克制」最大值
- 实测：喇叭芽 `[22,74,35,0]` 打水属性 = 70（藤鞭 35×2）
- 接入决策的方案：观测几场后再给 `choose_switch` 加权，避免直接改动胜率

### 招式表 Gen3 修正（再抓 3 处）
- `22` 藤鞭：Gen1-5 是 **35**（Gen6+ 才 45）
- `56` 水炮：**120**（原来误写成「泡沫 40」，56 根本不是泡沫）
- `145` 泡沫：Gen1-5 是 **20**（Gen6+ 才 40）
- `test_moves.py` 锁定 26 条常用招式 + 8 个物种属性，防止手抄再错

### 超时兜底
- `battle_loop` 轮次用完仍卡着：`close_menu()`，还在战斗就 `run_away()`，避免卡死子菜单

## 指令层 intent（2026-11-10 实测）

### 设计
- 目标语义，不下具体招：`prolong` / `no_kill` / `flee` / `only_class`（白名单）
- 生命周期：`ttl=None` 本场有效；否则每回合 -1，归零自动移除（audit 记 expire）
- 优先级：guard(100) > flee(80) > preserve(60) > no_kill(40) > only_class(30) > prolong(20)
- 安全护栏（不可被覆盖）：自身 HP < hp_floor(默认 25%) → prolong/no_kill 自动失效；HP < 15% → 强制追加 guard flee
- 审计：submit / clear / expire / dropped_low_hp / safety_flee 全记录
- 注入时机：`battle_loop` 每回合 `intent.effective(me, foe)`；回合结束 `intent.tick()`

### 实测（大嘴雀 vs 波波 Lv16）
- 注入 `prolong`（ttl=3，hp_floor=0）后：回合 2、3 选「瞪眼（变化招）」拖回合
- ttl 到期（第 4 回合）：自动恢复默认策略「啄」（攻击招）
- audit：`submit` → `expire` 完整
- 注意：`hp_floor` 默认 25% 会让低血时 prolong 失效（这是护栏，不是 bug）

### 测试
- `test_intent.py`：A-I（生命周期/替换/低血降级/自动脱战/优先级/决策接入）
- `test_battle_loop.py` K/L：flee 指令触发逃跑、prolong 指令选变化招

### 指令层 HTTP 与 no_kill 增强（2026-11-10）
- `POST /api/intent`（body: kind/params/ttl/source）→ 返回 id；`GET /api/intent` 查 active+audit；`POST /api/intent/clear` 清空
- `no_kill`：敌方 HP 低于阈值且当前没有变化招 → 换一只有变化招的队友拖回合（每场上限 2 次）
- `probe.summary` 增加 `intent_rounds`：每回合带了哪些指令
- 测试：`test_battle_loop` M/N（无变化招换人 / 有变化招原地拖）

### 队伍数组与换人（实测 2026-11-10）
- 普通换人（`switch_from_main`）**不改真实队伍数组** `0x02024284`，只改界面顺序（进程内 order）
- `active_slot()` 的 species 驱动工作正常（实测 active 1 → 3）
- 战斗中数组顺序稳定（before/encounter/round/after 完全一致）
- 03:42 曾观察到一次槽位顺序变化，未复现，标记“待观察”（疑似濒死换人/战后学招界面瞬态）
- 教训：迁移模块后必须跑实机；`learn.py` 迁出时漏了 `snapshot`、`advance_dialog`，已补 `test_learn.py`

## 统一日志（2026-11-10）

### 标准
- 文件：`logs/run-YYYYMMDD.jsonl`（每行一个事件），控制台仍输出 `[HH:MM:SS] mod event k=v`
- 字段：`ts / session / level / mod / event / data`
- `mod` 用模块名，`event` 用动词，错误以 `ERROR:` 开头；嵌套只用于 party/foe 这类快照
- 保留 7 天，按天滚动；`session` 区分同日多次运行

### 查询
```
python3 logq.py --mod switch
python3 logq.py --event 换人 --limit 20
python3 logq.py --grep got=2 --json
```

### 新增的状态记录
- `on_round` 的回合数据带 `party`（6 只的 slot/species/lv/hp）
- 换人日志带 `order_before` / `order_after`（界面顺序）
- 学招事件改为 `learn/forget_event`，不再写独立 txt
- `probe/round` 摘要进主日志；完整回合数据仍在 `logs/rounds-*.jsonl`（按场）

### 用途
类似“03:42 槽位瞬态”这种问题，事后可查 `party` 相邻两行 + `switch order_before/after` + `state` 变化，不再只靠手动读一次。

### 指令注册制（2026-11-10）
- `intent.register_kind(kind, priority, compile_fn)`：把指令编译成统一约束
- 约束：`move_mode(status/lowest) / allowed_types / force_flee / switch_if_no_status`
- 决策层 `choose_move(cons=...)` 与主循环只认约束，**不再判断 kind**
- 新增指令 = 注册 + 一个 compile 函数；`test_intent` J 验收“只注册即可生效”
- 旧接口 `choose_move(intents=...)` 保留，内部自动编译（兼容）

### 跨进程指令（2026-11-10）
- `intent.use_file_store()`：JSON 文件 + fcntl 锁，默认路径 `logs/intent.json`
- `api_server` / `farm` / `train` 启动时自动启用；`active()/effective()` 会先刷新
- 实测：8081 注入 prolong → 另一进程读到 `[('prolong', 3, 'ai')]`
- 注意：并发写是 last-writer-wins（写少读多场景够用），跨进程 tick 可能覆盖，后续需要再加合并

### AI 闭环（2026-11-10 实测）
- 链路：`ai_agent.py` → `GET /api/state` → `POST /api/intent` → `POST /api/task farm` → `GET /api/intent`
- `api_server` 的 `_run_battle()` 挂 `probe.Recorder`，结果写 `_battle["last"]`
- 实测：注入 prolong（ttl=5），战斗 2 回合 `intent_rounds={'prolong': 2}`，`match=2`，回读 `win`
- 注意：`/api/act fight` 只在已遇敌时有意义；遇敌+打用 `/api/task farm`

### no_kill 压血（2026-11-10）
- `move_mode=chip`：低伤招（`power*hits*eff <= 敌方HP*0.8`）优先压血；没有安全招退回变化招
- `prolong` 仍用 `status`（只拖局面，不压血），两者语义分开
- 实测：AI 注入 no_kill → 1 回合 win，intent_rounds 记录生效
- 威胁评估仍只写日志，未接入决策（避免无观测数据就改选招/换人）

### 寻路改进（2026-11-10）
- 对外坐标统一为**地块**（`state.to_tile/to_raw`），raw 只在底层读写用
- `_blocked` 改 dict+时间戳，TTL 600s；NPC 格不记（会移动）
- 到达后二次读坐标确认，防瞬态误判
- 只剩 `pathfind.goto` 一个执行入口；`nav` 只保留 BFS 规划
- 待办：跨图 A*（map_links + map_coords 目前仍是孤立的）

### 跨图 A*（2026-11-10）
- `map_route.plan(src,dst)`：连接表 + 全局坐标曼哈顿启发；复用房间边 cost+3
- `map_route.travel_map(dst,x,y)`：逐段 `pathfind.travel(出口)` → 朝外一步 → 校验换图
- 实测：6号 → 枯叶市 单段成功
- 限制：车站/通道是“复用房间”，同一出口按来源通向不同地图；连接表边不完整，多段路线需手动分段（先到 6号/5号，再调固定路线）
- 后续：补全通道边（带“来源”条件）后，A* 才能真正覆盖全图

### 寻路实测（2026-11-10）
- 枯叶市精灵中心门口 (15,8) -> 6号道路草地 (14,33)：**23.9s**
  - 出门 + 北门出界：6.9s
  - 6号入口 -> 草地：17s（NPC 在 (13,33)/(13,32) 挡路，绕行）
- 遇敌不计入；一场战斗约 +100s（8 回合）
- 修复：连续撞同一格 3 次 -> 临时记 60s 障碍（NPC 可绕），不再直接放弃

### 队伍数组顺序的真相（2026-11-10 截图 + 实机）
- **战斗主菜单**（未开队伍菜单）：`0x02024284` = 原始队伍顺序，active 可能在任意槽
- **队伍菜单打开**（party_option）：数组 = 界面顺序，active 固定在 slot0，右侧按界面顺序
- 所以换人光标必须按 **species 身份**定位：打开菜单前解析 species，菜单内再按 species 找光标
- 结论：
  - `active_slot()` 用 species 驱动（`0x02023BE4`）
  - `party_order()` 由 active 推导，仅用于主菜单
  - 换人成功判据 = 场上 species 变成目标（`turn==4` 也会出现在菜单里）
- 组件：`switch._cursor_for_species` / `_wait_species` / `_wait_array_stable`
