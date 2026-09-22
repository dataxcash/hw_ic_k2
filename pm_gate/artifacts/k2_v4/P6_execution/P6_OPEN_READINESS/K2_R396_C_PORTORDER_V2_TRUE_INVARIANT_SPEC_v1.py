#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R396 —— **方案先行**：C-PORTORDER **v2（真不变量）之冻结接口规格**
（承 #K2-138 §三 『准只读不变量验证器』· 宪法第一条『监理不替 ENG 写方案』⇒ 本件由 ENG 写方案）

【O-3 强制首行自陈 · 本窗口运行清单（承 #K2-138 §六 O-3）】
  · 同一冻结模型内迭代：R383（一次实现 · 单次运行）。
  · **变体重跑（自陈 · 触强止损 · 登记禁再犯）**：R384 · R387 · R388。
  · 纯普查/读数/验收（非求解运行）：R386 · R389 · R393 · R394 · R395。
  · **本件（R396）= 只出规格，不跑任何求解器、不跑任何不变量计算**（方案先行）。

本件之地位：**规格件（方案先行）· 非收口件**；**不替代** (a)/(b) 二值。
执行 v2 须**新授权**（v58 ②(甲) 已请裁『再授一个实现窗口』）。

—— 目标问题（冻结）——
  在 D（= 由闸所消费之同一冻结模型重建之 In5 车道中心线自由域）中，是否存在
  16 条**两两 >= 0.435** 之**非交叉**折线 π_i：a_i -> b_i（端点固定 · 仅 In5.Cu）？

—— 已由 R393/R395 机器确立、供 v2 复用之事实（**不重做**）——
  * 直线族分离切 min cap = **28**（R393）；一般曲线 min-cut = **16**（= 16 条逐锚小环，cap=Σ_k(floor(L_k/.435)+1)）。
    ⇒ **切面路线已闭合为『不可得』**（承 R395 自纠）。
  * **A 锚 0.435 盘两两相离**（最小中心距 0.9801mm > 0.870 · 16 分量 · 缝宽 0.1101mm > 0）
    ⇒ **无屏障 · 车道可在锚间穿行** ⇒ R390 §S1/S2『顺序被强制』**无依据**；[C2] 已被自有见证反例化。
  * 见证之配对型 = **嵌套(逆序) + 绕墙 winding 之旋转**（R385/R386）。

—— v2 之两条**有界、只读**取证路线（#K2-138 §三.3 之 ①/② 之严格化）——
  ①【主】端口环 + **洞群生成元**不变量（映射类群 / 辫型）：
      · 计算 D 之边界分量与**洞**（blocked 连通分量）→ 取**割系** Σ = 自 ∂D 到各洞之割线（成 H_1(D) 基）；
      · 对每条基割 γ_k，由「π_i 连 a_i 到 b_i」**唯一确定** π_i 与 γ_k 之**交点计数** n_{i,k}（模 2 / 全数）；
      · 非交叉族存在 ⇒ 交点计数须与 Σ 上之**序**一致（Pontryagin–Thom / 映射类群障碍）；
      · **输出** = 该一致性方程组**可解 / 不可解**；不可解 ⇒ 给出**具名障碍**（哪条 γ_k、哪对 lane、何矛盾）。
  ②【副】[C2] 之有限情形穷尽：**已弃用**（[C2] 已被 R395 机器反例化 ⇒ 前提不成立）。
  ③【备】若 ① 判「可解」⇒ **不得**据此宣布 (a)；须另请**构造器窗口**（属监理放行范围）。

—— 交付（二值 · 唯一终局）——
  (b) 成立 ⇒ 严格 U<16 证书：**松弛可靠** · 刚性量**具名+出处** · 附**独立复核脚本**（监理可复跑）· **残铜去向证明** ⇒ 依 #K2-132 §四 豁免自动生效 ⇒ 收口；
  (b) 不成立 ⇒ 立即回报卡点 ⇒ 由监理判『②-UP 是否须变』⇒ 按其路由处置（ENG 不自启 owner）。

—— 强止损（承 #K2-138 §三.5）—— 同参重跑>=2=FAIL · 禁变体重跑 · 禁有界搜索/启发式充证书 ·
  禁只读普查充件 · 禁半途烙板 · 禁派 WORKER · 临时仅 /tmp/opencode · 模型须**求解前冻结**并记 model_sha。

冻结常数（逐字不改）：CELL 0.03 · HW 0.08 · PITCH 0.435 · LANE_W 0.16 · LAYER In5.Cu
MODEL_SHA16 84f19701dfc1db31 · BOARD_SHA16 77aaa63fe016b450 · RASTER/ANCHOR 参见 K2_R379 契约
"""
from __future__ import annotations
import json, os, hashlib, datetime

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
OUT = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS",
                   "K2_R396_C_PORTORDER_V2_TRUE_INVARIANT_SPEC_v1.json")
CONTRACT = {
    "artifact": "k2_r396_c_portorder_v2_true_invariant_spec_v1",
    "schema": 1, "nature": "**规格件（方案先行）· 非收口件** · 不替代 (a)/(b)",
    "from": "ENG · ARCHER R396", "to": "监理",
    "authority": "#K2-138 §三（准只读不变量验证器）· 执行 v2 须**新授权**（v58 ②(甲) 已请裁）",
    "o3_window_run_declaration": {
        "same_frozen_model_iteration": ["R383"], "variant_reruns_declared": ["R384", "R387", "R388"],
        "survey_only": ["R386", "R389", "R393", "R394", "R395"],
        "this_artifact": "只出规格 · 未跑求解器/不变量计算",
    },
    "problem_frozen": "D 中是否存在 16 条两两>=0.435 之非交叉折线 a_i->b_i（端点固定 · 仅 In5.Cu）？",
    "facts_reused_not_redone": {
        "cut_route_closed": "直线族 min cap=28（R393）· 一般曲线 min-cut cap=16（R395，逐锚小环）⇒ 切面路线闭合为『不可得』",
        "no_barrier": "A 锚 0.435 盘两两相离（min 中心距 0.9801 > 0.870 · 16 分量 · 缝宽 0.1101>0）⇒ 无屏障/可穿行",
        "c2_refuted": "[C2]『seam=最东锚』被自有 gate-clean 见证反例化（seam=rank2）⇒ R390 条件式 U<=15 无效",
        "pairing_type": "嵌套(逆序)+绕墙 winding 之旋转（R385/R386）",
    },
    "routes": {
        "primary_1": {
            "name": "端口环 + 洞群生成元不变量（映射类群/辫型）",
            "steps": ["算 D 之边界分量与洞", "取割系 Σ（H_1(D) 基）",
                      "对每 γ_k 定 π_i 之交点计数 n_{i,k}（由 a_i,b_i 唯一确定）",
                      "检 Σ 上之序一致性（Pontryagin–Thom/映射类群障碍）"],
            "output": "一致性方程组**可解/不可解**；不可解 ⇒ **具名障碍**",
            "bounded": True, "read_only": True,
        },
        "secondary_2": {"name": "[C2] 有限情形穷尽", "status": "**弃用**（[C2] 已被 R395 反例化）"},
        "fallback_3": {"name": "若判『可解』", "action": "**不得**据此宣布 (a)；须另请**构造器窗口**（监理放行范围）"},
    },
    "deliverable": {"(b)_established": "严格 U<16 证书（松弛可靠 · 刚性量具名+出处 · 独立复核脚本 · 残铜去向证明）⇒ 豁免自动生效 ⇒ 收口",
                    "(b)_not_established": "立即回报卡点 ⇒ 监理判『②-UP 是否须变』⇒ 按其路由处置（ENG 不自启 owner）"},
    "stop_loss": ["同参重跑>=2=FAIL", "禁变体重跑", "禁有界搜索/启发式充证书", "禁只读普查充件",
                  "禁半途烙板", "禁派 WORKER", "临时仅 /tmp/opencode", "模型求解前冻结并记 model_sha"],
    "frozen_constants": {"CELL_mm": 0.03, "HW_mm": 0.08, "PITCH_mm": 0.435, "LANE_W_mm": 0.16,
                         "LAYER": "In5.Cu", "MODEL_SHA16": "84f19701dfc1db31", "BOARD_SHA16": "77aaa63fe016b450"},
    "boundary": "只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · 未跑求解器",
}


def main():
    d = dict(CONTRACT)
    d["ts"] = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    with open(OUT, "w") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "out": OUT, "nature": d["nature"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
