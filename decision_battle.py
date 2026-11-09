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


def choose_move(mon, enemy_types=None, intents=None, cons=None, enemy=None):
    """返回 (招式序号 0-3, 说明)。

    intents 来自 intent.effective()：
      prolong / no_kill -> 优先变化招，其次最低威力
      only_class        -> 只保留指定属性/威力类别的招
    其它情况走默认策略（威力 × 克制 × 段数）。
    """
    if _move_strategy is not None:
        return _move_strategy(mon, enemy_types)
    if cons is None and intents:
        import intent
        cons = intent.compile_all(intents, {"me": mon, "foe": enemy})
    status_mode = bool(cons and cons.move_mode == "status")
    chip_mode = bool(cons and cons.move_mode == "chip")
    allowed = cons.allowed_types if cons else None

    cands = []
    for i, (mid, pp) in enumerate(zip(mon["moves"], mon["pp"])):
        info = MOVES.get(mid)
        if not info or pp <= 0:
            continue
        name, typ, power = info
        if allowed and typ not in allowed:
            continue
        eff = move_effect(mid, enemy_types) if enemy_types else 1.0
        cands.append({"i": i, "name": name, "typ": typ, "power": power,
                      "eff": eff, "hits": MULTI_HIT.get(mid, 1.0)})

    if chip_mode:
        # 压血：只用预估不会击杀的低伤招；没有就退回变化招
        foe_hp = (enemy or {}).get("hp") or 0
        safe = [c for c in cands if c["power"] > 0
                and c["power"] * c["hits"] * c["eff"] <= foe_hp * 0.8]
        if safe:
            c = min(safe, key=lambda x: x["power"] * x["hits"] * x["eff"])
            return c["i"], f"指令(压血)：{c['name']}（低伤 {int(c['power'] * c['hits'] * c['eff'])}）"

    if status_mode or chip_mode:
        status = [c for c in cands if c["power"] == 0]
        if status:
            c = min(status, key=lambda x: x["i"])
            return c["i"], f"指令(拖回合/不击杀)：{c['name']}（变化招）"
        if cands:
            c = min(cands, key=lambda x: x["power"] * x["hits"])
            return c["i"], f"指令(拖回合/不击杀)：{c['name']}（最低威力）"

    atk = [c for c in cands if c["power"] > 0]
    if not atk:
        if allowed and cands:                     # 指令限定为变化招等
            c = min(cands, key=lambda x: x["i"])
            return c["i"], f"指令(only_class)：{c['name']}（变化招）"
        return 0, "没有可用攻击招式，默认第一招"
    best = max(atk, key=lambda c: c["power"] * c["hits"] * c["eff"])
    ht = f" ×{best['hits']:g}段" if best["hits"] > 1 else ""
    return best["i"], f"{best['name']}（{best['typ']} 威力{best['power']}{ht} 克制x{best['eff']:g}）"


def _foe_low(enemy, it):
    """敌方血量 <= 阈值（no_kill 用）。"""
    mhp = (enemy or {}).get("mhp") or 0
    if not mhp:
        return False
    return (enemy or {}).get("hp", 0) / mhp <= it.params.get("hp_floor", 0.2)


def has_status_move(mon):
    """有没有可用的变化招（PP>0 且威力 0）。"""
    for mid, pp in zip(mon.get("moves") or [], mon.get("pp") or []):
        info = MOVES.get(mid)
        if info and info[2] == 0 and pp > 0:
            return True
    return False


def has_attack_move(mon):
    """这只还有没有可用的攻击招（PP>0 且威力>0）。"""
    for mid, pp in zip(mon.get("moves") or [], mon.get("pp") or []):
        info = MOVES.get(mid)
        if info and info[2] > 0 and pp > 0:
            return True
    return False


def _best_damage(mon, enemy_types):
    """我方对敌的最大单回合伤害（威力×段数×克制）。"""
    best = 0.0
    for mid in mon.get("moves") or []:
        info = MOVES.get(mid)
        if not info or info[2] <= 0:
            continue
        best = max(best, info[2] * MULTI_HIT.get(mid, 1.0)
                   * move_effect(mid, enemy_types))
    return best


def score_switch_v2(mon, enemy, enemy_moves=None):
    """换人评分 v2：以「预计击杀回合差」为主（只用于影子观测）。

    foe_turns - my_turns 越大越该上；敌方有招式表时按实际招式算威胁。
    """
    import math
    et = (enemy or {}).get("types", ())
    my_out = _best_damage(mon, et)
    foe_hp = (enemy or {}).get("hp") or 1
    my_turns = math.ceil(foe_hp / max(my_out, 1.0))

    foe_out = 0.0
    if enemy_moves:
        for mid in enemy_moves:
            info = MOVES.get(mid)
            if not info or info[2] <= 0:
                continue
            eff = 1.0
            for mt in (mon.get("types") or ()):
                eff *= TYPE_CHART.get((info[1], mt), 1.0)
            foe_out = max(foe_out, info[2] * eff)
    if not foe_out:
        dmg = 1.0
        for et2 in et:
            for mt in (mon.get("types") or ()):
                dmg *= TYPE_CHART.get((et2, mt), 1.0)
        foe_out = 20.0 * dmg
    foe_turns = math.ceil((mon.get("hp") or 1) / max(foe_out, 1.0))
    lv = (mon.get("lv") or 0) - ((enemy or {}).get("lv") or 0)
    return (foe_turns - my_turns) * 10 + lv * 0.5


def threat_score(enemy_moves, my_types):
    """敌方招式表里对我方最痛的：威力 × 克制倍率（只用于观测/评估）。"""
    best = 0.0
    for mid in enemy_moves or ():
        info = MOVES.get(mid)
        if not info or info[2] <= 0:
            continue
        eff = 1.0
        for mt in (my_types or ()):
            eff *= TYPE_CHART.get((info[1], mt), 1.0)
        best = max(best, info[2] * eff)
    return best


def _takes_damage_from(mon_types, enemy_types):
    """敌方属性打我方属性的倍率（>1 表示被克制）。"""
    dmg = 1.0
    for et in (enemy_types or ()):
        for mt in (mon_types or ()):
            dmg *= TYPE_CHART.get((et, mt), 1.0)
    return dmg


def score_switch(mon, enemy):
    """换人评分：v2（预计击杀回合差 + 敌方实际招式）。

    分数越大越该上；没有敌方招式表时退回属性倍率近似。
    """
    return score_switch_v2(mon, enemy, (enemy or {}).get("moves"))


def _score_switch_legacy(mon, enemy):
    """旧评分（保留对照，不再使用）。"""
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
    # 等级压制：明显能秒杀时不换，省一回合
    my_lv = m.get("lv") or 0
    foe_lv = (enemy or {}).get("lv") or 0
    if my_lv and foe_lv and foe_lv <= my_lv - 8:
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
    # 等级压制：明显能秒杀时不换，省一回合
    my_lv = m.get("lv") or 0
    foe_lv = (enemy or {}).get("lv") or 0
    if my_lv and foe_lv and foe_lv <= my_lv - 8:
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
