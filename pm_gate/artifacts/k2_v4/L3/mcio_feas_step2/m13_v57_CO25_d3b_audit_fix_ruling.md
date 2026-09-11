# CO-25 — 【L2 自裁】D3b 判据修正落地：独立复核器 pad 净距**双缺陷**修复 + 6 条真缺陷定域；D3c 自裁决策

> 2026-09-12｜裁判：ARCHER（续接会话 ARCHER-2）｜依据：CO-24 §2/§3｜性质：**工具判据修正 + 归因收口（不改几何、不改 DRC 判据）**

## 0. 结论
`tools/p3_v57_co11_placement_verify.py` 的 pad 净距判据有**两个独立缺陷**（CO-24 只识别了第 1 个），修复后
对 CO-23 几何给出 **6 条真缺陷**，且与 shop DRC **逐值吻合**。修正为 **opt-in**（`CO11_PAD_UNITS=copper`），
默认 `centerline` = 旧行为，**W3-CN.37 / ALLOC.4 证据仍逐字节可复现**（已实测 legacy 仍 PASS 0）。

## 1. 缺陷（实测）
| # | 缺陷 | 后果 | 证据 |
|---|---|---|---|
| 1 | **量纲**：`seg_pad_gap/pad_gap_pt` 返回**中心距**，却与 `ESC=0.075`（SPEC 逃逸区**铜距**下限）比较，少减 `width/2=0.1025`（via 少减 `via_r=0.175`） | 判据放宽 0.1025 | CO-24 §2 |
| 2 | **几何近似**：`seg_pad_gap` 用「pad 中心在段上的投影点 → pad 矩形」近似，**高估**净距；pad 中心投影非真实最近点 | 假阴性 | `DN_OUT5_N`：近似给中心距 0.2452（铜距 0.1427 PASS），真值 0.1607（铜距 **0.0582**，shop DRC 同值） |
| 3 | 层盲：via-pad 检查不判层，埋孔(In2/In6)被拿来与 F.Cu SMD pad 比 ⇒ 13 个假阳性 | 假阳性 | `via(57.4,42.9)[In2,In6]` 正压 J3 B12-B15 pad 但无共层 |
| 4 | 豁免过宽：豁免「本页 4 pad」含**对侧极性 conn pad**，掩盖同页 P/N 之间的接入侵入 | 假阴性 | shop DRC `DN_OUT5_P × J4 A6[DN_OUT5_N] 0.0582` 被漏 |

修正（copper 模式）：真值 `seg_rect_gap`（含相交判定 + 非相交段端点最小距）+ `"F.Cu" in ls` 层判 +
按段落点极性收紧豁免（自有 conn pad + 芯片 pad）。

## 2. 修正后真缺陷（6 条，全在 J4 pad 场；`m13_v57_co25_pad_clearance_audit_copper.json`）
| 页面 | pol | 铜距 mm | shop DRC 对应 |
|---|---|---|---|
| `PCIE_DN4/out_MCIO` | P / N | **-0.0833** | `shorting_items` DN_OUT4_P × DN_OUT4_N（J4 A2 侧） |
| `PCIE_DN5/out_MCIO` | P / N | **0.0582** | `clearance` A6[DN5_N]×DN5_P / A7[GND]×DN5_N（**逐值同**） |
| `PCIE_DN6/out_MCIO` | P / N | **-0.0833** | mask bridge DN_OUT6 P×N（同区） |
⇒ 均为 `y=60.2 → 61.45` 的 0.9mm 斜向接入段（`#fcu_pad`），斜穿邻 pad。
**修正方向（下一周期几何）**：改为「45° + 竖直」狗腿，竖直段落在 pad 自身 x ⇒ 邻 pad 铜距 ≈0.3475（≥0.075 与 ≥0.175 均满足）；
仅动 3 页 F.Cu 接入段，不动 via/lane（L2）。

## 3. D3c 自裁（L2，非 L1）
shop DRC（`k2_v4_8L.kicad_pro`：PCIe85 0.175 / POWER 0.2，无 `.kicad_dru`/rule area）与**冻结 SPEC** `escape_transition_zone`（ECN-001）
不一致：0.4mm 节距接入段 0.175 铜距**物理不可行**（需 0.555 包络）。此项**不属 L1**（非拓扑/接口/信号流向/电源域/球重映射）⇒ **自裁，不停 owner**：
**裁定 (a)**：以**版本化 `*.kicad_dru` 规则域**实现 SPEC 已冻结的逃逸区（铜距 0.075），scope = J2/J3/J4/U6 pad 场矩形；
域外维持 0.175/0.2。性质 = **实现 SPEC**，非放宽 SPEC（SPEC 明文 `escape_clearance_mm: 0.075`，且 2026-08-16 已冻结）。
落地放在下一周期（改动 DRC 判据须与 L5 signoff 同批版本化 + 变更单，避免与几何混批）。

## 4. 未决（下一周期顺序）
1. **上游**：`m13_v57_CO25_upstream_change_request_W0R_refclk_keepout.md`（D3a 的模型输入缺口，禁暴力迭代）；
2. **D3b 几何**：3 页（DN4/5/6 out_MCIO）接入段改狗腿（消 6）；
3. **D3a**：W0-R 补齐后重导 refclk（消 60）；
4. **D3c**：落 `.kicad_dru` 规则域 + L5 signoff 同批版本化；
5. 全链 G4→G7 → new=0 → milestone tag。

## 5. 红线 / 未改物
未改四冻结源（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`）、未改 `k2_v4_8L.kicad_pro`、
未改引擎、未改任何板/图纸/ALLOC/引擎产物；几何零改动；引擎 AST `while=0`。
