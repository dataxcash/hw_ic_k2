# K2 · P4 · H3 的真阻断：**缺「载板机械接口」输入** + 「缩 keepout」被实测否定 · v1 · 2026-09-17

> 性质：ENG 只读取证 + 量化。**未改板 / SPEC / 判据 / 真源**。判定权归监理；owner 输入见 §5。
> 依据：监 (a) `#K2-19 §一-3`（H3 重解的三个约束与「无解即回报」）；(b) `#K2-19 §一-3 禁止②`（**缩 Ø6.0 须有「载板/standoff 头径 ≤ Ø5.x」的外部依据**）；(c) handoff §5-5 三候选 (a)(b)(c)。

## 1. 结论（三句）

1. **H3 的唯一真阻断不是「ENG 没找到解」，而是「仓内不存在载板机械接口规格」** —— 4 孔位图案与 Ø6.0 keepout 都是 **ENG 在 L2 自造的**，其依据本身被 SPEC 自记为**未推导**（§2）。
2. **候选 (c)「放松/缩小 Ø6.0 keepout」被实测否定**：把 keepout 从 Ø6.0 缩到 Ø5.0，H3 的最小位移只从 **35.3mm → 34.8mm**（几乎不变）；即便**完全取消 keepout**，也只能降到 **5.1mm**（§4）。
3. ⇒ 需要 owner 给的是**一个机械输入**（不是在三候选里挑）：**载板 standoff 位置是否可动** + **螺钉/柱头（含垫圈）外径**。二者一到，H3 在 L2 域内可解或明确不可解（§5）。

## 2. Ø6.0 的依据：SPEC 自记为「未推导」

- `SPEC rev-44 → /constraints/m3_keepout_mm = 3.0`（⇒ 每孔 Ø6.0 全区 rule area，见板 `K2_HOLE_KEEPOUT_H1..H4`：**8 层全覆盖**，`tracks/vias/copperpour not_allowed`、`pads/footprints allowed`）。
- 同一 SPEC 叶 **`/pd/zone_defs/m3_keepout_note`** 原文：
  > 「**板文件实测无 M3 孔实例** (drill 全 0.8=pin headers, 无 gr_circle/MountingHole footprint, 2026-08-21); 规则保留, **若未来开孔需重推导**」
- `K2-ENG-AUDIT-2026-09-15.md` 记：**「固定孔与走线回避区（机械接口）没有归属层级 → 结果一个都没有（U-10）」**；`L3/drawings/README.md` 把 4×M3/Ø6.0 的出处标为「**L2-1/L2-2（审计 §十）**」= ENG 自己的 L2 产物。
- 全仓检索（`standoff` / `铜柱` / `固定孔` / `mounting`，排除 archive/AppDir）：**仅命中 SPEC 自身与该 note 及图纸 README** ⇒ **无任何 owner 侧机械接口规格**。

⇒ 结论：`m3_keepout_mm = 3.0` 是占位规则；**它的外部依据在仓内不存在**，而「外部依据」正是 `#K2-19 §一-3 禁止②` 允许缩 keepout 的前提。

## 3. H3 与谁冲突（对象分离）

| 冲突对象 | 性质 | 能否动 |
|---|---|---|
| `J12.1`/`J6` 排针 **pad**（x 23.38–32.50，y 带 `[33.30,37.34]`…） | 电气接口（P3-4 冻结，`column_x=27.94`，出框余量 **0.08mm**） | **不可动**（#K2-19 禁止①） |
| 左侧条带内的 **F.Cu/B.Cu/In2/In5 铜**（连接器扇出） | 路由结果（L2 自裁域） | 理论可动，但代价高 |
| `K2_HOLE_KEEPOUT_H3`（Ø6.0，8 层） | 机械件回避区（ENG 自造，依据未推导） | 需 §1-2 的外部依据 |

`H3 = (26.1, 36.1)`，Ø3.2 NPTH；其原位的直接冲突是**与排针 pad 带同带** ⇒ `hole_clearance 8 / hole_to_hole 1 / pth_inside_courtyard 3 / courtyards_overlap 2 / solder_mask_bridge 2 = 16 条`（handoff §5-1）。

## 4. 量化：keepout 半径对「H3 最小位移」的影响（只读扫描，实测）

**扫描域**：`x ∈ [24.6, 30.0]`（守 H3 原 x=26.1 列）· `y ∈ [36.1, 76.0]`，步长 0.1mm。
**约束（已实现）**：孔边到板边 ≥1.5（JLC/边料）· Ø3.2 孔对 pad 铜 ≥0.25（保守：pad 外接半对角）· 孔-孔 ≥0.25（对 H1/H2/H4 及其余带孔 pad）· keepout 圆内**无任何层的 track**、**无 via**（`copperpour` 由 KiCad 自动避让，不计 — 现板 4 区即如此且无 `items_not_allowed`）。

| keepout 半径 `r`（对应 Ø） | 该 x 带内最近可行 y | **最小位移** |
|---|---|---|
| 3.0（Ø6.0 · 现口径） | 71.4 | **35.3 mm** |
| 2.5（Ø5.0 · 裁定设想的「头径 ≤ Ø5.x」） | 70.9 | **34.8 mm** |
| 2.0（Ø4.0） | 42.4 | **6.3 mm** |
| 1.6（= 仅孔、**无 keepout**） | 41.2 | **5.1 mm** |

- **独立复现 T-23**：本扫描 `r=3.0` ⇒ 35.3mm，与 T-23 的「最近可行位距原位 **36.3mm**」同量级（差 ≈1mm，来源 = 我的 pad/边料模型与扫描域差异）⇒ **T-23 结论获独立佐证**。
- **关键读数**：`Ø6.0 → Ø5.0` 只把位移从 35.3 改善到 34.8mm（**≈0**）。真正把位移压到 6mm 级的是 `r ≤ 2.0`，即 **头径 ≤ Ø4.0**（连垫圈/工具空间在内，实际可疑）。
- **⇒ 候选 (c) 不是出路**：H3 必须在**图案上移动**（≥5.1mm，且需 keepout 近取消；现实 ≥6.3mm），与 standoff 头径几乎无关。

**模型边界（诚实声明，供监理校准）**：本扫描**未**含 courtyard 约束（`pth_inside_courtyard` / `courtyards_overlap`）与 pad 旋转，故结果是**必要条件 + 位移下界**，不是充分解；权威判定须在施工步用 `kicad-cli pcb drc`（T-8）复核。

## 5. 需要 owner 的一句话（比「三候选择一」更省）

> **载板那侧的 standoff 位置是固定的吗？螺钉/铜柱头（含垫圈）外径是多少？**

映射（两个答案 → 三条明确路径）：

| ① 图案 | ② 头径 | 结果 |
|---|---|---|
| 可动（载板无固定柱位） | 任意 | ENG 在 L2 域内**重解 4 孔**（障碍集含排针列 + 既有铜），交「4 孔位 + 逐孔边料/净空实测 + 复跑 sha」（`#K2-19 §一-3` 的必带项）⇒ H3 闸解除 |
| 固定（须与载板柱位对上） | ≥ Ø5.x | **H3 与 P3-4 冻结列在同一 x 带硬冲突 ⇒ 在当前约束下无解** ⇒ 需重定义机械接口或电气接口之一（**超 ENG**） |
| 固定 | ≤ Ø4.0 | 仍**不能**只靠缩 keepout 解决（§4：位移下界 6.3mm）⇒ 仍需图案变动；本行不构成出路 |

**ENG 建议**：请 owner 先答①。若①=可动，则 (c) 与 (b) 都不必再议，ENG 直接重解（含把 Ø6.0 依据按实际 standoff 重推导，符合 SPEC 自己的「开孔需重推导」要求）。

## 6. 复跑命令（只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# 4 孔 + keepout 定位（只读）
python3 - <<'PY'
import re
t = open('k2/hw/k2_v4_8L.l5.kicad_pcb', encoding='utf-8').read()
for m in re.finditer(r'\(pad "" np_thru_hole circle\n', t):
    s = t.rfind('\n\t(footprint ', 0, m.start())
    ref = re.search(r'\(property "Reference" "([^"]+)"', t[s:m.start()])
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)', t[s:s+400])
    print('NPTH', ref.group(1) if ref else '?', at.groups() if at else None)
for m in re.finditer(r'\(name "(K2_HOLE_KEEPOUT_[^"]*)"\)', t):
    s = t.rfind('\n\t(zone\n', 0, m.start()); e = t.find('\n\t)\n', m.end()) + 4
    b = t[s:e]
    pts = [tuple(map(float, x.groups())) for x in re.finditer(r'\(xy ([-\d.]+) ([-\d.]+)\)', b)]
    print(m.group(1), 'r≈%.2f' % (max(p[0] for p in pts) - min(p[0] for p in pts))/2,
          re.findall(r'\((tracks|vias|pads|copperpour|footprints) (allowed|not_allowed)\)', b))
PY
# 位移下界扫描（模型与边界见 §4）—— 实现件 k2/docs/drafts/h3-mech-input/h3_scan.py b2c5b78b6dbb4e75
python3 k2/docs/drafts/h3-mech-input/h3_scan.py
#   期望: r=3.0 → 35.3mm · r=2.5 → 34.8mm · r=2.0 → 6.3mm · r=1.6 → 5.1mm
# 权威复核（施工步，非本件）：把 H3 及其 keepout 移到候选位后，仓库口径 kicad-cli pcb drc（T-8）比对逐条签名
```

—— ENG（ARCHER）· 2026-09-17 · 只读取证；本件不改任何件
