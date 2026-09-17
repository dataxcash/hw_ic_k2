# k2/docs/drafts/p4-manifest-completion-v2/ —— P4 判据缺口补齐草案（ENG 草案件）

> 状态：**未安装、未签认**（`not_countersigned: true`）。`criteria/`（0444, owner=ic_hw_gate）逐字节未动。
> 依据：监理 `#K2-20 §二`（`criteria/manifest` 不予签认 ⇒ 须先补齐转写）+ `§五-2`（ENG 起草 → 监理正/负控复验 → 版本 bump 安装 → 监理签认）。
> 提交与证据说明见：`k2/docs/K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md`。

## 件清单（sha256/16）

| 件 | sha256(16) | 说明 |
|---|---|---|
| `manifest.k2.draft-v2.yaml` | `e09427be14a78b78` | 转写补齐版判据清单草案（含 `null` = 待监理填的取值） |
| `adjudicate.draft-v2.py` | `a57b8ffd77524eb5` | 判定器草案（实现；自跑 kicad-cli DRC，防伪造绿） |
| `make_negatives_v2.py` | `1c46bd1bd58f5bb5` | 负控造件脚本（v2.3：8 件 m1..m8；m6 = 裸名件对照、**m7 = 有链件电气级跳变**、m8 = 断链 fail-closed） |

## 修订（v2.3 · 2026-09-17）—— **W-8 电气级实现**（`lib_footprint_electrical`）

依 **监理 #K2-19 §二 W-8**（板实作 pad 电气级必须 0；判据只容忍图形级）**修实现**：

- **原实现错**：`lib_footprint_electrical` 直接用 DRC 的 `lib_footprint_mismatch + lib_footprint_issues` 计数
  ⇒ 把 `fp_line` / `property` 等**图形/属性级**差异一并算入（实测 35 件），既非 W-8 语义、也与「容忍图形级」矛盾。
- **新实现**：判定器内**纯 stdlib** 逐件比 pad **数 / 名 / 形状 / 尺寸 / 钻孔 / 自转 / 局部位置**
  （`measure_footprint_electrical`；与 `k2/tools/k2_w8_footprint_audit_v1.py`（pcbnew 版）**同口径、同结论**，互为交叉验证）。
  库解析 = `fp_lib_table_paths`（含 `${KIPRJMOD}`）→ 未命中回落 `fp_lib_roots`（默认判定器 `--std-footprint-roots AppDir/share/kicad/footprints`）。
  无库链接 / 库不可载 件按 `lib_footprint_link_policy`（**null ⇒ fail-closed**，待监理填）。
- **实测结论（正控，当前板）**：可库比对 35 件中 **33 件电气级存在差异**（pad 几何 31 + pad 名集合 2），
  **仅 2 件一致**（`U4`/`U5`）；**24 件为裸封装名（无库链接）⇒ J-7 不可判**。
  ⇒ 监理 W-8 裁定之依据「电气级 = 0」**不成立**；根因与出路（(甲′)/(乙)）见 `k2/docs/K2-P4-W7-W8-DISPOSITION-PLAN-v1.md`。
- **负控（定向注入，8 件全过）**：
  `m1` 未连接→`unconnected_zero` FAIL · `m2` 清填充→`zone_filled` FAIL · `m3` 30° 段→`non45_segments` FAIL ·
  `m4` 拆 In6 外形→`drc_errors`+`v3_reference_continuity` FAIL · `m5` 改 refdes→`refdes_sets_equal`+`pin_map_complete` FAIL ·
  **`m7`（新增）U5 pad1 尺寸 +0.05mm（U5 = 板上与库电气级一致的 2 件之一）⇒ 电气级差异件 33 → 34、U5 被点名** ✅ ·
  **`m8`（新增）C89 库链接改指向不存在库件 ⇒ 库不可载 1、无可比对 35→34、检查 fail-closed FAIL** ✅ ·
  `m6` U1.11 pad 尺寸 +0.05mm：U1 为**裸名** ⇒ J-7 电气级**不可判**、差异计数不变（**覆盖缺口对照件**，非「实现失效」）。
- 造件脚本随之上调（m6 语义注明 + **新增 m7/m8** + 每件落 `fp-lib-table`/`lib/` 以便 `/tmp` 内库解析）。

## 修订（v2.2 · 2026-09-17）

- **C5b/IN-7 口径对齐**：`board_frame_and_keepout` 的回避区腿改为按已裁口径（`#K2-17 §五`：**5 开关含 copperpour，每区 ≥1 非 allowed**），并并列上报「仅 copperpour 受限」/「更严 4 开关口径」两个强度指标。v2.1 曾注「copperpour 不计」= 比裁定更严，且实测在本板**不可达**（`pads→not_allowed` ⇒ 199 条 `items_not_allowed`）⇒ 会使 P4 结构上不可闭。见 `k2/docs/K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md`。
- 正控随之 **PASS 11 / FAIL 7**（唯一变化项 = `board_frame_and_keepout`）。

## 修订（v2.1 · 2026-09-17）

- 依 **#K2-19 §二 W-9**（k2 门 = k2-scoped）实现 `pipeline_present` 的 scope：新增 `manifest.pipeline_scope: [k2]` + 判定器按 scope 过滤 sch 目录 ⇒ 报 `k2/hw/sch` 1 目录（原 6 目录）。
- 两者 sha 随之为上表 v2.1 值；`make_negatives_v2.py` 未变。

## 与 `/tmp` 副本的关系

本目录是 `/tmp/opencode/p4/draft/` 中同名草案件的**仓库耐久副本**（`/tmp` 为易失区）。
`manifest.k2.draft-v2.yaml` 与 `adjudicate.draft-v2.py` 与 `/tmp` 原件**逐字节同**（sha 一致）；
`make_negatives_v2.py` = `/tmp/opencode/p4/draft/make_negatives.py` 的 v2（2026-09-17 修：适配增量 16 板的新封装头格式 `\t(footprint "LIB:NAME"`，旧正则致 m6 未注入）。

## 变更纪律

`criteria/` 是只读冻结件（`897e8bfd…` / `7ce08757…`）。本目录的草案只有在监理完成正/负控复验后，才由**属主侧**以版本 bump 安装并签认。
