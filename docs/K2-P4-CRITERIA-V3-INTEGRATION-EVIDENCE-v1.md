# K2 · P4 · **判据草案 v3 集成证据**（v2 + J-8 出框 + V3）· v1 · 2026-09-17

> 缘起：监理自动续推「按已批准《K2 整体整改计划》推进当前阶段（P4，未全绿）」。
> 本轮把上轮的**两件测量**接成**可安装的判定器增量**（`#K2-22 §三-4`「判据实现批量安装」），并跑正负控。
> **未就地改 v2 草案**（`7cf8a50eb832c284` 仍由监理验收中）；**`criteria/` 未动**；未动生成器/SPEC/原理图/网表/仓库板/pro；未派 WORKER；临时仅 `/tmp/opencode`。
> **禁新增检查齿**：两检查项均实现**已冻结维度**（登记册 §C J-8「出框」· 计划 §3.3 V3「参考连续性」），无新维度。

## 1. 交付物

| 件 | sha256/16 | 说明 |
|---|---|---|
| `k2/docs/drafts/p4-j8-v3-criteria-v3/adjudicate.draft-v3.py` | **`b77eacb11a261925`** | **v2 的严格超集**：对 v2 `7cf8a50e` 的 diff = **3 处 hunk**（`--pads-outline-json`/`--v3-plane-json` 参数 · 两测量装载 · `pads_within_outline` / `ref_plane_continuity` 两检查块），共 +44 行，无删改 |
| `…/manifest.k2.v3.yaml` | **`4e3a629c22f85607`** | **安装件**：`pads_within_outline` 由 `enabled:false/pending` → **`enabled:true, consume: pads_outline_json`**；`ref_plane_continuity` 仍 `enabled:false, pending:<阈值待监理>`（机制齐备） |
| `…/manifest.k2.control-v3.yaml` | **`22bf55ac605b9a5d`** | **仅正负控用**（V3 置 `enabled:true` + `thresholds.ref_plane_continuity: {scope: nominal, min_coverage: 1.0}`）；**非安装件** |
| `…/README.md` | **`144e33e826c2e3e5`** | 两步跑法 + 口径说明 |
| 测量件（上轮） | `1b177638cde3cd55` · `7a3cc545c1447b04` | `measure_pads_within_outline.py` · `measure_ref_plane_continuity.py`（均无 `verdict` 字段） |

## 2. 正/负控矩阵（实跑，逐案命中）

| 案 | 板 | manifest | PWO | V3 | 期望 | 判 |
|---|---|---|---|---|---|---|
| **A** 安装件·l5 | `6ff49da5678c2108` | `manifest.k2.v3.yaml` | **OK**（0/0/0，sha 一致） | 未启用 | PWO PASS | ✅ |
| **B** POS | l5 | control-v3 | **OK** | **OK**（名义 3653/3653） | 双 PASS | ✅ |
| **C′** NEG-outline | 合成板（`D2` 北移 1.10mm `63a88da459817540`） | control-v3 | **FAIL**（AABB 2 · 真框 2） | OK（各用本板测量） | PWO FAIL | ✅ |
| **D** NEG-V3 | 冻结 `l4` `d4e81f647be7f980` | control-v3 | OK | **FAIL**（名义 0/2327，平面层 `[]`） | V3 FAIL | ✅ |
| **E** STALE-PWO | l5 板 + **它板**测量（sha `63a88da4`） | control-v3 | **FAIL**（证据陈旧 fail-closed） | OK | PWO FAIL | ✅ |
| **F** MISSING | l5 板，无测量 JSON | control-v3 | **FAIL**（缺件 fail-closed） | **FAIL**（缺件 fail-closed） | 双 FAIL | ✅ |

**A 案整判**：`adjudicate.draft-v3 + manifest.k2.v3` 于落件板 = **15 PASS / 2 FAIL**，FAIL 集 = `pipeline_present`（gate 安装项）·
`lib_electrical_level`（⑦ 库侧待裁）—— 与 v2 的 14P/2F 相比 **+1 PASS**（`pads_within_outline` 转 PASS），**FAIL 集未变**。

## 3. 口径（ENG 只交测量；应然值归监理）

1. `pads_within_outline`（已启用）：判定式 = **全 pad AABB 出框 = 0 且 接口件（P3-4 8 件）出框 = 0 且 全 pad 真外框多边形出框 = 0**。
   已同时报告三个计数（§2 明细行），若监理裁定口径为「仅接口件」，**改 manifest 一行即可放宽**（当前落件板三者皆 0）。
2. `ref_plane_continuity`（**待监理定阈值**）：`thresholds.ref_plane_continuity`：
   - `{scope: nominal, min_coverage: 1.0}` → 名义 zone 轮廓全长覆盖（本板 **3653/3653**）；
   - `{scope: strict_filled, min_coverage: 0.95}` → 含反焊盘空洞（本板 **3162/3653**；`0.99→3071`、`0.90→3196`）；
   - 亦可「排除短段」（测量件已给逐段明细，口径变更不需改代码）。
   **未定阈值前该检查保持 `enabled:false`**（不假装实现、不缩口径）。

## 4. 安装（gate 属主侧；ENG 不安装）

1. 抄 `adjudicate.draft-v3.py` → `criteria/adjudicate.py`（版本 bump）；`manifest.k2.v3.yaml` → `criteria/manifest.k2.yaml`；
2. 判定器前置需先跑两件测量（命令见 `…/README.md`）；`cron`/pipeline 需把两步串起来；
3. 监理以正/负控复验（本件 §2 六案可复跑）→ 登记两份新 sha + 锚 `rev=3` + `not_countersigned:false`。

## 5. 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j8-v3-measurement-v1; C=k2/docs/drafts/p4-j8-v3-criteria-v3
PRO=k2/hw/k2_v4_8L.l5.kicad_pro
# 测量
$K $D/measure_pads_within_outline.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --json /tmp/opencode/l2/j8_l5.json
$K $D/measure_ref_plane_continuity.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --json /tmp/opencode/l2/v3_l5.json
# v2→v3 diff（应为 3 hunk / +44 行）
diff -u k2/docs/drafts/K2-P4-criteria-draft-v2/adjudicate.py $C/adjudicate.draft-v3.py
# 判据（安装件 / 控制件）
python3 $C/adjudicate.draft-v3.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --manifest $C/manifest.k2.v3.yaml \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro $PRO --drc-cli AppDir/bin/kicad-cli \
  --pads-outline-json /tmp/opencode/l2/j8_l5.json --v3-plane-json /tmp/opencode/l2/v3_l5.json
```

## 6. 边界

未动：`criteria/` 原件（`897e8bfde60e2cfe`·`7ce08757eff25557`）· v2 草案（`7cf8a50eb832c284` 仍待监理验收）· 冻结板 `d4e81f64…` ·
仓库板 `6ff49da5678c2108` / pro `d5e0ca067a7b585e` · 生成器 / SPEC / 原理图 / 网表真源。
P4 仍**未全绿**（`pipeline_present` + `lib_electrical_level` + G-ROOT-1/2/3 未修）⇒ fail-closed 不变。

—— ENG（ARCHER）· 2026-09-17
