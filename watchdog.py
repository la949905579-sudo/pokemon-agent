"""健壮性：看门狗 + 等回合完成。"""
import sys, time
sys.path.insert(0, "/root/workspace")
import action

_lead_failed = False   # 本场战斗换首发失败过就不再重试

# 看门狗：连续 N 轮「场景+双方血量」完全没变化，认为卡住
_wd = {"last": None, "count": 0}


def wait_round_end(max_polls=60, verbose=False):
    """等这一回合结束（turn 回到 1）或战斗结束。

    只用轮询次数不用真实时间 —— 加速/不加速都适用。
    期间遇到动画/结算（turn 0/4/5）就按 A 推进。
    """
    for i in range(max_polls):
        s = action.snapshot()
        if not s["battle"]:
            return "end"
        if s["turn"] == 1:
            return "ready"
        if s["turn"] in (0, 4, 5):
            action.tap_a()
            time.sleep(0.25)
        else:
            time.sleep(0.15)
    return "timeout"


def _watchdog(key, limit=12):
    """连续 limit 轮无进展 -> 返回 True。"""
    if key == _wd["last"]:
        _wd["count"] += 1
    else:
        _wd["last"] = key
        _wd["count"] = 0
    if _wd["count"] >= limit:
        _wd["count"] = 0
        return True
    return False


