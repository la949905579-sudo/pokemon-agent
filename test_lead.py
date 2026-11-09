"""离线测试：开场选最优首发。"""
import sys
sys.path.insert(0, "/root/workspace")
import decision

# 简化队伍：电(皮卡丘)、虫毒(大针蜂)、水(卡咪龟)、草毒(喇叭芽)
P = lambda slot, lv, types, moves: {"slot": slot, "lv": lv, "hp": 30, "mhp": 30,
                                     "types": types, "moves": moves, "pp": [20]*4}
party = [
    P(0, 13, ("电",), [98, 45, 39, 86]),      # 电光一闪等
    P(1, 27, ("虫", "毒"), [31, 40]),
    P(2, 25, ("水",), [55, 57]),
    P(3, 13, ("草", "毒"), [71, 78]),
]

def t(name, enemy, want):
    got = decision.choose_lead(party, enemy)
    print(f"{name}: enemy={enemy['types']} -> slot {got} (期望 {want})", "OK" if got == want else "FAIL")
    assert got == want, (got, want)

# 敌人：一般/飞行（无克制）-> 等级最高的大针蜂 slot1
t("无克制(纯一般)", {"lv": 15, "types": ("一般",)}, 1)
# 敌人：水 -> 电(2x) 或 草(2x)，都克制；皮卡丘 Lv13 vs 喇叭芽 Lv13 同级，按 eff 都 2x，等级相同则取第一个（slot0）
t("水系", {"lv": 15, "types": ("水",)}, 1)
# 敌人：飞行 -> 电(2x) 皮卡丘 slot0
t("飞行系(电系招式0威力不算)", {"lv": 15, "types": ("飞行",)}, 1)
# 敌人：火 -> 卡咪龟(水 2x) slot2
t("火系", {"lv": 15, "types": ("火",)}, 2)

# 扩展接口
decision.set_lead_strategy(lambda p, e: 3)
print("自定义策略 ->", decision.choose_lead(party, {}), "OK" if decision.choose_lead(party, {}) == 3 else "FAIL")
decision.set_lead_strategy(None)
print("全部通过")
