# K2 · P4 · **裁定前纯证据包 #3**（#2 `l6` pro DRC 中立**实证** · #10 `L-1` 28 件具名清单 · #7/#9 在册复核）· v1 · 2026-09-19

> 授权：handoff `k2-p4-handoff-20260920-inc114-context-handoff.md` §7-3「裁定前可做的纯证据项」。
> **未改任何载体**（`l4/l5/l6` pro · 生成器 · SPEC · 判据 · 库 均不动）；演算 `/tmp/opencode/arc_r3/`。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 · 受审板 `l6 30fa849641323f98`

---

## 0. 一句话

- **#2（`l6` pro `net_settings` 允许集外差异）→ 已实证「DRC 中立」**：`l6` 板 × **l6 pro** 与 × **l5 pro** 两臂 DRC **逐条相同**（**164 / 0 error / 0 unconnected**，逐类计数同；去时间戳后**两臂与在册件归一化 sha 全同 `af773f2501ca72a2`**）⇒ 选项 ① **接受**（依据充分）。
- **#10（`L-1`）**：**28 件「仅板来源」逐件具名**已出（守恒核对 `54 = 11(SPEC) + 15(L3 布局解) + 28(仅板)`）⇒ P4 关门时「具名接受」可直接引用本清单（零改造）。
- **#7 / #9**：在册件复核与 `l6` 同锚（`board_sha16 = 30fa849641323f98`）——`164 = 74 已登记 + 90 未登记(7 类)`；`min_clearance` bracket **[0.100, 0.105]**；`band_occupancy.max_ratio 0.07586`。

---

## 1. #2 `l6` pro `net_settings` —— 结构剖析 + **两臂 DRC 实证**

### 1.1 结构（`l5` pro `35c8f34bde7ac00c` → `l6` pro `12ad219b9f66b7b3`）

| 量 | l5 pro | l6 pro | 判定 |
|---|---|---|---|
| `classes`（类定义） | Default/LOW_SPEED/PCIe85/POWER | 同 | **逐字段同**（clearance `0.1/0.1/0.175/0.2`；`track_width 0.09/0.15/0.205/0.5`；`via 0.35`） |
| `netclass_patterns` | `{}`（空） | `{}`（空） | 同（「键差」全在 `netclass_assignments`） |
| `netclass_assignments` | 145 键 | 100 键 | — |
| **仅 l5 有（54 键）** | `*_U3`/`*_U7` 后缀等 | — | **板内命中 0/54 ⇒ 死键，零 DRC 影响** |
| **仅 l6 有（9 键）** | — | `DS320_STRAP_*` | **板内命中 9/9**，归 `LOW_SPEED`；**`LOW_SPEED.clearance == Default.clearance == 0.1`** |

（`l5` 面 54 死键示例：`PCIE_DN_OUT0…_U3`·`PCIE_UP_OUT0…_U7`·`STRAP_*_U3/_U7`·`VREG1/2_U3/_U7`·`PD0/1_U3/_U7`·`ALL_DONE_N_U3/_U7`。）

### 1.2 **两臂 DRC 实证**（决定性）

方法：**复刻** `criteria/adjudicate.py::measure_drc` 的同款步骤（fresh work-dir；复制板 + 该臂 pro（改名同 stem）+ `fp-lib-table` + `lib/`；`kicad-cli pcb drc --format json --severity-all`）。

| 臂 | pro | violations | error | warning | unconnected | 归一化 sha16（去 `date`/`$schema`） |
|---|---|---|---|---|---|---|
| A | **l6 pro** `12ad219b` | 164 | **0** | 164 | **0** | `af773f2501ca72a2` |
| B | **l5 pro** `35c8f34b` | 164 | **0** | 164 | **0** | `af773f2501ca72a2` |
| 在册 | l6（`drc_violations_clean_workdir.json` `ad472105`） | 164 | 0 | 164 | 0 | `af773f2501ca72a2` |

- **两臂 violations 逐条相同**（`missing_courtyard` 54 · `silk_over_copper` 37 · `track_not_centered_on_via` 30 · `lib_footprint_mismatch` 20 · `silk_overlap` 15 · `via_dangling` 4 · `silk_edge_clearance` 2 · `track_dangling` 1 · `copper_sliver` 1），`unconnected_items` 亦同。
- ⇒ **#2 可一句话裁「接受」**（未放松下限：两臂 error 均 0，warning 总数/逐类不变）。

---

## 2. #10 `L-1` —— **28 件「仅板来源」具名清单**（P4 关门「具名接受」可直接引用）

来源权威守恒（机检，逐 ref；`placed` = 真源 YAML 54 件）：

| 权威类 | 条数 | refs |
|---|---|---|
| SPEC canonical 字段（逐值一致） | **11** | `J2` `J3` `J4` `U1` `U4` `J6` `J9` `J11` `J12` `J13` `C82` |
| L3 布局解 `p3_placement_solution.json::placed`（逐值一致） | **13** | `C73` `D2` `L1` `R35` `R36` `R37` `R38` `R39` `R40` `R41` `R43` `R44` `R45` |
| L3 布局解 **陈旧**（已被板侧修复超越；以板为准） | **2** | `C86` `R42` |
| **仅板来源**（冻结输入中无任何非板坐标） | **28** | 见下 |

**28 件清单（逐件具名，供 P4 关门具名接受）**：

```
C74 C75 C76 C77 C78 C79 C80 C81 C83 C84 C85 C87 C88 C90
D1 E2
R1 R21 R28 R29 R3 R31 R32 R33 R34
U2 U5 U6
```

- 守恒核对：`11 + 15(p3 含 2 陈旧) + 28 = 54` ✅；板侧 refs 58 = 54 + `H1..H4`（NPTH 固定孔，非真源件）。
- 口径（C4）：`PLACEMENT_SOLUTION_v1.json`（rev=2 `086d453d23c5fbff`）= **已批准落位的 canonical 捕获，非独立求解**；**不得主张独立推导**，P5 打样件不得隐去。

---

## 3. #7 / #9 在册复核（受审板 `l6` 同锚）

- **#7 `J-1` 7 类 warning 台账**：在册 DRC `ad472105c88b2256` 逐类 = **164** = 已登记 `missing_courtyard` **54** + `lib_footprint_mismatch` **20**（=74）+ **未登记 7 类 90 条**（`silk_over_copper` 37 · `track_not_centered_on_via` 30 · `silk_overlap` 15 · `via_dangling` 4 · `silk_edge_clearance` 2 · `track_dangling` 1 · `copper_sliver` 1）。⇒ 与决策纸 #7 数字逐项一致；安装归 gate 属主。
- **#9 `density_and_clearance` rev=3 前置读数**：在册 `density_board_l6_30fa8496.json`（`board_sha16 = 30fa849641323f98`）`band_occupancy.max_ratio = 0.07586`（3 带，y 轴）；`min_clearance_drc_…json`：**`max_zero_violation_threshold = 0.100` / `first_violating = 0.105`** ⇒ 真值区间 **[0.100, 0.105]**（≥ 0.100 达标）。两件均**不含 verdict 字段**（测量件），阈值/启用权归监理 + gate 属主。

---

## 4. 复现

```bash
# #2 两臂 DRC（复刻 adjudicate.measure_drc；fresh work-dir）
python3 /tmp/opencode/arc_r3/drc_two_arm.py         # 产出 wd_l6pro/drc.json · wd_l5pro/drc.json
# 归一化比对（去 date/$schema）
python3 - <<'P'
import json,hashlib
for p in ('/tmp/opencode/arc_r3/wd_l6pro/drc.json','/tmp/opencode/arc_r3/wd_l5pro/drc.json',
          'k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-l6-20260920/drc_violations_clean_workdir.json'):
    d=json.load(open(p)); d.pop('date',None); d.pop('$schema',None)
    print(hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()[:16], p)
P
# #10 清单
python3 - <<'P'
import json,yaml
d=yaml.safe_load(open('k2/hw/data/k2_sch.errata-2.yaml'))
placed=[p['ref'] for s in d['sheets'] for p in s.get('placements',[])]
spec=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-51.json'))['components']
specr=set(spec['connectors'])|set(spec['mcu'])|set(spec['oring'])|set(spec['anchor_fixes'])|set(spec['pin_headers']['positions'])
p3=set(json.load(open('k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json'))['placed'])
print(sorted(set(placed)-specr-p3))
P
```
读数件（`/tmp` 易失）：`/tmp/opencode/arc_r3/{drc_two_arm.json, wd_l6pro/drc.json, wd_l5pro/drc.json}`。

---

## 5. 边界

未改生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；**未写 `.omo/supervision/**`**；未派 WORKER；未新增检查齿；未放松下限（两臂 error 均 0、warning 逐类不变）；未以「接近 0」充绿；后台等待用 `k2/tools/k2_wait_pid.sh`（#K2-33）。临时仅 `/tmp/opencode/arc_r3/`。
