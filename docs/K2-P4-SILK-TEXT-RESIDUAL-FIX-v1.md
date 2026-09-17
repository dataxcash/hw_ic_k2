# K2 · P4 · ③ 丝印位号残余修复（v1）· 2026-09-17

> 对应 handoff §4-2「**③ 丝印口径**」与 §7-2「批③ ⇒ 实现丝印 4 条」。
> 本件**不申请口径**：以物理修复把残余归零，故「降层 F.Fab / 缩字 / 容忍」议题自动作废。

## 1. 对象（复合板 `686e9c2b1768c5d3` 实测残留）
| DRC 类 | 条 | 对象 | 说明 |
|---|---|---|---|
| `silk_over_copper` | 3 | **C80 · R41 · R45 的位号参考字段** | 笔画压阻焊开窗 |
| `silk_overlap` | 1 | **R45 ↔ C80 的位号** | 两文本笔画互叠 |

全部为**位号文本**（非封装丝印线段）；此前 W-7 的丝印组（64 条）已把 43+21 降到 3+1，残余 3 件被判「无落点」——成因是 W-7 用**文本外框**作判定，比 DRC 的**字形笔画**判定严格得多。

## 2. 方法（几何优先；DRC 只作末检）
工具 `k2/tools/k2_p4_silk_text_fix_v1.py`（sha256/16 = `ac213369aa0e104c`）：
1. **判定 = 与 DRC 同语义的字形级几何**：文本取 `PCB_FIELD.GetEffectiveTextShape()`（真实笔画）；
   障碍 = pad 的 `GetEffectiveShape(F/B_Mask)` + `GetSolderMaskExpansion`、via/track 的 mask 开窗、
   **可见**丝印图元/字段笔画（隐藏字段 DRC 亦不计）；间隙取 DRC 默认 **0**（不是外框 + 40µm 余量）。
2. **求解**：本体外框中心环采样（半径 0→6.5mm 步 0.05mm × 24 向）+ 本体中心 + 局部 ±0.2mm/0.01mm 精修；
   打分 = 位移最小 → 0° 优先 → 上下位优先；多目标按可行落点数升序贪心、逐件互让（`--max-shift-mm` 默认 3.0 保可读）。
3. **不缩字、不降层、不改孔径/铜/叠层/丝印层归属**；待修件由 **DRC 报告**定位（`--drc-report`），不自设新齿。

## 3. 结果
| 项 | 值 |
|---|---|
| 移动 | C80 (91.0,57.0)→(89.095,58.516) 2.434mm · R41 (29.5,33.83)→(31.832,33.83) 2.332mm · R45 (93.3,58.12)→(95.769,58.548) 2.506mm（均 0°；字号/线宽不变） |
| 板 | `686e9c2b1768c5d3` → **`6ff49da5678c2108`** |
| 字节面 | 与复合板逐行 diff = **仅 3 行**（三个位号字段的封装内 `(at …)` 局部偏移）；铜/区域/孔径/层归属/其它一切字节不变 |
| DRC（探针语义） | 79 → **75**：`silk_over_copper` 3→**0** · `silk_overlap` 1→**0** · `lib` 35 · `missing_courtyard` 40（其余逐类不变）；error 0 · 未连接 0 |
| 几何自检 | 剩余冲突 **[]**；未落位 **0** |
| 嵌套碰撞 | **0** |
| 冻结判定器 | **PASS 6 / FAIL 4**，与复合板**逐条同集合同明细**（`zone_filled` 10/18 · `rule_severity_manifest` 9/62 · `refdes_sets_equal` 板有图无 4 · `pipeline_present`）；`non45` **0/4721** · 钻孔 NPTH4/PTH16 不变 |
| 确定性 | **三次**独立复跑（`/tmp/opencode/silk-4` · `silk-5` · `silk-6`，含清理后版本）结果板**逐字节同** `6ff49da5678c2108` |

## 4. 落件并入 ①（一笔落，不再二次评审）
`k2/tools/k2_p4_composed_land_v2.py`（sha256/16 = `f702bf8be289358d`，supersedes v1）：
- docstring/结果文案升为**五步复合**（W-7 → PDN → tncv → C86 → **③ 丝印**）；
- **新增 `--silk-report` fail-closed**：无台账或 `moves` 为空即拒绝落件（丝印步骤不可无凭落地）；
- rev-47 变更记录新增 `silk_refdes`（工具/方法/逐条移动/字节面范围）。

**沙箱端到端实证**（`/tmp/opencode/land-sbx3`，仅写 /tmp）：
板 `6ff49da5678c2108` · dst pro **逐字节不变** `f68a5fb2f82bd02d` · rev-47 **`9ba09cbc148d6836`** ·
`project.yaml` **`9cee872bd6fbdc67`** · 落件后 DRC（仓库 pro 语义）**error 0 / warning 35 / unconnected 0**。

**批准 ① 的落件命令（必须带二次确认 T-41）**：
```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/usr/bin/python3.11 k2/tools/k2_p4_composed_land_v2.py \
  --result-board <五步复合板> --result-sha16 6ff49da5678c2108 \
  --silk-report <silk_fix_report.json> --apply --confirm-repo-write
```

## 5. 复跑链（在 handoff §6 之后追加第 ⑤ 段；确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli; PRO=k2/hw/k2_v4_8L.l5.kicad_pro
# ⑤ 丝印残余修复（期望 6ff49da5678c2108）
$K k2/tools/k2_p4_silk_text_fix_v1.py \
  --board /tmp/opencode/c86/k2_v4_8L.l5.repaired.pdn-stitched.tncv-aligned.c86-relocated.kicad_pcb \
  --work-dir /tmp/opencode/silk --expect-sha16 686e9c2b1768c5d3 \
  --drc-report /tmp/opencode/c86/drc_before.json --apply \
  --drc-cli $CLI --drc-pro /tmp/opencode/c86/<同名探针 pro> \
  --fp-lib-table k2/hw/fp-lib-table --lib-dir k2/hw/lib \
  --baseline-report /tmp/opencode/c86/drc_before.json
```

## 6. 剩余与闸口
- ① 落件批准：**目标已由 `686e9c2b1768c5d3` 升为 `6ff49da5678c2108`（严格更优：5 类 79→75，silk 全 0）**，其余前置/副作用不变。
- ④ `missing_courtyard` 40：**待监理口径**（(a) 容 3 对 overlap / (b) placement 重解 / (c) 具名豁免；T-39 联合不可满足仍成立）。
- `lib_footprint_mismatch` 35：W-8 / O-2 另案（以板为准）。
- `criteria/` 两份 sha 未动；仓库板/pro/SPEC/rev-47 **未落**（本件只出 /tmp 实证）。
