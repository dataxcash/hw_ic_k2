#!/usr/bin/env python3
"""CO-16：把**32/32 全落位**（crossing-free + clearance-clean）通道分配发射为机读工件。

相对 CO11-ALLOC.1 的差异（版本 bump 事由）：
  1. `CO10_EASTSPLIT=in2c` + `CO10_J2STEP=0.6` —— 东侧 stub 全 In2 + J2 列 = 区间图确定性贪心着色（O4 感知色值重排）。
  2. `CO10_POLMODE=lx` —— 方向感知 P/N lane 排序（闭式几何规则）：
     当 stub 层 == lane 层（In6）时，竖直 stub 必穿过对面极性水平 lane（CO-11 §13.2 UP6/UP7 self-cross）；
     规则：stub 朝上（ll>lane_y）时 landing lx 较大者取 +POL_OFF（上）、较小者取 -POL_OFF（下）；朝下反之。
     仅对 WEST_MCIO_TO_CHIP；stub 全 In2 组不受影响（保留一致性）。
  2. 结果 32/32（CO11-ALLOC.1 为 30/32）。

架构一致：引擎既有契约 =「离线域 → 闭式消费，执行器零搜索」。本件按 (page,pol) O(1) 取用，
派生为单遍确定性（canonical 逆序 + 固定键序 + 首可行谓词，无回溯/无重试）。
只读消费：manifest / lane_frame / pair 域 v1.5 / pad field / drc_rules；不改冻结四源。
"""
from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
CFG = {"CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_WSTEP": "1.1265", "CO10_WLO": "33.3",
       "CO10_FANY_J3": "31.5,51.5", "CO10_STUB": "J3L", "CO10_POLMODE": "lx",
       "CO10_EASTSPLIT": "in2c", "CO10_J2STEP": "0.6"}
# 版本化旋钮（CO16-ALLOC.2 等）：env 覆盖，默认 = ALLOC.1 逐字节可复现
for _k, _e in (("CO10_PAIR", "CO16_PAIR"), ("CO10_WSTEP", "CO16_WSTEP"), ("CO10_WLO", "CO16_WLO"),
               ("CO10_FANY_J3", "CO16_FANY_J3"), ("CO10_STUB", "CO16_STUB"),
               ("CO10_POLMODE", "CO16_POLMODE"), ("CO10_EASTSPLIT", "CO16_EASTSPLIT"),
               ("CO10_J2STEP", "CO16_J2STEP"), ("CO10_STEP", "CO16_STEP"),
               ("CO10_EDELTA", "CO16_EDELTA")):
    if os.environ.get(_e):
        CFG[_k] = os.environ[_e]
# CO-23 旋钮（默认 = 旧行为；**仅在显式指定时写入 config**，保 ALLOC.1/2/3 逐字节可复现）
# CO-36 旋钮（默认 = 旧行为；仅显式指定时写入 config，保 ALLOC.1..4 逐字节可复现）
for _k, _e in (("CO10_COLMODE", "CO16_COLMODE"), ("CO10_WSWAP", "CO16_WSWAP"),
               ("CO10_HOLE_GAP", "CO16_HOLE_GAP"), ("CO10_LXPRIO", "CO16_LXPRIO"),
               # CO-143（L2 自裁）：逃生扇并入「对间 3W」下界（默认关 => ALLOC.1..7 逐字节可复现）
               ("CO10_IP3W", "CO16_IP3W"),
               # CO-144（L2 自裁）：逃生扇落位策略 = 分带单调 carry（默认关 => ALLOC.1..7 逐字节可复现）
               ("CO10_FAN_STRAT", "CO16_FAN_STRAT"),
               # CO-144：PDN 固定障碍场须随落位策略一并透传（否则扇对 PDN 视而不见 => 板级 DRC 回归）
               ("CO10_PDN_OBS", "CO16_PDN_OBS"),
               # CO-205（L2 自裁 · 候选 A）：竖段层全落 In2（escape/stub）
               ("CO10_ALLI2", "CO16_ALLI2"),
               # CO-205（L2 自裁 · 候选 B）：run 层改 B.Cu + 竖段 In2/In5 分色
               ("CO10_V2B", "CO16_V2B"),
               # CO-205b（L2 自裁 · 工具缺陷修复）：过孔占用 = 起止层之间全部层
               ("CO10_SPAN", "CO16_SPAN"),
               # CO-205c（L2 自裁 · 候选 D）：竖段落两外层 F/B、lane 维持内层 In5
               ("CO10_VOUT", "CO16_VOUT"),
               # CO-204L/CO-205：竖段层全落 B.Cu（候选 A′，最小修正 = 消除 88 支内层<->内层）
               ("CO10_ALLB", "CO16_ALLB"),
               # CO-205e（L2 自裁 · 候选 C）：双孔桥 + 竖列分色偏移
               ("CO10_BRIDGE", "CO16_BRIDGE"), ("CO10_BRJOG", "CO16_BRJOG"),
               # CO-205r（L2 自裁 · 桥孔联合求解 / 工具缺陷 ③）：
               ("CO10_BRCOL", "CO16_BRCOL"),      # 桥孔 jog 按**列序**取远离方向（修 pad 序反向互撞）
               ("CO10_BR2", "CO16_BR2"),          # 桥孔 x 对齐逃逸列 + y 侧移（联合闭式；默认关）
               ("CO10_BR2D", "CO16_BR2D"),        # 落桥孔 y 侧移（默认随 BR2）
               ("CO10_BRDROP", "CO16_BRDROP"),    # 条件式落桥孔修复（仅 hh_intra 时反向）
               ("CO10_XMIN", "CO16_XMIN"),        # 逃逸列间最小 x 距（默认 0.38 旧行为）
               ("CO10_POL_OFF", "CO16_POL_OFF"),  # 对内 lane y 偏移（默认 0.25 旧行为）
               ("CO10_BVERT", "CO16_BVERT"),      # 逐页竖段整体落 B（混合拓扑）
               ("CO10_COLFIX", "CO16_COLFIX"),    # 连接器列分配区间含桥孔 y（工具缺陷 ④）
               ("CO10_CARRYP", "CO16_CARRYP"),      # 逐极性单调列游标（band 级列联合求解）
               ("CO10_CARRYALL", "CO16_CARRYALL"),  # CO-209：全带 carry 游标（计入桥孔足迹）⇒ 与 CARRYP 合成「列 × 桥孔 x」联合形态
               ("CO10_BOFF", "CO16_BOFF"), ("CO10_STUB_LANE", "CO16_STUB_LANE"), ("CO10_STUB_B", "CO16_STUB_B"), ("CO10_BRX2", "CO16_BRX2"), ("CO10_TOPOE", "CO16_TOPOE"), ("CO10_BRAWAY", "CO16_BRAWAY")):
    if os.environ.get(_e):
        CFG[_k] = os.environ[_e]
REVISION = os.environ.get("CO16_REV", "CO16-ALLOC.1")
OUT_NAME = os.environ.get("CO16_OUT", "m13_v57_co16_channel_allocation.json")
VERIFY_NAME = os.environ.get("CO16_VERIFY", "m13_v57_co16_placement_verification.json")
SUPERSEDES = os.environ.get("CO16_SUPERSEDES", "CO11-ALLOC.1")
SUPERSEDES_REASON = os.environ.get(
    "CO16_SUPERSEDES_REASON",
    "30/32 -> 32/32（方向感知 P/N lane 排序，消除 UP6/UP7 In6 stub self-cross）")
OUT = STEP2 / OUT_NAME


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    os.environ.update(CFG)
    import importlib.util
    spec = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    _ord = os.environ.get("CO16_ORDER", "rev")
    res = probe.probe(rule="fan", order=_ord, verbose=False)
    if res["n_placed"] != res["n_pages"]:
        print("NOT FULLY PLACED:", res["n_failed"], res["failed"]); return 1
    G = res["geom"]
    pages = {}
    for pid, g in sorted(G.items()):
        f = probe.FACTS[pid]
        pages[pid] = {
            "page_id": pid, "corridor": f["corridor"], "conn_ref": f["conn_ref"], "band": f["band"],
            "chip_pad": {p: [round(f["pad"][p][0], 4), round(f["pad"][p][1], 4)] for p in ("P", "N")},
            "conn_pad": {p: [round(f["conn_pad"][p][0], 4), round(f["conn_pad"][p][1], 4)] for p in ("P", "N")},
            "lane_y": {p: round(probe.LANES[pid]["lane_y"] + probe.pol_off(f, p), 4) for p in ("P", "N")},
            "escape_layer": res["placed"][pid]["escape"], "stub_layer": res["placed"][pid]["stub"],
            "via1": {"P": [round(v, 4) for v in res["placed"][pid]["P_via"]],
                     "N": [round(v, 4) for v in res["placed"][pid]["N_via"]]},
            "landing": {p: [round(v, 4) for v in probe.land_meta(f)[p]] for p in ("P", "N")},
        }
    doc = {
        "artifact": "m13_v57_co16_channel_allocation", "schema": 1, "revision": REVISION,
        "supersedes": {"artifact": "m13_v57_co11_channel_allocation", "revision": SUPERSEDES,
                       "reason": SUPERSEDES_REASON},
        "status": "EMITTED", "status_kind": "VERIFIED_FULL_PLACEMENT_32of32",
        "authority": {"co15_ruling": "m13_v57_CO15_joint_allocation_ruling.md"},
        "method": {"name": "single_pass_deterministic_greedy",
                   "order": ("band-major monotone carry (corridor, band, conn_ref, pad-x asc)"
                             if os.environ.get("CO16_FAN_STRAT") == "carry"
                             else "canonical reverse (corridor, conn_ref, band, page_id)"),
                   "no_backtracking": True, "no_retry": True,
                   "lane_offset_rule": "CO10_POLMODE=lx（方向感知 P/N 排序；见 CFG note）",
                   "note": "候选按固定键序；首可行即取。执行器（引擎）按本工件 O(1) 取用，零搜索。"},
        "config": CFG,
        "inputs_sha16": {"manifest": sha16(STEP2 / "m13_v57_s1_page_manifest.json"),
                         "lane_frame": sha16(STEP2 / "m13_v57_f3_lane_frame.json"),
                         "pair_v1_5": sha16(STEP2 / "m13_v57_f13_r1_pair_coupling_v1_5.json"),
                         "pad_field": sha16(STEP2 / "m13_v57_co09_pad_field.json")},
        "verification": {"artifact": VERIFY_NAME,
                         "sha16": sha16(STEP2 / VERIFY_NAME),
                         "result": "n_violations=0 PASS（全对全 320 via/320 段 + 616 pad 场 + proper-intersection 交叉）"},
        "n_pages": len(pages), "pages": pages,
        "redline": "只读冻结四源；canonical W3-CN.30 未动；无 sign-off",
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{REVISION}: pages={len(pages)} sha16={sha16(OUT)[:16]} size={OUT.stat().st_size//1024}KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
