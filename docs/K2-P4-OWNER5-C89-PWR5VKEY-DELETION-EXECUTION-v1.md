# K2 · P4 · **owner ⑤ 执行（删 `C89` + `PWR_5V_KEY`）验收件** · v1 · 2026-09-18

> 授权：owner 裁定「删」（`.omo/supervision/ledger/OWNER-RULING-20260918-delete-C89-PWR5V.md`）+ 监理 **#K2-24** 执行放行令
> （§三 7 载体**一次做净**；§四 守恒闸；§二**窄授权**=仅 `C89`/`PWR_5V_KEY` 及其连带引用）。
> 红线（本件遵守）：冻结四源 `d4e81f64…`/`fb07d25a…`/`dd794c54…` 与 SPEC 原件**逐字节不动**（修订走版本 bump）· `criteria/` 只读 ·
> 禁派 WORKER · 临时仅 `/tmp/opencode` · **不得以删差异宣称归零（C-12）** · **禁切名义口径** · **未获批不改生成器/原理图**。
> ENG（ARCHER）· 2026-09-18 · 执行前：受审板 `6ff49da5678c2108` · pro `d5e0ca067a7b585e` · SPEC rev-49 `b8f4a7cb67b575f0`

## 0. 结论（五条）

1. **7 载体一次做净**（逐件前后 sha 见 §1）：真源 bump（`errata-2`，新件）· SPEC bump **rev-50** · pro netclass · BOM · 受审板 · P3 图集/落位解 · CO-90 F3。
2. **守恒闸 §四 逐项通过**（证据见 §2）：未连接 **0** · DRC **违规类型集不增**（同址对照臂证明）· 非 45° **0/4720** · 阻抗/等长/走廊**不退化**（SPEC 深 diff 断言 + 图集 C4/C6/D1 全 pass + refplane 严口径逐值同前） · **冻结四源原件 sha 不变**。
3. **⚠️ 生成器一项未达（具名上报，§4）**：`k2_gen_v5.py` 的 ref 清单取自**冻结锚板**（`k2/k2_v4.kicad_pcb` → 设计源板，仍含 `C89`），与新真源（54 件）**结构性冲突** ⇒ `❌ 写盘阻断: [YAML] K2 清单含 YAML sheets 不存在 ref: ['C89']`。**修此项 = 改生成器 = 红线（须批）** ⇒ 本件**未改生成器**，具名上报并给最小补丁提案。**该冲突同时是 G-ROOT-1 锚板依赖的「ref 清单」面**（pad 几何面仍属 ⑦）。
4. **判定器 PASS/FAIL 集合不变**（§3）：**PASS 7 / FAIL 3**（`zone_filled` 10/18 · `refdes_sets_equal` 原理图 **54** / 板 **58** · `pipeline_present`）；其中 ⑤ 相关读数按预期消解：`net_declared_realized` 的「<2 焊盘」**1 → 0**。
5. **⑤ 硬前置已解除**（本裁定）⇒ `pipeline.yaml` 安装链的条件**只剩其自身**（#K2-23 §二-6 乙 + `D-7a`）；**但生成器阻断（§4）会先撞上该链**，须一并裁。

## 1. 逐载体前后 sha（sha256 前 16；T-22 备份见各步日志）

| # | 载体 | 前 | **后** | 说明 |
|---|---|---|---|---|
| 1 | **真源网表**（新件）`k2/hw/data/k2_sch.errata-2.yaml` | 无 | **`61c4694e3b4df564`** | 基线 = `errata-1` `17d540f058631a5e`；删 3 处：`nets.PWR_5V_KEY` · `C89` placement · `nets.GND` 成员 `C89/B`（语义断言：nets 101→100 · GND 211→210 · placements 55→54，其余逐项相同） |
| 1b | `k2/hw/data/k2_sch.yaml`（原件） | `dd794c54f7ce7417` | **`dd794c54f7ce7417`（未动 ✅）** | 冻结件逐字节不动 |
| 1c | `k2/hw/data/k2_sch.errata-1.yaml`（上游） | `17d540f058631a5e` | **未动 ✅** | 保留为历史线 |
| 2 | **SPEC**（新件）`…/SPEC_k2_v4.spec-rev-50.json` | 无 | **`ed0950687e5aec97`** | 基线 rev-49 `b8f4a7cb67b575f0`；改动路径 **深 diff 断言 ⊆ 允许集**：`layer_plan.low_speed_nets.nets` 19→18 · `pd.zone_defs.power_pad_connect.entries` 185→184 · live `board_sha16`×3 + `basis`×3（`6ff49da5…`→`dae8dc8d…`） · 新增 `_spec_rev_50` 留痕 |
| 2b | `SPEC…rev-47/48/49.json`（原件） | `9ba09cbc…`/`11ad1da3…`/`b8f4a7cb…` | **未动 ✅** | 历史 rev 逐字节不动 |
| 2c | **`pd.zone_defs.power_pad_connect.retired_superseded_*` 的 `C89` 条目** | 2 条 | **保留 2 条（具名）** | 红线「退役几何/决策须**显式留存**」；#K2-24 §三-2 限定「**live 字段**」⇒ 留存册不改（见 §5） |
| 3 | **pro netclass** `k2/hw/k2_v4_8L.l5.kicad_pro` | `d5e0ca067a7b585e` | **`35c8f34bde7ac00c`** | 删 `netclass_assignments["PWR_5V_KEY"]=["POWER"]`（146→145）；**文本级 3 行 diff**，JSON 结构与其余字段不变 |
| 4 | **BOM** `k2/fab/k2_v4_bom.csv` | `9e4ddf4a44302b76`（55 refs） | **`db081546bbe64c37`（54 refs）** | 来源＝真 sch netlist；与真源 placements **交叉核对一致**；`C89` 已不在 |
| 5 | **受审板** `k2/hw/k2_v4_8L.l5.kicad_pcb` | `6ff49da5678c2108` | **`dae8dc8d48ff5b81`** | 删 `C89` footprint + 其 GND 短段（`44.45→45.225` F.Cu）+ 端点缝合 via（`45.225,37.5`）→ **孤网 `PWR_5V_KEY` 自板 net 表移除**；`PWR_5V_KEY` 全程 **0 track/via**（删除干净，见 §2-①）。计数：fps 59→58 · pads 687→685 · tracks 4721→4720 · vias 711→710 · nets 102→101 · zones 18→18 |
| 6 | **P3 图集** `p3_drawings.json` | `d6613754a7382c99` | **`e284e9afd9054408`**（`drawings_rev` **v10→v11**；器件 **55→54**） | 同族：`01` `ae84c110…`→**`a7977a2f8fe9bfe6`** · `02` `caddcf3f…`→**`95504f874110eb63`** · `05` `41453c89…`→**`fa1d0572a80e149b`** · `03/04/06/07` **未漂** · `README.md` `0b26d038…`→**`36b6b9843344068d`** |
| 6b | **落位解** `p3_placement_solution.json` | `faddc9de5519c5ec` | **`faddc9de5519c5ec`（逐字节不变，具名）** | 基线重跑（新板）产出同 sha：`C89` 不在其 15 件解内 ⇒ **无内容可 bump**；器件 55→54 的 bump 落在图集（#K2-24 §三-6 的实质项） |
| 7 | **CO-90 F3** | 登记开放 | **关闭 + 留痕（§5）** | — |
| 派生 | 原理图（1 件）`k2/hw/sch/power_12v_dc_in_dcdc_5v_ldo_3v3.kicad_sch` | `cb3c2134de77cfd6` | **`dbaa989e0688cd53`** | 由新真源确定性重出；**其余 5 件逐字节相同**；符号库 `IOCONVERT.kicad_sym` `6b572ceb…` **未变** |
| 派生 | `k2/pm_gate/project.yaml` | `c887422e68ac5885` | **`56583331599fab0f`** | `spec_name → rev-50` · `nets_yaml → hw/data/k2_sch.errata-2.yaml`（2 行 diff） |

**执行链（工具，均 dry-run + `--apply --confirm-repo-write` 双闸 + T-22 先备份后写）**：
`k2/tools/k2_p4_owner5_truesource_bump_v1.py` · `…_spec_rev50_owner5_del_c89_v1.py` · `…_del_c89_board_v1.py` · `…_del_c89_pro_v1.py` · `…_land_v1.py`（通用落件器）。

## 2. 守恒闸（#K2-24 §四）逐项证据

| 项 | 结果 | 证据 |
|---|---|---|
| **① 未连接 = 0** | ✅ **0** | 落件后 DRC（同名 pro `…l5.kicad_pro`）：`发现 0 个未连接的项目` |
| **② DRC 违规类型集不增** | ✅ **不增** | 落件后：73 = `missing_courtyard` 39 + `lib_footprint_mismatch` 34（前：75 = 40 + 35）⇒ **类型集 ⊆ 前**；**同址对照臂**（未改板拷入沙箱）显示沙箱会额外产生 `lib_footprint_issues` ×6（库表解析位置伪差）⇒ 该类型**非本删减所致**（落件后 in-place 为 **0** 条） |
| **③ 非 45° = 0** | ✅ **0/4720** | 判定器 `non45_segments: 非 45° 段 0/4720` |
| **④ 85Ω ±10% / 对内 ≤0.15 / 对间 ≤1.0 / 走廊 不退化** | ✅ **不退化** | SPEC 深 diff 断言：`impedance`/`length`/`corridors`/`stackup` **零改动路径**；图集判据 `C4_interface_inframe`（最小余量 **0.08 @J9** 同前）/`C6_corridor_basis`/`D1_pinheader_interference` **全 pass**；`refplane_continuity` 严口径双口径**逐值同前**（rect 3051/3653 · 缺口 20.9450 mm² · 胶囊 3021/3653） |
| **⑤ 冻结四源原件 sha 不变** | ✅ | `d4e81f647be7f980` · `fb07d25ac426ff84` · `dd794c54f7ce7417` · `897e8bfde60e2cfe`+`7ce08757eff25557` **逐件实测不变** |
| **⑥ 生成器两次连跑 sha 相同（若涉生成器输入）** | ❌ **未达 ⇒ 具名上报（§4）** | 涉生成器输入（真源）⇒ 应做；但生成器**先撞 fail-fast**（ref 清单源 = 冻结锚板），无法产出 ⇒ **不静默**，见 §4 |
| 附加：板内一致性 | ✅ | 落件后：`C89` 不存在 · `PWR_5V_KEY` 网不存在 · `PWR_5V_KEY` 全程 0 track/via · 孤网已清 |

## 3. 判定器 PASS/FAIL 集合（新基线；`--nets k2_sch.errata-2.yaml --board …l5.kicad_pcb --pro …l5.kicad_pro`）

**PASS 7**：`device_has_pads`（0 焊盘器件 0）· `drill_count`（NPTH=4/PTH=16）· `non45_segments`（**0/4720**）· `rule_severity_manifest`（未登记豁免 ignore 0/62）·
`net_declared_realized`（0 焊盘声明网 = 0；**<2 焊盘 = 0**，前值 1 ⇒ ⑤ 侧消解）· `pin_map_complete` · `verdict_schema`。
**FAIL 3**：`zone_filled`（10/18；在库口径未修，裁后应 10/10）· `refdes_sets_equal`（原理图 **54** / 板 **58**；板有图无 4 = `H1..H4`）· `pipeline_present`（`hw/sch` 未覆盖）。
⇒ **集合与执行前逐项同名**（仅数值随删除位移：`4721→4720`、`<2 焊盘 1→0`、`55/59→54/58`）。

## 4. ⚠️ 生成器阻断（**具名上报；本件未改生成器**）

**现象（可复跑）**：
```bash
cd /home/fila/jqdDev_2025/ic_hw
K2_OUT_PCB=/tmp/opencode/g.kicad_pcb K2_OUT_JSON=/tmp/opencode/g.json python3 k2/tools/k2_gen_v5.py
# ⇒ ❌ 写盘阻断 (fail-fast): [YAML] K2 清单含 YAML sheets 不存在 ref: ['C89']
```
**根因（文件:行）**：`k2/tools/k2_gen_v5.py:54` `PCB_REF_PATH = ROOT/k2_v4.kicad_pcb`（→ symlink → **冻结设计源板** `hw/k2_v4_8L.kicad_pcb`，仍含 `C89`）；
`:68-77` `_derive_k2_refs_from_true_source()` 由**该板**解析 ref 集；`:79` `K2_REFS`；`:830-835` 断言 `K2_REFS_SET ⊆ yaml_refs`。
⇒ 真源删 `C89` 后该断言**恒假**（锚板不可改）。**这不是新缺陷**，而是 **G-ROOT-1「生成器依赖锚板」的 ref 清单面**（#K2-22 §一 G-ROOT-1 的 pad 几何面仍属 **⑦**）。
**最小补丁提案（须监理批；ENG 未实施）**：`K2_REFS` 改由**真源 YAML** 导出（`sheets[].placements[].ref`）——即 `:79` 一行改为读 `YAML_PATH`；
  `PCB_REF_PATH` 仅保留「pad 几何」用途（该面待 ⑦）。**影响面**：ref 清单权威回归真源（与 #K2-23 §二-1 权威链一致）；pad 几何不变 ⇒ S2/S6 等自检语义需复跑确认。
**两个选项（请监理择一）**：(a) 批准该最小补丁（ENG 立即可做 + 复跑 S1–S8/确定性/E4）；(b) 与 **⑦/G-ROOT-1** 同批做（本项并入）。
**门影响**：优先序 5 的 `pipeline.yaml` 安装链会**先撞本项**（生成器在链内）⇒ 建议 (a) 先解，或在链内显式豁免（须监理定）。

## 5. CO-90 F3 关闭 + 留痕（载体 7）

- 原登记：`k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_*.md` 内「**CO-90 F3**：网范围/电源域口径 ⇒ 待 PM/owner」。
- **关闭依据**：owner 已裁「删」（`OWNER-RULING-20260918-delete-C89-PWR5V.md`）+ 本件 §1 已执行全部连带载体。
- **留痕方式（不改历史证据件）**：本件 + ledger 为关闭记录；`C89` 的**退役留存册条目保留**（`retired_superseded_clearance_v1` / `retired_superseded_bom`；红线『退役几何/决策须显式留存』）；
  SPEC rev-50 内 `_spec_rev_50.deleted.retained_named` 显式登记「保留 2 条」⇒ 分母问题（`C89/A` 1 焊盘）随 pad 消失而消（判定器「<2 焊盘」= 0，§3）。
- **归属说明**：原 ENG 证据件 §48 把「更新该口径登记」列为**监理/PM** 面 ⇒ ENG 只交关闭证据，登记册本身（历史件）**不重写**。

## 6. 复跑链（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# ① 真源 bump（沙箱；逐项语义断言）
python3 k2/tools/k2_p4_owner5_truesource_bump_v1.py --out /tmp/opencode/x.yaml   # 期望 sha16 61c4694e3b4df564
# ② SPEC rev-50（沙箱 + project.yaml 沙箱副本；深 diff 断言）
python3 k2/tools/k2_p4_owner5_spec_rev50_owner5_del_c89_v1.py --board-sha16 dae8dc8d48ff5b81 \
  --spec-new /tmp/opencode/rev50.json --project-yaml /tmp/opencode/project.yaml   # 期望 ed0950687e5aec97 / 56583331599fab0f
# ③ 板 / pro（沙箱重出；期望同 sha）
AppDir/usr/bin/python3.11 k2/tools/k2_p4_owner5_del_c89_board_v1.py --out /tmp/opencode/b.kicad_pcb  # dae8dc8d48ff5b81
python3 k2/tools/k2_p4_owner5_del_c89_pro_v1.py --out /tmp/opencode/p.kicad_pro                      # 35c8f34bde7ac00c
# ④ 原理图重出（沙箱）
K2_SCH_YAML=k2/hw/data/k2_sch.errata-2.yaml K2_OUT_SCH=/tmp/opencode/sch python3 k2/tools/k2_sch_gen_v1.py
# ⑤ BOM / 图集（沙箱）
python3 k2/tools/k2_p4_bom_gen_v1.py --out /tmp/opencode/bom.csv          # db081546bbe64c37（54 refs）
cp k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json /tmp/opencode/p3x/ 2>/dev/null || mkdir -p /tmp/opencode/p3x
K2_P3_OUT=/tmp/opencode/p3x AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py   # e284e9afd9054408（54 件）
# ⑥ 守恒闸
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
AppDir/bin/kicad-cli pcb drc --severity-all -o /tmp/opencode/drc.rpt k2/hw/k2_v4_8L.l5.kicad_pcb   # 期望 73w/0e/0unconn
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-refplane-strict-gap-v1/two_caliber_sensitivity.py \
  k2/hw/k2_v4_8L.l5.kicad_pcb /tmp/opencode/two.json    # 期望 rect 3051/3653 · capsule 3021/3653（同前）
sha256sum k2/hw/k2_v4_8L.l4.kicad_pcb k2/hw/k2_v4_8L.kicad_pcb k2/hw/data/k2_sch.yaml criteria/adjudicate.py criteria/manifest.k2.yaml
```

## 7. 边界与未做项

**已改（均有 owner 裁定 + #K2-24 授权）**：§1 表列 7 载体 + 派生（原理图 1 件 / project.yaml）+ 图集索引 README + 5 把执行工具 + 本件。
**未改**：冻结四源原件（含 `k2_sch.yaml`）· SPEC rev-47/48/49 原件 · `errata-1` · `criteria/**` · `_shared/**` · **生成器 `k2_gen_v5.py`（§4 具名阻断，未动）** · 原理图生成器 · 库/`fp-lib-table`/模板 · L5 旧交付包 · `.omo/supervision/**`。
**未做（具名）**：生成器 ref 源补丁（§4，须批）· `pipeline.yaml` 安装（⑤ 前置已解，但须先解 §4；且其自身条件 = #K2-23 §二-6 乙+`D-7a`）· 其余 54 条闭环表条目（#K2-24 §五）。
**C-12 声明**：本件**不宣称**其他未闭条目已消；判定器 FAIL 集合同前（§3）；`ref_plane_continuity` 严口径仍 83.52%（本件未切口径）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `dae8dc8d48ff5b81` · SPEC rev-50 `ed0950687e5aec97`
