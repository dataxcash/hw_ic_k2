# K2 · P4 · `R1` 观察 **`U6` 0 焊盘**的载体归属裁定（不属 G-ROOT-1 继承）· v1 · 2026-09-18

> 缘起：handoff inc54 §6-3-(b)「R1 新观察 `U6` 0 焊盘的**载体归属**（是否同属 G-ROOT-1）」。`R1` 出自
> `K2-P4-GROOT-LIVE-REPRODUCTION-v1.md` §2 表末「额外 0-pad 件：`U6`」——该件只登记现象，未定根因。
> 本会话无监理放行 ⇒ ENlegal 面；**只读 + `/tmp` 补丁演示**，仓库零载体改动（仅新增本证据件）。
> 锚（sha16）：设计源板 `fb07d25ac426ff84` · l5 受审板 `6ff49da5678c2108` · 生成器 `d8d15a31061f450f`（`parse_ref_pcb` 载体）。

## 0. 结论（四句）

1. **`U6` 的 0 焊盘不属 G-ROOT-1（锚板 0 焊盘继承）**：设计源板 `k2/hw/k2_v4_8L.kicad_pcb` 的 `U6` footprint **实有 354 个 `(pad …)` 行**（本会话实测），锚板并非 0 焊盘。
2. **真载体 ＝ 生成器 `parse_ref_pcb()` 的 pad 正则**（`k2/tools/k2_gen_v5.py:220-224`）：它要求 `(at X Y)` **恰两值**且**强制尾随 `(net "…")`**；而 `U6` 的 pad 是 **3 值 `(at x y 90)`**（旋转）且部分无 net ⇒ **0 命中** ⇒ `pads={}`（空 dict）**且不抛错**（`anchor is not None` 分支，仅 `else:` 分支 fail-closed）⇒ **静默丢 354 pad**。**这是一种 fail-open**，与 D-2/D-3/D-4/D-7 同族（但载体在 k2 生成器，不在共享层）。
3. **机械证明（`/tmp` 2 行补丁，仓库零写入）**：同一镜像树内，未打补丁 → 产物 **262 pad（`U6`=0）**；打补丁（旋转可选 + 去掉 net 强制）→ 产物 **616 pad（`U6`=354）**，**其余 41 件逐一不变**，6 项自检全 **PASS**。未打补丁产物 sha16 `f615ffe6b83b88a3` 与 inc48 记录基线**一致**（装置忠实性交叉验证）。
4. **影响面量化**：锚板 42 件合计 **616** pad 行，严格正则仅命中 **262**；**失去的 354 全部且仅在 `U6`**（其余 41 件 0 损失）。
   旁证二条：① `U1` 产物 **33** pad（锚板值）vs l5 板 **58**（P4 修复后）＝**真 G-ROOT-1 循环依赖**（P-1 补丁**不**修此项）；② `K1_DNP` 集合含 `U6` 但**全文件零消费**（dead declaration，与 D-6「声称≠实际」同族）。

## 1. 装置（确定性，仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 直跑冻结生成器 → /tmp（对照，已复现）
mkdir -p /tmp/opencode/inc56
K2_OUT_PCB=/tmp/opencode/inc56/k2_v5.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc56/k2_v5_layout.json python3 k2/tools/k2_gen_v5.py
# ② /tmp 镜像树（hw/pm_gate/_shared/k2_v4.kicad_pcb/boards 均 symlink 回仓库），生成器为**副本**；
#    副本内仅改 2 行（见 §4）⇒ 对照 A/B：ctl=未打补丁 · fix=已打补丁
#    镜像根 /tmp/opencode/inc56/m_k2（重建见 §7）
```
> 镜像树使 `ROOT`＝镜像根，`PCB_REF_PATH/YAML_PATH/SPEC_PATH` 全经镜像内相对路径解析，仓库零写入。

## 2. 证据 1：锚板 pad 行 vs 严格正则命中（逐件，全 42 件）

| 件 | 锚板 `(pad ` 行 | 严格正则命中 | 判 |
|---|---|---|---|
| **`U6`** | **354** | **0** | **全部失配 ⇒ 静默 0 焊盘** |
| 其余 41 件（`J2` 74 · `J3`/`J4` 38 · `U1` 33 · C/R/A 类 …） | 262 | 262 | 一致 ✓ |
| 合计 | **616** | **262** | 差 = 354 = `U6` |

⇒ 产物 `U6` 块（`/tmp/opencode/inc56/k2_v5.kicad_pcb`）实测：`fp=ForgeOS:DS320PR1601`、**`pad_lines=0`**、块长 493 字节（对照锚板 `U6` 块 62 277 字节）。

## 3. 证据 2：正则失配的字节级原因（锚板 `U6` 原始 pad）

```
(pad "A1" smd circle
        (at -3.94 -11.05 90)          ← 3 值（含旋转）；正则要求 (at X Y) 恰 2 值 ⇒ 失配
        (size 0.3 0.3)
        (layers "F.Cu" "F.Mask" "F.Paste")
        (uuid "9ed5e61c-…")            ← layers 之后不是 (net …)
)                                      ← 原正则还强制尾随 (net "…") ⇒ 即使 at 是 2 值亦失配
```
实测统计（`U6` 块内）：`(at X Y Z)` **3 值 = 359**（含 fp_text/property）· `(at X Y)` 2 值 = **0** · pad 总数 354 · 其中带 `(net …)` 者 **246**。
⇒ **失效模式 #1（当前生效）**：3 值 `at`，354/354 pad 全中。
⇒ **失效模式 #2（潜伏）**：强制 `(net "…")`；`U6` 内 108 个 pad 无 net token（354−246，**与登记册 `M-03`「U6 … 108 ball 无网络」独立吻合**），若 `at` 已是 2 值形式则它们会单独触发失配。

## 4. 证据 3：`/tmp` 补丁 before/after（机械证明载体归属）

补丁（**仅 `/tmp` 副本**；`k2_gen_v5.py` 2 行）：

```diff
-            r'\(at\s+([-\d.]+)\s+([-\d.]+)\)\s+'
+            r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)\s+'
             r'\(size\s+([-\d.]+)\s+([-\d.]+)\)'
             r'(?:\s+\(drill\s+([-\d.]+)\))?\s+'
-            r'\(layers\s+([^)]+)\)\s+\(net\s+"([^"]+)"\)',
+            r'\(layers\s+([^)]+)\)',
```

| 案 | 装置 | 产物 `pads 总数` | `U6` pad | 其它 41 件 | 6 项自检 | 产物 sha16 |
|---|---|---|---|---|---|---|
| **CTL** | 副本**未**打补丁 | **262** | **0** | 不变 | 全 PASS | `f615ffe6b83b88a3`（＝inc48 基线 ✓） |
| **FIX** | 副本**已**打补丁 | **616** | **354** | **逐一不变**（`J2` 74/`J3` 38/`J4` 38/`U1` 33/排针 0） | 全 PASS | `60461d17edc2fba0` |

⇒ 唯一变化＝`U6` 的 354 pad ⇒ **载体归属闭合：`U6` 0 焊盘由 `parse_ref_pcb` pad 正则造成**（非锚板缺 pad）。
⇒ **补丁语义caveat（不作最终修复主张）**：该 2 行演示**丢弃 pad 旋转**（`at` 第三值未进 `pads` 字典）。`U6` 全为 circle pad（旋转不敏感）故无实害；**最终 G9 实现须携带 pad 旋转**（矩形 pad 会错向）。

## 5. 归属裁定（与 G-ROOT-1 的关系）

| 现象 | 载体 | 机制 | 与 G-ROOT-1 关系 | 修法 |
|---|---|---|---|---|
| **`U6` 0 pad** | `parse_ref_pcb` pad 正则（生成器解析器） | 锚板**有** 354 pad，但解析器**静默丢** | **同通道、不同根因**（G-ROOT-1 ＝锚板自身缺 pad） | 单独修解析器 **可**解 `U6`；**不**解排针 |
| `J6/J9/J11/J12/J13` 0 pad | 锚板（设计源板**真缺** pad 行） | 锚板 0 ⇒ 继承 0（循环依赖） | **G-ROOT-1 本体** | 去锚板依赖（G9，库/真源取几何） |
| `U1` 33 pad（产物）vs 板 58 | 锚板（设计源板为修复前值） | 锚板值被逐字继承 | **G-ROOT-1 本体**（P-1 不修） | 同上 |

**收敛含义**：G9（去锚板依赖）**一次同时消除**上述三者；而只修 P-1 只解 `U6`、仍留排针与 `U1` 陈旧 ⇒ **P-1 不应作为独立修复项单独落地**（否则须二次改动）。

## 6. 建议（**监理裁**；ENG 不自行登记/不新增检查齿）

1. **登记方式（二选一）**：(a) 并入 **G-ROOT-1** 作为具名子项（如 `G-ROOT-1-P`：锚板**解析器** fail-open）；或 (b) 独立登记为既有 fail-open 家族的第 6 例（载体 = k2 生成器，非共享层）。**两者均须监理定夺**；ENG 本件只出证据。
2. **不新增检查齿（owner ②）**：本件**未**定义新判据/新阈值；`U6` 的既有覆盖＝冻结 `device_has_pads`（每封装 pad ≥1）+ 计划 `V2 pad==引脚`，二者**当前未在岗**。
3. **与 §5-1（权威源）/§5-7（放行改生成器）合并执行**：P-1 的实现位置在 `parse_ref_pcb`，与 G9 同文件同段，**宜同批投递**（避免两次动生成器）。

## 7. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 对照：冻结生成器 → /tmp（262 pad / U6=0）
K2_OUT_PCB=/tmp/opencode/inc56/k2_v5.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc56/k2_v5_layout.json python3 k2/tools/k2_gen_v5.py
# ② 镜像树重建（src=/tmp/opencode/inc56/m_k2）
M=/tmp/opencode/inc56/m_k2; mkdir -p $M/tools $M/boards
ln -sfn $PWD/k2/hw $M/hw; ln -sfn $PWD/k2/pm_gate $M/pm_gate; ln -sfn $PWD/k2/_shared $M/_shared
ln -sfn $PWD/k2/boards/k2_sch.yaml $M/boards/k2_sch.yaml; ln -sfn $PWD/k2/k2_v4.kicad_pcb $M/k2_v4.kicad_pcb
ln -sfn $PWD/k2/tools/k2_jlc_template.kicad_pro $M/tools/k2_jlc_template.kicad_pro
cp k2/tools/k2_gen_v5.py $M/tools/k2_gen_v5.py
# ③ CTL（未打补丁）
(cd $M && K2_OUT_PCB=/tmp/opencode/inc56/ctl.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc56/ctl.json python3 tools/k2_gen_v5.py)
# ④ 打 2 行补丁（见 §4）后 FIX
(cd $M && K2_OUT_PCB=/tmp/opencode/inc56/fix.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc56/fix.json python3 tools/k2_gen_v5.py)
# ⑤ 量测：逐件 pad 行 / 正则命中 / 产品 sha —— 配方见本件 §2/§4（平衡括号提取 + 严格正则）
python3 - <<'PY'
import re,pathlib,hashlib
def blocks(p):
    s=pathlib.Path(p).read_text(encoding='utf-8');o=[]
    for m in re.finditer(r'\(footprint\s+"[^"]+"',s):
        st=m.start();d=0;i=st;ins=False
        while i<len(s):
            c=s[i]
            if c=='"':ins=not ins
            elif not ins:
                if c=='(':d+=1
                elif c==')':
                    d-=1
                    if d==0:break
            i+=1
        o.append(s[st:i+1])
    return o
for lbl,p in [('CTL','/tmp/opencode/inc56/ctl.kicad_pcb'),('FIX','/tmp/opencode/inc56/fix.kicad_pcb')]:
    b=blocks(p);tot=sum(x.count('(pad ') for x in b)
    u6=[x for x in b if '"U6"' in x][0]
    print(lbl,'total_pads',tot,'U6_pads',u6.count('(pad '),'sha16',hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16])
PY
# ⑥ 锚板侧：每件 pad 行 vs 严格正则命中（见 §2）；U6 原始 pad 样本（见 §3）
```

## 8. 边界

本件**只读 + `/tmp` 补丁（未落库）**：未改板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/SPEC/图纸/真源/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc56`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）；
**未改闭环表**（登记由监理定夺，见 §6）。
—— ENG（ARCHER）· 2026-09-18 · 设计源板 `fb07d25ac426ff84` · 生成器 `d8d15a31061f450f`
