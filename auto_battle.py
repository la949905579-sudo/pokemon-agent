"""战斗门面：拆分为 switch / watchdog / battle_loop，这里统一导出。"""
import sys
sys.path.insert(0, "/root/workspace")

from switch import (                    # noqa: F401
    party_order, active_slot, reset_party_order,
    _pick_and_switch, switch_from_main, handle_force_switch, do_switch,
    _cursor_for_slot, advance_b, move_to,
)
from watchdog import _watchdog, wait_round_end   # noqa: F401
from battle_loop import battle_loop               # noqa: F401
