"""route --- rip-up & reroute 引擎（#K2-356 专项）。当前状态：**未实现**（如实报，不许冒充能力）。

合同（#K2-356 §二.1）：入 = 新放置 + 约束（层分配 / 45° / 8 对等长 / 间距 / 四角禁区 / 铜皮多边形）；
出 = 全连通 + DRC 零新增 + 已验收倒角/等长保持。先验 = W1 规律库 N1-N10 + 在册扇出结构。
"""
from __future__ import annotations

STATUS = {"implemented": False, "reason": "rip-up & reroute engine not built yet (#K2-356 work order)",
          "exams": ["A", "B"], "entry": "route --exam A|B --in <board> --out <board>",
          "note": "until it can pass exam A/B the board may not be changed (#K2-356 sec.2.4 / #K2-358 sec.3)"}


def run(*_a, **_k):
    return {"status": "NOT_IMPLEMENTED", **STATUS}
