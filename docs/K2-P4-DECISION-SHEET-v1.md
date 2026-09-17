# K2 · P4 · **裁决单**（一页；owner/监理一次答复即可推进）· v1 · 2026-09-17

> 性质：ENG 汇总（**不改任何件**）。用途 = 把多轮取证压成一页**可执行决策**，供监理升级人工 / owner 一次性答复。
> 判定权归监理；ENG 只交测量与草案。冻结件、`criteria/`、真源 **逐字节未动**。

## 0. 一屏现状（可复现口径）

| 项 | 值 |
|---|---|
| P4 板 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = **`d9813bc554a2d611`**（同名 pro = `f68a5fb2f82bd02d`） |
| canonical SPEC | `SPEC_k2_v4.spec-rev-44.json` = **`acc64b447ef55e90`** |
| 门禁 | DRC 违规 **51**（error **15** / warning **36**）· 未连接 **2** · 非 45° **0 / 4701** · 对内等长 max **0.0788**（判据 ≤0.15）· 段/孔/总长 **4701 / 713 / 6273.2870mm** |
| 冻结判定器（`criteria/adjudicate.py` `897e8bfde60e2cfe`） | PASS 6 / FAIL 4（**PROVISIONAL**） |
| **草案判定器**（补齐版，交监理复验） | **PASS 11 / FAIL 7**（7 项见 §1/§2） |
| 阶段 | P0–P3 关门；**P4 未全绿**；P5/P6 未开 ⇒ **不出 Gerber**（fail-closed） |
| 冻结八源 | 本会话多次复算**全部一致**；`criteria/`（0444, owner=ic_hw_gate）未动 |

## 1. owner（**三条硬闸**；答完即消 DRC error 15 + 未连接 2）

| # | **一句话问题** | 证据（sha256/16） | 答复后解锁 |
|---|---|---|---|
| **O-1** | **载板那侧的 standoff 位置固定吗？螺钉/铜柱头（含垫圈）外径是多少？** | `K2-P4-H3-MECHANICAL-INPUT-GAP-v1.md` `4532740a33213fcc` | ①**可动** ⇒ ENG 在 L2 域内重解 4 孔并接 `12V_IN` ⇒ 消 H3 组 **16** 条 + 未连接 **1**；②固定且头径 ≥Ø5.x ⇒ 需重定义机械或电气接口之一（超 ENG） |
| **O-2** | **W-8/J-7：33–35 件的 pad 级差异 —— 判据容忍 pad 级，还是源侧按库重落？** | `K2-J7-W8-FOOTPRINT-LIB-AUDIT-v1.md`；覆盖缺口见提交件 §3.3 | 任一 ⇒ 消 `lib_footprint_mismatch` **35**（连带 `lib_footprint_electrical` 与 **35** 条 warning 处置） |
| **O-3** | **`DS320_STRAP_A_ADDR0_15-8`：移动 R42，还是放开 1 条既有 PCIe 铜？** | handoff §5-3（R42.1 盘中心 ±1.2mm 内 5 个 span 类**全无合法孔位**） | 任一 ⇒ 未连接 **2 → 1** |

> **O-1 的两个附带结论（已实测，供裁）**：① 候选「放松/缩小 Ø6.0 keepout」**不是出路** —— Ø6.0→Ø5.0 只把 H3 最小位移从 35.3 改善到 34.8mm（`H3-MECHANICAL-INPUT-GAP` §4）；② 该 keepout 的依据本身被 SPEC 自记**未推导**（`pd.zone_defs.m3_keepout_note`：「无 M3 孔实例；若未来开孔需重推导」）。

## 2. 监理（自有权内；**5 项待裁 + 1 项登记**）

| # | 待裁 | ENG 建议 | 证据（sha256/16） |
|---|---|---|---|
| **S-1** | J-9 / M-13 门禁接线出路 **(A)/(B)/(C)** | **(A)** —— 真源 bump 补 `nc` 白名单(105) + 处置 `PWR_5V_KEY` + 出 BOM（已证**充分**：meta-gate PASS + `verify` **3/3 PASS**，不会堵死 k2 提交） | `K2-P4-J9-WIRING-OPTION-A-FEASIBILITY-v1.md` `b4631b5f5f3d1458` |
| **S-2** | C5b/IN-7 口径强度（5 开关 vs 4 开关） | **认已裁 5 开关口径**（现状 PASS）；更强齿须走廊级移铜 | `K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md` `21e6b1d26084084d` |
| **S-3** | 「铜到板边」口径**登记**（内层盲孔） | **只登记**（JLC ≥0.2 已 PASS：实测最小 0.256）；**不加齿、不移铜** | `K2-P4-EDGE-CLEARANCE-INNER-VIA-SCOPE-v1.md` `4dab972bf45b9f89` |
| **S-4** | **W-7 九条逐条批** | 4 条零命中 ⇒ `ignore→warning`（自证）；余 5 条按方案 | `K2-P4-W7-IGNORE-DISPOSITION-v1.md` |
| **S-5** | **manifest 正/负控复验 + 签认**（含 §4 七项口径 + `board:` 转写 l4→l5） | 按提交件执行 | `K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md` `2ef6278fe63ef204`；**36 条 warning 的逐条签名已由 ENG 交**（`K2-P4-WARNING-DISPOSITION-MEASUREMENT-v1.md` `86142e37b30137e6`，disposition 留空待监理填） |
| **S-6** | 提交件 §4 的七项口径：J-8 关键间距 · density 阈值 · `drill_pth_min` · V3 严格语义 · J-7 覆盖守卫 · J-9 · C5b | 逐项见提交件（ENG 不代填阈值） | 同上 |
| **S-6a** | **J-8「密度分布」的登记来源需先认口径**：登记册 **M-12** 原文为「左半 30/42、右半 12；**三横带占用 19–27%**」，审计复算**复现不出**（按「器件焊盘外接框 ∩ 带面积 / 带面积」实测 **5.3% / 17.8% / 0.7%**，`M-12 = 口径不明，须补定义`）。草案现用「**10mm 格峰值件数**（实测峰值 5、26 格：分布 {1:9, 2:7, 3:6, 4:2, 5:2}）」仅为**提案**。⇒ 请监理在「①M-12 横带占用比 ②10mm 格峰值 ③其它」中**择一口径**，ENG 按口径实现 + 报告实测 | — | 本件 + 提交件 §4-1 |

## 3. 答复后的执行序（**一次到位；禁越阶段**）

1. **O-1** ⇒ H3 重解 4 孔 + `12V_IN` 接入（L2 自裁域，守恒闸：边料/净空/复跑 sha）
2. **O-3** ⇒ strap 端点处置（L2）
3. **O-2** ⇒ W-8 落地（判据容忍或源侧重落，二者其一）
4. **S-1** ⇒ `k2/pipeline.yaml` 接线（+ 真源 bump 或分阶段）
5. **S-4 / S-5 / S-6** ⇒ manifest 安装 + 签认（`not_countersigned → false`）
6. ⇒ 判定器**全绿** ⇒ **P4 完工申报**（判定归监理）⇒ **W-10 出 Gerber**：8 铜层 + 阻焊/丝印/边框/job + Excellon（含 HDI 盲埋孔）+ 叠层图 + 阻抗表 + MANIFEST；DFM 逐项对 JLC HDI 通道全 PASS
7. **P5**（打样 + 首件 bring-up）在 **P4 关门后**才开

## 4. ENG 侧声明

- 以上各轮：**未改板**（`d9813bc554a2d611`）/ SPEC（canonical `acc64b447ef55e90`）/ 判据 / 真源 / 生成器；`criteria/` 未动；未派 WORKER；未越阶段。
- **ENG 侧已无「既未阻塞、又能在 P4 内推进」的动作** —— 剩余 7 项 FAIL 与 3 条 owner 闸已一一映射到 §1/§2；此外仅剩「自检」（非目的）。
- 任一 **O-*** 或 **S-*** 答复后，ENG 可在同一轮内落板/落件，并逐条报 **sha + 判据复算**（**不报「接近」**）。

## 5. 证据件索引（全部在仓内，sha 可复算）

| 件 | sha256(16) |
|---|---|
| `K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md`（判据缺口补齐：转写 + 正/负控 + 七项口径） | `2ef6278fe63ef204` |
| `K2-P4-J9-WIRING-OPTION-A-FEASIBILITY-v1.md`（J-9 出路 (A) 可行性证明） | `b4631b5f5f3d1458` |
| `K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md`（C5b 口径 + 更强读法不可达） | `21e6b1d26084084d` |
| `K2-P4-H3-MECHANICAL-INPUT-GAP-v1.md`（H3 真阻断 + 缩 keepout 被否） | `4532740a33213fcc` |
| `K2-P4-EDGE-CLEARANCE-INNER-VIA-SCOPE-v1.md`（铜到板边内层盲孔口径） | `4dab972bf45b9f89` |
| `K2-P4-SPEC-REV40-TOOLPIN-ERRATA-v1.md`（SPEC 工具 pin 勘误） | `6900a29e6fc26076` |
| `K2-P4-W7-IGNORE-DISPOSITION-v1.md`（W-7 九条逐条方案） | 见件内 |
| `K2-P4-WARNING-DISPOSITION-MEASUREMENT-v1.md`（36 条 warning 逐条签名 + 依赖映射） | `86142e37b30137e6` |
| 草案件 `drafts/p4-manifest-completion-v2/`（manifest/adjudicate/make_negatives/README） | `360b3d1cf377bedb` / `f7b23e99dc277ec6` / `8a000f5c294e3a8d` / `d5f5051c6aa2f8da` |
| 草案 `drafts/j9-wiring-option-a/`（errata-2 / BOM / pipeline 草案） | `bdacbf944ca0c796` / `ce2bb814f31be54b` / `b74d1f1e883c2ca3` |
| 草案 `drafts/h3-mech-input/h3_scan.py`（H3 最小位移扫描） | `b2c5b78b6dbb4e75` |

—— ENG（ARCHER）· 2026-09-17
