# K1 锚重基线（N-3 落件后）· 2026-09-20

- 依据：handoff §8「N-3 落件后**报 K1 锚重基线**」；判据 = **已签认** `criteria/manifest.k1.yaml`（`c175be51c3338a53`）+ **DRC 实跑**。
- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K1_ANCHOR_REBASELINE_POST_N3_20260921_v1.json（59c72c8856aaafef）`
  + W-8 测量件 `K1_W8_FOOTPRINT_AUDIT_20260921_v1.json（146b8543fb629b43）`。
- 命令（同口径可复算）：
  `python3 criteria/adjudicate.py --project k1 --board k1/k1_v1.kicad_pcb --pro k1/k1_v1.kicad_pro --nets <k1_sch.yaml> --sch-dir <sch> --root . --manifest criteria/manifest.k1.yaml --drc-cli AppDir/bin/kicad-cli --drc-work-dir <全新> [--w8-audit-json <…>] --out <verdict.json>`

## 一、主读数

| 口径 | N-3 前 | N-3 后 | 翻转 |
|---|---|---|---|
| 签认 manifest + DRC 实跑（18/19 维；`ref_plane_continuity` K1 = `enabled:false`） | **7 PASS / 11 FAIL** | **9 PASS / 9 FAIL** | `refdes_sets_equal`（原理图 **37→42** vs 板 42）· `net_declared_realized`（0 焊盘声明网 **3→0**）· **回退 0** |
| 再加 W-8 测量件 | — | 10 PASS / 8 FAIL | `lib_electrical_level` **空过**（见 §二） |

- **前值 7/11 与 #K2-49 落件报告逐维一致** ⇒ 本基线与前序读数同口径、可复现。
- `pin_map_complete` **16 → 16（未回退）**：16 节点**全部为 J1**（符号脚号 1..16 ∉ 板 pad A*/B*/SH）⇒ **R-1 待监理自裁**。

## 二、⭐ 新发现 **W8-VAC-1（中 · 防充绿）**

- K1 板 **42/42 footprint 无库 nickname**（板内 FPID 为裸名，如 `C_0402_1005Metric`）⇒ W-8 电气级比对**零对象**
  （工具口径：无 nickname ⇒ `no_library_link`）⇒ `lib_electrical_level` 的 `0/0` 是「**无可比对象**」而非「板 = 库」。
- **禁用该空过宣称 K1 电气级合规（C-12）**；不含 W-8 件时该维 `fail-closed`（**更诚实**）。
- 根因：K1 建板器写出的 footprint 未带 `ForgeOS:` 前缀；`k1/fp-lib-table` 已注册（M2 落件）但**板内未回填 lib_id**。
- 修法：把 42 件 FPID 补为 `ForgeOS:<name>`（**板/库变更 ⇒ 需批**，须重跑 DRC/判定），或由监理裁定该维在「无库链接」下的口径（K2 同族已有 `_reclassify_w8` 先例）。

## 三、其余 FAIL（逐维成因，均已在册）

`zone_filled`（K1 无铜区）· `drill_count`（NPTH 2<4）· `drc_errors`（13 error ⇒ K1-D1/D2/D3）· `unconnected_zero`（156 = **K1 未布线中间态**，K1-D5 非缺陷）·
`keepout_active`（K1 无 keepout）· `pads_within_outline` / `density_and_clearance`（**缺 K1 版 J-8 测量件** ⇒ fail-closed）· `pin_map_complete`（R-1）。

## 四、边界

只读复算（DRC work-dir / 产物 / 旧件沙箱全在 `/tmp/opencode`，仓库零改）；未改判据/生成器/SPEC/原理图；未派 WORKER；未越阶段门。

---

# 附：**全五件测量输入**（同日续推）—— K1 判定面达本环境可达上限

- 读数（签认 `criteria/manifest.k1.yaml` + DRC + W-8 + J-8 出框 + J-8 密度/间距 + min-clearance bracket）：
  **10 PASS / 8 FAIL**（`provisional=false`，18/19 维参与；`ref_plane_continuity` K1 侧 `enabled:false`）。
- 两维由 **fail-closed → 实读数**（均 FAIL，且**与手工缺陷册逐条一致**）：

| 维 | 机读 | 与在册缺陷册交叉核对 |
|---|---|---|
| `pads_within_outline` | 全 pad(AABB)=**2** · 接口件=**2** · 真框多边形=**2**（`J1.SH` ×2） | **K1-D1**（pads_within_outline 2 pad = J1 SH）✓ 一致 |
| `density_and_clearance` | 10mm/frame_origin 封装峰值 **12（>8）** · 最小铜间距 **<0.100**（T=0.100 起即违规 ⇒ 实达区间 `[None, 0.1]`）· pad 到边 **-0.39mm** | **K1-D7**（密度/铺铜）与 **K1-D3**（最紧样本 = `U1` pad17[no net] ↔ `J6` PTH pad1[`PWR_CTRL_OUT`]）✓ 同址 |
| `lib_electrical_level` | **空过 PASS**（42/42 `no_library_link`） | **W8-VAC-1** ⇒ **禁用其宣称合规** |

- 测量器全部**板参数化**（`--board`）；唯一 K1 侧自由参数 = `--interface-refs`，由 K2 缺省
  `[J2,J3,J4,J6,J9,J11,J12,J13]` 换为 **K1 接口集 `[J1,J6,J9,J10,J13,J14]`**（已在件中具名）。
  四件测量件均带 `board_sha16=eda1dc91eec76aa7` = 受审板 ⇒ 非陈旧（fail-closed 通过）。
- 证据件：`K1_ANCHOR_REBASELINE_POST_N3_20260921_v1.json（ef7160de72900d2d）` +
  `K1_W8_FOOTPRINT_AUDIT_20260921_v1.json（146b8543…）` · `K1_PADS_WITHIN_OUTLINE_20260921_v1.json（b8e4f0e4…）` ·
  `K1_DENSITY_AND_CLEARANCE_20260921_v1.json（2b274031…）` · `K1_MIN_CLEARANCE_DRC_BRACKET_20260921_v1.json（cfabf764…）`。
- 结论：**K1 判定面已达本环境可达上限**（18/19 维有读数；余 1 维 K1 侧不适用）。其余 FAIL 均已有具名成因与归属（K1-D 系列 / R-1 / W8-VAC-1）。
