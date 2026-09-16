# L2 自裁裁定 —— **In5/In6 层角色口径收口（U2）** v1

> **性质**：**不新增决策**，只作**口径收口 + 留痕**。`In5 = signal / In6 = GND` 系
> **2026-09-12 L2 叠层分配自裁**（CO-67 / CO-68 / CO-73）并在 canonical SPEC `rev-5/rev-6/rev-7` 在册；
> 本件把 **owner 裁决件的历史字母表** 与 **canonical / 交付板** 的冲突（handoff §4 U2）
> 正式判为 **历史残留**，并收口 `L2-ERRATA-8L-v1.md` §4 与 `README-canonical.md` §3 的「待裁」项。
> **授权**：owner 常设裁定（指令 #14）—— **叠层分配属 L2 自裁域**；「改叠层拓扑」议题**已作废**。
> **VETO 保留**：监理依职权可否决 / 回写（回滚路径见 §5）。
> **作用域**：本目录非冻结件；**未改**任何冻结件 / SPEC 原件 / 板几何 / `criteria/`。

## 1. 判定

| 项 | 判定 |
|---|---|
| **canonical 层角色** | **GND 平面 = `In1/In3/In6`**；**信号 = `F/In2/In5/B`**；电源 = `In4`（双区拆分） |
| **owner 裁决件** `stackup_8layer_decision.md`（`552b2fb922cd8f53`，2026-08-19）的 `F/G/S/G/P/G/S/B` 表 | **历史口径（层名旧标）** ⇒ 仅**逐层字母表**作废；该件「**8 层定案**」本体、料号 `JLC08161H`、成本/SI 背书等依据**全部继续有效**（其实体语义 = 平面在职次序，见 §2-1） |
| **是否升级 owner** | **否** —— 本件无 L1 事项：不改拓扑 / 接口 / 信号流向 / 球重映射，不新增几何 |

## 2. 依据（三重，均可复跑）

### 2-1 canonical SPEC 内源（**决定性**：该角色早有 L2 自裁在册）

| 出处 | 原文要点 |
|---|---|
| `SPEC_k2_v4.spec-rev-5.json` → `_spec_rev_5`（2026-09-12） | `authority`: **「L2 叠层分配自裁（CO-66/CO-68；CO-67 红线张力裁定 = L2）」**；`changes[1]`: **「stackup.*.Cu：In5 signal / In6 GND（方案(a) 平面在位次序；层数/平面数/电源域不变）」** |
| `SPEC_k2_v4.spec-rev-6.json` → `_spec_rev_6`（2026-09-12） | 「`pd.gnd_planes: In5.Cu -> In6.Cu`（LID REV6：**In5=信号、In6=GND**）」「`pd.zone_defs.gnd_planes[In5] -> In6.Cu`（**层名更正；形状/网不变**）」 |
| `SPEC_k2_v4.spec-rev-7.json` → `_spec_rev_7`（2026-09-12） | `authority`: **「L2 PDN/叠层分配 自裁（CO-73；PDN·层角色声明一致性终扫）」**；「`layer_plan.in6_usage`：更正为 REV6 In6=GND 平面（在册）」 |
| canonical `SPEC_k2_v4.spec-rev-24.json`（`317140048c80a569`） | `stackup.In6.Cu` = `"GND_PLANE (full)"`；`stackup.In5.Cu` = `"signal (PCIe + escape)"`；`layer_plan.in6_usage` = 「…In6.Cu = **GND 平面**（4 平面之一；信号层 = F/In2/In5/B）。**CO-73 更正**：原文『8L In6.Cu semantics…』为 **6L 时代残留**」；`impedance.per_layer.In5.Cu` = `symmetric_stripline` refs `[In4, In6]` |
| `SPEC_k2_v4.spec-rev-7/16/24` 共有 | `zone_defs.decoupling_via_to_plane.rule` = 「GND pad via 直达 **In1/In3/In6** GND 平面」 |

⇒ 「In5/In6 待裁」= **陈旧登记**：canonical 侧自 **2026-09-12** 起即为 `In6 = GND`，且已由 **L2 自裁**（CO-67 / CO-73）在册，非新决策、非 owner 闸口。

### 2-2 交付板实测（ENG 自解析 `k2/hw/k2_v4_8L.l4.kicad_pcb`，sha16 `d4e81f647be7f980`；未复用历史结论）

- **段层分布**（全板 2512 段）：`F.Cu 359` · `In2.Cu 106` · **`In5.Cu 2008`** · **`In6.Cu 0`** · `B.Cu 39`
  ⇒ **In6 无任何信号段**（平面），In5 承载 PCIe / 逃逸。
- **zone 13** = **4 个无网 `F.Cu` 保留区**（`ESC_J2/J3/J4/U6`，`filled_polygon = 0`）
  + **9 个铜区**（`In1/In3/In6 = GND`；`In4 × 6` = `12V_IN / MCU_VDD / P3V3 × 2 / P3V3_AUX × 2`；`filled_polygon = 0`）
  ⇒ 与 **#K2-17 §二 C7 口径（9 铜区）逐项一致**。

### 2-3 判据面

`criteria/adjudicate.py`（`897e8bfde60e2cfe`）· `criteria/manifest.k2.yaml`（`7ce08757eff25557`）：
grep `in5|in6|stackup|layer_plan` **零命中** ⇒ **判据面零影响**（同 #K2-16 §1-4 结论）。

## 3. 影响面

- **P3 图集**：`L3/drawings/04_layer_assignment.svg` 已按本口径出 ⇒ **无需重出**（P3 判据集合不变）。
- **P3 门**：本件**不属 P3 判据项** ⇒ 不改变 **U1**（P3-3 / P3-6 复算）与 **U3**（P4 开工令）的待监理状态；**P4 仍 fail-closed**。
- **P4**：输入前置 `IN-1..IN-9` 不变；C7 口径（**9 铜区**）不变 ⇒ **无新增项**。
- **文档侧**：`README-canonical.md §3` 由「待监理裁」改为**已收口**（引本件）；`L2-ERRATA-8L-v1.md` §4 的请裁项由本件收口。

## 4. 若 owner 主张「按 owner 表实作」

= **改叠层拓扑**（`In5` ↔ `In6` 互换）⇒ 属 **L1**（拓扑 / 信号流向），且与「**交付板永不改**」
「工艺冻结 A / 拓扑变更议题已作废」冲突：需 **全板重布**（In5 实数 2008 段 / In6 0 段；
PCIe 长廊、阻抗券、逃逸全链重算）。**ENG 不执行**；须由 owner 明示重开 L1 方可议。

## 5. 留痕 / 复核 / VETO

- **本件**：`L2_RULING_in5_in6_role_v1.md` —— sha256 **不自载**（避免自指），以 `.omo/start-work/ledger.jsonl` 本轮记录的全文 sha256 为准。
- **连带收口**：`README-canonical.md`（v1 `1ad55180c4c74e65` → 本版，新 sha 见台账本轮记录）。
- **红线遵守**：未改 `d4e81f64…` / `fb07d25a…` / `dd794c54…` / `SPEC rev-19..24 原件` / `criteria/` 两份 /
  `L1·L2 frozen`（0444，ENG 只读）；未写 `.omo/supervision/**`；未派 WORKER；无 `/tmp` 依赖。
- **VETO 路径**：监理若裁「以 owner 表为准」⇒ 回退本件 + `README-canonical.md §3` 回滚至 `1ad55180c4c74e65`，
  转 owner L1 流程；本件其余内容（实测/依据）仍可作为证据保留。
