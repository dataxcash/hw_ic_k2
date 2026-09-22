#!/usr/bin/env python3
"""K2 · R379 —— 收口窗口 项3「一次实现」之**冻结接口规格**（方案先行 · 只读契约 · 不含实现）
FROZEN MODEL: C-B2UP-1_REALGEOM_BUS_v1  model_sha16 84f19701dfc1db31
BOARD: k2/hw/k2_v4_8L.l9.kicad_pcb  77aaa63fe016b450
INPUTS: obstacle raster e1ba05e38e3b61f9 (cell 0.03/hw 0.08) · anchor table e6bb322818cd95cb · in5 object set 0bcc060322cc1299
用法（下一会话）：实现 `solve()` 本体；**同参重跑 ≥2 = FAIL**；**禁**改模型/参数/格距/工具；**禁** rip-up 变体。
"""
from __future__ import annotations
import json, hashlib, math
from dataclasses import dataclass

CELL_MM, HW_MM, PITCH_MM, KEEPOUT_MM, LANE_W_MM = 0.03, 0.08, 0.435, 0.5300, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
RASTER_SHA16, ANCHOR_SHA16 = "e1ba05e38e3b61f9", "e6bb322818cd95cb"

@dataclass(frozen=True)
class Lane:
    a_rank: int; net: str; A: tuple; B: tuple          # 端点位移必须 = 0

@dataclass(frozen=True)
class Inputs:
    free: "np.ndarray"      # bool[NX,NY] · True = 可布（cell 0.03）· 由 RASTER_SHA16 校验
    x0: float; y0: float; lanes: tuple                  # lanes 按 a_rank 升序

@dataclass(frozen=True)
class Witness:
    routes: dict            # net -> [[x,y], ...] （In5.Cu 折线 · 首末 = A / B）
    gate: dict              # exact_gate 输出（须 互距0 ∧ 净距0 ∧ 端点0）
    buildability: dict      # mode ∈ {"no_move","relocation_listed"} · 含 ②(ii) 几何核

# ---- 契约：实现者必须满足 ----
def assert_inputs(inp: Inputs) -> None:
    """① free 指纹 == RASTER_SHA16 ② lanes == 16 且 a_rank 0..15 ③ 端点非 NaN。"""
    assert hashlib.sha256(__import__("numpy").packbits(inp.free).tobytes()).hexdigest()[:16] == RASTER_SHA16
    assert len(inp.lanes) == 16 and [l.a_rank for l in inp.lanes] == list(range(16))

def solve(inp: Inputs) -> "Witness | None":
    """**待实现（一次实现）**。要求：
       (1) 每 lane 一条自由格点路径（8-邻域 · 仅 In5.Cu · 避障碍）
       (2) **束序非交叉**：16 条按 a_rank 定序 ⇒ 沿任一切面之**穿越序一致**（允许折返/winding，序不变）
       (3) 两两互距 ≥ PITCH_MM；对非 lane 对象净距 ≥ HW_MM + max(0.175, req(net))
       (4) 端点位移 = 0
       返回 witness（16/16）或 None。**不得**以布通率/有界搜索冒充见证。
    """
    raise NotImplementedError("一次实现：由下一窗口实现本函数并**单次运行**")

def certify_upper_bound(inp: Inputs) -> "dict | None":
    """**(b) 路线**：真实几何之严格上界证书（如切面容量 min-over-cuts Σ floor(w/0.435)+1 < 16）。
       须松弛可靠（松弛不可行 ⇒ 真实不可行）· 刚性量具名取自冻结件 · 附独立复核脚本。
       **不得**以模型类上界冒充。"""
    raise NotImplementedError

def main(model_json: str, anchor_json: str, out_json: str) -> None:
    """装载冻结输入 ⇒ assert_inputs ⇒ w = solve(inp) ；若 None ⇒ certify_upper_bound(inp)
       ⇒ exact_gate（工具 `k2_p4_b2_in5_lane_router_v3.exact_gate`）⇒ 落件（R380+）⇒ 二值日志。"""
    raise NotImplementedError

CONTRACT = {
 "model_sha16": MODEL_SHA16, "board_sha16": BOARD_SHA16,
 "inputs": {"raster": RASTER_SHA16, "anchors": ANCHOR_SHA16},
 "binary": {"(a)": "16/16 见证 + exact_gate(互距0∧净距0∧端点0) + buildability(含②(ii))",
            "(b)": "真实几何严格 U<16 证书（非模型类上界）", "else": "报卡点交监理"},
 "stop_loss": ["同参重跑 ≥2 = FAIL", "禁变体重跑", "禁半途烙板", "禁派 WORKER", "禁以布通率充见证"],
 "forbidden": ["改冻结模型", "改参数/格距/工具", "rip-up 变体", "改冻结四源/criteria/SPEC 设计内容"],
}
if __name__ == "__main__":
    print(json.dumps(CONTRACT, ensure_ascii=False, indent=1))
