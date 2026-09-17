# K2 · P4 · `G-ROOT-1/2/3` **输入权威表**（放行后「一次可做、零返工」）· v1 · 2026-09-18

> 缘起：handoff inc54 §6-3-(a)「Z4 的 G-ROOT **输入权威表**：把 G9/G10/G-ROOT-3 所需输入逐项标注权威源与**陈旧读数**，
> 使放行后一次可做且不返工」。本会话**无监理放行** ⇒ 只做 ENlegal 面：**只读实测 + 本证据件**（仓库零载体改动；未新增判据/脚本）。
> 锚（sha16）：受审板 `6ff49da5678c2108` · 设计源板 `fb07d25ac426ff84` · 生成器 `d8d15a31061f450f` · SPEC rev-47 `9ba09cbc148d6836` ·
> L3 图纸 `21e8891ea3fc4c06` · 真源 `dd794c54f7ce7417` · errata-1 `17d540f058631a5e` · 库 `ForgeOS.pretty` 20 件。

## 0. 结论（四句）

1. **G9/G10/G-ROOT-3 的全部输入已逐项定位权威源并实测各载体现值**（表 A/B/C）。放行后**不需要新增任何 L1/owner 输入**（唯一例外＝表 C 的真源路径选择，属既有 §5-8 未决项）。
2. **权威分三类，决定「谁能一句话放行」**：
   - **A 类 · 权威＝既有独立裁定** ⇒ 刷新＝**版本化传播**，**不构成 C-1 自证**：`column_x=27.94`（L2-3 裁定 + #K2-21 §二 守恒闸）· `H3=(45.10,75.10)`（#K2-19 §一-3「H3 = L2 热机械 = 自裁域」）。
   - **B 类 · 板是唯一实载、无独立成文应然** ⇒ 须监理裁「**以板为准**」或另给应然：孔/逃逸 keepout 枚举与开关、In4 分区粒度、KO-7。**先例＝#K2-19 §二 W-8 已裁「以板为准」**（同类裁定，属监理自有权）。
   - **C 类 · 真源路径甲/乙**（`nets_yaml`）⇒ 本表**不裁**，绑定 handoff §5-8。
3. **新陈旧读数（本会话新测的第 4–6 例，全部佐证 Z4「L3 图纸族整体落后 P4 落板」）**：
   `p3_drawings.json` 自述 `spec = SPEC_k2_v4.spec-rev-25.json`（`74f31d08a8be2f17`）而 `project.yaml → rev-47`；
   `pour_zones.count=13 / filled_count=0`（＝l4 前填充口径，板为 10/10）；`criteria.C3` 记 `U1 footprint_pads=49`（板实测 **58**）。
4. **零返工警告（本表最高价值）**：G9 的「库为几何源」与板的**电气级基准**在 `J3/J4` 上**互斥**
   —— 库 pad 名 `1..38`，板 pad 名 `A1..A19/B1..B19`（U-03）⇒ **G9 放行后仍须先解 ⑦ 库/板名集**，否则 J3/J4 一实施即返工。见 §6 依赖序。

## 1. 方法与装置（只读、可复跑）

- 解析器：内联 KiCad s-expr tokenizer（§7），只读 `hw/k2_v4_8L.l5.kicad_pcb` / `.kicad_mod` / `.yaml` / `.json`；**不落盘、不改件**。
- 判读口径沿用 `#K2-21 §一`（`zone_filled` 只计**有网非 keepout**）与 `#K2-19 §二 W-8`（电气级必须 0 差、图形级容忍）。
- 未新增检查齿（owner ②）：本表**只登记**，不定义新阈值/新维度。

## 2. 表 A · `G9`（G-ROOT-1 去锚板依赖）输入权威表

| # | 输入 | 生成器现取 | **权威源** | 各载体现值（本会话实测） | 陈旧? | 放行后动作 |
|---|---|---|---|---|---|---|
| A1 | 排针 pad **数/号** | 锚板 `pads`（`k2_gen_v5.py:339-346`） | **真源** `k2_sch.yaml::symbols[].pins` | `HEADER_4PIN`={TX1,RX2,GND3,VCC4} · `HEADER_2PIN`={PWR_BTN#1,GND2} · `HEADER_2PIN_12V`={VIN_12V1,GND2} · `HEADER_4PIN_EC`={GND1,EC_SCL2,EC_SDA3,EC_3V3@4}（引脚号在真源内；`EC_3V3` 属 left 组 pin 4） · `HEADER_2PIN_AUX`={P3V3_AUX1,GND2} | 否 | 消费真源（每 ref 的 symbol 由 `sheets[].placements` 绑定） |
| A2 | 排针 pad **网名** | 锚板 `pads` | **真源** `nets` | J6/{PWR_CTRL_OUT,GND} · J9/{UART_TX,UART_RX,GND,MCU_VDD} · J11/{GND,I2C2_SCL,I2C2_SDA,P3V3_AUX} · J12/{12V_IN,GND} · J13/{SWDIO,SWCLK_BOOT0,GND,MCU_VDD}（板 16 pad 逐项一致） | 否 | 消费真源 |
| A3 | 排针 pad **几何** | 锚板 `pads` | **库** `ForgeOS.pretty/PinHeader_1x02|1x04.kicad_mod` | 库＝板一致：`thru_hole circle` 1.5×1.5 / drill 0.8 / local y ±1.27（2pin）、±1.27,±3.81（4pin）/ 局部距 2.54 | 否 | 经 `fp-lib-table`（`d731638859be9a08`）解析库 |
| A4 | 排针 **column_x** | 锚板 `at` | **L2-3 裁定 = 27.94**（+ #K2-21 §二 守恒闸） | **SPEC rev-47 = 26.5（8 处）**；图纸 = 27.94（25 处，含 `criteria.D1_pinheader_interference.column_x=27.94`）；板 fp at x=27.94（5/5 实测）；#K2-21 守恒闸 = 27.94 | **SPEC 陈旧** | bump `components.pin_headers.column_x` + `positions.*.x` → `27.94`；**同步 `check_pin_headers`(S8) 比对源**（现强制 26.5，会拒正确值） |
| A5 | 排针 **positions.y / rot** | 锚板 `at` | SPEC `positions`（与板一致） | y = J12 35.32 · J6 39.66 · J13 46.54 · J9 55.96 · J11 65.38；rot = 90 | 否 | 消费 SPEC；板 5 件逐值一致 |
| A6 | 排针 `pad_diameter` / `min_net_gap` | SPEC（`pad_diameter` 现**零消费** = U-07） | SPEC | 1.5 / 0.3（`layout_basis` 中心距 1.8 = 1.5+0.3） | 否 | 消费 SPEC（S1 依赖该值） |
| A7 | 其余件 pad 几何（含 `U1/U6/J2/J3/J4/E2`） | 锚板 `pads`（全板：`:332/:345-346`） | **库**（W-8）+ ⑦ 裁定 | **计数** 板=库：J2 **74**=74 ✓ · U6 **354**=354 ✓ · J3/J4 **38**=38 ✓ · 排针 16=16 ✓；**名集**：J3/J4 板 `A1..A19/B1..B19` vs 库 `1..38` ✗（U-03）；U1 板 **58** pad（图纸 C3 记 49）；E2 8=8 | **⑦ 待裁** | **先解 ⑦ 库/板名集**（库按板重建 + 重指 `lib_id`）再按库取几何，否则 U-03/M-09 返工 |

## 3. 表 B · `G10`（G-ROOT-2：NPTH / keepout / 铺铜产出）输入权威表

| # | 输入 | 生成器现取 | **权威源** | 各载体现值（本会话实测） | 陈旧? | 放行后动作 |
|---|---|---|---|---|---|---|
| B1 | 固定孔 **H1–H4 逐座标** | 生成器**无**产出 | **#K2-19 §一-3（L2 自裁）= 板值** | 板 4×NPTH Ø3.2：H1(26.10,75.60) · H2(139.60,39.60) · **H3(45.10,75.10)** · H4(114.60,36.10)；**图纸 H3=(26.1,36.1)＝裁决前值** | **图纸 H3 陈旧** | 图纸 `mounting_holes` 刷新至板值（引用 `K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` 的 L2 裁定，**非**引用板） |
| B2 | 孔参数 | 生成器**无** | 图纸（与板一致） | drill 3.2 · keepout Ø6.0 · 边料 ≥1.5；板实测 drill 3.2 · keepout bbox **6.00×6.00** | 否 | 消费 |
| B3 | **孔回避区**（全层） | 生成器**无** | **板（B 类）** | 板 4 个 `K2_HOLE_KEEPOUT_H1..H4`：全 8 层 · 6.00×6.00 · **精确居中 d=0.00** · tracks/vias/copperpour `not_allowed`、pads/footprints `allowed`；图纸 `KO-1..4`(Ø6.0,count=4) **五开关全 blocked** | **开关口径差** | 监理裁「以板为准」（W-8 式）后生成 4 区 |
| B4 | **逃逸回避区 `ESC_*`** | 生成器**无** | **板（B 类）** | 板 4 个 F.Cu、`copperpour not_allowed`：`ESC_U6`(82.10,49.11,105.34,58.29) · `ESC_J3`(53.45,42.40,65.55,46.60) · `ESC_J4`(53.45,60.60,65.55,64.80) · `ESC_J2`(131.50,42.23,136.15,65.17)；图纸 `KO-5`/`KO-6` **各 count=1（不 1:1）**，规则值在 `keepout_geometry.escape_zone`(0.075/0.4/no_90/no_via) | **枚举陈旧** | 裁口径后生成 4 区（每区 ≥1 非 allowed） |
| B5 | **有网铜区** | 生成器**无** | **板（B 类）** | 板 **10/10 全填充**：`In1/In3/In6=GND` + `In4`{`12V_IN`×2,`P3V3_AUX`×2,`P3V3`×2,`MCU_VDD`×1}；图纸 `pour.gnd_planes`/`power_plane=In4` 一致，但 `power_partition` 仅 2 区；**图纸 `pour_zones.count=13 / filled_count=0`** | **图侧 13/0 陈旧** | 裁分区粒度后生成 10 区 + 出图前 `ZONE_FILLER` 强制填充 |
| B6 | **KO-7 板边** | 生成器**无** | 图纸 `keepout_geometry`（板无边 zone） | 图纸 `KO-7`(count=4, `edge_copper_min=0.3`) + `edge_inset_rect_mm=[23.3,33.3,142.7,78.7]`；板**无独立 KO-7 实体 zone**（由 `edge_copper_min` 规则承载） | 口径差 | 裁是否补实体 zone（若不补须登记理由） |

## 4. 表 C · `G-ROOT-3`（真源路径硬编码）输入权威表

| # | 输入 | 生成器现取 | **权威源** | 各载体现值（实测） | 陈旧? | 放行后动作 |
|---|---|---|---|---|---|---|
| C1 | 真源网表路径 `nets_yaml` | 硬编码 `ROOT/boards/k2_sch.yaml` + **symlink 兜底**（`:39`） | **配置** `project_config()["nets_yaml"]` | config = `hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）；**图纸自述 `nets_yaml` = 同一份 errata-1（一致）**；生成器经 symlink 实读 `hw/data/k2_sch.yaml`（`dd794c54f7ce7417`） | **生成器与配置/图纸不一致** | 加模块级访问器 + `YAML_PATH = ROOT/_PMCFG.project_config()["nets_yaml"]`（约 3 行，`/tmp` 已端到端验证）；**但须先裁 §5-8 甲/乙**（G11 后生成器即读 errata-1，而 errata-1 ⇒ `netlist_connect` FAIL 106） |
| C2 | 锚板路径 `PCB_REF_PATH` | 硬编码 `ROOT/k2_v4.kicad_pcb` + symlink | **随 G9**（去锚板依赖） | symlink → `hw/k2_v4_8L.kicad_pcb`（`fb07d25ac426ff84`） | 待 G9 | 随 G9 一并删 symlink（E4 判据：`K2_OUT_PCB` 连跑两次 sha 相同） |

## 5. 须监理「一句话」的冲突清单（按类；ENG 不择一）

| # | 类 | 冲突 | 请裁内容 | 触 L1/owner? |
|---|---|---|---|---|
| 5-1 | **A** | SPEC `column_x=26.5` ↔ 权威 `27.94`（S8 自检反强制陈旧值） | 放行 SPEC/图纸族**版本化刷新**（A4/A5） | 否（既有 L2-3 裁定之传播） |
| 5-2 | **A** | 图纸 `H3=(26.1,36.1)` ↔ 板 `(45.10,75.10)` | 放行图纸 `mounting_holes` 刷新（B1） | 否（#K2-19 §一-3 = L2 自裁） |
| 5-3 | **B** | keepout 枚举/层集/开关（板 8 个 vs 图纸 KO-1..7、`pads` 开关 opposite）· In4 分区粒度（板 7 区 vs 图纸 2 区）· KO-7 实体 zone 有无 | 裁「**以板为准**」（W-8 式）或另给应然 | 否（若判属接口/拓扑则升级） |
| 5-4 | **C** | `nets_yaml` 甲（errata-2）/ 乙（errata-1 + D-7a） | 裁路径（handoff §5-8） | 否（属监理/gate） |
| 5-5 | **⑦** | `J3/J4` 库 pad 名 `1..38` ↔ 板 `A1..A19/B1..B19`（同 U-03） | 放行「库按板重建 + 重指 `lib_id`」 | 否（ENG 侧 7 件登记项） |

**C-1 判读（供监理参考；ENG 只陈述）**：C-1（`truth_binding.py::SelfSourceError`）禁「把**被验对象**当判据真源」。
本表建议对 B 类采 **「写入输入层 + 登记来源」**：把板实测值写进 **SPEC/图纸（输入层）**，并在件内具名登记「来源＝受审板实测 + 监理「以板为准」裁定」，
判据仍比对 **输入层**（生成器消费输入层），从而避免判据直接消费产物。**此判读之采纳权归监理。**

## 6. 放行后执行映射（依赖序；每步唯一输入源 ⇒ 零返工）

```
Step 0  裁 §5（5-1..5-5）
Step 1  A 类版本 bump：SPEC → rev-48（column_x/positions=27.94；不动其它）+ L3 图纸 rev（H3=板值）
Step 2  解 ⑦：库 J3/J4 按板名集重建 + 重指 lib_id（否则 Step 4 返工）   ← 本表新增的硬依赖
Step 3  G11：访问器 + YAML_PATH 配置驱动 + 删 2 个 symlink（随 5-4 裁定）
Step 4  G9：pad 几何改为 真源(symbols/nets) + 库(fp-lib-table) 消费；全 ref fail-closed（禁静默回退）；
             S8 比对源改权威 27.94；验收 = 板逐 pad（数/名/尺寸/旋转/位置，W-8 电气级 0 差）
Step 5  G10：NPTH 4（板值）+ keepout 8（4 全层 + 4 F.Cu）+ zone 10（有网）+ 强制 ZONE_FILLER
Step 6  同轮复算：DRC + 判据（V2/E4/J-3/J-8/drill_count 复用，不新增齿）+ 守恒（tracks/vias/zones/nets/pads）
        → 落件后以落件板 sha 重跑五件测量（测量板 sha16 必须 == 受审板）→ verdict 入 ledger
```
**不可跳过 Step 2**：跳过 ⇒ G9 对 J3/J4 产出 `1..38` 名集，与板基准冲突，实施即返工（U-03/M-09 重开）。

## 7. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 本件全部实测的内联解析（板 pad/zones/keepout + 库 + 真源 + 图纸 + 配置）见本件 §2/§3/§4 逐格；
#    核心三查：
python3 - <<'PY'
import json
d=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json'))
print("drawings spec self-ref:",d['spec']," nets_yaml:",d['nets_yaml'])
print("pour_zones:",d['pour_zones']['count'],"/",d['pour_zones']['filled_count'])
print("H3 drawing:",d['mounting_holes']['positions']['H3']," col_x(SPEC):",
      json.load(open('k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json'))['components']['pin_headers']['column_x'])
PY
# ② 配置 vs 生成器（G11 输入）
grep -n 'nets_yaml\|spec_name' k2/pm_gate/project.yaml
grep -n 'YAML_PATH' k2/tools/k2_gen_v5.py
ls -la k2/boards/k2_sch.yaml k2/k2_v4.kicad_pcb
# ③ 库 vs 板 pad 名集（零返工依赖；按 footprint 分段，避免全板混淆）
python3 - <<'PY'
import re,pathlib
lib=sorted(set(re.findall(r'\(pad "([^"]*)"',pathlib.Path('k2/hw/lib/ForgeOS.pretty/MCIO_4i_SFF-1016_RASide.kicad_mod').read_text(encoding='utf-8'))))
tok=re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
def parse(t):
    ts=tok.findall(t);pos=0
    def rd():
        nonlocal pos
        x=ts[pos];pos+=1
        if x=='(':
            o=[]
            while ts[pos]!=')': o.append(rd())
            pos+=1;return o
        return x[1:-1] if x.startswith('"') else x
    return rd()
root=parse(pathlib.Path('k2/hw/k2_v4_8L.l5.kicad_pcb').read_text(encoding='utf-8'))
kids=lambda n,k:[c for c in n if isinstance(c,list) and c and c[0]==k]
for f in kids(root,'footprint'):
    ref=None
    for x in kids(f,'fp_text'):
        if len(x)>2 and x[1]=='reference': ref=x[2]
    for x in kids(f,'property'):
        if len(x)>2 and x[1]=='Reference': ref=x[2]
    if ref in ('J3','J4'):
        nm=sorted({p[1] for p in kids(f,'pad')})
        print(ref,'n=',len(nm),'board_names[:4]=',nm[:4],' lib_names[:4]=',lib[:4],' EQUAL=',nm==lib)
PY
```
> 板侧按 footprint 分段解析见本件 §2 的 tokenizer 配方（`kids(f,'pad')`），一次读入、零落盘。

## 8. 边界

本件**只读 + 新增 1 份证据件**：未改板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/SPEC/图纸/真源/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc55`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 生成器 `d8d15a31061f450f` · SPEC rev-47 `9ba09cbc148d6836` · 图纸 `21e8891ea3fc4c06`
