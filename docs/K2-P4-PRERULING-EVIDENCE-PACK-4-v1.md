# K2 · P4 · **裁定前纯证据包 #4**（#1 选项②「成因派生定义」**干跑实测**：**l6 不闭合**）· v1 · 2026-09-19

> 授权：handoff `k2-p4-handoff-20260920-inc114-context-handoff.md` §7-3（取证；**不触载体**）。
> 干跑器 `/tmp/opencode/arc_r4/measure_derived_antipad.py`（+ `measure_derived_v2.py`，加逐参考层分解）；**与在册闭运算器同 plane/segment 口径**（同器 `A_gap` 逐数复现，见 §2）。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 · 受审板 `l6 30fa849641323f98`

---

## 0. 一句话（**决策相关**）

按决策纸 **#1 选项②的字面定义**（`antipad = pad/via 按 zone clearance 外扩并集`）干跑：**`l6` 残余非反焊盘缺口 = 0.122997 mm²（FAIL，非 0）**，且对「是否排除所在平面网」不敏感（0.122862 mm²）。负控冻结板 `l4` = **772.7965 mm²（FAIL）** ⇒ 器不松。
⇒ **选项②按字面不能关 #1**；而 **选项①（钉 `R=0.5`）实测 0.000000 且 `R*∈(0.35,0.40]`**（证据包 #2）。故**事实层面**：① 可即刻关（零改造、l4 负控恒 FAIL）；② 若要采，须**再补定义**（对 0.12mm² 级边界残差的具名口径）或**容忍值**——二者均属口径裁定，ENG 不择一。

| 口径（同一板、同一 `A_gap` 定义） | `l6` 残余 (mm²) | `l4`（冻结负控） |
|---|---|---|
| R 闭运算 **R=0.25** | 20.890482 **FAIL** | 798.52 **FAIL** |
| R 闭运算 **R=0.40** | 0.006330 ≈PASS（= 固定孔 keepout） | — |
| R 闭运算 **R=0.50** | **0.000000 PASS** | 798.52 **FAIL** |
| **成因派生（本件，pad/via⊕0.2mm）** | **0.122997 FAIL** | **772.7965 FAIL** |

---

## 1. 口径与实现（可复核）

- **缺口定义**（与在册器同）：高速段（网名前缀 `PCIE_`）按线宽外扩矩形 − 相邻层中覆盖率最高平面层的**已填充 zone 并集**；参考层选择、4 层内层（In1/In3/In4/In6）、`A_gap` 汇总口径全部对齐（实测 `A_gap = 20.955203 mm²` == 在册 `A_gap 20.9552`；`l4` = `798.172376` == 在册 798.1724）。
- **派生反焊盘** `D(L) = ∪( layer L 上 pad 铜形(`GetEffectivePolygon`) ⊕ zone clearance ) ∪ ( layer L 上 via 圆 ⊕ clearance )`；clearance = 该层 zone 自身 clearance（`l6` 四层全 **0.2mm**）。
- **残余** = 缺口 − `D` − 固定孔 keepout（板外另计，不计入主残余）。**track 缝隙 / zone 间缝隙不扣除**（保守）。
- 两模式：**excl_planenet**（排除与平面同网的 pad/via = 严守定义）· **all_nets**（全含 = 最宽）⇒ 上报两者区间。
- 内层实测：`l6` 内层 **0 条走线**（仅在层外路由）⇒ 本件无「走线开槽」混淆项；`l6` 内层 pad 20/层 · via 312–602/层。

## 2. 结果（`l6` 受审板 `30fa849641323f98`）

| 量 | 值 (mm²) |
|---|---|
| `A_gap`（总缺口） | **20.955203** |
| `residual_derived_excl_planenet` | **0.122997**（**0.587%** of A_gap） |
| `residual_derived_all_nets` | **0.122862** |
| 逐参考层：`In1` / `In6` / `In3` / `In4` | 0.066576 / 0.043268 / 0.007557 / 0.005597 |
| 逐网最大（top5，皆 P/N 对） | `PCIE_UP_OUT0_P_J2` 0.004429 · `PCIE_DN_OUT1_N_MCIO` 0.003864 · `PCIE_DN_OUT3_N_MCIO` 0.003858 · `PCIE_DN_OUT0_N_MCIO` 0.003840 · `PCIE_DN_OUT2_N_MCIO` 0.003819 |

⇒ 残差**散布**（0.59%、单网 ≤0.0045mm²、跨 4 层、最大层 0.067mm²）——量级与**平面填充边界/zone 边缘缝隙**相当，**不是**系统性平面分割（后者应呈现为整段长条、单网 mm² 量级）。**但本件不主张其为「几何伪影」**（无独立证据），只报读数。

## 3. 负控 `l4`（冻结板 `d4e81f647be7f980`）

`A_gap = 798.172376`（== 在册闭运算器 l4 读数）· `residual_derived = 772.796523`（In4 430.146 · In1 288.797 · In6 53.853）⇒ **派生口径对未铺铜/平面退缩板照样判 FAIL**（口不放宽）。

## 4. 决策影响（供 #1 一句话裁定）

| 路径 | `l6` 判 | 代价/备注 |
|---|---|---|
| **① 钉 `R=0.5`** | **PASS 0.000000** | 零改造（只定阈值）；`R*=~0.40` 有 ≥0.1mm 余量；l4 负控恒 FAIL ⇒ **非缩口径**；建议采纳 |
| **② 成因派生（字面）** | **FAIL 0.122997** | 须**再补**一项口径（0.12mm² 级边界残差：是具名容忍，还是先证为几何伪影），否则不闭合；ENG 不自行定 |
| ③ 混合 | — | 例如 R 口径定阈值 + 派生口径作**信息项**（不改变主判） |

## 5. 具名事故（本笔，如实登记）

- **`pkill -f measure_derived_v2.py` 自匹配**：该 pattern 亦命中**本会话自身命令行** ⇒ 向自己发 SIGTERM（rc=143，shell 被杀；仓库/进程无损伤）。**与 #K2-33 §一 同根因族**（`pgrep/pkill` 的 `-f` 全命令行匹配）——建议 #K2-33 规约**扩展具名**：不仅禁 `pgrep -f` 轮询，亦禁 `pkill -f <本笔工件名>`（改用 `kill -TERM <pid>`）。
- 两次干跑失败（如实）：① l4 负控首跑 `max() arg is an empty sequence`（无填充层取 clearance 崩）；② v2 首跑 `per_layer` 未初始化。均已按 pid 判活重跑修毕（#K2-33 合规：全程 `k2_wait_pid.sh --pid`，无自匹配轮询）。

## 6. 复现

```bash
P=AppDir/usr/bin/python3.11; cd k2
$P /tmp/opencode/arc_r4/measure_derived_v2.py --board hw/k2_v4_8L.l6.kicad_pcb \
   --spec pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-51.json --json /tmp/opencode/arc_r4/derived_v2_l6.json
$P /tmp/opencode/arc_r4/measure_derived_v2.py --board hw/k2_v4_8L.l4.kicad_pcb \
   --spec pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-51.json --json /tmp/opencode/arc_r4/derived_v2_l4.json
```
读数件（`/tmp` 易失）：`derived_v2_l6.json` · `derived_v2_l4.json`（`board_sha16` = `30fa849641323f98` / `d4e81f647be7f980`）。

## 7. 边界

未改生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿；**未以「接近 0」充绿**（0.122997 具名报 FAIL，未主张伪影）；`R` 口径**未自定**（仍待监裁）；冻结件 l4 只读。临时仅 `/tmp/opencode/arc_r4/`。
