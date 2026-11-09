"""指令层（intent）：AI/用户下「目标」，决策层决定「怎么做」。

与 bridge.py（场景裁剪）互补：bridge 是信息流向决策层，这里是控制流。

kind（白名单）：
  prolong     尽量拖回合：优先变化招 / 最低威力，避免击杀
  no_kill     别打死：敌方 HP 低于阈值时停手（换变化招/低威力）
  flee        尽快脱战：逃跑优先（失败交给现有兜底）
  only_class  只用某类招：params={"type": "水"} / {"power": 0}
  preserve    保血：低血换人（复用 battle_loop 现有逻辑，仅作标记）

生命周期：ttl=None 表示本场有效；否则每回合 -1，归零自动移除。
安全护栏（不可被指令覆盖）：
  - 自身 HP < hp_floor（默认 25%）时，prolong/no_kill 自动失效
  - 自身 HP < 15% 时强制追加 guard flee
冲突：按 priority 排序（guard > flee > preserve > no_kill > only_class > prolong）。
审计：submit/drop/expire/safety 全部记入 audit()。
"""
import time
import uuid
from dataclasses import dataclass, field

PRIORITY = {
    "guard": 100, "flee": 80, "preserve": 60,
    "no_kill": 40, "only_class": 30, "prolong": 20,
}

_store = []          # List[Intent]
_audit = []          # List[dict]
_seen = set()        # 去重 (intent_id, event)


@dataclass
class Intent:
    kind: str
    params: dict = field(default_factory=dict)
    ttl: int | None = None
    priority: int | None = None
    source: str = "user"
    id: str = ""

    def __post_init__(self):
        if self.kind not in PRIORITY:
            raise ValueError(f"未知指令: {self.kind}")
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if self.priority is None:
            self.priority = PRIORITY[self.kind]


def _log(intent, event, extra=None):
    key = (intent.id, event)
    if key in _seen:
        return
    _seen.add(key)
    _audit.append({
        "t": round(time.time(), 3), "id": intent.id, "kind": intent.kind,
        "event": event, "source": intent.source, **(extra or {}),
    })


def submit(intent):
    """注入指令；同 kind 的旧指令被替换，返回新 id。"""
    _store[:] = [i for i in _store if i.kind != intent.kind]
    _store.append(intent)
    _log(intent, "submit")
    return intent.id


def clear(intent_id=None):
    """清空全部或单条。"""
    if intent_id is None:
        for i in list(_store):
            _log(i, "clear")
        _store.clear()
    else:
        for i in list(_store):
            if i.id == intent_id:
                _store.remove(i)
                _log(i, "clear")
                break


def active():
    return list(_store)


def tick():
    """回合结束调用：ttl 递减，归零移除。"""
    for i in list(_store):
        if i.ttl is None:
            continue
        i.ttl -= 1
        if i.ttl <= 0:
            _store.remove(i)
            _log(i, "expire")


def _hp_ratio(me):
    mhp = (me or {}).get("mhp") or 0
    if not mhp:
        return 1.0
    return (me or {}).get("hp", 0) / mhp


def effective(me, foe=None, force=False):
    """过护栏 + 排序后返回本回合生效的指令。

    force=False 时复用 0.3s 内的结果，避免同一回合重复计算；force=True 强制重算。
    """
    now = time.time()
    if not force and _cache["t"] and now - _cache["t"] < 0.3 and _cache["me"] == id(me):
        return list(_cache["out"])
    hp = _hp_ratio(me)
    out = []
    for it in list(_store):
        floor = it.params.get("hp_floor", 0.25)
        if it.kind in ("prolong", "no_kill") and hp < floor:
            _log(it, "dropped_low_hp", {"hp": round(hp, 3)})
            continue
        out.append(it)
    if hp < 0.15 and not any(i.kind == "flee" for i in out):
        g = Intent("flee", {"auto": True}, ttl=1, priority=PRIORITY["guard"],
                   source="guard")
        _log(g, "safety_flee", {"hp": round(hp, 3)})
        out.append(g)
    out.sort(key=lambda i: -i.priority)
    _cache.update(t=now, me=id(me), out=list(out))
    return out


_cache = {"t": 0.0, "me": None, "out": []}


def audit():
    return list(_audit)


def reset():
    """测试用：清空全部状态。"""
    _store.clear()
    _audit.clear()
    _seen.clear()
    _cache.update(t=0.0, me=None, out=[])
