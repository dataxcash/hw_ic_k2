# K2 · P4 · **判据「19 维 canonical 清单」候选合并件草案** · v1 · 2026-09-18

> 缘起：handoff inc73 §6-3-**(dd)**「『19 维 canonical 清单』候选合并件草案（统一 v4 族命名 + 无条件维处置 + 别名映射与 `enabled` 缺省，纯文档/草案，待裁）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读取证 + 纯文档/草案**（新增 1 文档 + 1 草案 YAML 于 `docs/drafts/`），未安装、未签认、未改 `criteria/**`。
> 锚（6 份清单 + 2 份判定器）：`criteria/manifest.k2.yaml` `7ce08757eff25557`（在库 9 维）· `manifest.k2.draft-v2.yaml`（17）· `manifest.k2.draft-v3.yaml`（18）· `manifest.k2.v3.yaml`（18/16 enabled）· `manifest.k2.v4.yaml`（18/16）· `manifest.k2.control-v4.yaml`（18/18）·
> `criteria/adjudicate.py` `897e8bfde60e2cfe` · `adjudicate.draft-v4.py` `1cda68521d0e56be` · **本件候选** `docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml` **`3f003cffe33a6cfd`**。
> **归属**：清单与阈值/口径＝**监理**（`not_countersigned: true`）；本件**不代裁**、**不新增检查齿**（owner ②）。

## 0. 结论（6 条）

1. **6 份清单一共有 24 个维名 + 1 个判定器内建名 = 25 个名称形态**，其中 **5 个是纯别名**，**20 个语义维**：
   **18 个 v4 家族 gated 维** ＋ **`gerber_plane_g36`（须裁归属）** ＋ **`rule_severity_manifest`（判定器无条件执行）**。
2. **别名 5 组已钉死**（§2）：`drc_warning_disposition→drc_warning_dispositions` · `lib_footprint_electrical→lib_electrical_level` · `density_and_spacing→density_and_clearance` · `v3_reference_continuity→ref_plane_continuity` · `board_frame_and_keepout→{pads_within_outline, keepout_active}`（**一对二拆分**）。
   ⇒ 两族的维数**不可相加**（inc71 结构发现 2 的闭合）。
3. **canonical 候选＝19 维**（18 gated + `rule_severity_manifest`），已写成草案 YAML（`3f003cffe33a6cfd`）：**零新增齿**（维度集 == `adjudicate.draft-v4.py` 实际 `C.get()` 守卫集 ∪ {无条件维}）、**零别名**（不含任何 v2/v3 族维名）、**零无消费者键**（不使用 `aliases` 等 adjudicator 不读的键）。
4. **等价性实测**：在库判定器 `897e8bfd` 用 canonical 草案 与 用 在库清单，对受审板 + 真源**逐维结果完全相同**（10 维：6 OK / 4 FAIL，同为 PROVISIONAL）⇒ **合并零回归**。
5. **须监理裁 3 项**：**(i) `gerber_plane_g36` 归属**（P4 收编 / 明确剔除并改挂 P5；见 §3-A）· **(ii) 无条件维处置** O1/O2/O3（§3-B）· **(iii) `enabled` 缺省**（§4：本候选 17 true / 2 false）。
6. **附带发现 2 项**（均在 §5，均**不**由本件修）：`net_declared_realized` 声明口径 ≠ 实判口径（详见 (ee) 件）· `drill_count` 阈值在库 `>=1` vs v4 `npth_min: 4`（**须监理定**）。

## 1. 24 个维名 → 语义维 映射（逐名，无抽样）

| # | 维名 | 出现于（6 件中） | 语义 | 处置 | 证据/备注 |
|---|---|---|---|---|---|
| 1 | `zone_filled` | **6/6** | 铜区填充 | **canonical** | 在库即此名 |
| 2 | `device_has_pads` | **6/6** | 器件 ≥1 pad | **canonical** | |
| 3 | `drill_count` | **6/6** | NPTH 下限 | **canonical**（阈值须裁） | 在库 `>=1`；v4 `npth_min: 4`；adjudicate 读 `npth_min`（默认 1） |
| 4 | `net_declared_realized` | **6/6** | 声明网落地 | **canonical**（口径须裁） | 见 §5-A（声明 `>=2` vs 实判 `zero==0`） |
| 5 | `pin_map_complete` | **6/6** | 引脚↔焊盘映射 | **canonical** | |
| 6 | `non45_segments` | **6/6** | 非 45° 段 = 0 | **canonical** | |
| 7 | `refdes_sets_equal` | **6/6** | 图↔板 refdes | **canonical** | v4 加「排除 H*，逐条列名」细则 |
| 8 | `pipeline_present` | **6/6** | `pipeline.yaml` 覆盖 | **canonical** | v4 加 `scope: k2` |
| 9 | `verdict_schema` | **6/6** | 产物无 `verdict` 键 | **canonical** | |
| 10 | `drc_errors` | 5/6（v2 起） | DRC error = 0 | **canonical** | 不在冻结 9 维内 |
| 11 | `drc_warning_dispositions` | 3/6（v3.1 起） | 警告类型 ⊆ 处置表 | **canonical** | 别名源见 #23 |
| 12 | `unconnected_zero` | 5/6 | 未连接 = 0 | **canonical** | |
| 13 | `fp_lib_table_present` | 5/6 | `fp-lib-table` 存在 | **canonical** | |
| 14 | `lib_electrical_level` | 3/6（v3.1 起） | 库电气级差异 = 0 | **canonical** | 别名源见 #24 |
| 15 | `pads_within_outline` | 3/6（v3.1 起） | pad 出框 = 0 | **canonical** | 拆自 #21 |
| 16 | `keepout_active` | 3/6（v3.1 起） | keepout 非全 allowed | **canonical** | 拆自 #21 |
| 17 | `density_and_clearance` | 3/6（v3.1 起） | J-8 密度/关键间距 | **canonical**（阈值待监理） | 别名源见 #22 |
| 18 | `ref_plane_continuity` | 3/6（v3.1 起） | 参考平面连续性 | **canonical**（阈值待监理） | 别名源见 #25 |
| 19 | **`gerber_plane_g36`** | **1/6（仅 v2/v3-draft）** | 平面层 Gerber G36>0 | **须裁：P4 收编 or 剔除**（§3-A） | 在 `p4-manifest-completion-v3/adjudicate.draft-v3.py:593` **有实现**；**v3.1/v4 族已剔除**（仅留未被消费的 `measure_gerber_planes`） |
| 20 | **`rule_severity_manifest`** | **0/6（判定器内建）** | `ignore` deny-by-default | **须裁：无条件维处置**（§3-B） | 三份判定器均 `chk()` 但**无 `C.get().enabled` 守卫** |
| 21 | `board_frame_and_keepout` | 2/6（v2/v3-draft） | 板框 + keepout（合并） | **别名（一对二）** → #15 + #16 | v3.1 起拆分 |
| 22 | `density_and_spacing` | 2/6（v2/v3-draft） | = #17 | **别名** → `density_and_clearance` | 仅维名不同 |
| 23 | `drc_warning_disposition` | 2/6（v2/v3-draft） | = #11 | **别名** → `drc_warning_dispositions` | **仅复数/单数** |
| 24 | `lib_footprint_electrical` | 2/6（v2/v3-draft） | = #14 | **别名** → `lib_electrical_level` | |
| 25 | `v3_reference_continuity` | 2/6（v2/v3-draft） | = #18 | **别名** → `ref_plane_continuity` | |

> 计数校验：24（清单并集） = 18 canonical gated ＋ 5 别名 ＋ 1 须裁（`gerber_plane_g36`）；再加 1 内建无条件维 ⇒ **19 = 18 ＋ 1 canonical 候选**。

## 2. 别名表（钉死，供跨件引用）

| 旧族名（v2 / v3-draft） | canonical（v4 族） | 关系 |
|---|---|---|
| `drc_warning_disposition` | `drc_warning_dispositions` | 单数→复数 |
| `lib_footprint_electrical` | `lib_electrical_level` | 同名改称 |
| `density_and_spacing` | `density_and_clearance` | 同名改称 |
| `v3_reference_continuity` | `ref_plane_continuity` | 同名改称 |
| `board_frame_and_keepout` | `pads_within_outline` + `keepout_active` | **一对二拆分**（维数变化的唯一来源） |

## 3. 须监理裁的两处

### 3-A `gerber_plane_g36` 的归属
- **事实**：该维是「计划 §P4-3 平面落图前置」的**转写**（非登记册 §C 冻结维）；实现只在 `k2/docs/drafts/p4-manifest-completion-v3/adjudicate.draft-v3.py:593-604`（族 sha `e6c2489a87890046`），**v3.1/v4 族不含**。
- **选项**：**(甲) 收编** ⇒ canonical 判定器须取 v2/v3-draft 族（或 v4 补该块），且**须先有 Gerber 目录**才可判（P5 面）；**(乙) 明确剔除** ⇒ 记为「P5 交付面判据」并在 canonical 清单中**不出现**，避免"声明在岗、无人读"。
- **ENG 陈述**：该维**依赖 Gerber 产物**，而 P4 明确**不得出交付 Gerber**（owner ③/P5 未开）⇒ 在 P4 阶段**天然不可判**；ENG 倾向 (乙)+挂 P5，但**判定归监理**。

### 3-B 无条件维 `rule_severity_manifest` 的处置
| 方案 | 做法 | 影响 |
|---|---|---|
| **O1**（**本候选采用**） | 列入 `checks`，`enabled: true` | 行为不变；清单与判定器**行为一致**；但 `enabled:false` **不会**真正关闭（判定器无守卫）⇒ **须同步加 1 行守卫**才名副其实 |
| **O2** | 不入 `checks`，另立声明键（如 `unconditional_checks`） | 语义最清楚；但引入**零消费者键**（与 pipeline 合并变体 3 键同类风险） |
| **O3** | 不入清单，仅在文档登记「判定器内建无条件维」 | 零 schema 变更；但跨件引用时「19 维」的构成**不可由清单自证** |

## 4. canonical 候选与 `enabled` 缺省

候选件：`k2/docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml` **`3f003cffe33a6cfd`**（`manifest_version: 5-canonical-draft` · `not_countersigned: true`）。

| 组 | 维度 | `enabled` 缺省（候选） |
|---|---|---|
| 冻结族 9 | `zone_filled` `device_has_pads` `drill_count` `net_declared_realized` `pin_map_complete` `non45_segments` `refdes_sets_equal` `pipeline_present` `verdict_schema` | **true** |
| 草案族 7 | `drc_errors` `drc_warning_dispositions` `unconnected_zero` `fp_lib_table_present` `lib_electrical_level` `pads_within_outline` `keepout_active` | **true** |
| 阈值待监理 2 | `density_and_clearance` `ref_plane_continuity` | **false**（机制已实现；**给阈值即可启用**，未给 ⇒ fail-closed） |
| 无条件 1 | `rule_severity_manifest` | **true**（O1；见 §3-B） |
| **合计** | **19** | **17 true / 2 false** |

## 5. 附带发现（本件**不**修，登记备裁）

**A. `net_declared_realized` 声明口径 ≠ 实判口径**（→ 详 `k2/docs/K2-P4-NETDECLAREDREALIZED-CONTROL-DRAFT-v1.md`）
- manifest `expect: "every_declared_net_pads >= 2"`，判据只 gate `nets_with_zero == 0`（`adjudicate.py:230-233`；v4 `:258-261` 同型）；`nets_with_lt2` **只报告不判定**。
- 实板（真源）实测：`nets_with_zero=0`（OK）而 **`nets_with_lt2=1`** ⇒ **声明 ≥2 被违反仍 PASS**。四案正/负控已备。

**B. `drill_count` 阈值分歧**
- 在库 `expect: "npth >= 1"`（登记册 M-11 原文）vs v4 `{npth_min: 4, expect: "npth >= 4"}`；判定器读 `npth_min`（默认 1）。
- 本候选**保留 v4 的 `npth_min: 4`**（与安装家族一致）；**应然值归监理**（若采 ≥1，须改回并留痕）。

## 6. 自检与等价性复跑

```bash
cd /home/fila/jqdDev_2025/ic_hw
CAN=k2/docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml
# ① 结构自检：19 维 / 全含显式 enabled / 维度集 == v4 判定器守卫集 ∪ {rule_severity_manifest} / 无别名
python3 - <<'PY'
import yaml, re
c=yaml.safe_load(open('k2/docs/drafts/p4-criteria-19dim-canonical-v1/manifest.k2.canonical-draft-v1.yaml',encoding='utf-8'))['checks']
v4=open('k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py',encoding='utf-8').read()
g=set(re.findall(r"C\.get\('([a-z0-9_]+)'", v4))
legacy={'lib_footprint_electrical','density_and_spacing','v3_reference_continuity','drc_warning_disposition','board_frame_and_keepout','gerber_plane_g36'}
print('dims',len(c),'all_enabled_explicit',all('enabled' in v for v in c.values()))
print('== v4_guarded+unconditional:',set(c)==g|{'rule_severity_manifest'},'legacy_present:',sorted(set(c)&legacy))
PY
# ② 等价性：在库判定器 × 两清单 → 逐维结果须相同
python3 criteria/adjudicate.py --project k2 --manifest criteria/manifest.k2.yaml \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --nets k2/hw/data/k2_sch.yaml --root k2 --out /tmp/opencode/v_lib.json >/dev/null
python3 criteria/adjudicate.py --project k2 --manifest $CAN \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --nets k2/hw/data/k2_sch.yaml --root k2 --out /tmp/opencode/v_can.json >/dev/null
python3 -c "
import json;a=json.load(open('/tmp/opencode/v_lib.json'));b=json.load(open('/tmp/opencode/v_can.json'))
f=lambda d:{r['check']:r['ok'] for r in d['oks']+d['fails']}
print('in-lib',a['n_pass'],a['n_fail'],'canonical',b['n_pass'],b['n_fail'],'identical',f(a)==f(b))"
```

**实测结果**：`dims 19 / all_enabled_explicit True / == v4_guarded+unconditional True / legacy_present []`；等价性 `in-lib 6 4 canonical 6 4 identical True`（同为 `PROVISIONAL`，因在库清单 `not_countersigned: true`）。

## 7. 边界

本件**只读取证 + 纯文档/草案**：未改 `criteria/**`（**在库清单与判定器未动**）、`_shared/**`、SPEC、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、真源、图纸、闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**（owner ②：候选维度集 == 现有实现集，零新维）。
—— ENG（ARCHER）· 2026-09-18 · 候选件 `3f003cffe33a6cfd` · 在库判定器 `897e8bfde60e2cfe`
