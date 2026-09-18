# K2 · P4 · **E-4/E-5「判据在岗 + 签认」提交件 v1**

> 依据：监理 **#K2-28 §五**（唯一工作包 = E-4/E-5）+ **§六-2**（同批 C1/C2/§2.4）。
> 判据锚 rev=1（MATCH）· 冻结四源未动 · `criteria/**` 只读（**两份原件 sha 未变**）· 未派 WORKER · 临时仅 `/tmp/opencode`。

## 0. 一句话结论

**`k2/pipeline.yaml` 已安装并通过（`engine verify k2` 4/4 PASS）**；在库判定器复跑 **PASS 8 / FAIL 2**（**`pipeline_present` 由 FAIL 转 PASS**，两次逐字节同）；**19 维 canonical 在岗清单 + 逐维正/负控**已汇总；**签认请求**与**锚 rev=2 登记请求**见 §4/§5；§五-5 两维读数见 §6（`ref_plane_continuity` 严口径 **83.52% < 1.0 不可达**，须裁；`density_and_clearance` 机制齐备、阈值待裁）。

**本件不改 `criteria/**`**（安装 + 签认 = gate 属主/监理执行）——故 E-4 验收「`criteria/` 两份原件 sha 不变」成立。

---

## 1. `k2/pipeline.yaml` 安装（§五-1）

- 件 = **「职责分离（phases-only）」变体**（`docs/drafts/p4-pipeline-yaml-disambiguation-v1/pipeline.phases-only.draft.yaml`；D-1 消歧推荐件）→ 安装落点 **`k2/pipeline.yaml`** sha16 **`c89cc57fb988f821`**。
- **G11 真源绑定**：`netlist_connect.nets_yaml` = **`k2/hw/data/k2_sch.errata-2.yaml`**（现行真源；owner ⑤ #K2-24 授权 bump）——#K2-23 §二-6「乙」路径 + **D-7a**（NC 白名单 ①②，已落 `_shared`）。
- **fail-closed**：`checks` 段（提交期前置门禁）与 `verify` 段（产物验证）均声明 `REQUIRED_SCH_CHECKS` 三类；缺声明即 `required.py` 拒绝放行。
- **路径口径（实测修正）**：sch/nets/bom 路径须为 **k2 项目根相对**（`hw/sch/...`）；初版误用仓库根相对（`k2/hw/...`）⇒ **k2 pre-commit hook 拒绝提交**（`FileNotFoundError: k2/k2/hw/sch/...`），已修正并复验 **4/4 PASS**（修正后 sha16 **`c89cc57fb988f821`**）。

```
# 路径口径 = **k2 项目根相对**（config.abs_path 以 pipeline.yaml 所在目录为基准）⇒ **须在 k2 仓库根运行**
$ cd k2 && PYTHONPATH="$PWD/_shared:$PWD" python3 _shared/eda_core/pipeline/engine.py verify k2
  preflight/check[project_sch_coverage]: PASS
  verify/sch_structural: PASS
  verify/netlist_connect: PASS
  verify/bom_consistent: PASS
verify 完成: 3 项检查全 PASS   (rc=0)
```

## 2. 在库判定器复跑（E-4 机判）

```
$ python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
    --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch \
    --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
⇒ PASS 8 / FAIL 2（PROVISIONAL：manifest 未签认）；两次复跑 **逐字节同**
```

| 集合 | 维 | 逐项可解释性 |
|---|---|---|
| **PASS（8）** | `device_has_pads` · `drill_count` · `non45_segments` · `rule_severity_manifest` · `net_declared_realized` · `pin_map_complete` · **`pipeline_present`（本轮新转 PASS）** · `verdict_schema` | `pipeline_present`: "含 .kicad_sch 但无 pipeline.yaml 的目录 **0** 个" |
| **FAIL（2）** | `zone_filled`（已填充 **10/18**）· `refdes_sets_equal`（原理图 **54** / 板 **58**） | ① `zone_filled` = **在库口径未修**（#K2-23 §二-9：裁后按 v4 口径应为 10/10）② `refdes_sets_equal` = 板有图无 **4** = `H1..H4`（**纯机械件**；v4 口径「排除 `H*` + 逐条列名」后应为 PASS） |

⇒ 两 FAIL 均为**已具名口径项**（对应 19 维 canonical 的 `zone_filled` / `refdes_sets_equal` 两条 `expect` 文字），**非新缺陷**。

## 3. 19 维 canonical 在岗清单 + 别名钉死（§五-2）

**清单件**：`docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml` **`3f003cffe33a6cfd`**（`enabled` 缺省 = **17 true / 2 false**；2 false 见 §6）。

**5 组别名钉死**（两族命名不可相加的闭合；v2/v3 族名 **不得**出现在 canonical）：

| v2/v3 族（别名源） | canonical（v4 族） |
|---|---|
| `drc_warning_disposition` | `drc_warning_dispositions` |
| `lib_footprint_electrical` | `lib_electrical_level` |
| `density_and_spacing` | `density_and_clearance` |
| `v3_reference_continuity` | `ref_plane_continuity` |
| `board_frame_and_keepout` | **`pads_within_outline` ＋ `keepout_active`（一对二拆分）** |

**19 维在岗清单**（冻结族 9 + 草案族 7 + 阈值待裁 2 + 无条件 1）：

| # | 维 | enabled | 机判 expect（摘要） |
|---|---|---|---|
| 1 | `zone_filled` | true | 填充数 == 总数（v4 口径 10/10） |
| 2 | `device_has_pads` | true | 每器件 pad ≥ 1 |
| 3 | `drill_count` | true | `npth >= 4` |
| 4 | `net_declared_realized` | true | 每声明网落地 pad ≥ 2（**口径分歧见 §3-A**） |
| 5 | `pin_map_complete` | true | 缺 pad == 0 |
| 6 | `non45_segments` | true | 非 45° == 0 |
| 7 | `refdes_sets_equal` | true | 图集 == 板集（排除 `H*`，逐条列名） |
| 8 | `pipeline_present` | true | k2 域内每个含 `.kicad_sch` 目录被覆盖 |
| 9 | `verdict_schema` | true | 产物无 `verdict` 键 |
| 10 | `drc_errors` | true | DRC error == 0 |
| 11 | `drc_warning_dispositions` | true | 板 warning 类型 ⊆ 处置表 |
| 12 | `unconnected_zero` | true | 未连接 == 0 |
| 13 | `fp_lib_table_present` | true | `fp-lib-table` 存在 |
| 14 | `lib_electrical_level` | true | 电气级差异 == 0（以板为准；审计板 sha 须 == 受审板） |
| 15 | `pads_within_outline` | true | 出框 pad == 0（双口径；sha 须 == 受审板） |
| 16 | `keepout_active` | true | 每 keepout ≥1 flag != allowed |
| 17 | `density_and_clearance` | **false** | 阈值待裁（§6） |
| 18 | `ref_plane_continuity` | **false** | 阈值待裁（§6；严口径不可达） |
| 19 | `rule_severity_manifest` | true（**无条件**） | 未登记豁免 ignore == 0 |

**逐维正/负控证据**（汇总件 = `docs/K2-P4-CRITERIA-19DIM-CONTROL-INVENTORY-DRAFT-v1.md`；本轮补齐/复跑的 3 组见下）：

| 维 | 正控 | 负控 |
|---|---|---|
| `net_declared_realized` | 声明 3 网全落地 ⇒ **OK** | ①1 网 0 pad ⇒ **FAIL** ②不传 `--nets` ⇒ **FAIL**（fail-closed）③1 pad/网 ⇒ **OK**（*结构发现：声明 `>=2` 未 gate*，见 `docs/K2-P4-NETDECLAREDREALIZED-CONTROL-DRAFT-v1.md`） |
| `density_and_clearance` | B-POS ⇒ **OK**（峰值 5 ≤6 · 最小铜间距 0.100 ≥0.100mm） | C-NEG-density ⇒ **FAIL**（峰值 8 >6）· D-NEG-clearance ⇒ **FAIL**（0.100 < 0.12）· E-STALE ⇒ **FAIL** · F-MISSING ⇒ **FAIL** · G-THRESH-NULL ⇒ **FAIL**（本轮 7 案实测，见 §6） |
| `lib_electrical_level` | ⑦ 候选 ⇒ 0 差异 | 基线 33 件逐件不同 · 合成负控恰命中 `['C73']` |
| `fp_lib_table_present` | 在库 `d7316388…` ⇒ PASS | 四案（缺失/陈旧 ⇒ FAIL） |
| `pads_within_outline` | AABB 与真外框双口径 0 | P3-4 出框件 |
| `keepout_active` | 8 keepout、0 全 allowed | 闭环表相关行 |
| `rule_severity_manifest` | l5 pro `ignore = 0` ⇒ PASS | l4 板 9 条 ignore ⇒ FAIL（deny-by-default） |
| 其余 11 维 | 见汇总件 §1（逐维列名，无抽样） | 同上 |

## 4. **签认请求**（§五-3；签认 + `criteria/**` 安装 = 监理/ gate 属主执行）

| # | 待签/待装件 | 现态 | sha16 | 请求动作 |
|---|---|---|---|---|
| 1 | `docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml` | `not_countersigned: true`（草案） | `3f003cffe33a6cfd` | **装为 canonical 清单**（落 `criteria/`）+ 置 `not_countersigned: false` |
| 2 | `docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py` | 草案判定器 | `1cda68521d0e56be` | **装为 `criteria/adjudicate.py`**（rev bump；含 18 维守卫 + 无条件维） |
| 3 | `docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml` | 安装候选（18 维 / 16 enabled） | `004f7ac2666da437` | 备查（与 #1 二选一） |
| 4 | `docs/drafts/p4-j8-density-clearance-v1/manifest.k2.control-v4.yaml` | 控制件（18 维 / 全 enabled + 示例阈值） | `2531d4c616d855e9` | 正控装置（**含示例阈值**；正式阈值待 §6 裁定） |
| 5 | `criteria/adjudicate.py` / `criteria/manifest.k2.yaml` | **在库 rev=1**（ENG 只读） | `897e8bfde60e2cfe` / `7ce08757eff25557` | **本件未动**；签认后由监 bump |

**须监理同裁的 3 项**（§3-A 与 §6）：① `gerber_plane_g36` 归属（收编 P4 / 改挂 P5）② `rule_severity_manifest` 无条件维处置 O1/O2/O3（草案采 O1）③ `enabled` 缺省（17 true / 2 false）。

## 5. **锚 rev=2 登记请求**（§五-4）

| 类 | 件 | sha16 |
|---|---|---|
| 流程声明（新） | `k2/pipeline.yaml` | `c89cc57fb988f821` |
| canonical 清单（待装） | `manifest.k2.canonical-draft-v1.yaml` | `3f003cffe33a6cfd` |
| 判定器（待装） | `adjudicate.draft-v4.py` | `1cda68521d0e56be` |
| 安装候选 / 控制件 | `manifest.k2.v4.yaml` / `manifest.k2.control-v4.yaml` | `004f7ac2666da437` / `2531d4c616d855e9` |
| 仪器 | `measure_density_and_clearance.py` `dccaaa476c807def` · `measure_min_clearance_drc.py` `4386efde7451bf8e` · `measure_pads_within_outline.py` `1b177638cde3cd55` · `measure_ref_plane_continuity.py` `7a3cc545c1447b04` · `run_controls_v4.py` `8c9d3bd46d1ceb9b` · `w8_audit.draft-v2.py` `34b83cff5fe8ade7` · `k2_w8_footprint_audit_v1.py` `75404d706413d546` | 见左 |
| **在库 rev=1（不变）** | `criteria/adjudicate.py` `897e8bfde60e2cfe` · `criteria/manifest.k2.yaml` `7ce08757eff25557` | **不变** ✅ |

## 6. §五-5 两维严口径读数 + 阈值（**须裁**）

### 6-A `ref_plane_continuity`（受审板 `dae8dc8d48ff5b81`，本轮复测）

| 口径 | 读数 | 覆盖率 | `min_coverage: 1.0` 可达? |
|---|---|---|---|
| **nominal**（任一侧存在平面） | `3653/3653` | **100%** | 可达（= 控制件 `scope: nominal`） |
| **strict_filled（矩形）** | `3051/3653` | **83.52%** | **不可达** |
| capsule（严口径的另一种取法） | `3021/3653` | 82.70% | 不可达（`rect_only_gaps = 0`） |

**守恒级证明（inc85 件 `K2-P4-REFPLANE-CONTINUITY-STRICT-GAP-AND-CONSERVATION-v1.md`）**：`799.9698 = 779.0247 + 20.9450 mm²`（差 **0.0**），缺口 **99.97% 归因反焊盘/平面分区** ⇒ **可用域 < 所需覆盖**（非实现缺陷）。
⇒ **裁定请求**：(a) scope=**nominal** + `min_coverage: 1.0`（**注意：#K2-23 §二-9 明令「不得切名义口径充绿」⇒ 采 (a) 须监理/owner 明示授权**）；(b) scope=**strict_filled** + `min_coverage ≤ 0.8352`（**降阈值，须具名登记**）；(c) 物理整改（改受审载体 ⇒ 重走落件链）。**ENG 不择一。**

### 6-B `density_and_clearance`（本轮 7 案实测，受审板 `dae8dc8d48ff5b81`）

**正控（B-POS，控制件阈值）实测**：峰值器件 **5/格**（≤6）· 最小铜间距 **0.100mm**（≥0.100）· 横带占用 **0.07586**（≤0.1）· 孔环 **0.075mm**（≥0.075）· pad 到边 **0.38mm**（≥0.3）⇒ **OK**。
**负控**：C（合成拥挤板峰值 8 >6）**FAIL** · D（阈值提到 0.12 > 实达 0.100）**FAIL** · E（用 l4 测量 ⇒ sha 不匹配）**FAIL** · F（缺测量 JSON）**FAIL** · G（启用但阈值空）**FAIL（fail-closed）**。
**候选阈值（= 控制件示例，请监裁）**：`cell_mm 10 · cell_origin absolute_zero · max_fp_per_cell 6 · min_copper_clearance_mm 0.10 · max_band_occupancy_ratio 0.10 · min_via_annular_mm 0.075 · min_pad_to_edge_mm 0.30`。

## 7. 守恒 + 边界 + 复跑

- 冻结四源 `d4e81f647be7f980` / `fb07d25ac426ff84` / `dd794c54f7ce7417` / `897e8bfde60e2cfe`+`7ce08757eff25557` **逐项不变** ✅ · `criteria/**` **两份原件 sha 不变** ✅ · 受审板/pro **未改** ✅ · 两次连跑同 sha ✅。
- **同批已落**：**C1**（`p3_placement_solution.json` rev=2 补正 `C86`→`31.55,58.85`、`R42`→`93.3,61.55`，sha16 **`dfbf65c5b456cdd2`**；L2 布局解随之 rev=2 内部一致化 **`086d453d23c5fbff`**，`strap_solution_stale` 28→0 且产物 sha 不变 `d67c0f048f0d0423`）· **C2**（L-1 来源限制登记，见闭环表 §14）· **§2.4**（`k2_gen_v5.py` 注释更正为 `errata-2`）· **§三 库旧件退役**（12 件 → `k2/archive/k2_v4_stale_lib_20260918/` + `MANIFEST.md`，库 36→**24** 文件、digest `078f7dc78d980696`→**`efcd88b35d6d846c`**；`MountingHole_3.2mm_M3` 保留）· **§四** `k2/tools/k2_p4_RETIRED.md`（44 件清单标记 RETIRED(离链)，未删/未移动）。

```bash
cd /home/fila/jqdDev_2025/ic_hw
cd k2 && PYTHONPATH="$PWD/_shared:$PWD" python3 _shared/eda_core/pipeline/engine.py verify k2   # 期望 4/4 PASS
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
# 期望 PASS 8 / FAIL 2（pipeline_present PASS）
env -u SHARUN -u PYTHONHOME -u PYTHONPATH python3 \
  k2/docs/drafts/p4-j8-density-clearance-v1/run_controls_v4.py                          # 期望 A–G 七案如上
```
**fail-closed**：P4 未全绿不下单、不出交付 Gerber；P5 未开。

—— ENG（ARCHER）· 2026-09-18 · E-4/E-5 提交件 · pipeline.yaml `c89cc57fb988f821` · canonical 草案 `3f003cffe33a6cfd` · 在库判定器 `897e8bfde60e2cfe`（未动）
