# 工具使用手册（TOOLS）

> 面向接手会话：每个模块/脚本的用途、怎么调用、注意事项。
> 配套阅读：`docs/history/ARCHITECTURE.md`（分层与 import 关系）、`docs/history/NOTES.md`（地址与实测结论）。

## 0. 环境前提

- RetroArch（mGBA 核心）+ 游戏**必须前台**（后台会暂停，内存读不到）
- UDP 通道：读内存 `127.0.0.1:55355`，按键 `127.0.0.1:55400`
- 所有命令在 `/root/workspace` 下执行
- 测试全离线：`python3 run_tests.py`（当前 **29/29**，即 29 个 `test_*.py`；`run_tests.py` 按文件计数）
- 模拟器后端：`EMU_BACKEND=native` 走 NativeEmu 的 TCP 桥（见第 12 节），不设则走上面的 RetroArch 通道

---

## 1. 底层通信

### memory.py
```python
import memory
data = memory.rd(0x02024284, 100)  # 返回 bytes
```
- 单次读上限 0x1000，超过自动分块（大地图 54×69 依赖此修复）
- 读失败返回已读到的部分；调用方要检查 `len()`

### ra.py
```python
import ra
ra.press("a", 0.3)        # a/b/start/select/up/down/left/right/l/r/x/y
ra.press("up", 0.06)      # 只转身不走路
ra.release_all()          # 异常退出时自动松开（已注册 atexit/signal）
```
- 按键是 UDP 事件，**不保证**游戏已处理；需要随后读状态确认

### addresses.py
- 地址表（唯一真源）；改地址只改这里 + `docs/history/NOTES.md`

---

## 2. 信息层（只读）

### state.py
```python
import state
state.coords()        # 原始坐标 (x,y)
state.to_tile(p)      # 地块坐标 = 原始 - 7
state.to_raw(t)       # 反算
state.in_battle()     # bool
state.in_dialog()     # bool
state.turn_state()    # 0 开场 / 1 主菜单 / 2 招式 / 4 动画
state.wait_turn(4, timeout=8)
state.menu_kind()     # battle_main/battle_moves/party_option/choice/...
state.party_menu_open()
state.status_flags(0) # 异常状态：睡眠/中毒/麻痹/灼伤/冰冻
state.snapshot()      # 一致性快照（scene/battle/dialog/coords/turn）
```

### bdata.py
```python
from bdata import my_mon, enemy_info
m  = my_mon(0)      # {species,lv,hp,mhp,moves,pp,types}
e  = enemy_info()   # {species,lv,hp,mhp,types,moves}
```
- 空槽位返回零值（species=0），用 `hp <= 0` 过滤
- 战斗主菜单时 `my_mon(i)` = 原始队伍顺序；菜单打开时 = 界面顺序（**用 species 做身份**）

### terrain.py
```python
import terrain
addr, w, h, vals = terrain.load()   # vals = 地块数组（u16）
terrain.walkable(vals, w, x, y)     # 可走？（含树苗 317 / 覆盖层）
terrain.is_grass(vals, w, x, y)
terrain.npc_tiles()                 # 当前地图 NPC 占格集合
terrain.mark_blocked(x, y)          # 记录「数据可走、实际走不动」
```
- 定位：`gMapHeader`(0x02036DFC) 优先；指针非法时回退 EWRAM 扫描（约 4s，随后缓存）
- 覆盖层落在 `maps/override_<addr>.json`，下次自动绕开
- 已知限制：数据「不可走但实际可走」的格发现不了

### info.py
```python
import info
info.scene()      # map / battle_main / battle_intro / party_option / dialog / ...
info.context()    # 场景 + 战斗 + 队伍 的组合快照
```

---

## 3. 寻路

### nav.py（纯 BFS，可离线测）
```python
import nav
path = nav.bfs_turns(vals, w, h, start, goal, blocked)
```
- 转弯惩罚 1.6；`can_step` 处理高度层：同层可走，**单向坎允许高→低（差 1~2）**，反向禁止

### pathfind.py（执行层）
```python
import pathfind
pathfind.goto(x, y)          # 走到地块坐标；返回 True/warped/battle/dialog/False
pathfind.travel(x, y)        # 同上 + 遇敌自动打 + 换图支持
pathfind.route_5_to_6()      # 固定跨图路线（实测）
pathfind.route_6_to_5()
```
- 卡点：连续 3 段无进展会记障碍（TTL 60s）并重规划
- 撞墙/NPC 会调用 `terrain.mark_blocked` 持久化

### map_links.py
```python
import map_links
map_links.add_link(0x82e55d0, (6,52), 0x8320808, (7,10), side="up")
map_links.links_from(0x82e55d0)
```

### map_route.py（跨图 A*）
```python
import map_route
map_route.plan(0x82e9260, 0x82df30c)   # 规划跨图路线
map_route.travel_map(0x82df30c, 31, 37) # 执行（含通道固定路线）
```
- 6号↔5号/华蓝 走 `FIXED` 实测路线；其他区域靠 map_links 数据

---

## 4. 战斗

### action.py（只按键）
```python
import action
action.walk("up", 3)          # 走 n 格（0.09s/格）
action.tap_a(); action.tap_b()
action.open_move_menu(); action.use_move(idx)
action.advance_dialog()       # 连按 A 直到对话结束
action.run_away()
action.pick_and_switch(...)   # 战斗主菜单换人
```

### switch.py（槽位/换人）
```python
import switch
switch.active_slot()          # 当前出场槽位（species 驱动）
switch.party_order()          # [active] + 其余（仅主菜单语义）
switch.switch_from_main(1)    # 主菜单换第 1 槽
switch.do_switch(species, ...) # 按 species 换人
switch.ensure_active()        # 濒死换人
```
- 换人成功判据 = 场上 species 变成目标（`_wait_species`）
- 光标按 species 在**当前数组**定位（菜单内外顺序不同）

### decision.py / decision_battle.py（纯函数）
```python
import decision
decision.choose_move(me, foe, cons=None, intents=None)
decision.score_switch(mon, enemy)      # v2：预计回合差 + 敌方招式
decision.should_flee(me, foe, ...)
decision.should_switch_opening(party, enemy, active)
```
- `cons` 来自 intent 编译；`intents` 影响过滤器
- 开场换人：敌比我低 8 级以上不换（等级压制）

### battle_loop.py
```python
import battle_loop
battle_loop.battle_loop(max_rounds=12, verbose=True, on_round=cb)
```
- `on_round(rec)`：每回合观测（probe.Recorder 订阅）
- 结束原因：win / win_levelup / fainted / timeout / fled

### watchdog.py
- `wait_round_end()`：等 turn 回 1，同时按 A 推动画

---

## 5. 任务层

### farm.py（自动练级）
```bash
python3 farm.py 10 20 1800
# 场数 / 目标等级(可省) / 秒上限
```

### train.py（练级 + 回合观测）
```bash
python3 train.py 1 180     # 场数 / 秒上限；回合写入 logs/rounds-*.jsonl
```

### encounter.py
```python
import encounter
encounter.find_encounter()   # 找草 → 走进去 → 遇敌
```

### learn.py
```python
import learn
learn.learn_moves_guard()    # 升级学招对话处理
```

### intent.py（指令层）
```python
import intent
intent.use_file_store()      # 跨进程（logs/intent.json）
i = intent.submit("prolong", {"ttl": 5}, ttl=5, source="ai")
intent.compile_all(me, foe)   # → Constraints / modifiers
intent.effective(me, foe)
intent.audit()
```
- kind 白名单：`prolong` / `no_kill` / `flee` / `only_class`

---

## 6. 观测与日志

### log.py
```python
import log
log.info("mod", "event", {"k": 1})   # 统一 JSONL：logs/run-YYYYMMDD.jsonl
```

### logq.py（查询）
```bash
python3 logq.py --mod pathfind --event goto --since 1h
python3 logq.py --level ERROR --grep 失败 --json
```

### probe.py（回合记录器）
```python
from probe import Recorder
battle_loop.battle_loop(on_round=Recorder())
```

### probe_enemy.py / move_probe.py
```bash
python3 probe_enemy.py 3      # 逼敌方出招 3 场
python3 move_probe.py 90      # 10Hz 采样战斗结构原始字节
```

---

## 7. HTTP 服务

### api_server.py
```bash
python3 api_server.py 8081
```
- `GET /api/state`：场景/坐标/队伍
- `POST /api/intent` / `GET /api/intent` / `POST /api/intent/clear`
- `POST /api/task` `{name:"farm", args:{battles}}`
- `GET /api/intent` 回读 `last_battle`

### state_server.py
```bash
python3 state_server.py 8080   # 下屏网页：状态 + 动作按钮
```

---

## 8. 地图工具

```bash
python3 mapdraw.py 12,39        # 当前地图可视化（可带目标格）
python3 map_coords.py           # 全局坐标（BFS 推算偏移）
python3 map_links_vis.py out.png # 地图连接图
python3 track_route.py          # 记录手动坐标轨迹（logs/route-*.jsonl）
```

---

## 9. 版本与测试

```bash
python3 run_tests.py            # 全部 24 个
python3 run_tests.py pathfind   # 按名字过滤
python3 changelog.py            # 生成 CHANGELOG 草稿
```

---

## 10. legacy/ 与实验代码

- `legacy/`：旧实验脚本，**不要 import**
- `bridge.py` / `handlers.py`：注册制中间层，未接入主链路
- `auto_battle.py`：`battle_loop` 的兼容门面

---

## 11. 常见坑（接手必读）

1. 换人：菜单内外队伍数组顺序不同，**身份用 species**
2. `turn==4` 在菜单里也会出现，别用它判断战斗结束
3. 大地图（>0x1000 字节）必须分块读
4. `gMapHeader` 指针可能是垃圾值 → 靠 EWRAM 扫描兜底 + 缓存
5. 单向坎：高→低可跳，反向不行；树苗 317 需居合斩
6. 覆盖层（`maps/override_*.json`）是实测校正，别随手删

---

## 12. NativeEmu（Android 模拟器 + TCP 桥）

**是什么**：`native-emu/` 里的自研双屏 GBA 模拟器（mGBA 内核 + Kotlin/Compose + NDK）。上屏玩游戏，下屏是控制台；自动化通过本机 TCP 桥读写内存和按键。

### 12.1 Python 侧客户端

```bash
# 切到原生后端（默认走 RetroArch UDP）
export EMU_BACKEND=native
python3 -c "import memory; print(memory.rd(0x02024284, 32).hex())"
```

- `emu_bridge.py`：`rd/wr/press/frame/ping`，端口 `127.0.0.1:55401`
- `memory.py` / `ra.py`：按 `EMU_BACKEND` 分派，其余代码不用改
- 桥是行协议，**单连接串行**；一次只发一条，别并发

### 12.2 桥命令（行协议）

| 命令 | 返回 | 说明 |
|---|---|---|
| `ping` | `pong` | 探活 |
| `read <addrHex> <len>` | `ok <hex>` | 读内存，地址如 `2024284` |
| `write <addrHex> <hex>` | `ok` | 写内存 |
| `press <mask> <ms>` | `ok` | A=1 B=2 SELECT=4 START=8 RIGHT=16 LEFT=32 UP=64 DOWN=128 R=256 L=512 |
| `frame` | `ok <n>` | 当前帧号 |
| `status <json>` | `ok` | 外部推送下屏状态（map/x/y/team/battle） |

### 12.3 构建与发布（本机不能编译）

手机是 arm64 + proot，NDK/aapt2 是 x86_64，**本地一定编不过**，只能走 CI：

```bash
git push                                   # 改 native-emu/** 触发 .github/workflows/build-native-emu.yml
# CI 跑 :app:testDebugUnitTest + :app:assembleDebug，产物 artifact app-debug
GITHUB_TOKEN=xxx python3 publish_release.py build-<sha>   # 构建失败会拒绝发布
```

- 签名固定 `native-emu/app/keystore.jks`，口令在 `keystore-info.txt`（不进仓库）；换签名会 `INSTALL_FAILED_UPDATE_INCOMPATIBLE`
- `publish_release.py` 只发**最新一次成功构建**的 APK；构建红的时候别手动补发

### 12.4 日志位置（排查第一步）

| 文件 | 内容 |
|---|---|
| `/sdcard/Download/emu_native.log` | 内核 init 步骤、ROM 加载 |
| `/sdcard/Download/service.log` | 前台服务/保活 |
| `/sdcard/Download/bridge.log` | TCP 桥连接 |

### 12.5 改 Kotlin 前的三个坑

1. 缺 Compose import 是最常见的 CI 红（如 `detectTapGestures` 要 `androidx.compose.foundation.gestures.*`），**改完先在本地 grep 一遍 import**
2. 构建失败时**别用空提交反复触发**，先看 CI 的 `e: file://…` 行定位哪个文件哪一行
3. 内核侧坑（编译宏、初始化顺序、skipBios、RGB565）见 `native-emu/README.md`，别在这里改
