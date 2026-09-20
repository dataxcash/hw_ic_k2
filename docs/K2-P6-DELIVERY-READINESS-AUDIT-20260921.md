# K2 · 交付就绪核对 + 阶段门闭合结论（2026-09-21 · 监理自动续推轮）

**性质**：只读核对（按已批准《K2 整体整改计划》· 阶段门 fail-closed）。**未改**真源/判据/生成器，**未新增判据维**，**未落**批 6 候选（release-gated）。

## 0. 阶段门总态（当前阶段 = P6）
| 阶段 | 判据态 | 依据（live / 裁定） |
|---|---|---|
| P0 | HOLDS | 冻结四源逐字节同 |
| P1 | HOLDS | 负控 l4 rc=1 · 正控伪造 verdict 被拒 · 权限 444/555 · fail-closed · rev=3 在岗 |
| P2 | HOLDS | #K2-15 关门 + l7 三等式差 0 |
| P3 | HOLDS | 120×46(y[33,79]) · NPTH 4×Ø3.2 · 出框 0 |
| P4 | HOLDS | canonical 19 = 19 OK/0 FAIL · verdict `190b73be0f728a56` |
| **P5** | **PENDING_EXTERNAL** | V4–V7 `NOT_RUN`（实测方外部，ENG 不得自证） |
| **P6** | **判据面 PASS** | ① `k2_p6_1_acceptance_v1.py` ⇒ **PASS(rc=0)**；② `k2_p6_2_acceptance_v1.py` ⇒ 结构差异 **0** ⇒ PASS(state) |

⇒ 按计划 §②，**P0–P4 与 P6 阶段门判据均已达成**；**唯一未闭阶段门 = P5（外部实测）**。**未发现越阶段**。

## 1. owner #14③ 完工定义 · 十项逐项（10/10）
| # | 要件 | 证据 | 判 |
|---|---|---|---|
| 1 | 8 铜层 | `01_gerber_rs274x/` 14 件 = 8 Cu + 2 Mask + 2 Silk + Edge_Cuts + gbrjob | OK |
| 2-4 | 阻焊/丝印/边框 | F/B_Mask · F/B_Silkscreen · Edge_Cuts | OK |
| 5 | job | `k2_v4_8L.l7-job.gbrjob` | OK |
| **6** | **Excellon 含 HDI 盲埋孔** | 板 **729 via / 非通孔 448（61.5%）**：F→In1 168 · F→In2 128 · F→In4 4 · F→In5 19 · In2→In5 92 · In5→B 37 · F→B 281；`02_drill_excellon/` **7 个 .drl**：主档 T1 0.2mm×281(通孔) + T2 0.8mm×16(PTH)，另 6 档层对专档（168/128/92/37/19/4）**逐档孔数与板普查相等** | **OK** |
| 7 | 叠层图 | `03_stackup/HDI_stage_diagram.svg`（内嵌 as-built 448/729 + 7 层对 + 板 sha）+ `JLC08161H_stackup.svg` | OK |
| 8 | 阻抗表 | `04_impedance/`（85Ω±10% ⇒ 76.5–93.5Ω；M1/M2 双模型；**F.Cu 最紧 0.2825mm 具名披露 ⇒ ΔZ≈−0.84% 仍落窗**） | OK |
| 9 | MANIFEST 逐文件 sha256 | `MANIFEST.json` 53 件（逐件 sha256+bytes） | OK |
| 10 | DFM 对 JLC HDI 通道 | `06_rulings/jlc_dfm_hdi_l7.json` ⇒ **16 PASS / 1 ACCEPT / 0 FAIL** | OK |

## 2. 交付锚完整性（本会话实测）
- `MANIFEST.json` = `6ee7495de61f749f` · tarball = `0e88e107e2da8192`（**冻结锚未移动**）
- **53/53 件 sha256 + bytes 全部相等**；无缺失件、无 MANIFEST 外多余件
- tarball 解出 54 件与 `jlc_package/` **逐字节同**（无 only-in-tarball / only-in-package / 内容差异）
- `MANIFEST.board_sha16` = 盘上 `l7` = `c5a7df90aadb66e0` ✓

## 3. 已知残余（均已登记，非阶段门要件）
- **ACCEPT（1 项）**：阻焊坝 9 处 <0.09mm ⇒ 板厂按「无阻焊坝」印制；**已实证回退修法**（`pad_to_mask_clearance` 0.05→0.02 ⇒ 9→0）属**改板级**，本次打样不做。
- F.Cu 少数耦合点低于 SPEC **名义几何窗**（0.2825 < 0.295）⇒ 具名披露，阻抗目标仍满足。
- 正面丝印越框 4 处（H4/R41/D2/C87）⇒ 板厂按框裁剪（装饰级）；铜层越界 0。
- JLC HDI 通道**具体限值**（阶数上限/激光孔径比/介质厚）属**板厂 DFM 答复 = 外部输入**（L2 裁定 §5 已登记）。
- 批 6（K1 同源模型覆盖增强 v4）**非阶段门要件**，**待监理放行**后按手册 7 步落件。

## 4. 结论
ENG 侧整改程序在**判据面已闭合**；交付包按 **owner #14③ 十项齐备且锚完整自洽** ⇒ 具备对外交付条件（下单/报价/交期属商务，#14④）。**唯一未闭阶段门 = P5 外部实测**（V4–V7 回件前 ENG 不自证）。
