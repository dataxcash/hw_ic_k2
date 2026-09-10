# m13 v57 — G3 收口记录（G3 → G4/W3 解封）

> 日期：2026-09-10（Asia/Taipei）｜k2 HEAD：`54587b6`（+ 本卡提交）
> 依据：`m13_v57_g3_freeze_contract_v1.md` / `_v1_1` / `_v1_2` / **`_v1_3`**、
> D0 决策卡、F-3/F-4/F-6b/F-8/F-11/F-13 工件与独立验证器。

## 1. G3 冻结项结清

| 项 | 裁决/交付 | 证据工件 | 独立验证 | 状态 |
|---|---|---|---|---|
| F-1 W0R-FIX | B1.5 PASS（条件并入 D0） | `m13_v57_big_w0r_corridor_model.json` `80ee9adb…` | `…_validation.json` `05148d08…` | 闭 |
| F-2 证书 schema | canonical 10 字段（v1 §1） | v1 契约 | — | 闭 |
| F-3 lane 域/容量帧 | lane 域 32 位 + 容量 10.22/21.9/45.4 | `m13_v57_f3_lane_frame.json` `ff804e1e…` | `p3_v57_f3_lane_frame_validator.py` | 闭 |
| F-4 独立验证器 | 单端谓词 n=8/16，200/200 | `m13_v57_f4_indver_report.json` | 范围声明边界 | 闭 |
| F-5 行键 | `row_y=(N.y+P.y)/2` + WEST 按 `conn_ref` 分帧 + 帧内 x 升序 | v1 §2 | 矩阵 W1-9 重放 | 闭 |
| F-6 双端可达 | 双端谓词已实现 | `m13_v57_f6b_report.json` `9070ed53…` | 200/200 + MUS | 闭 |
| F-7 侧向 + R1.5 | `chip_side` + R1.5 x 域 EAST[93.55,105.25]/WEST[82.35,93.55] | v1 §4 | — | 闭（资源层由 W3 落实） |
| F-8 R3 隙候选域 | 守恒 72/72、冲突图 22 边、REFCLK 8/8 | `m13_v57_f8_r3_gap_candidates.json` `8a316329…` | `p3_v57_f8_r3_validator.py` | 闭 |
| F-9 R4 出链 | 出链（D0-1）+ SPEC-REV-1 | `m13_v57_d0_decision_card.md` `a69cc7f5…` | 板/网表实测 | 闭 |
| F-10/F-10b REFCLK 层 | F.Cu（D0-2） | 同上 | 三源冲突记录 | 闭 |
| F-11 证据协议 | 全链 64hex | `m13_v57_f11_evidence_alignment.md` `7adcaff7…` | 6 生产者重放 | 闭 |
| F-12 landing 重发射 | 原子重发射协议（v1 §5） | v1 契约 | — | 闭（W3 执行） |
| **F-13 R1 参数溯源 + 列对耦合** | 见 v1.3 §1/§2 | `m13_v57_f13_r1_param_trace.json`、`m13_v57_f13_r1_pair_coupling.json` | `…_validation.json` PASS | **闭** |

## 2. 门控链

- G0 待记录 → G1 条件性 PASS → G2 = D0（已签）→ **G3 = 收口（本卡）** → G4/W3 = **解封**。
- W3 授权条件（D0 §2 + v1.3）：必须消费 R4 出链 + REFCLK=F.Cu + D0-3 corridor x-ranges +
  D0-4 修订 reach 口径 + F-13 列对耦合字段；landing 与图纸原子重发射（F-12）。

## 3. F-13 遗留发现（交 W3/S2）

1. 冻结 verdict 的 `pair` 字段 16/32 页不满足列对错距 → 由其派生的 PROVISIONAL `chip_landing_rows`
   在列对口径不可继承（与 F-12 一致）；32/32 页在双约束下域非空。
2. R1.5 资源层（F-7）x 域已裁，但**承载几何/互斥谓词**尚缺字段 → W3 开工卡列为必交付项。
3. `k∈{1,2,3,5}` 表降级为拥塞/逃逸代价指标（D0-4 修订，非终判）。

## 4. 禁令复述

不改冻结四源（SPEC `0bd52ed4…` / manifest `a8ef3ea8…` / PCB `f6273de6…` / rules `0a459839…`）；
不改 `_shared`；不原地改写已发布契约。
