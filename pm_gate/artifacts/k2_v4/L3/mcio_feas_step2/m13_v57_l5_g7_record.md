# m13 v57 — **G7（L5 sign-off + 知识提升）记录：FAIL → REOPEN owning layer**

> 2026-09-11｜卡：`m13_v57_l5_kickoff_card_v1.md`｜检查器：`tools/p3_v57_l5_signoff.py`（只读取证；KiCad pcbnew/kicad-cli 10.0.5）
> ｜主体：L4 板 `k2_v4.l4.kicad_pcb`（sha `33ded90443f2e2c2`）vs 冻结基线 `k2_v4.kicad_pcb`（`f6273de6…`）

## 1. 结论
- **G7 = FAIL**（记录已出，证据如下）。按 rollback 规约：**reopen owning layer（W3/L4）**；**不得在 L5 就地修**。

## 2. 记录与证据
| 记录 | verdict | 关键数 |
|---|---|---|
| `m13_v57_l5_fab_record.json`（`51f6a759…`）| n/a | 6 铜层；track/via/net 计数 + 钻孔表 + 指纹 |
| `m13_v57_l5_dfm_dft_record.json`（`23c2b327…`）| **FAIL** | DRC：冻结基线 43 → L4 **496**；**新增 453** = `{clearance:171, shorting_items:117, hole_clearance:26, copper_edge_clearance:26, solder_mask_bridge:110, hole_to_hole:3}`；未连项 416→352 |
| `m13_v57_l5_si_pi_emc_record.json`（`c2bf87a8…`）| **FAIL** | 线宽 0.205 合规 ✓；**对内等长 max skew = 24.476mm ≫ 0.15mm（FAIL）**；hole/mask/edge 见 DRC |

## 3. 根因（闭式、指向 W3 口径）
- **W3 度量不完整**：`same_layer_crossings` 计了「真交叉 + 共线重叠（段-段）」与「via-via 间距」，
  **未计** ① **track↔track 净距（平行最小间距）** ② **via↔track 净距** ③ 孔-铜 / 板边铜 / 阻焊桥。
  453 条新增违例**全部涉及本 66 网**（已逐条按网名分类核实），即图纸几何在真实铜（0.205 线宽 / 0.35 via）下
  不满足净距 ⇒ **并非既有铜的旧账**。
- **SI 对内等长未纳入 W3 构造**：P/N 落点（J2 内侧/外侧槽、J3/J4 全局槽）未做长度匹配 ⇒ skew 最高 24.5mm。

## 4. 影响 / 回退
- G6（L4）的**连通性 DOD 达成**（每节点按处方连接；图纸只读；板消费一致），但其产物**不满足制造/信号签核**。
- 回退：**reopen W3**（补全度量口径 = 净距/孔铜/板边/阻焊；并纳入对内等长约束），重跑 W3→W4→L4→L5。
- L5 不修：本轮仅出证据。

## 5. 指纹
- L4 板 `k2_v4.l4.kicad_pcb` `33ded90443f2e2c2`｜图纸 `caa516abdaf8e823`（rev W3-CN.22）｜冻结四源 MATCH
- 记录：fab `51f6a759…` / dfm `23c2b327…` / si `c2bf87a8…`

## 6. 下一步（阻塞上报）
- 依宪法：**发现上游问题立即停机回上层**。W3 需补全 **净距类度量（track/via/孔铜/板边/阻焊）+ 对内等长**，
  属新的 W3 修订周期（版本化、预授权域内可实施；触及契约口径须按 ROOT-1 记录）。
