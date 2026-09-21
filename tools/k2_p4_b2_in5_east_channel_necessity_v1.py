#!/usr/bin/env python3
"""K2 · R266 —— **东通道共存『禁区/自由带』精确量测 + A 侧缝枚举读数**（只读 · 零搜索 · 零重跑求解器）

用途：把 ②-UP 残差（东通道 16 条共存）从"布线器搜不出来"升级为**可复算的几何量**：
  ① A 侧 y=54.880 缝枚举（N 行 keepout 0.5300 · pitch_eff 0.435）⇒ _P 出口容量 vs 需求；
  ② 东通道内 8 条西组列 vs 8 个东组 B 锚 x 之 **0.435 硬净距禁区**并集测度与自由带测度
     ⇒ 静态（固定列位）模型下西组列位上限（< 8 ⇒ 静态无解）。
口径（物理 · 承 handoff/#K2-130）：keepout 0.5300 = hw 0.08 + 0.35 + margin 0.100 · lane_w 0.16 · 车道互距 ≥0.435。
输入（只读）：/tmp/opencode/archer/{sites_phys.json, sites_b_board_v1.json}
输出：stdout（JSON）· 不落板 · 不写 .omo/supervision/**。
"""
import json, math, sys

PITCH   = 0.435
CH0, CH1 = 135.40, 142.60     # 东通道自由 x 区间（R260/R265 在册）
PX      = 0.5300              # A 侧球位 keepout 半径
LANES   = [f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")]


def load():
    A = json.load(open("/tmp/opencode/archer/sites_phys.json"))
    B = json.load(open("/tmp/opencode/archer/sites_b_board_v1.json"))
    return A, B


def slit_readout(A):
    NX = sorted(A[f"PCIE_UP_OUT{i}_N_J2"][0] for i in range(8))
    PXr = sorted(A[f"PCIE_UP_OUT{i}_P_J2"][0] for i in range(8))
    slits = []
    for i in range(7):
        a, b = NX[i] + PX, NX[i + 1] - PX
        slits.append({"x0": round(a, 4), "x1": round(b, 4), "w": round(b - a, 4),
                      "cap": int(math.floor((b - a) / PITCH + 1e-9)) + 1})
    east = {"x0": round(NX[7] + PX, 4), "x1": 103.360,
            "w": round(103.360 - (NX[7] + PX), 4)}
    cap = sum(s["cap"] for s in slits) + int(math.floor(east["w"] / PITCH + 1e-9)) + 1
    return {"y": 54.880, "keepout": PX, "pitch_eff": PITCH,
            "N_row_x": [round(v, 3) for v in NX], "P_row_x": [round(v, 3) for v in PXr],
            "slits": slits, "east_free_span": east,
            "P_exit_capacity": cap, "P_demand": 8, "margin_vs_demand": cap - 8}


def merge(v):
    v = sorted(v); out = []
    for a, b in v:
        if out and a <= out[-1][1] + 1e-12:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(round(a, 4), round(b, 4)) for a, b in out]


def channel_zones(B):
    """每个东组 B 锚 x 的 0.435 禁区（西组竖直段须避开）。"""
    exb = sorted(B[n][0] for n in LANES if B[n][0] >= CH0)
    zones = [[x - PITCH, x + PITCH] for x in exb]
    z = merge([(max(a, CH0), min(b, CH1)) for a, b in zones if min(b, CH1) > max(a, CH0)])
    free, cur = [], CH0
    for a, b in z:
        if a > cur: free.append((round(cur, 4), round(a, 4)))
        cur = max(cur, b)
    if cur < CH1: free.append((round(cur, 4), CH1))
    meas = round(sum(b - a for a, b in z), 4)
    fmeas = round(sum(b - a for a, b in free), 4)
    # 自由带内按 0.435 间距最多可放几条（贪心 · 上界）
    cap = 0
    for a, b in free:
        cap += int(math.floor((b - a) / PITCH + 1e-9)) + 1
    return {"east_anchor_x": [round(x, 3) for x in exb],
            "zones": z, "zone_union_mm": meas, "free_bands": free, "free_measure_mm": fmeas,
            "max_west_columns_static": cap, "west_lanes_needed": 8}


def main():
    A, B = load()
    out = {"tool": "k2_p4_b2_in5_east_channel_necessity_v1",
           "caliber": {"keepout": 0.5300, "lane_w": 0.16, "lane_center_min": PITCH,
                       "channel_x": [CH0, CH1]},
           "step1_slit_readout": slit_readout(A),
           "step3_channel_necessity": channel_zones(B)}
    out["verdict"] = ("static(model:fixed columns) INFEASIBLE: %d west columns max < 8 needed"
                      % out["step3_channel_necessity"]["max_west_columns_static"])
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
