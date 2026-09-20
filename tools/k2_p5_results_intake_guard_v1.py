#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2 P5 首件回件 —— **可判性守卫（intake guard）** · v1 · 2026-09-21

轮标：K2-2026-09-21 · ARCHER-R97 · 「P5 回件可判性机械化」（§12 自动化优先）
目的：外部回件（results_template 实例）到达时，**一命令**回答两个问题：
  (A) 回件**可判吗**？（锚一致 · 责权边界 · 必填齐 · 证据 sha 可核）—— fail-closed
  (B) 各条**读数**相对**已冻结阈值**是多少？（附 建议读数，**非判定**）

【定位 · 必读】本工具 **不是判定器**：
  · 判定权归**监理**（`results_template.json::judged_by = 监理` · 验收计划 §5 责任边界）。
  · 本工具 **零新增判据维 / 零新增检查齿**：逐条阈值**全部**取自**已冻结**的
    `L6/first_article_l8/results_template.json`（含 `criterion`/`note`/`expected_nominal_V`/
    `windows_V`/`tj_conversion_caliber`）+ `RULES.md` + `K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md`。
    本工具**只做**：① 结构/锚/证据完整性 fail-closed；② 把已有数值对已有阈值**算出差值**并打印。
  · 本工具**不写**任何工件（除 stdout / 可选 `--json-out`）；**不改**模板、**不改**交付锚、**不改**判据。

用法：
  python3 tools/k2_p5_results_intake_guard_v1.py <results.json> [--json-out /tmp/opencode/x.json]
  python3 tools/k2_p5_results_intake_guard_v1.py --self-test          # 内置正/负夹具自证
退出码： 0 = 可判（admissible）· 1 = 不可判（inadmissible）· 2 = 用法/内部错
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

K2 = Path(__file__).resolve().parents[1]          # .../k2
ART = K2 / "pm_gate" / "artifacts" / "k2_v4"

BOARD_SHA16 = "7a5c89913d6e5d0a"
MANIFEST = ART / "L6/jlc_package_l8r2/MANIFEST.json"
TARBALL = ART / "L6/DELIVERY_l8r2/k2_v4_8L.l8r2_gerber_package.tar.gz"
RULES = ART / "L6/first_article_l8/RULES.md"

STATUS_ENUM = ("NOT_RUN", "PASS", "FAIL", "INCONCLUSIVE")
ZDIFF_LO, ZDIFF_HI = 76.5, 93.5
NOMINAL_V = {"12V_IN": 12.0, "P3V3": 3.3, "P3V3_AUX": 3.3, "MCU_VDD": 3.0}
PCT_NOMINAL = 0.05            # V6-1 ±5%
DROP_BUDGET_PCT = 3.0         # V5 ≤3%
TJ_LIMIT_C = 120.0            # V7
TJ_T1_TRIGGER_C = 117.0       # V7 T1 触发
PSI_JT = 3.6                  # ℃/W（TI SNLS683 §6.4；反推唯一口径）
AUX_WIN = (3.135, 3.465)
SW_DP_IDCODE_INT = 0x0BC11477   # Cortex-M0+ CoreSight SW-DP IDCODE
FRU_ADDRS = {"0x52", "0xa4", "0xa5"}

FAIL, WARN, INFO = "ADMISSIBILITY_FAIL", "WARN", "NOTE"


class Guard:
    """收集 fail-closed 项（Δ）与读数（R）。"""

    def __init__(self) -> None:
        self.fails: list[dict[str, str]] = []
        self.warns: list[dict[str, str]] = []
        self.readings: list[dict[str, Any]] = []

    def fail(self, where: str, why: str) -> None:
        self.fails.append({"where": where, "why": why})

    def warn(self, where: str, why: str) -> None:
        self.warns.append({"where": where, "why": why})

    def read(self, item: str, field: str, value: Any, verdict: str, basis: str) -> None:
        self.readings.append(
            {"item": item, "field": field, "value": value, "suggested_reading": verdict, "basis": basis}
        )


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def norm_hex(x: Any) -> int | None:
    """十六进制 ID 归一为 **int**（避免 hex() 去前导零致 0x0BC11477 ≠ 0xBC11477）。"""
    if isinstance(x, str):
        s = x.strip().lower()
        if s.startswith("0x"):
            try:
                return int(s, 16)
            except ValueError:
                return None
    if isinstance(x, int) and not isinstance(x, bool):
        return int(x)
    return None


def fmt_hex(v: int | None) -> str:
    return "None" if v is None else f"0x{v:08X}"


def get(d: Any, *keys: str) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


# ---------------------------------------------------------------- A. 可判性

def check_anchor_and_identity(g: Guard, r: dict) -> None:
    """锚一致性 + 结构 + 责权边界（fail-closed：任一不满足 ⇒ 回件不可判）。"""
    if r.get("artifact") != "k2_p5_first_article_results":
        g.fail("artifact", f"须为 'k2_p5_first_article_results'，实测 {r.get('artifact')!r}")
    if r.get("schema") != 1:
        g.fail("schema", f"须为 1，实测 {r.get('schema')!r}")
    if r.get("board_sha16") != BOARD_SHA16:
        g.fail("board_sha16", f"须为受审板 {BOARD_SHA16}，实测 {r.get('board_sha16')!r}")

    # 交付锚：回件所载 sha256 必须等于**本仓现行** MANIFEST/tarball 实测值
    # （防「量的是别的 rev/别的包」——首件必须来自本包）
    da = r.get("delivery_anchor") or {}
    for label, path, key in (("MANIFEST.json", MANIFEST, "manifest_sha256"),
                             ("tarball", TARBALL, "tarball_sha256")):
        if not path.is_file():
            g.fail(f"delivery_anchor/{key}", f"本仓缺件 {path} —— fail-closed")
            continue
        actual = sha256_file(path)
        claimed = da.get(key)
        if not claimed:
            g.fail(f"delivery_anchor/{key}", "回件未载交付锚 sha256 —— 无法证明首件出于本包")
        elif str(claimed).lower() != actual:
            g.fail(f"delivery_anchor/{key}",
                   f"锚不符：回件 {claimed} ≠ 本仓实测 {actual}（**首件可能非出于本包**）")
        else:
            g.read("S0_anchor", key, claimed, "MATCH", f"{label} 实测 sha256 相同")

    # 责权边界：验收计划 §5「不得由 ENG 自证」
    mb = str(r.get("measured_by") or "").strip()
    if not mb or mb.startswith("<"):
        g.fail("measured_by", "未填实测方 —— RULES §0 责任边界要求具名实测方")
    elif any(t in mb.upper() for t in ("ARCHER", "ENG", "CODEX")):
        g.fail("measured_by", f"实测方 = {mb!r} 疑为 ENG ⇒ **违『不得 ENG 自证』**，须监理确认")
    if r.get("status_enum") and list(r["status_enum"]) != list(STATUS_ENUM):
        g.fail("status_enum", f"状态枚举须为 {list(STATUS_ENUM)}，实测 {r['status_enum']}")

    # 规程件在位（回件所引 plan/rules）
    for key in ("plan", "rules"):
        rel = r.get(key)
        if not rel:
            g.warn(f"{key}", "回件未载引用路径")
            continue
        p = K2 / str(rel).replace("k2/", "", 1)
        if not p.is_file():
            p = (K2.parent / str(rel))
        if not p.is_file():
            g.warn(f"{key}", f"引用件不存在于本仓：{rel}")


def check_evidence(g: Guard, where: str, ev: Any) -> None:
    """证据清单：dict{path,sha256} 须实测相符；空 ⇒ 不可判（RULES §0.2 原始件留存）。"""
    if not ev:
        g.fail(f"{where}.evidence", "证据为空 —— RULES §0.2 要求原始件 + sha256")
        return
    if not isinstance(ev, list):
        ev = [ev]
    for i, e in enumerate(ev):
        tag = f"{where}.evidence[{i}]"
        if isinstance(e, dict):
            p = e.get("path")
            s = e.get("sha256")
            if not p:
                g.fail(tag, "缺 path")
                continue
            f = Path(p)
            if not f.is_absolute():
                f = K2 / p
            if not f.is_file():
                g.warn(tag, f"原始件不在本仓（外部件 ⇒ 需监理核对留档）：{p}")
            elif s and str(s).lower() != sha256_file(f):
                g.fail(tag, f"sha256 不符：载 {s} ≠ 实测 {sha256_file(f)}")
            elif s:
                g.read(where, f"evidence[{i}].sha256", s, "MATCH", "原始件 sha256 相符")
        elif isinstance(e, str) and e.strip():
            g.warn(tag, f"证据为路径串（未载 sha256）：{e}")
        else:
            g.fail(tag, "证据条目既非路径串亦非 {path,sha256}")


# ------------------------------------------------------- B. 逐项读数（非判定）

def item_status(g: Guard, r: dict, key: str) -> str | None:
    it = (r.get("items") or {}).get(key)
    if not isinstance(it, dict):
        g.fail(f"items.{key}", "缺该验收项（required=true）")
        return None
    st = it.get("status")
    if st not in STATUS_ENUM:
        g.fail(f"items.{key}.status", f"状态须属 {list(STATUS_ENUM)}，实测 {st!r}")
    if st == "NOT_RUN":
        g.fail(f"items.{key}.status", "仍为 NOT_RUN ⇒ 该项不可判")
    check_evidence(g, f"items.{key}", it.get("evidence"))
    return st


def v4(g: Guard, r: dict) -> None:
    key = "V4_impedance_coupon"
    if item_status(g, r, key) is None:
        return
    m = get(r, "items", key, "measured") or {}
    z = m.get("per_layer_zdiff_ohm") or {}
    for lay in ("F.Cu", "In2.Cu", "In5.Cu", "B.Cu"):
        v = z.get(lay)
        if not is_num(v):
            g.fail(f"{key}.{lay}", "Zdiff 未给数值 ⇒ 该层不可判")
        else:
            g.read(key, f"Zdiff[{lay}]", v,
                   "IN_RANGE" if ZDIFF_LO <= v <= ZDIFF_HI else "OUT_OF_RANGE",
                   f"85Ω±10% ⇒ [{ZDIFF_LO},{ZDIFF_HI}]Ω")
    cov = m.get("covers_geometry") or {}
    for geom in ("center_mm_0.6", "tightest_edge_gap_mm_0.2825"):
        if cov.get(geom) is not True:
            g.fail(f"{key}.covers_geometry.{geom}", "券未确认覆盖该几何（强制）⇒ 覆盖要求不满足")
        else:
            g.read(key, f"covers[{geom}]", True, "COVERED", "RULES §V4 覆盖要求（强制）")


def v5(g: Guard, r: dict) -> None:
    key = "V5_pdn_dc_drop"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    rails = m.get("rails") or {}
    # RULES §V5：「注明所用测点 refdes」——载于任一惯用键或 note；缺 ⇒ 不可判
    lp = it.get("load_point_refdes") or m.get("load_point_refdes") or m.get("load_points")
    note_blob = json.dumps(it, ensure_ascii=False)
    for rail, nom in NOMINAL_V.items():
        d = rails.get(rail) or {}
        vs, vl, ia, dp = d.get("V_source"), d.get("V_load"), d.get("I_A"), d.get("drop_pct")
        if not (is_num(vs) and is_num(vl) and is_num(ia)):
            g.fail(f"{key}.{rail}", "V_source/V_load/I_A 三项须均为数值（电流须声明来源见 note）")
            continue
        if vs <= vl:
            g.fail(f"{key}.{rail}", f"V_source({vs}) ≤ V_load({vl}) ⇒ 读数不自洽")
        calc = (vs - vl) / nom * 100.0
        g.read(key, f"{rail}.drop_pct", round(calc, 4),
               "IN_BUDGET" if abs(calc) <= DROP_BUDGET_PCT else "OVER_BUDGET",
               f"≤{DROP_BUDGET_PCT}% 预算（标称 {nom}V 计）")
        if is_num(dp) and abs(dp - calc) > 0.05:
            g.warn(f"{key}.{rail}.drop_pct", f"回件自报 {dp} ≠ 独立复算 {round(calc,4)}（差 >0.05pp）")
        if rail == "P3V3_AUX":
            if lp is None:
                g.fail(f"{key}.P3V3_AUX.load_point_refdes",
                       "未载负载点 refdes（RULES §V5 强制 · 该轨取近端会假绿）⇒ 不可判")
            else:
                blob = json.dumps(lp, ensure_ascii=False) + note_blob
                if not ("J3" in blob or "J4" in blob):
                    g.fail(f"{key}.P3V3_AUX.load_point_refdes",
                           f"负载点未落在 J3/J4（实测载 {lp!r}）⇒ 违具名测点强制")
                else:
                    g.read(key, "P3V3_AUX.load_point", lp, "NAMED_OK", "须为 J3/J4 之 P3V3_AUX pad")
        if not d.get("I_A_source") and not it.get("I_A_source") and not m.get("I_A_source"):
            g.warn(f"{key}.{rail}.I_A_source", "电流来源未显式声明（RULES §V5 要求 datasheet 或保守值）")


def v6_1(g: Guard, r: dict) -> None:
    key = "V6_1_rail_voltages"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    if not str(m.get("condition") or "").strip():
        g.fail(f"{key}.condition", "condition 缺失 ⇒ 该判不可判（#K2-55 明文）")
    else:
        g.read(key, "condition", m.get("condition"), "RECORDED", "主判工况须为独立运行（J13/VCC 无外供）")
    rails = m.get("rails") or {}
    for rail, nom in NOMINAL_V.items():
        v = rails.get(rail)
        if not is_num(v):
            g.fail(f"{key}.{rail}", "电压未给数值 ⇒ 该轨不可判")
            continue
        lo, hi = nom * (1 - PCT_NOMINAL), nom * (1 + PCT_NOMINAL)
        g.read(key, f"{rail}_V", v, "IN_WINDOW" if lo <= v <= hi else "OUT_OF_WINDOW",
               (f"标称 {nom}V ±5% ⇒ [{round(lo,4)},{round(hi,4)}]V"
                + ("（#K2-55 主判标称 3.0V · 独立运行）" if rail == "MCU_VDD" else "")))
    aux = m.get("MCU_VDD_aux_j13_3V3")
    if not is_num(aux):
        g.warn(f"{key}.MCU_VDD_aux_j13_3V3", "辅助读数未记（RULES §V6-1『须同记』；不参与主判）")
    else:
        g.read(key, "MCU_VDD_aux_j13_3V3", aux,
               "IN_WINDOW" if AUX_WIN[0] <= aux <= AUX_WIN[1] else "OUT_OF_WINDOW",
               f"辅助窗 [{AUX_WIN[0]},{AUX_WIN[1]}]V（不参与主判）")


def v6_2(g: Guard, r: dict) -> None:
    key = "V6_2_mcu_swd_id"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    did = m.get("device_id_read")
    if did is None or (isinstance(did, str) and not did.strip()) or (isinstance(did, dict) and not did):
        g.fail(f"{key}.device_id_read", "未载实测 device ID ⇒ 不可判（二值项）")
        return
    blob = json.dumps(did, ensure_ascii=False)
    hx = norm_hex(did)
    if hx is None and isinstance(did, dict):
        for cand in (get(did, "sw_dp_idcode"), get(did, "sw_dp"), get(did, "idcode")):
            hx = norm_hex(cand)
            if hx is not None:
                break
    if hx is None:
        g.warn(f"{key}.device_id_read", f"未能解析出十六进制 IDCODE（载 {blob[:120]}）⇒ 须监理目视")
    else:
        g.read(key, "sw_dp_idcode", fmt_hex(hx),
               "MATCH_EXPECTED" if hx == SW_DP_IDCODE_INT else "MISMATCH_EXPECTED",
               f"设计侧期望 {fmt_hex(SW_DP_IDCODE_INT)}（Cortex-M0+ CoreSight SW-DP）")


def v6_3(g: Guard, r: dict) -> None:
    key = "V6_3_fru_i2c"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    found = {str(a).strip().lower() for a in (m.get("addresses_found") or [])}
    if not found:
        g.fail(f"{key}.addresses_found", "未载总线扫描命中地址 ⇒ 不可判（二值项）")
        return
    hit = found & FRU_ADDRS
    g.read(key, "addresses_found", sorted(found),
           "EXPECTED_HIT" if hit else "EXPECTED_MISS",
           f"期望 7-bit 0x52（8-bit 0xA4/0xA5）· 载 fru_eeprom_bus={m.get('fru_eeprom_bus')!r}")


def v6_4(g: Guard, r: dict) -> None:
    key = "V6_4_link_gen4_x4"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    ports = m.get("ports") or {}
    missing = [p for p in ("J2", "J3", "J4") if ports.get(p) is None]
    if missing:
        g.fail(f"{key}.ports", f"端口 {missing} 无读数 ⇒ 不可判（双路均须记录）")
    if m.get("both_directions") is None:
        g.fail(f"{key}.both_directions", "未载双向结果 ⇒ 不可判")
    fs = m.get("final_state") or {}
    sp, wd = fs.get("speed_GTs"), fs.get("width")
    for nm, v, want, unit in (("speed_GTs", sp, 16, "GT/s"), ("width", wd, 4, "lane")):
        if not is_num(v):
            g.fail(f"{key}.final_state.{nm}", f"未载 LTSSM 终态 {nm} ⇒ 不可判")
        else:
            g.read(key, nm, v, "AS_SPEC" if v == want else "NOT_AS_SPEC", f"判据 = x4 Gen4 即 {want}{unit}")


def v6_5(g: Guard, r: dict) -> None:
    key = "V6_5_stability_30min_aer"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    if not is_num(m.get("duration_min")) or m["duration_min"] < 30:
        g.fail(f"{key}.duration_min", f"时长 {m.get('duration_min')!r} < 30min ⇒ 不可判")
    aer = m.get("aer_count")
    if not is_num(aer):
        g.fail(f"{key}.aer_count", "AER 计数未给 ⇒ 不可判")
    else:
        g.read(key, "aer_count", aer, "ZERO" if aer == 0 else "NONZERO", "判据 = AER 计数 0")
    if not m.get("log_files"):
        g.fail(f"{key}.log_files", "无原始日志 ⇒ RULES §0.2 证据要求未满足")


def v7(g: Guard, r: dict) -> None:
    key = "V7_thermal_o2"
    it = (r.get("items") or {}).get(key) or {}
    if item_status(g, r, key) is None:
        return
    m = it.get("measured") or {}
    asm = m.get("assembly") or {}
    o2_ok = (str(asm.get("heatsink", "")).replace("×", "x") == "30x30mm Al"
             and asm.get("interface_pad_C_per_W") == 1.0)
    if not o2_ok:
        g.fail(f"{key}.assembly", f"未按 O2 实施 ⇒ **直接记 T1 触发**（装配前置强制）：{asm}")
    if not is_num(asm.get("airflow_mps")):
        g.fail(f"{key}.assembly.airflow_mps", "风冷风速未载 ⇒ 不可判（O2 要求 ~2 m/s）")
    else:
        g.read(key, "airflow_mps", asm["airflow_mps"],
               "O2_OK" if asm["airflow_mps"] >= 1.5 else "BELOW_O2",
               "O2 = ~2 m/s 风冷")
    if not is_num(m.get("Ta_C")):
        g.fail(f"{key}.Ta_C", "环境温度未载 ⇒ 不可判")
    if not str(m.get("Tj_measure_method") or "").strip():
        g.fail(f"{key}.Tj_measure_method", "未载反推口径（唯一式 Tj = T_top + P·ψJT）⇒ 不可判")
    cases = m.get("cases") or {}
    if not cases:
        g.fail(f"{key}.cases", "四工况全缺 ⇒ 不可判")
    for cname, c in cases.items():
        tj, ttop, pw = c.get("Tj_meas_C"), c.get("Ttop_C"), c.get("P_W")
        if not is_num(tj):
            g.fail(f"{key}.{cname}.Tj_meas_C", "Tj 实测未给 ⇒ 该工况不可判")
            continue
        g.read(key, f"{cname}.Tj_meas_C", tj, "BELOW_LIMIT" if tj <= TJ_LIMIT_C else "OVER_LIMIT",
               f"L2 v2.0 限值 {TJ_LIMIT_C}℃（T1 触发线 {TJ_T1_TRIGGER_C}℃）")
        if tj > TJ_T1_TRIGGER_C:
            g.warn(f"{key}.{cname}.Tj_meas_C",
                   f"Tj {tj}℃ > {TJ_T1_TRIGGER_C}℃ ⇒ **T1 触发**：须立即开新 rev（目标 θJA_eff ≤ 9.5℃/W）")
        if is_num(ttop) and is_num(pw):
            calc = ttop + pw * PSI_JT
            g.read(key, f"{cname}.Tj_from_formula", round(calc, 2),
                   "CONSISTENT" if abs(calc - tj) <= 1.0 else "INCONSISTENT",
                   f"Tj = T_top + P·ψJT（ψJT={PSI_JT}）⇒ {round(calc,2)}℃ 应 ≈ 载入 Tj {tj}℃")
            if abs(calc - tj) > 1.0:
                g.warn(f"{key}.{cname}", f"反推式不自洽：式给 {round(calc,2)} vs 载 {tj}（差 >1℃）")
        else:
            g.fail(f"{key}.{cname}", "Ttop_C 或 P_W 缺失 ⇒ 反推式无法复算")


def observations(g: Guard, r: dict) -> None:
    obs = r.get("observations_p5_named") or {}
    for k, v in obs.items():
        if (v or {}).get("checked") is None:
            g.fail(f"observations_p5_named.{k}.checked", "P5 具名实板观察点未填（验收计划 §3 要求）")


# ------------------------------------------------------------------ driver

def run(results: dict) -> Guard:
    g = Guard()
    check_anchor_and_identity(g, results)
    v4(g, results)
    v5(g, results)
    v6_1(g, results)
    v6_2(g, results)
    v6_3(g, results)
    v6_4(g, results)
    v6_5(g, results)
    v7(g, results)
    observations(g, results)
    return g


def report(g: Guard, results_path: str) -> dict:
    admissible = not g.fails
    return {
        "artifact": "k2_p5_results_intake_guard_report",
        "schema": 1,
        "generated_by": "k2/tools/k2_p5_results_intake_guard_v1.py",
        "results_path": results_path,
        "admissible": admissible,
        "admissibility_fails": g.fails,
        "warnings": g.warns,
        "readings": g.readings,
        "authority": "判定权归监理；本件为零新增判据维之『可判性 + 读数』机械化件，不置 status",
        "n_admissibility_fails": len(g.fails),
        "n_warnings": len(g.warns),
        "n_readings": len(g.readings),
    }


def print_human(rep: dict) -> None:
    print(f"== K2 P5 回件可判性守卫（intake guard）==  {rep['results_path']}")
    print(f"判定：{'**可判（admissible）**' if rep['admissible'] else '**不可判（inadmissible）**'}"
          f"  · fail={rep['n_admissibility_fails']} · warn={rep['n_warnings']} · 读数={rep['n_readings']}")
    if rep["admissibility_fails"]:
        print("\n-- 不可判项（fail-closed；必须由实测方补齐/更正后方可判）--")
        for f in rep["admissibility_fails"]:
            print(f"   [X] {f['where']}: {f['why']}")
    if rep["warnings"]:
        print("\n-- 提醒（不阻断可判性）--")
        for f in rep["warnings"]:
            print(f"   [!] {f['where']}: {f['why']}")
    if rep["readings"]:
        print("\n-- 读数对已冻结阈值（**建议读数 · 非判定**）--")
        for r in rep["readings"]:
            print(f"   {r['item']:<24} {r['field']:<34} {str(r['value']):<28} {r['suggested_reading']:<16} | {r['basis']}")
    print("\n判定权归监理（本工具不置 status、不改模板/锚/判据）。")


# --------------------------------------------------------------- self-test

def _base() -> dict:
    return {
        "artifact": "k2_p5_first_article_results",
        "schema": 1,
        "board": "k2_v4_8L.l8.kicad_pcb",
        "board_sha16": BOARD_SHA16,
        "delivery_anchor": {
            "package": "pm_gate/artifacts/k2_v4/L6/jlc_package_l8r2",
            "manifest_sha256": sha256_file(MANIFEST),
            "tarball_sha256": sha256_file(TARBALL),
        },
        "plan": "k2/docs/K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md",
        "rules": "pm_gate/artifacts/k2_v4/L6/first_article_l8/RULES.md",
        "measured_by": "某第三方实测方（示例）",
        "judged_by": "监理",
        "status_enum": list(STATUS_ENUM),
        "items": {
            "V4_impedance_coupon": {
                "status": "PASS", "evidence": ["/tmp/opencode/coupon.pdf"],
                "measured": {"per_layer_zdiff_ohm": {"F.Cu": 85.0, "In2.Cu": 84.0, "In5.Cu": 86.0, "B.Cu": 85.5},
                             "covers_geometry": {"center_mm_0.6": True, "tightest_edge_gap_mm_0.2825": True}},
            },
            "V5_pdn_dc_drop": {
                "status": "PASS", "evidence": ["/tmp/opencode/v5.log"], "load_point_refdes": {"P3V3_AUX": "J3", "P3V3": "U1.1", "12V_IN": "J9.1", "MCU_VDD": "U1.44"},
                "measured": {"rails": {
                    "12V_IN": {"V_source": 12.0, "V_load": 11.9, "I_A": 1.0, "drop_pct": 0.833},
                    "P3V3": {"V_source": 3.3, "V_load": 3.27, "I_A": 0.5, "drop_pct": 0.909},
                    "P3V3_AUX": {"V_source": 3.3, "V_load": 3.2, "I_A": 0.3, "drop_pct": 3.03},
                    "MCU_VDD": {"V_source": 3.0, "V_load": 2.95, "I_A": 0.2, "drop_pct": 1.667}}},
            },
            "V6_1_rail_voltages": {
                "status": "PASS", "evidence": ["/tmp/opencode/v6_1.log"], "measured": {"condition": "独立运行（J13/VCC 不接外供）",
                    "rails": {"12V_IN": 12.0, "P3V3": 3.3, "P3V3_AUX": 3.3, "MCU_VDD": 3.0},
                    "MCU_VDD_aux_j13_3V3": 3.3}},
            "V6_2_mcu_swd_id": {"status": "PASS", "evidence": ["/tmp/opencode/swd.log"], "measured": {"device_id_read": "0x0BC11477"}},
            "V6_3_fru_i2c": {"status": "PASS", "evidence": ["/tmp/opencode/i2c.log"], "measured": {"buses": ["I2C1", "I2C2"], "addresses_found": ["0x52"], "fru_eeprom_bus": "I2C1"}},
            "V6_4_link_gen4_x4": {"status": "PASS", "evidence": ["/tmp/opencode/lspci.txt"], "measured": {"ports": {"J2": "ok", "J3": "ok", "J4": "ok"}, "both_directions": True, "final_state": {"speed_GTs": 16, "width": 4}}},
            "V6_5_stability_30min_aer": {"status": "PASS", "evidence": ["/tmp/opencode/aer.log"], "measured": {"duration_min": 30, "aer_count": 0, "log_files": ["aer.log"]}},
            "V7_thermal_o2": {"status": "PASS", "evidence": ["/tmp/opencode/tj.log"], "measured": {
                "assembly": {"heatsink": "30×30mm Al", "interface_pad_C_per_W": 1.0, "airflow_mps": 2.0},
                "Ta_C": 25.0, "Tj_measure_method": "Tj = T_top + P·ψJT（ψJT=3.6）",
                "cases": {"U6_EQ0-2_typ": {"P_W": 4.7, "Tj_pred_C": 91.7, "Tj_meas_C": 91.0, "Ttop_C": 74.08},
                          "U6_EQ0-2_max": {"P_W": 6.0, "Tj_pred_C": 106.0, "Tj_meas_C": 106.0, "Ttop_C": 84.4},
                          "U6_EQ5-19_typ": {"P_W": 5.8, "Tj_pred_C": 103.8, "Tj_meas_C": 104.0, "Ttop_C": 83.12},
                          "U6_EQ5-19_max": {"P_W": 7.0, "Tj_pred_C": 117.0, "Tj_meas_C": 117.0, "Ttop_C": 91.8}},
                "Tj_conservative_upper_bound_C": 117.0}},
        },
        "observations_p5_named": {
            "mask_dam_9_sites": {"checked": True, "finding": "9 处无阻焊坝，未见桥连"},
            "silk_overhang_4": {"checked": True, "finding": "H4/R41/D2/C87 位号被裁剪"},
        },
    }


def self_test() -> int:
    print("### self-test 1/2：正夹具（应 admissible）")
    g1 = run(_base())
    rep1 = report(g1, "<fixture:positive>")
    print_human(rep1)
    ok1 = rep1["admissible"]

    print("\n### self-test 2/2：负夹具（篡改锚 + 缺 condition + 未按 O2 + 越预算 → 应 inadmissible）")
    bad = _base()
    bad["delivery_anchor"]["manifest_sha256"] = "0" * 64
    bad["items"]["V6_1_rail_voltages"]["measured"]["condition"] = ""
    bad["items"]["V7_thermal_o2"]["measured"]["assembly"]["airflow_mps"] = None
    bad["items"]["V5_pdn_dc_drop"]["measured"]["rails"]["P3V3_AUX"]["V_load"] = 3.0
    bad["items"]["V6_4_link_gen4_x4"]["measured"]["final_state"]["speed_GTs"] = 8
    bad["measured_by"] = "ARCHER (ENG)"
    g2 = run(bad)
    rep2 = report(g2, "<fixture:negative>")
    print_human(rep2)
    ok2 = (not rep2["admissible"]) and any("锚不符" in f["why"] for f in rep2["admissibility_fails"])

    print(f"\nself-test: positive admissible={ok1} · negative inadmissible&anchor-caught={ok2}")
    n_over = [r for r in rep2["readings"] if r["suggested_reading"] in ("OVER_BUDGET", "NOT_AS_SPEC")]
    print(f"self-test: negative 夹具另捕获越界读数 {len(n_over)} 条（须 ≥2）")
    good = ok1 and ok2 and len(n_over) >= 2
    print("self-test: " + ("PASS" if good else "**FAIL**"))
    return 0 if good else 2


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="K2 P5 首件回件可判性守卫（不判定 · 判定权归监理）")
    ap.add_argument("results", nargs="?", help="回件 results JSON 路径")
    ap.add_argument("--json-out", help="把报告写到该路径（默认仅 stdout）")
    ap.add_argument("--self-test", action="store_true", help="跑内置正/负夹具自证")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.results:
        ap.print_help()
        return 2
    p = Path(a.results)
    if not p.is_file():
        print(f"ERROR: 回件不存在 {p}", file=sys.stderr)
        return 2
    try:
        res = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: 回件非合法 JSON：{e}", file=sys.stderr)
        return 2
    rep = report(run(res), str(p))
    print_human(rep)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n报告已落：{a.json_out}")
    return 0 if rep["admissible"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
