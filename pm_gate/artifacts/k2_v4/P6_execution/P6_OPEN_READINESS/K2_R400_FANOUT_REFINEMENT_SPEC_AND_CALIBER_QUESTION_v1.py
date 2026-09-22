#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R400 —— **方案先行**：端子扇出「障碍感知整形」之冻结规格 + **唯一口径歧义**（交监理）

【O-2/O-3 强制首行自陈 · 本窗口运行清单】
  同一冻结模型内迭代：R383 · R397 · R398 · R399 · **本件 R400（规格 · 不跑任何计算）**。
  变体重跑（已登记 FAIL 级 · 禁再犯）：R384 · R387 · R388。 只读普查/复核：R386/R389/R393/R394/R395/R396。
  ⇒ 本件**只出规格**，**不跑构造器/求解器/任何几何计算**。

依据：#K2-140 §三.5（R399「不成」之具名障碍）· §五（本窗不再授第三窗）· §三.3（方法=构造性；
  禁求解器变体/同参重跑/有界搜索充证据）· #K2-139 O-3（「先定方案再动手」记正）。

—— R399 已确立之事实（供本规格复用 · 不重做）——
  · 束层（走廊/槽位）**不是**约束：x=110 处自由宽 **22.32mm** ≫ 16 槽需 7.2mm；构造解 **pitch 违例 0**。
  · **卡点 = 端子扇出腿**：`A→(x_A,y_slot)` 与 `(x_B,y_slot)→B` 两条**竖直腿**撞 SoC 逃逸铜
    （净距违例 35 · 最小 −0.43mm · 逐 lane/逐处具名，如 OUT0_N vs I2C1_SDA −0.205、OUT0_P vs P3V3 −0.38）。
  · 端点位移 0；走廊槽序（南→北）= B 焊盘 x 升序 = [0,3,11,4,12,7,15,8,6,14,5,13,10,2,9,1]。

—— 待整形之规格（constructor v2「扇出整形」）——
  * 输入（**冻结** · 复用 R399 之记账补正）：板 l9（脚本实算 sha16 77aaa63fe016b450）
    + 基模型 model_l8.json（文件 sha16 c42731c4258ae691）+ 补丁 P（24 段/4 孔）⇒ derived-l9（指纹脚本实算）。
  * 目标：**两条腿**改为**障碍感知**构造：仅在两腿（A→槽位、槽位→B）内避障；**束层与槽序保持不变**。
  * 二值：两腿无障碍 ⇒ 16/16 过闸（+buildability）⟹ (a)；否则 ⟹ 新的具名障碍（哪条/哪个量/最小复现）。
  * 止损：**一次实现 · 一次运行**；禁参数扫描；禁变体重跑；模型冻结记指纹；只读；不烙板；不派 WORKER。

—— ⚠ 唯一口径歧义（**请监理裁定** · 属判据语义澄清 = 监理职权）——
  「障碍感知」两腿之**几何求解方式**是否仍属 #K2-140 §三.3 所准之「**构造性**」？二选：
    (甲) **准**：允许**确定性**之单次**避障路径构造**（如「以锚孔为中心、沿自由域最大净空方向之单次最短路」）——
         理由是它**一次实现一次运行、无参数扫描、无变体**，属**直接生成几何**；
    (乙) **不准**：视为「求解器变体」⇒ 则本窗内 ENG **无可动项**，请监理按 #K2-140 §五 处置。
  ⇒ ENG **不自裁此口径**，亦**未据此跑任何计算**（本件零计算）。
"""
from __future__ import annotations
import json, os, hashlib, datetime

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
OUT = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS",
                   "K2_R400_FANOUT_REFINEMENT_SPEC_AND_CALIBER_QUESTION_v1.json")
SPEC = {
  "artifact": "k2_r400_fanout_refinement_spec_and_caliber_question_v1", "schema": 1,
  "nature": "**规格件（方案先行）· 非收口件 · 零计算**",
  "o2_o3_window_run_declaration": {
    "same_frozen_model_iteration": ["R383", "R397", "R398", "R399"],
    "this_artifact": "R400 —— 只出规格 · 不跑任何计算",
    "variant_reruns_registered": ["R384", "R387", "R388"],
    "survey_only": ["R386", "R389", "R393", "R394", "R395", "R396"]},
  "from": "ENG · ARCHER R400", "to": "监理",
  "authority": "#K2-140 §三.3/§三.5/§五 · #K2-139 O-3",
  "facts_from_R399": {
    "bundle_layer_not_binding": {"corridor_free_width_mm": 22.32, "slots_need_mm": 7.2, "n_lane_pitch_viol": 0},
    "blocker": {"where": "端子扇出两腿（A→槽位 · 槽位→B）竖直段", "n_clearance_viol": 35,
                "clearance_min_mm": -0.43,
                "examples": [["PCIE_UP_OUT0_N_J2", "I2C1_SDA", "seg", -0.205],
                             ["PCIE_UP_OUT0_N_J2", "GND", "via", -0.206],
                             ["PCIE_UP_OUT0_P_J2", "PCIE_UP6_N", "seg", -0.3318],
                             ["PCIE_UP_OUT0_P_J2", "P3V3", "via", -0.38]]},
    "corridor_order_ranks_south_to_north": [0, 3, 11, 4, 12, 7, 15, 8, 6, 14, 5, 13, 10, 2, 9, 1]},
  "spec_constructor_v2": {
    "inputs_frozen": {"board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": "77aaa63fe016b450",
                      "base_model": "/tmp/opencode/archer/model_l8.json",
                      "base_model_file_sha16": "c42731c4258ae691",
                      "patch": "P_l8_to_l9_in5_neck_removal（24 段 + 4 孔）",
                      "bookkeeping": "承 R399 §bookkeeping_fix · 指纹全部脚本实算"},
    "change_scope": "**仅**两腿改为障碍感知构造；**束层与槽序不变**",
    "deliverable_binary": {
      "(a)": "16/16 具名坐标 + exact_gate(互距0∧净距0∧端点0) + buildability(no_move|relocation_listed) + 独立复核脚本",
      "(b)/不成": "新的具名障碍（哪条 · 哪个几何量 · 最小可复现例）"},
    "stop_loss": ["一次实现 · 一次运行", "禁参数扫描", "禁变体重跑", "模型冻结记指纹", "只读", "不烙板", "不派 WORKER"]},
  "caliber_question_for_supervisor": {
    "question": "「障碍感知」两腿之**几何求解方式**是否仍属 #K2-140 §三.3 所准之『构造性』？",
    "option_jia": "准：允许**确定性**单次避障路径构造（一次实现一次运行 · 无参数扫描 · 无变体 · 直接生成几何）",
    "option_yi": "不准：视为『求解器变体』⇒ 本窗内 ENG 无可动项 ⇒ 请按 §五 处置",
    "eng_position": "**ENG 不自裁此口径**；本件**零计算**，未据此跑任何东西。"},
  "boundary": "只读 · 零计算 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER"}


def main():
    d = dict(SPEC); d["ts"] = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    with open(OUT, "w") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "nature": d["nature"], "out": OUT}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
