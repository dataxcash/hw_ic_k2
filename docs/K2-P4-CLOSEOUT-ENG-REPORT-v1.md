# K2 · P4 · **关门前 ENG 报告**：`criteria` **rev=3 在岗** · **19 维 = 19 OK / 0 FAIL** · 闭环表 **52/5/2** · **L-1 具名接受（C4）** · v1 · 2026-09-19

> 依据：**#K2-35**（rev=3 安装 + 签认 + 锚 rev=3；§4 口径裁 = V3 覆盖**信息项**、**不加 AND 门**）· **#K2-34** §一/§三。
> ENG（ARCHER）· 2026-09-19 · 判据锚 **rev=3**（`eb244d81` / `1937a40a` / `e2b49fdd`）· 受审板 **`l7 c5a7df90aadb66e0`**
> 只写 `k2/docs/**` + k2 册/闭环表；**未写 `.omo/supervision/**`**；`criteria/` **只读**。

---

## 0. 一句话

`criteria` **rev=3 在岗**（ENG 独立复核锚 **MATCH**；`adjudicate.py` = 草案**逐字节**）；canonical 19 维（在岗判据 × `l7`，带齐 6 路测量输入）= **19 OK / 0 FAIL · passed=True · provisional=False**（前：rev=2 同板 = **15 OK / 2 FAIL**）。§三-4 各件（5 件测量 + **册重锚** + C1/C2/L-1 + DRC + 确定性 + `engine verify`）齐备；§三-7 闭环表 **根闭 52 / OUT 5 / 未闭 2**（余 `F-9` 待监理裁定 · `N-01` 顺延 P5）；**L-1 具名接受（C4）** 文本就绪（§5）。**P4 关门判定权归监理**，本件只交证据与就绪声明。

---

## 1. rev=3 在岗核（ENG 独立复核）

| 件 | sha16 | 期望（#K2-35） | 判 |
|---|---|---|---|
| `criteria/manifest.k2.yaml` | `eb244d811ad7859b` | 同 | **MATCH** |
| `criteria/adjudicate.py` | `1937a40ae68bc288` | 同 | **MATCH**（= `docs/drafts/p4-k234-criteria-rev3-v1/adjudicate.rev3.py` **逐字节**） |
| `criteria/CHANGELOG` | `e2b49fdd3aec0283` | 同 | **MATCH** |
| 属主/权限 | `ic_hw_gate:ic_hw_gate` · 文件 `444` · 目录 `555` | 同 | **OK**（ENG 不可写） |

结构复核：`manifest_version 6-k234-rev3` · `not_countersigned=false` · `covered 19 / uncovered []` · `checks` **19/19 enabled** · `drc_warning_dispositions` **9 条** · `thresholds.ref_plane_continuity = {caliber: non_antipad_gap==0, radius_R_mm: 0.5}` · `board = k2_v4_8L.l7.kicad_pcb`。

---

## 2. canonical 19 维（在岗 rev=3 × `l7`）—— 前/后

命令（cwd=容器根；`--root .`）：`criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l7.kicad_pcb --pro k2/hw/k2_v4_8L.l7.kicad_pro --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --root . --drc-cli AppDir/bin/kicad-cli --drc-work-dir <全新> --w8-audit-json <册>/w8_audit_board_l7_c5a7df90.json --pads-outline-json <册>/pads_within_outline_board_l7_c5a7df90.json --v3-plane-json <册>/ref_plane_continuity_board_l7_c5a7df90.json --refplane-gap-json <册>/refplane_nonantipad_board_l7_c5a7df90.json --density-json <册>/density_board_l7_c5a7df90.json --min-clearance-json <册>/min_clearance_drc_board_l7_c5a7df90.json`

**结果：19 OK / 0 FAIL · passed=True · provisional=False（countersigned=True）**。原 2 条 FAIL 的收敛：

| 维 | rev=2 | **rev=3** | 机制 |
|---|---|---|---|
| `drc_warning_dispositions` | FAIL 未登记 7/9 | **OK 0/9** | #K2-34 §一-7 七条 + 原两条（登记制不豁免） |
| `lib_electrical_level` | FAIL 差异 2 + pad 名 1 | **OK 0 + 0** | (i-a) µm 修复 + (B) 口径（豁免 2 / 1） |
| `ref_plane_continuity` | 未启用 | **OK non_antipad_gap 0.0 @R=0.5** | #K2-34 §一-1 + #K2-35 §4 |
| `density_and_clearance` | 未启用 | **OK 峰 7≤8 · 铜间距 0.1≥0.1** | #K2-34 §一-9 + #K2-23 §二-9 |

其余在岗维**均 OK 且不回退**：`zone_filled` 10/10（keepout 8 另计）· `drill_count` NPTH4/PTH16 · `non45_segments` 0/5037 · `unconnected_zero` 0 · `drc_errors` error 0（167 全 warning）· `refdes_sets_equal` 54/54 · `pin_map_complete` 0 · `net_declared_realized` 0 · `device_has_pads` 0 · `pads_within_outline` 0/0/0（676 pad）· `keepout_active` 8/8 · `rule_severity_manifest` ignore 0/62 · `fp_lib_table_present` ✓ · `verdict_schema` 0 · `pipeline_present` scope=k2 0 缺。
`engine verify k2`（cwd=k2，`PYTHONPATH=k2/_shared:$PWD/k2`）= **4/4 PASS**。

---

## 3. §三-4 各件（具名）

| # | 项 | 件 | 读数 |
|---|---|---|---|
| 1 | 19 维标准调用 | 本件 §2 | **19 OK / 0 FAIL** |
| 2 | 5 件测量 | 册 `E3-standard-call-l7-20260919/` | w8 51/2/1/4 · 出框 0/0/0 · refplane `non_antipad_gap 0.0` · 密度峰 7/0.07586 · 铜间距 [0.10,0.105] |
| 3 | **册再重锚** | `k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-l7-20260919/MANIFEST.md` | **11 件** · 逐件 sha + `board_sha16` 自检 **BAD=0** · 在岗 rev=3 verdict = **19/0**（保留 rev=2 历史件 + 草案影子件） |
| 4 | DRC（全新 work-dir） | 册 `drc_violations_clean_workdir.json` | 违规 **167**（全 warning）· error **0** · unconnected **0**；9 类全登记；`track_not_centered_on_via` 30→33（µm 修复副作用，具名） |
| 5 | C1/C2/L-1 | `p3_placement_solution.json dfbf65c5` · `PLACEMENT_SOLUTION_v1.json 086d453d` | 与 #K2-29 登记值**逐字节同**（零改动） |
| 6 | 确定性 | 链产物 | **3 跑同 sha `c5a7df90`**（落件 + 常态 + 撤 `l4`/`l5` 三臂）；还原后 l4/l5 未变 |
| 7 | 引擎门禁 | `engine verify k2` | **4/4 PASS** |

---

## 4. §三-7 闭环表（`K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md`）

- **§21（v1.13）**：#K2-34 §一-8「无判据类」**5 条转根闭**（`M-02` `M-14` `F-3` `N-02` `N-03`）。
- **§22（v1.14）**：rev=3 在岗后 **7 条转根闭**（`U-03` `U-09` `M-09` `M-12` `J-1` `J-7` `J-8`）。
- **计数**：根闭 **52** / OUT **5** / 未闭 **2**。
  - `U-03` **注**：`k2_render_3d.py:29` 的 MCIO 硬编码盒（16.0×7.0×4.6）**未改** ⇒ 归 **OUT #5 族**（3D 预览=证据层，计划 §1.3；同 `U-01`/`M-15`/`F-11`）；**请监理确认归 OUT #5 或另裁**。
  - `F-9`：走廊口径 L2 冻结表回改 = **owner 面**（影响量化已给：阻抗 ΔZ=0、制造无影响）⇒ **是否阻 P4 关门请监理明示**。
  - `N-01`：**顺延 P5**（P4 未关门未出新 Gerber；出面前置 `G36>0` 已实测）。

---

## 5. `L-1` 具名接受（C4）—— ENG 就绪文本（#K2-34 §一-10）

> 「**`L-1` 具名接受（C4）**：经查 `k2/pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json`（rev=2 **`086d453d23c5fbff`**）之性质为**已批准落位（板侧 as-built）的 canonical 捕获**，**非独立求解**；54 件中 **28 件属「仅板来源」**，另有 2 件（`C86`/`R42`）其解已被板侧修复超越而行陈旧。据此：**接受该 28 件以板侧坐标为权威来源**，用于 P4 及后续 P5 打样；**不主张**其为「独立推导」，**不得**在 P5 打样件与交付文档中隐去该来源限制；如后续需「完全非板来源」的坐标表，须另按 (b) placement 求解器工作包 或 (c) SPEC canonical 字段 bump 授权。」

**28 件逐件具名**（守恒 11 SPEC + 15 L3（含 2 陈旧）+ 28 仅板 = 54）：

```
C74 C75 C76 C77 C78 C79 C80 C81 C83 C84 C85 C87 C88 C90
D1 E2
R1 R21 R28 R29 R3 R31 R32 R33 R34
U2 U5 U6
```

C1/C2 载体本笔复核未变（`dfbf65c5b456cdd2` / `086d453d23c5fbff`）。

---

## 6. P4 关门检查单（ENG 交证；**判定权归监理**）

| 门件 | 态 | 依据 |
|---|---|---|
| 全 J 类 + V1/V2/V3 绿 | **绿** | 19 维 19 OK / 0 FAIL |
| 判据集 == manifest 应然集 | **绿** | `checks` 19/19 enabled；在岗判定器 19 维逐维命中 |
| manifest 签认 | **绿** | rev=3 COUNTERSIGNED（#K2-35） |
| #K2-22 §三 闭环表全闭 | **52 / 5 / 2** | 余 `F-9`（待监理裁定）· `N-01`（顺延 P5） |
| E-1..E-5 | **全过** | E-3 闭环表 · E-4 `engine verify 4/4` · E-5 `criteria/**` ENG 写入全失败 |
| 不回退项 | **保持** | 未连接 **0** · DRC error **0** · `zone_filled` **10/10** · 两次连跑逐字节同 |
| `L-1` 具名接受（C4） | **文本就绪**（§5） | #K2-34 §一-10 |

⇒ **请监理就 `F-9`（及 `U-03` 渲染盒归属）一句话裁定后作 P4 关门判定**；ENG 证据链已齐备，**未越阶段**（P5 未开、未出 Gerber）。

---

## 7. 边界

**本笔已改**：`k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md`（§22）· 册 `E3-standard-call-l7-20260919/`（+`verdict_19dim_rev3_*`、`MANIFEST.md` 重写）· 本件。
**未改**：`criteria/**`（rev=3 只读）· 冻结四源（`d4e81f64` 等）· 生成器/SPEC/原理图/板/库（本笔零载体改动）· `_shared/**`；未出 Gerber；未派 WORKER；未新增检查齿；未以「接近 0」充绿。

—— ENG（ARCHER）· 2026-09-19 · 受审板 `l7 c5a7df90aadb66e0` · 判据锚 **rev=3**
