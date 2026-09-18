# K2 · P4 · **闭环表 3 处采纳后判据侧影响复核草案**（M-02 / F-12 / N-07：0 处读数变化）· v1 · 2026-09-18

> 缘起：handoff inc69 §6-3-(u)「`M-02`/`F-12`/`N-07` 采纳后**判据侧影响复核**（这三条进入「载体已修待判据」后，对 19P/0F 判据集的读入口径复核，纯只读复算）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读复算**，仓库零载体改动（仅新增本证据件）。
> 锚：闭环表条目 `M-02`/`F-12`/`N-07`（v1.4 `2de0dea4f5a5729d`；修正提案 `86e73a061e57f5d4`/diff `2b5f73d0e96a3c10`）· 判定器草案 `adjudicate.draft-v4.py` **`1cda68521d0e56be`**（19 维）· 安装件 `criteria/manifest.k2.yaml` `7ce08757eff25557`（9 维）· `k2/hw/fp-lib-table` `d731638859be9a08` · `k2/hw/lib/ForgeOS.pretty` 20 件。
> **归属**：这三条的「根闭」判定＝**监理**；本件只给**判据侧读数影响**，**不新增检查齿**（owner ②）。

## 0. 结论（四条）

1. **3 处修正对 19P/0F 判据读数的影响 = 0 处**：`M-02` 无判据消费文档层；`F-12` 的库表半边对应 `fp_lib_table_present`（**已在 19 维内且启用**，载体已修 ⇒ 该维 PASS）；`N-07` 对应 `refdes_sets_equal`（**已在 19 维内**），实测**实例态未标注 = 0** ⇒ 该维读数不受影响。
2. **`M-02`（README/架构文档）**：判据侧**无**任何维度消费 `k2/README.md` / `docs/01-architecture*.md` ⇒ 修正后属「**载体已修、无判据（不适用）**」；若监理要求机器判据，须**新增检查齿**（owner ② 冲突），本件不提议。
3. **`F-12`（库表 ＋ refdes）**：`fp_lib_table_present` 的实现读**板工程目录下 `fp-lib-table` 的存在性**（v4 §320-323）。实测：文件存在 `d731638859be9a08`、`ForgeOS` 1 条、`ForgeOS.pretty` **20** 件 ⇒ **载体侧已满足**，该维在安装后应 PASS；refdes 半边由 `N-07` 结论消解，**不改** `refdes_sets_equal`。
4. **`N-07`（未标注 refdes）**：`refdes_sets_equal` 读 `sch_refdes` 集 vs 板 ref 集。本轮只读复算：`k2/hw/sch/*.kicad_sch` 中**实例态未标注 = 0**，**31 个 `?` 全部位于 `(lib_symbols …)` 定义子树**（分布 `connectors 2 · mcu_sideband 13 · power_12v… 9 · power_decoupling… 3 · redriver… 4 · k2_sch 0`；前缀 `J?/U?/R?/C?` 共 7 类）⇒ **判 OUT 不改变任何 PASS/FAIL**。

## 1. 逐条影响表

| 条 | 修正后状态 | 相关判据维（19 维内） | 读入口径 | 读数是否变化 | 后续动作 |
|---|---|---|---|---|---|
| `M-02` | 载体已修（三文档 `DS160PR810`/`U3`/`U7` = 0） | **无** | — | **否** | 监理定义「无判据」类的根闭口径（或判 OUT/具名不适用） |
| `F-12` | 载体已修（库表 ＋ refdes 伪缺陷） | `fp_lib_table_present` | 板工程目录 `fp-lib-table` 存在性 | **否**（已 PASS 条件满足） | 随判据安装启用即可 |
| `N-07` | **OUT（具名：前提不成立）** | `refdes_sets_equal` | `sch_refdes` 集 == 板 ref 集 | **否**（实例态 0 个 `?`） | 采纳 inc66 (p) 的闭环表 diff 即可 |

## 2. 19 维清单（`adjudicate.draft-v4.py` `1cda68521d0e56be`；PROVISIONAL 19P/0F）

```
density_and_clearance · device_has_pads · drc_errors · drc_warning_dispositions · drill_count ·
fp_lib_table_present · keepout_active · lib_electrical_level · net_declared_realized · non45_segments ·
pads_within_outline · pin_map_complete · pipeline_present · ref_plane_continuity · refdes_sets_equal ·
rule_severity_manifest · unconnected_zero · verdict_schema · zone_filled
```
与本 3 条相关者：**`fp_lib_table_present`**（F-12）· **`refdes_sets_equal`**（N-07）；`M-02` 无。
（注：安装件 `criteria/manifest.k2.yaml`（9 维）**不含** `fp_lib_table_present`/`lib_electrical_level` 等 ⇒ 「在岗」仍待安装 + 签认，见 inc67 (t) 件 §1。）

## 3. 「根闭」资格说明（不改变判定，仅记账）

闭环表「全闭」= 「载体已修」**且**「防复发判据在岗」。本 3 条采纳后：
- `F-12`：载体已修 ✅ ＋ 判据**已实现、待安装**（`fp_lib_table_present`）⇒ 安装后具根闭资格。
- `N-07`：判 **OUT（具名）** ⇒ 不参与「载体未修」计数（30→27 的一部分），**无根闭问题**。
- `M-02`：载体已修 ✅ ＋ **无判据** ⇒ 是否计「根闭」或「根闭（不适用）」**须监理定义口径**（本件不预判）。

## 4. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# N-07：实例态 vs lib_symbols 占位（期望 实例态=0 / lib_symbols=31）
python3 - <<'PY'
import re, pathlib
def strip(t):
    out=[]; i=0
    while True:
        j=t.find('(lib_symbols', i)
        if j<0: out.append(t[i:]); break
        out.append(t[i:j]); k=j; d=0; q=False; e=False
        while k<len(t):
            c=t[k]
            if q:
                if e: e=False
                elif c=='\\': e=True
                elif c=='"': q=False
            else:
                if c=='"': q=True
                elif c=='(': d+=1
                elif c==')':
                    d-=1
                    if d==0: k+=1; break
            k+=1
        i=k
    return ''.join(out)
P=re.compile(r'\(property "Reference" "([^"]*\?)"'); ti=tl=0
for f in sorted(pathlib.Path('k2/hw/sch').glob('*.kicad_sch')):
    t=f.read_text(encoding='utf-8'); b=strip(t); ti+=len(P.findall(b)); tl+=len(P.findall(t))-len(P.findall(b))
print('实例态未标注 =', ti, '· lib_symbols 占位 =', tl)
PY
# F-12：库表与库件（期望 存在 / ForgeOS 1 条 / 20 件）
ls k2/hw/fp-lib-table && grep -c 'ForgeOS' k2/hw/fp-lib-table && ls k2/hw/lib/ForgeOS.pretty/*.kicad_mod | wc -l
```

## 5. 边界

本件**只读复算**：未改判据/SPEC/生成器/板/pro/真源/图纸/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`/闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 判定器草案 `1cda68521d0e56be` · 闭环表 v1.4 `2de0dea4f5a5729d`
