# Pokemon FireRed 自动化工具

通过 RetroArch 的 UDP 接口读取游戏内存、注入按键，实现宝可梦（火红中文版）的自动化操作。

**运行环境**：Android 手机 + proot Ubuntu + RetroArch（游戏在前台或分屏）

---

## 快速开始

```bash
cd /root/workspace

# 跑全部测试（19 个）
python3 run_tests.py

# 读当前游戏状态
python3 -c "import info,state; print(info.scene(), state.coords())"

# 自动打一场（遇敌后调用）
python3 -c "import auto_battle; auto_battle.battle_loop()"

# 起点到终点自动寻路（同地图）
python3 -c "import pathfind; print(pathfind.goto(10,15))"

# 启动外部 API（端口 8081）
python3 api_server.py 8081

# 启动下屏网页（端口 8080）
python3 state_server.py 8080
```

---

## 架构

四层，单向依赖：

```
┌─────────────────────────────────────────┐
│  info.py        信息层：读游戏状态        │
│    scene() / coords() / snapshot() /    │
│    facing() / consistent_snapshot()     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  bridge.py      中间层：判定+裁剪+分发    │
│    register_scene(name, fields, handler)│
└──────────────┬──────────────────────────┘
               │ handlers.py（场景处理器）
┌──────────────▼──────────────────────────┐
│  decision_*.py  决策层：纯逻辑，不碰内存    │
│    decision_battle.py  战斗（出招/换人）   │
│    decision_map.py     地图（转身/走路）   │
│    decision.py         门面（兼容旧接口）  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  action.py      执行层：按键              │
│    walk() / use_move() / tap_a() / ...  │
└─────────────────────────────────────────┘
```

**核心原则**：
- 信息层只读，决策层纯函数（方便离线测试），执行层只按键
- 每层不依赖上层实现细节

---

## 模块说明

### 信息层

| 文件 | 职责 |
|---|---|
| `memory.py` | UDP 内存读写（`rd`） |
| `addresses.py` | 地址表（全部实测过） |
| `state.py` | 状态函数（坐标/战斗/对话/菜单/朝向） |
| `terrain.py` | 地图数据（地形/草地/NPC/门），带缓存 |
| `info.py` | 场景识别 + 一致性快照 + 扩展钩子 |

### 中间层 & 决策

| 文件 | 职责 |
|---|---|
| `bridge.py` | 注册制中间层：场景 → 字段裁剪 → 决策分发 |
| `handlers.py` | 各场景处理器（battle/map/dialog/choice） |
| `decision_battle.py` | 战斗决策：出招/换人/首发/克制 |
| `decision_map.py` | 地图决策：转身/走路/草里降频 |
| `decision.py` | 门面（`from decision_battle import *` 兼容） |

### 执行层

| 文件 | 职责 |
|---|---|
| `action.py` | 按键动作（含按住 B 跑步） |
| `ra.py` | UDP 按键注入（`press`） |
| `nav.py` | 寻路（BFS + 转弯惩罚） |

### 组合层

| 文件 | 职责 |
|---|---|
| `pathfind.py` | `goto` / `travel`（遇敌自动打） |
| `switch.py` | 换人（队伍顺序/光标映射） |
| `watchdog.py` | 看门狗 + 等回合完成 |
| `battle_loop.py` | 战斗主循环 |
| `auto_battle.py` | 门面 |
| `bdata.py` | 宝可梦数据表（招式/属性/克制） |
| `encounter.py` | 遇敌 |

### 工具

| 文件 | 职责 |
|---|---|
| `state_server.py` | 下屏网页服务（8080） |
| `api_server.py` | 外部 API（8081） |
| `mapdraw.py` | 单地图可视化（碰撞/树/栅栏/门/路径）|
| `map_links.py` / `map_links_vis.py` | 地图连接记录 + 连接图 |
| `map_coords.py` | 全局地图坐标系（多地图统一坐标）|
| `track_route.py` | 记录用户手动操作的坐标轨迹 |
| `log.py` | 全模块日志（控制台 + 文件）|
| `run_tests.py` | 一键测试入口 |

---

## 扩展方法

### 加一个新场景（比如商店）

```python
# 1. 写处理器（handlers.py）
def handle_shop(data):
    return {"action": "buy", "why": f"买 {data.get('item')}"}

# 2. 注册（handlers.register_all 里）
bridge.register_scene("shop", ("item",), handle_shop)
```

核心 `bridge.py` 一行不用改。

### 换一种决策策略（比如换出招逻辑）

```python
import decision
decision.set_move_strategy(lambda mon, enemy_types: (2, "我的策略"))
```

### 加一个新的信息检测

```python
import info
info.register_scene("my_state", my_detector, priority=50)
```

---

## 测试

```bash
python3 run_tests.py          # 全部
python3 run_tests.py battle   # 只跑含 battle 的
```

测试文件按模块划分（`test_info.py` / `test_decision.py` / ...），全部离线运行，不碰实机。

---

## 关键机制

| 机制 | 说明 |
|---|---|
| **按住 B 跑步** | `walk` 时同时按住 B，每格 0.21s（步行 0.45s） |
| **执行闭环** | 按 A 后检查 turn 是否变化，确认出招生效 |
| **看门狗** | 连续 12 轮状态无变化 → 按 A，再 3 轮 → 按 B |
| **一致性快照** | 读前读后对比坐标/回合，防读到一半状态变了 |
| **地图缓存** | 同地图不重读 1920 字节地形数据 |
| **转弯惩罚寻路** | 同样步数优先少转弯 |

---

## 文档索引

| 文件 | 内容 |
|---|---|
| `README.md` | 本文档：架构、模块、扩展、测试 |
| `NOTES.md` | 技术笔记：地址表、实测数据、踩坑记录 |
| `HANDOFF.md` | 会话交接：当前游戏状态、待办事项 |

---

## 版本与变更

- **版本规则**：日期版 `YYYY.MM.DD-N`，git tag 为 `vYYYY.MM.DD-N`
- **收口流程**：每批“实机验证通过” → CHANGELOG 记一条 → 打 tag
- **commit 前缀**：`feat:` / `fix:` / `refactor:` / `docs:` / `test:`
- **生成草稿**：`python3 changelog.py [since]`（按前缀归类到 CHANGELOG）

## 注意事项

1. **游戏必须在前台或分屏**：后台会暂停，读不到内存
2. **按键注入有风险**：脚本被 kill 时可能按键卡住（`ra.py` 有三重释放保护）
3. **换首发功能有 bug**：`_lead_enabled` 默认关闭（见 HANDOFF）
4. **测试用 `legacy/` 目录**：旧实验文件都在那里，可参考但别引用
