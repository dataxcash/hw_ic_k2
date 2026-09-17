# K2 · P4 · **⑥+⑦ 复合候选板**（P4 末态单一候选）· 证据件 v1 · 2026-09-18

> 缘起：`⑥`（L2 placement + 40 件 courtyard，候选 `b2cfb087839afd73`）与 `⑦`（按板重建库快照 + 全板 `lib_id` 重指，
> 候选 `f93a1698adcf4863`）是**各自从同一基线派遣**的两个待放行候选。二者共同落板才构成 **P4 末态**
> （无 DRC 违规、封装链接自洽），因此本件验证**兼容性**并给出**单一复合候选**。
> 对象 = 已落件五步复合板 `6ff49da5678c2108`（`k2/hw/k2_v4_8L.l5.kicad_pcb`）。**本件未改仓库**；落件归监理。

## 1. 复合链（两跳，全部 dry-run）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli
B=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro
# ① ⑥（L2 placement + courtyard）
$K k2/tools/k2_p4_l2_placement_courtyard_v1.py --board $B --pro $P --kicad-cli $CLI \
      --work-dir /tmp/opencode/p4final/a6          # 期望候选 b2cfb087839afd73
# ② ⑦ 以 ① 的候选为输入（库快照必须建在补 courtyard **之后**，courtyard 属封装内容）
$K k2/tools/k2_p4_lib_snapshot_v1.py --board /tmp/opencode/p4final/a6/k2_v4_8L.l5.l2-placed.kicad_pcb \
      --pro $P --kicad-cli $CLI --work-dir /tmp/opencode/p4final/b7    # 期望 9682dd026f48c04a
```

**复合候选板 = `9682dd026f48c04a`**（`k2_v4_8L.l5.l2-placed.libsnap.kicad_pcb`）；**库快照 27 件**
（lib digest sha16 = `a63fff0769f0d0c5`；较纯 ⑦ 的 24 件多 3 件 —— 补 `CrtYd` 后同件名件的 land pattern 再分化，
属**应然**：courtyard 是封装定义的一部分）。两跳各自 `gates.passed = true`；同 work-dir 两次复跑**逐字节同**
（`cmp` IDENTICAL）。

## 2. 复合板硬闸（**DRC 违规 = 0**）

| 量 | 基线 `6ff49da` | ⑥ 候选 | **复合候选 `9682dd02`** |
|---|---|---|---|
| DRC `error` | 0 | 0 | **0** |
| DRC `unconnected` | 0 | 0 | **0** |
| DRC warning 总 | 75 | 35 | **0** |
| ├ `missing_courtyard` | 40 | **0** | **0** |
| ├ `lib_footprint_mismatch` | 35 | 35 | **0** |
| └ 其它 | 0 | 0 | 0 |
| 非 45° | 0 | 0 | **0** |
| `column_x`（J6/J9/J11/J12/J13） | 27.94 | 27.94 | **27.94** |
| 接口件出框（P3-4 8 件） | 0 | 0 | **0** |

## 3. 守恒闸（独立复算，不复用工具自述）

| 检查 | 结果 |
|---|---|
| 逐 ref **pad 局部几何**（形状/尺寸/钻径/局部偏移/朝向）base vs 复合 | **59/59 全等** |
| 绝对位置有变者 | **仅 `D2` `L1` `U4`**（= ⑥ 登记的三件位移，无第四件） |
| PCIE 网络段/via 集合（等长 + 85Ω 域） | **3653 段 / 252 via 逐条相同** |
| 铜总量 | tracks 4722 · vias 711 · zones 18 · nets 102 · fps 59 · pads 687（⑥ 起 `+1` 段，⑦ 后不变） |
| ⑦ 跳内 base→候选 铜几何集合 | **逐条相同**（⑦ 只改 55 行 footprint 头行；文本差异**全为头行**） |
| 非 45° | 0 |

⇒ ⑦ 对 ⑥ 的产物是**纯 lib_id 重指**（零几何副作用）；⑥ 的等长/85Ω/列位/出框守恒在复合板上仍成立。

## 4. 判据复算（草案 v4 安装件；判定归监理）

| W-8 口径 | 复合候选 |
|---|---|
| v1（安装件） | **15 PASS / 2 FAIL** = `pipeline_present` + `lib_electrical_level`（差异 8+0，**全为放置约定**，见 inc39 证据 §4） |
| v2（放置帧归一草案 `34b83cff5fe8ade7`） | **16 PASS / 1 FAIL** = **仅 `pipeline_present`**（gate 安装项） |

补充：复合板 `drc_warning_dispositions` 的分母 = **0/0**（无 warning 须处置）；`pads_within_outline` = 0（AABB 与
真外框双口径、接口件亦 0）；`keepout_active` 8/8；`zone_filled` 10/10；`refdes_sets_equal` 图 55 / 板 55。

## 5. 落件运行手册（**须监理放行**；本件不执行）

1. **前置**：板 sha 变更 ⇒ 须 **SPEC 版本 bump**（pre-commit `check_pcb_spec_correlation` 要求
   `.kicad_pcb` 变更伴随同笔 SPEC 变更）；现存 `SPEC_k2_v4.spec-rev-47.json` + `project.yaml` bump 属**未提交**状态
   （见 inc39 handoff §5 旁证）。**SPEC 与 generation 源一概不改动几何**。
2. **两跳 apply**（顺序不可颠倒；各自 T-41/T-22 protect）：
   `⑥ --apply --confirm-repo-write` → 复算 `b2cfb087839afd73` →
   `⑦ --apply --confirm-repo-write` → 复算 `9682dd026f48c04a` + 库 27 件。
   或直接以复合候选板落板（等价；⑦ 会写板 + 库，⑥ 的几何已在板内）。
3. **库内快照外旧件 12 件**：⑦ 工具默认**保留不删**（列出待裁）。
4. 落件后复算：DRC 违规 0 · 判定器 v2 口径 16P/1F · 冻结判定器集合不变。

## 6. 边界

仓库板 `6ff49da5678c2108` / pro `d5e0ca067a7b585e` / `hw/lib/ForgeOS.pretty`（20 件）/ `hw/fp-lib-table`
`d731638859be9a08` / 冻结件 `d4e81f647be7f980`·`fb07d25ac426ff84` / 真源 yaml / SPEC rev-19..47 / `criteria/` 两份
`897e8bfde60e2cfe`·`7ce08757eff25557` / 各判据安装件 **均未动**；未派 WORKER；临时仅 `/tmp/opencode`。

—— ENG（ARCHER）· 2026-09-18 · 复合候选 `9682dd026f48c04a` · 库 digest `a63fff0769f0d0c5`
