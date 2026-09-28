"""M2 · `eda_eng ripup` --- 执行拆除（#K2-360 §一 M2）。**当前：未实现**（M1 先绿）。"""
from __future__ import annotations

STATUS = {"implemented": False, "module": "M2", "order": "#K2-360 sec.2 (M1 -> M2 -> M3 -> M4, one at a time)",
          "contract": "M1 plan -> teardown board; test: unconnected == expected N, other nets untouched (segment diff)"}


def run(*_a, **_k):
    return {"status": "NOT_IMPLEMENTED", **STATUS}
