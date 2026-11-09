"""决策层门面：按场景拆分到子模块，这里统一导出（保持旧接口兼容）。

  decision_battle.py  战斗：出招 / 换人 / 首發
  decision_map.py     地图：转身 / 走路 / 草里降频
"""
import sys
sys.path.insert(0, "/root/workspace")

from decision_battle import (          # noqa: F401
    move_effect, best_damage_effect, choose_move, has_attack_move,
    choose_switch, choose_lead, should_switch, should_flee, score_switch,
    should_switch_opening,
    set_move_strategy, set_switch_strategy, set_lead_strategy,
    current_strategies,
)
from decision_map import (             # noqa: F401
    need_turn, walk_plan, choose_next_step,
    grass_tiles, clear_run, run_limit,
    GRASS_ID, MAX_RUN, MAX_RUN_GRASS,
)
