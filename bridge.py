"""中间层（bridge）：场景判定 + 数据裁剪 + 决策分发。

设计原则（高独立性）：
  - 核心不含任何具体场景逻辑
  - 场景通过 register_scene() 注册：字段清单 + 决策处理器
  - 增删功能 = 注册/注销一个场景，不动核心
  - info / decision / action 都不知道彼此细节

用法：
    import bridge, handlers
    handlers.register_all()          # 注册内置场景
    req = bridge.route(info.scene(), info)   # 判定 + 裁剪
    decision = bridge.dispatch(req)         # 分发到处理器
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


# ---------------- 数据结构 ----------------

@dataclass
class Request:
    """中间层产物：场景 + 裁剪后的数据。"""
    scene: str
    data: Dict[str, Any] = field(default_factory=dict)
    note: str = ""


# ---------------- 场景注册表 ----------------

@dataclass
class SceneHandler:
    """一个场景的完整定义（字段 + 处理器）。"""
    fields: List[str]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


_SCENES: Dict[str, SceneHandler] = {}


def register_scene(name: str, fields, handler):
    """注册场景（插件式）。"""
    _SCENES[name] = SceneHandler(fields=list(fields), handler=handler)


def unregister_scene(name: str):
    """注销场景（删功能时用）。"""
    _SCENES.pop(name, None)


def registered_scenes() -> List[str]:
    return sorted(_SCENES.keys())


# ---------------- 核心流程 ----------------

def collect(scene: str, source) -> Dict[str, Any]:
    """只取该场景声明的字段。source 必须提供 get(key)。"""
    h = _SCENES.get(scene)
    if not h:
        return {}
    out = {}
    for k in h.fields:
        try:
            out[k] = source.get(k)
        except Exception:
            out[k] = None
    return out


def route(scene: str, source) -> Request:
    """判定场景 -> 裁剪数据 -> 产出请求。"""
    if scene not in _SCENES:
        return Request(scene="unknown", note=f"未注册场景: {scene}")
    return Request(scene=scene, data=collect(scene, source),
                   note=f"激活: {scene}")


def dispatch(req: Request) -> Dict[str, Any]:
    """把请求交给对应处理器；未注册返回 noop。"""
    h = _SCENES.get(req.scene)
    if not h:
        return {"action": "none", "why": f"没有 {req.scene} 的处理器"}
    return h.handler(req.data)
