# K2 · P4 · **判据侧 fail-closed 负控实证**（5 类注入 · 零静默通过）+ 判据集↔实现集对账 · v1 · 2026-09-19

> 授权：handoff §7-3（「重跑既有仪器复算」；取证）。**只读执行** `criteria/adjudicate.py`（未改判据/载壳；注入件全在 `/tmp/opencode/arc_r7/`）。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 `d251bea7c2cb1873` · 受审板 `l6 30fa849641323f98` · pro `12ad219b9f66b7b3`

---

## 0. 一句话

以**受审板 `l6` 的标准调用**为基线（**15 OK / 2 FAIL**），逐类注入「缺证据 / 陈旧证据 / 缺 DRC / 未登记 ignore / 产物含 verdict」⇒ **5 类注入**皆**新增 FAIL 或转「fail-closed」措辞**，**无一静默通过**；且 `manifest.checks`（19 条）与 `adjudicate.py` 的 `chk()`（19 名）**集合全等**（无「enabled 但未实现」的静默 PASS 齿）。
⇒ P4 门的「fail-closed」性质**经实证**；另具名：`density_and_clearance` / `ref_plane_continuity` 两维**现为 `enabled:false`（阈值待裁）**，不计入 15+2 ⇒ **P4 关门须先由 #1/#9 裁定启用并转绿**。

---

## 1. 判据集 ↔ 实现集对账（静态）

| 量 | 值 |
|---|---|
| `criteria/manifest.k2.yaml::checks` | **19** 条（`enabled:true` **17**（=`countersigned_scope.covered`）· `enabled:false` **2**） |
| `adjudicate.py` 中 `chk('<name>'` 出现名集 | **19**，与上**逐名全等** |
| **enabled 但未实现** | **0** ⇒ 无静默 PASS 齿 |
| 未启用（阈值待裁） | `density_and_clearance`（`pending` 阈值键）· `ref_plane_continuity`（`pending` scope/min_coverage） |
| 与 19 维 verdict 一致 | 17 counted = **15 OK + 2 FAIL** ✓ |

## 2. 负控 5 臂（实测；逐臂输出件 `/tmp/opencode/arc_r7/v_*.json`）

| 臂 | 注入 | oks / fails | 命中 FAIL（新） | 判 |
|---|---|---|---|---|
| **base** | — | 15 / 2 | （基线：`drc_warning_dispositions`·`lib_electrical_level`） | 基线成立 |
| **A** | W-8 证据 `board_sha16` 篡改（陈旧） | 15 / 2 | `lib_electrical_level`：**「…≠… ⇒ 不一致（证据陈旧，fail-closed）」** | ✅ 陈旧证据不放行 |
| **B** | **缺** `--w8-audit-json` | 15 / 2 | `lib_electrical_level`：**「缺 W-8 电气级审计 JSON（--w8-audit-json）⇒ fail-closed」** | ✅ 缺证据不放行 |
| **C** | **缺** `--drc-cli` | **13 / 4** | `drc_errors`·`drc_warning_dispositions`·`unconnected_zero` **各「缺 DRC 实跑（--drc-cli）⇒ fail-closed」** | ✅ 缺 DRC 不放行（**3 维连坐**） |
| **D** | pro 未登记 `ignore`（`silk_overlap`） | **14 / 3** | `rule_severity_manifest`：**「未登记豁免的 ignore 1/62: ['silk_overlap']」** | ✅ deny-by-default 生效 |
| **E** | 产物含 `verdict` 字段（`--artifacts`） | **14 / 3** | `verdict_schema`：**「产物中出现 verdict 字段的文件: ['fake_verdict.json']」** | ✅ 产物守卫生效 |

> **如实登记（本笔）**：E 首跑误选了在册 `verdict_19dim_*.json` 作注入件 —— 该件**不含** `"verdict":` 键（键为 `passed/n_pass/fails/oks/...`）⇒ 守卫未触发（**非缺陷**）；随即换 `{"verdict":...}` 探针重跑，命中 FAIL（上表 E）。

## 3. 结论与 P4 关门含义

1. **判据侧 fail-closed 性质成立**（5/5 注入皆拦），且与在册 15 OK / 2 FAIL **同源可复现**（证据包 #6：verdict 逐字节同）。
2. **P4 关门前置新增具名一条**：`density_and_clearance` 与 `ref_plane_continuity` 现为 **`enabled:false`**（阈值未定）⇒ 即便 #6/#7 收口，仍须：
   - **#1** 裁定 ⇒ 启用 `ref_plane_continuity`（阈值口径：`scope`/`min_coverage` 或新口径）——证据包 #2 §1 显示 **R=0.5 ⇒ 0.0（PASS）**；
   - **#9** 裁定 ⇒ 启用 `density_and_clearance` rev=3（测量已达标：峰 7 · bracket **[0.100,0.105]**）；
   ⇒ 二者启用并转绿后，「**判据集 == manifest 应然集 ∧ 全维绿**」方成立。
3. **未改任何载体/判据**；注入件仅 `/tmp`。

## 4. 复现

```bash
bash /tmp/opencode/arc_r7/failclosed_arms.sh     # base + A–E 五臂（每臂全新 --drc-work-dir）
python3 - <<'P'                                  # 判据集 ↔ 实现集
import yaml,re
m=yaml.safe_load(open('criteria/manifest.k2.yaml'))
print(sorted(m['checks']))
print(sorted(set(re.findall(r"chk\(\s*['\"]([a-z0-9_]+)['\"]", open('criteria/adjudicate.py').read()))))
P
```

## 5. 边界

未改生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿（**本件为既有判据的负控实跑，非新增齿**）；未放松下限；未以「接近 0」充绿。临时仅 `/tmp/opencode/arc_r7/`。
