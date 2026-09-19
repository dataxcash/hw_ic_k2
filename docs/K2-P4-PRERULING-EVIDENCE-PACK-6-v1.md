# K2 · P4 · **裁定前纯证据包 #6**（门态**独立复算**（19 维 verdict 逐字节同） · **`l7` 落件 runbook（执行就绪，未执行）**）· v1 · 2026-09-19

> 授权：handoff §7-3（「重跑既有仪器复算」；**不触载体**）。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 `d251bea7c2cb1873` · 受审板 `l6 30fa849641323f98` · pro `12ad219b9f66b7b3`

---

## 0. 一句话

- **§1 门态独立复算**：本轮以**全新 DRC work-dir** 重跑 W-8 审计 + **19 维标准调用**（5 件测量输入取在册册）⇒ **`15 OK / 2 FAIL` 复现**，FAIL 集与 detail 串**逐字同**，且**复算 verdict JSON 与在册件逐字节相同（2771 B）** ⇒ P4 门态**无随机性、可独立重建**；两项 FAIL 恰为待裁项（#7 `J-1` 登记 · #6 `U-03`/`M-09`/`J-7`）。
- **§2 `l7` 落件 runbook**：把 handoff §7-2 a→d 展开为**逐条可执行命令 + 停线条件**（仪器 sha 齐备），使裁定后执行**机械化、零即兴**。**本件不执行任何一步。**

---

## 1. 门态独立复算（本笔实测，`/tmp/opencode/arc_r6/`）

| 项 | 复算 | 在册 | 判 |
|---|---|---|---|
| W-8 审计（`l6` 板） | `58 / identical 49 / diff 5 / name_set_only 0 / no_link 4 / unloadable 0` | 同 | **全字段同**（含 `board` 路径字段） |
| 19 维 verdict | `passed=False` · **oks 15 · fails 2** | 同 | **FAIL 集相同**：`['drc_warning_dispositions','lib_electrical_level']` |
| FAIL detail 串 | `未登记 warning 类型 7/9: ['copper_sliver','silk_edge_clearance','silk_over_copper','silk_overlap','track_dangling','track_not_centered_on_via','via_dangling']…` / `电气级差异 5 + 仅 pad 名差异 0…` | 逐字同 | ✅ |
| **verdict JSON 字节** | `/tmp/opencode/arc_r6/verdict_l6.json` | 册 `verdict_19dim_board_l6_30fa8496.json` | **逐字节相同（2771 B）** |
| 本次 fresh DRC | `164 / error 0 / unconnected 0` | 同 | ✅ |

复算命令（容器根，`--root .` = #K2-29 §二-3 钉死口径）：
```bash
python3 criteria/adjudicate.py --project k2 \
  --board k2/hw/k2_v4_8L.l6.kicad_pcb --pro k2/hw/k2_v4_8L.l6.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --root . \
  --drc-cli AppDir/bin/kicad-cli --drc-work-dir /tmp/opencode/arc_r6/adj_drc \
  --w8-audit-json  <册>/w8_audit_board_l6_30fa8496.json \
  --pads-outline-json <册>/pads_within_outline_board_l6_30fa8496.json \
  --v3-plane-json <册>/ref_plane_continuity_board_l6_30fa8496.json \
  --density-json <册>/density_board_l6_30fa8496.json \
  --min-clearance-json <册>/min_clearance_drc_board_l6_30fa8496.json \
  --out /tmp/opencode/arc_r6/verdict_l6.json --measure-out /tmp/opencode/arc_r6/measure_l6.json
```
⇒ **结论**：P4 现状（P4 施工中 · 无 error · 未连接 0 · `zone_filled` 10/10 · 19 维 15/2）**可独立复算且确定**；**不**存在「读数漂移」或「仅在一次运行成立」的隐患。

---

## 2. `l7` 落件 runbook（**裁定后**执行；本件不执行）

> 触发条件：监理就 #6 择 **(A)/(B)**（或 (C) 则本 runbook 作废）。
> 变量：`W=/tmp/opencode/l7`（临时工作区，**禁**写仓库）、`PATCH`= 生成器补丁集（#6 裁定面）。

### 2.0 前置断言（任一不满足 ⇒ 停机）
1. `sha256(…l6.kicad_pcb)=30fa849641323f98` · `sha256(…l6.kicad_pro)=12ad219b9f66b7b3` · **冻结 l4 `d4e81f647be7f980` 未动**；
2. 判据 rev=2 三件 sha 未变（`d251bea7` / `1cda6852` / `568d2e93`）；
3. 基线读数快照（用于前→后比对）：`unconnected 0` · DRC `error 0` · `zone_filled 10/10` · 19 维 `15 OK / 2 FAIL` · 5 件测量 `w8 49/5/4/0`。

### 2.1 段1 / 段2-3（链复现）
```bash
cd /home/fila/jqdDev_2025/ic_hw
K2_OUT_PCB=$W/s1.kicad_pcb K2_OUT_JSON=$W/s1.json AppDir/usr/bin/python3.11 k2/tools/k2_gen_v5.py      # 段1
AppDir/usr/bin/python3.11 k2/tools/k2_route_segment_v1.py --in $W/s1.kicad_pcb --out $W/z.kicad_pcb --upto all   # 段2+段3(zone)
sha256sum $W/s1.kicad_pcb $W/z.kicad_pcb | cut -c1-16   # 前→后记录；段1 预期 ≠ d67c0f04（补丁面已变）
```
- 若 #6 选 **(A)**：先按裁定补 `gen`（pad `rot` + 无号 `F.Paste` 发射面）再跑；若 **(B)**：**不改生成器**，本步仅按 (i-a) 的 `:339/:345`（有效 2 处；`:319` 对现行输入 no-op）打补丁。
- **停线**：生成器自检非 `6/6 PASS`、或 54 器件/672 pads/100 网变动 ⇒ 停。

### 2.2 落件 + pro 断言 + SPEC bump
```bash
cp $W/z.kicad_pcb k2/hw/k2_v4_8L.l7.kicad_pcb
# pro：链产 pro（源 tools/k2_jlc_template.kicad_pro ecce278068e6d330）——落件后立即断言：
python3 - <<'P'
import json;d=json.load(open('k2/hw/k2_v4_8L.l7.kicad_pro'));b=d['board']
rs={k:v for k,v in b['design_settings']['rule_severities'].items() if v=='ignore'}
print("ignore:",len(rs),"/",len(b['design_settings']['rule_severities']))          # 期望 0/62
print("top_level_sheets:",d['schematic']['top_level_sheets'])                        # 期望 k2_sch.kicad_sch
print("sheets 键存在:", 'sheets' in d['schematic'])                                  # 期望 False
P
```
- **SPEC bump**：**新增** `SPEC_k2_v4.spec-rev-52.json`（**旧 rev 逐字节不改**），与 rev-51 的 diff **仅** `board_sha16`（新板）＋ bump 记录字段（`authority`/`basis`）；`k2/pm_gate/project.yaml` 的 `spec_name` 指针同笔改指 rev-52。

### 2.3 全链重锚（逐件报「前 → 后 sha + PASS/FAIL 集」）
| # | 件 | 命令（工具 sha16） |
|---|---|---|
| 1 | W-8 审计 | `AppDir/usr/bin/python3.11 k2/tools/k2_w8_footprint_audit_v1.py --board <l7> --proj-lib k2/hw/lib --out-json … --out-md …`（`75404d706413d546`） |
| 2 | 出框 | `… docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py`（`1b177638cde3cd55`） |
| 3 | 参考连续性（V3 覆盖口径） | `… p4-j8-v3-measurement-v1/measure_ref_plane_continuity.py`（`7a3cc545c1447b04`） |
| 4 | 密度/间距 | `… p4-j8-density-clearance-v1/measure_density_and_clearance.py`（`dccaaa476c807def`） |
| 5 | 最小铜间距 bracket | `… p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board <l7> --pro <l7 pro> --kicad-cli AppDir/bin/kicad-cli --work-dir <**全新目录**> --json …`（`4386efde7451bf8e`）——⚠ 必用全新 work-dir |
| 6 | **19 维标准调用** | §1 同款命令（板/pro/5 件输入换 `l7`，`--drc-work-dir` **全新**）；期望：`unconnected 0 · error 0 · zone_filled 10/10 · non45 0/5125` 不回退，FAIL 集按裁定收敛 |
| 7 | 测量册再重锚 | 新建 `k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-l7-<date>/`，`MANIFEST.md` 记逐件 sha + `board_sha16 == <l7>` 自检（fail-closed 扫描 = 0 BAD） |
| 8 | 引擎门禁 | `PYTHONPATH=k2/_shared:$PWD/k2 python3 _shared/eda_core/pipeline/engine.py verify k2`（期望 4/4） |

### 2.4 确定性（链产物）
```bash
bash /tmp/opencode/inc114/arm3/run_arm3.sh   # 模式：移走 l4/l5 板+pro → 跑全链 → 无条件还原 → 比 sha
```
- **撤三臂**后链产物 sha 与常态跑**逐字节同**；**且连续两次全链跑同 sha**（不同 ⇒ **不得入库**）。
- 结果落 `$W/arm_l7.log` + sha 三元组。

### 2.5 停线条件（fail-closed，任一命中即停并报监理）
`unconnected > 0` · DRC `error > 0` · `zone_filled < 10/10` · W-8 出现**新增** `electrical_diff` · 两次连跑不同 · 冻结四源/l4 漂移 · 判据 sha 变动。

### 2.6 边界
本 runbook **不执行**任何一步；`l7` 属「新落件」（非改冻结件）；**不改** `criteria/**`（#7 登记与 #9 rev=3 启用另由 gate 属主 + 签认）。

---

## 3. 复现 & 边界

- 本件读数件：`/tmp/opencode/arc_r6/{verdict_l6.json, measure_l6.json, w8_l6.json, adj_drc/}`（易失，可由 §1 命令重建）。
- **未改**生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿；未放松下限；未以「接近 0」充绿。
