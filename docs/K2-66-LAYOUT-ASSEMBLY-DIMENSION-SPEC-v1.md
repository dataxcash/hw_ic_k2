# K2 · 新判据维 `layout_and_assembly_quality` —— 齿化规格（ENG 出件 · 待 gate 属主安装）

> 依据：**#K2-66 §三/§五-3**（owner 2026-09-21 已授权齿化）· 判据锚 **rev=6（MATCH）**。
> 本件 = **给 gate 属主（`criteria/`）的安装件**：维定义 + 阈值表 + 测量器接线。**ENG 不改 `criteria/`**（只读 · owner #14⑦）。

## 一、维定义

- **id**：`layout_and_assembly_quality`
- **语义**：板级「布局 / 可装配 / 可测试 / 制造外观」质量；**与 19 维（电气+可制造）并列**，
  **不改 19 维任何一条**（零放松下限 · C-12）。
- **测量器**：`k2/tools/k2_layout_quality_check_v1.py`（`8146dc74985bae79`）——**只测量 · 不置 status**；判定权归监理。
- **权威口径**：`silk_over_copper` 与 `courtyards_overlap` **以 `kicad-cli pcb drc` 为准**（见 §三 具名说明）。

## 二、阈值表（= #K2-66 §三 · 逐字）

| 子项 | 阈值 | 测量 |
|---|---|---|
| fiducial | ≥2（3 推荐 L 形）· Ø1.0mm · 开窗 2× · 距边 ≥3.35mm | footprint pad |
| 测试点 | ≥1/电源轨 + 高速通道 · 周围 2.5mm 无器件 | footprint pad |
| 极性 / 1 脚丝印 | 极性件 100% | fp silk 图元 |
| 器件轮廓丝印 | 100% | fp silk 图元 |
| 板卡信息 | 板名 + 版本 + 日期 | title_block / gr_text |
| silk 压铜 | **0** | **kicad-cli DRC `silk_over_copper`** |
| courtyard | 100% · 无重叠（IPC-7351B） | fp F.CrtYd / DRC `courtyards_overlap` |
| 板框圆角 | ≥1–2mm | Edge.Cuts arc |
| 铜平衡 | 40–60%/层 · 层间差 ≤15–20% | 铜面积/板面积 |
| **90° 直角** | **0**（强条 R4-1） | 走线拐角角 |
| 高速线过孔 | ≤2/线（强条 R1-5/R5-1） | via/网 |
| 对间 3W | ≥0.875mm（强条 R3-2） | 走廊（已裁 B3） |

## 三、具名说明（**不得隐去**）

1. **`silk_over_copper` 口径**：l8 基线 `kicad-cli pcb drc` 实测 = **37**（= #K2-66 表 A6 之数 ⇒ 该行权威口径 = kicad-cli DRC）。
   `k2_layout_quality_check_v1.py` 现用「丝印 bbox ∩ 焊盘 mask 开窗 bbox」= **亚口径**（l8 上给 39），
   **与 kicad-cli 有系统偏差** ⇒ **齿化必须以 kicad-cli DRC 数为准**；测量器须按 §四 对齐。
2. **courtyard 覆盖 vs 无重叠**：本板器件密集 ⇒ 「100% 覆盖」与「无重叠」可能联合不可满足
   （同 #K2-21 courtyard 联合不可满足先例）⇒ 若不可满足须**监理裁**（本件不预设）。
3. **高速线过孔 ≤2/线**：l8 实测 32 条 PCIE 车道均为 **4 via/线**（层序 F→In2→In5→B）⇒ **须重布线**（见证据件 §remaining）。

## 四、测量器待对齐项（ENG 后续 · 非本件阻塞）

- `silk_over_copper`：改用 `kicad-cli pcb drc --format json` 的 `silk_over_copper` 计数（或精确 mask 孔径几何）。
- `courtyards_overlap`：改读 DRC。
- `90°`：与 DRC/强条口径对齐（现为自解析拐角角）。
- 新增 `B3`/`B4`（3W/蛇形）读数。

## 五、安装（gate 属主）

`criteria/manifest.k2.yaml` 增 `layout_and_assembly_quality: {enabled: true, expect: "...", source_of_truth: "<drill/board>"}` + `criteria/CHANGELOG` 记 rev 递增（**属主执行**；ENG 不写）。
