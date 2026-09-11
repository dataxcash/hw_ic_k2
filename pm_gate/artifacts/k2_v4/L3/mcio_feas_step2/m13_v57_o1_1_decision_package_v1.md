# m13 v57 — **O1-①（第 4 信号层）决策包 v1**（整改通知 #01 响应）

> 2026-09-11｜作者：ARCHER（执行侧，只论证不实施）｜触发：整改通知 #01（监理）
> 前置：P8 干净复测（canonical WIN2.5 域）——净距关 ⇒ R1 32/32；fab-limit 放宽 ⇒ R1 29/32
> **本包不含任何 stackup/加层实施**；owner 未裁前禁止实施（§0 红线）。

## 0. 闸口合规（Gate）
| 项 | 实测 |
|---|---|
| 冻结四源 SHA 前缀 | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` — **4/4 MATCH** |
| canonical `m13_v57_w3_joint_assignment.json` | **revision=W3-CN.25、verdict=FEASIBLE_ALL、certificates=0**（未被探针就地覆写） |
| `git -C k2 status`（tracked） | 仅 `? _shared`（既有冻结偏差）；无 canonical 工件被就地覆写 |
| 探针临时物 | 全部落 **`/tmp/opencode/`**（109 件）；仓库内无探针落盘 |
| 未实施 stackup/加层 | ✅（本包仅论证） |

## 1. O1-① 语义：两种解释与可行性
**(a) 新增物理层（6L → 8L restack）**：在现有 6 层之外**新增**铜层作第 4 信号层。
**(b) 复用既有非信号层（In1 / In3 / In4）**：把某个平面层改作信号层。
- SPEC `/stackup`（冻结）：`F.Cu`=PCIe diff microstrip（**ref In1 GND**）+ chip escape；`In1.Cu`=**GND_PLANE（full）**；
  `In2.Cu`=**唯一内层信号层**（stripline，**dual GND ref**）；`In3.Cu`=**GND_PLANE（full）**；`In4.Cu`=**POWER_PLANE（P3V3）**；`B.Cu`=signal。
- ⇒ **(b) 不可行**：In1/In3 是 F/In2/B 的**参考平面**，改作信号 ⇒ 参考平面连续性破坏（微带/带状线阻抗与回流路径失效）；
  In4 是 P3V3 电源平面 ⇒ owner 已驳（PD 红线）+ PI 破坏。**故 O1-① 只能是 (a)：新增物理层。**
- SPEC `/material`：`JLC 6L stackup (JLC06161H ...; SI9000 final after freeze)` ⇒ (a) = 6L→8L，**改板厂叠层**。

## 2. PD/SI 评估（改叠层的后果；实施前置要件）
| 维度 | 现状（冻结） | 加第 4 信号层的影响 |
|---|---|---|
| 叠层 | 6L：F(sig)/In1(GND)/In2(sig)/In3(GND)/In4(PWR)/B(sig) | 6L→8L：新增介质+铜；**层序/厚度/Er 全变** ⇒ SPEC `/material` 与 `/stackup` 须重冻结 |
| 参考平面连续性 | F ref In1；In2 ref In1/In3；B ref In3 | 新增层改变参考距离/平面排列 ⇒ **F/In2/B 的参考连续性需重判**（可能出现跨分割回流） |
| 阻抗/回流 | 85Ω diff ±10%，`w=0.205 / g=0.175`，模型 `JLC_SI9000_H1_5.0mil_Er1_4.3`，`coupon_required: true` | 叠层变 ⇒ SI9000 模型失效 ⇒ **须重推 w/g + 重做阻抗 coupon**；回流路径随参考层变化 |
| 电源完整性 (PI) | In4 = 单 P3V3 平面（DS320PR1601 VCC1-4 30 balls） | 新增信号层挤压 PWR/GND 平面间距/面积 ⇒ **平面电容/PDN 阻抗需重评** |
| 制造 | JLC06161H（6L 工艺） | 8L 需不同工艺/叠层（新 process id）⇒ **DFM/报价/交期重评** |
| 冻结链影响 | G0/G1 基线 + D0 裁决（In4=电源） + 四源 | **SPEC 层意图/叠层属冻结件** ⇒ 加层 = **系统设计变更**，须 owner 签 + 全链 re-baseline |

**结论**：O1-① = **6L→8L 系统设计变更**（非项目层）；须先有 SI9000 重推 + 阻抗 coupon + PI 重评 + 制造重评 + 全链 re-freeze。

## 3. 最小物理变更优先的替代矩阵（逐项实测状态与代价）
| # | 杠杆 | 实测状态（canonical 域） | 代价/边界 |
|---|---|---|---|
| A1 | **逃逸域扩宽**（F-13 WIN 2.5→3.5） | **已测：无效**（域 195,916→571,904 rows；净距下仍 29/32） | 项目层（低）；**已耗尽** |
| A2 | **F-5 帧/lane 序修订（lane 按源序）** | **已证不可行**（card v1.3 §R-8 闭式证明：chip 侧 lane 序 vs 连接器落点 y 序对 (J4dn,J4up) 要求相反） | 项目层（低）；**闭式排除** |
| A3 | **净距放宽（fab-limit，逃逸/过渡区）** | **已测：不足**（P7/P8：0.305/0.3775/0.45 ⇒ R1 29/32） | 项目层（低，owner 已批）；**已耗尽** |
| A4 | **新构造拓扑 T-5 / T-5′**（3 层通道 / 层变点移走廊入口） | **已测：更差**（T-5′ same_layer 477；T-5 完整 106；R1 29/32） | 项目层（中）；**已试 2 族** |
| A5 | **连接器/球重映射**（改 net→pad 归属） | **未测** | 触**权威网表/连接器映射**（系统设计）→ 需 owner；收益未知（可重排落点序，或解 A2 的序冲突） |
| A6 | **全局不可行证明**（对所有合法构造类） | **未做**（W3-FCC.1 仅**构造域**证书） | 研究级（高）；若成立则合法终止 |
| A7 | **第 4 信号层（O1-①）** | 未实施（§1/§2） | **系统设计变更（高）**；须 PD/SI + 重冻结 |

**优先级（最小物理变更）**：A5（改映射，系统设计但不动叠层）→ A6（证明，零物理变更）→ A7（加层）。A1–A4 已耗尽。

## 4. 建议与待裁项
1. **不建议直接加层**：A1–A4 已耗尽但 **A5/A6 未试**——按"最小物理变更优先"，应先裁 **A5（连接器/球重映射，需 owner）** 或 **A6（授权全局不可行证明）**。
2. 若 owner 仍选 **O1-①**：须同时批准 **§2 的 PD/SI 前置工作**（SI9000 重推 + 阻抗 coupon + PI 重评 + 8L 制造重评 + 四源/SPEC 层叠 re-freeze）——**本包不实施**。
3. canonical `W3-CN.25` 与四源在本包中**零变更**。

## 5. 可复现（命令 + 原始输出）
```bash
# 闸口
sha256sum k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json \
  k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json \
  k2/k2_v4.kicad_pcb k2/_shared/eda_core/drc_rules.json | cut -c1-16
# -> 0bd52ed48e720b8c / a8ef3ea8ecff99d7 / f6273de613f43d05 / 0a459839e15960b8
python3 -c "import json;d=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment.json'));print(d['revision'],d['verdict'])"
# -> W3-CN.25 FEASIBLE_ALL
# P8 干净复测（探针在 /tmp/opencode；canonical 域）
python3 /tmp/opencode/probe_engine_noclr_canon.py --quiet --out /tmp/opencode/pc_noclr_canon.json
python3 /tmp/opencode/probe_engine_relief_canon.py --quiet --out /tmp/opencode/pc_relief_canon.json
# 原始输出（resource_gate.verification_check）：
#   noclr_canon : r1_assigned=32 / 32   same_layer_crossings=0     (= 基线干净)
#   relief_canon: r1_assigned=29 / 32   same_layer_crossings=28    (= fab-limit 放宽仍不足)
```
（原始 JSON 见 `/tmp/opencode/pc_noclr_canon.json`、`/tmp/opencode/pc_relief_canon.json` 与
`m13_v57_w3_full_clearance_infeasibility_cert.json` 的 P0..P8。）
