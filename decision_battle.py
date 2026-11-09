"""战斗决策模块（纯逻辑）。

由中间层在「战斗场景」下激活：出招 / 换人 / 选首发。
"""
import sys
sys.path.insert(0, "/root/workspace")
import log
from bdata import MOVES, TYPE_CHART, MULTI_HIT

_move_strategy = None
_switch_strategy = None


def set_move_strategy(fn):
    """替换选招策略：fn(mon, enemy_types) -> (招式序号, 说明)。None 恢复默认。"""
    global _move_strategy
    _move_strategy = fn


def set_switch_strategy(fn):
    """替换换人策略：fn(party, enemy) -> 槽位。None 恢复默认。"""
    global _switch_strategy
    _switch_strategy = fn


def current_strategies():
    return {"move": _move_strategy, "switch": _switch_strategy}


def move_effect(move_id, enemy_types):
    """这个招式对敌方属性的克制倍率。"""
    info = MOVES.get(move_id)
    if not info:
        return 1.0
    _, typ, _ = info
    eff = 1.0
    for et in (enemy_types or ()):
        eff *= TYPE_CHART.get((typ, et), 1.0)
    return eff


def best_damage_effect(mon, enemy_types):
    """这只宝可梦对敌方最有效的**攻击**倍率（只算有威力的招）。"""
    best = 0.0
    for mid in mon.get("moves", []):
        info = MOVES.get(mid)
        if not info or info[2] <= 0:
            continue
        best = max(best, move_effect(mid, enemy_types))
    return best if best > 0 else 1.0


def choose_move(mon, enemy_types=None):
    """返回 (招式序号 0-3, 说明)。优先克制，其次威力；PP=0 跳过。"""
    if _move_strategy is not None:
        return _move_strategy(mon, enemy_types)
    best = None
    for i, (mid, pp) in enumerate(zip(mon["moves"], mon["pp"])):
        info = MOVES.get(mid)
        if not info or pp <= 0:
            continue
        name, typ, power = info
        if power <= 0:
            continue
        eff = move_effect(mid, enemy_types) if enemy_types else 1.0
        hits = MULTI_HIT.get(mid, 1.0)
        score = power * hits * eff
        if best is None or score > best[0]:
            best = (score, i, name, typ, power, eff, hits)
    if best is None:
        return 0, "没有可用攻击招式，默认第一招"
    hits = best[6]
    ht = f" ×{hits:g}段" if hits > 1 else ""
    return best[1], f"{best[2]}（{best[3]} 威力{best[4]}{ht} 克制x{best[5]:g}）"


def _takes_damage_from(mon_types, enemy_types):
    """敌方属性打我方属性的倍率（>1 表示被克制）。"""
    dmg = 1.0
    for et in (enemy_types or ()):
        for mt in (mon_types or ()):
            dmg *= TYPE_CHART.get((et, mt), 1.0)
    return dmg


def score_switch(mon, enemy):
    """换人目标评分（越高越好）。

    评分构成：
      - 攻击：对敌人最好的克制倍率（eff 0~4）x 10
      - 防御：敌人打我方的倍率（takes 0~4）x -8
      - 等级：比敌方高加分，低扣分
      - 血量：健康度加分
    """
    enemy_types = (enemy or {}).get("types", ())
    enemy_lv = (enemy or {}).get("lv", 0)
    eff = best_damage_effect(mon, enemy_types)
    takes = _takes_damage_from(mon.get("types", ()), enemy_types)
    lv = mon.get("lv", 0)
    hp_ratio = (mon.get("hp", 0) / mon["mhp"]) if mon.get("mhp") else 0
    score = eff * 10 - takes * 8
    score += (lv - enemy_lv) * 0.5
    score += hp_ratio * 5
    return score


def choose_switch(party, enemy, exclude_slot=None):
    """选换人目标（评分制）：返回队伍槽位。

    party: [{slot, lv, hp, mhp, species, types, moves, pp}, ...]
    enemy: {lv, hp, types}
    规则：给每个可用成员打分（克制/被克/等级/血量），选最高分。
    """
    if _switch_strategy is not None:
        return _switch_strategy(party, enemy)
    cands = [m for m in party
             if m and m.get("hp", 0) > 0 and m.get("slot") != exclude_slot]
    if not cands:
        return None
    best = max(cands, key=lambda m: score_switch(m, enemy))
    log.debug("decision", "choose_switch", slot=best["slot"],
              score=round(score_switch(best, enemy), 1), enemy=enemy.get("types"))
    return best["slot"]


def should_flee(me, enemy, party, hp_threshold=0.15, lv_gap=8,
                enemy_species=None, trapped=False, trainer=False):
    """是否该逃跑（野怪）。

    先判断能不能逃：
      - 训练家战 → 不能逃
      - 敌方特性禁逃（小磁怪/地鼠等）→ 不能逃
      - 我方被束缚（trapped）→ 不能逃
    """
    if trainer or trapped:
        return False
    if enemy_species is not None:
        try:
            from bdata import PREVENT_ESCAPE_SPECIES
            if enemy_species in PREVENT_ESCAPE_SPECIES:
                return False
        except Exception:
            pass
    return bool(_should_flee_reason(me, enemy, party, hp_threshold, lv_gap))


def _should_flee_reason(me, enemy, party, hp_threshold=0.15, lv_gap=8):
    """是否该逃跑（野怪）。

    条件（任意一个）：
      1. 敌人等级比我高 lv_gap 以上（打不过）
      2. 我方血量 < hp_threshold（避免濒死）
      3. 我方被克制 ≥ 2x 且血量 < 35%
    返回 True/False。
    """
    if not me or not enemy:
        return False
    my_lv = me.get("lv", 0)
    enemy_lv = enemy.get("lv", 0)
    hp_ratio = (me.get("hp", 0) / me["mhp"]) if me.get("mhp") else 1.0
    if enemy_lv >= my_lv + lv_gap:
        return True
    if hp_ratio <= hp_threshold:
        return True
    takes = _takes_damage_from(me.get("types", ()), enemy.get("types", ()))
    if takes >= 2.0 and hp_ratio < 0.35:
        return True
    return False


def should_switch_opening(party, enemy, active, margin=1.0):
    """开场换人：队首评分低于最佳候选 margin 以上就换。

    返回目标槽位或 None。
    """
    if not enemy or active is None:
        return None
    m = next((x for x in party if x and x.get("slot") == active), None)
    if not m:
        return None
    target = choose_switch(party, enemy, exclude_slot=active)
    if target is None or target == active:
        return None
    t = next((x for x in party if x and x.get("slot") == target), None)
    if t is None:
        return None
    if score_switch(t, enemy) > score_switch(m, enemy) + margin:
        return target
    return None


def choose_lead(party, enemy):
    """选最有利的首发：有克制招的优先（乘数高→等级高），没有就选等级最高的。

    party: [{slot, lv, hp, mhp, types, moves, pp}, ...]
    enemy: {lv, hp, types}
    返回槽位，队伍全灭返回 None。
    """
    if _lead_strategy is not None:
        return _lead_strategy(party, enemy)
    enemy_types = (enemy or {}).get("types", ())
    cands = [m for m in party if m and m.get("hp", 0) > 0]
    if not cands:
        return None
    killers = []
    for m in cands:
        eff = best_damage_effect(m, enemy_types)
        if eff > 1.0:
            killers.append((eff, m.get("lv", 0), m["slot"]))
    if killers:
        killers.sort(key=lambda x: (-x[0], -x[1]))
        return killers[0][2]
    cands.sort(key=lambda m: -m.get("lv", 0))
    return cands[0]["slot"]


_lead_strategy = None


def set_lead_strategy(fn):
    """扩展接口：自定义首发选择（fn(party, enemy) -> slot 或 None）。"""
    global _lead_strategy
    _lead_strategy = fn


def should_switch(party, enemy, active, hp_threshold=0.45, score_margin=3.0):
    """是否值得主动换人（满足任意一个条件就换）。

    条件：
      1. 当前精灵被克制 ≥ 2x（敌人打我方）
      2. 当前血量 < hp_threshold（默认 45%）
      3. 有评分明显更高的目标（评分高 score_margin 以上）
    返回：应该换到的槽位，或 None。
    """
    if not enemy or active is None:
        return None
    m = next((x for x in party if x and x.get("slot") == active), None)
    if not m:
        return None
    target = choose_switch(party, enemy, exclude_slot=active)
    if target is None or target == active:
        return None

    takes = _takes_damage_from(m.get("types", ()), enemy.get("types", ()))
    hp_ratio = (m.get("hp", 0) / m["mhp"]) if m.get("mhp") else 0
    cur_score = score_switch(m, enemy)
    t = next((x for x in party if x and x.get("slot") == target), None)
    better = bool(t and score_switch(t, enemy) > cur_score + score_margin)

    # 任意一个条件成立就换
    if takes >= 2.0 or hp_ratio < hp_threshold or better:
        return target
    return None
