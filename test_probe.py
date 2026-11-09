"""离线测试：probe_menu 用方向键试探主菜单/队伍列表。"""
import sys
sys.path.insert(0, "/root/workspace")
from unittest.mock import patch
import state
import ra


def run_probe(main_reacts):
    """main_reacts=True 模拟主菜单（FF8 变）；False 模拟队伍列表（B0A9 变）。"""
    mem = {0x02023FF8: 0, 0x0203B0A9: 1}
    pressed = []

    def fake_rd(addr, n):
        return bytes([mem[addr]])

    def fake_press(name, dur=0.35):
        pressed.append(name)
        if main_reacts:
            if name == "right" and mem[0x02023FF8] == 0:
                mem[0x02023FF8] = 1
            elif name == "left" and mem[0x02023FF8] == 1:
                mem[0x02023FF8] = 0
        else:
            if name == "down" and mem[0x0203B0A9] < 5:
                mem[0x0203B0A9] += 1
            elif name == "up" and mem[0x0203B0A9] > 0:
                mem[0x0203B0A9] -= 1

    with patch.object(state, "rd", fake_rd), patch.object(ra, "press", fake_press):
        k = state.probe_menu()
    return k, mem, pressed


k, mem, pressed = run_probe(True)
assert k == "main", (k, mem)
assert mem[0x02023FF8] == 0, "试探后应还原主菜单光标"
print("A 主菜单识别 ok", pressed)

k, mem, pressed = run_probe(False)
assert k == "party", (k, mem)
assert mem[0x0203B0A9] == 1, "试探后应还原队伍光标"
print("B 队伍列表识别 ok", pressed)
print("全部通过")
