#!/usr/bin/env python3
"""canonical 19 **求解器导入陷阱**（只读；不改 criteria/）。
在 sys.meta_path 前置陷阱：任何 `eda_core.hs_route_model` 导入 ⇒ 立即 ImportError。
  --selftest : 正向对照（主动导入 ⇒ 证明牙齿会响）
  其余参数   : 原样透传给 criteria/adjudicate.py
"""
import importlib.abc, runpy, sys

class Trap(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == "eda_core.hs_route_model" or name.startswith("eda_core.hs_route_model."):
            raise ImportError("TRAP: 本次运行试图导入求解器 eda_core.hs_route_model")
        return None

sys.meta_path.insert(0, Trap())
if sys.argv[1:2] == ["--selftest"]:
    try:
        import eda_core.hs_route_model  # noqa
        print("TRAP_FAILED: 未拦截")
        sys.exit(2)
    except ImportError as e:
        print("TRAP_OK:", e)
        sys.exit(0)
_argv = sys.argv[1:]
runpy.run_path("criteria/adjudicate.py", run_name="__main__")
