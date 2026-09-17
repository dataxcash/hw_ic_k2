# K2 · P4 · `G10` **固定孔逐座标候选表 + keepout/铺铜台账 + 生成段草案**（含第三例「图纸陈旧」）· v1 · 2026-09-18

> 缘起：handoff inc52 §6-3-(a)「G10 半边：固定孔逐座标候选表 + keepout/zone 生成段草案」。
> 本会话仍**无监理放行** ⇒ ENlegal 面。仪器：`kicad-cli`/自解析 只读读 `k2/hw/k2_v4_8L.l5.kicad_pcb`（受审板）+ L3 图纸族 + L2 冻结件。**仓库零写入。**

## 0. 结论

1. **①孔位「从 L3 图纸取」不可按原文实施**：图纸 `mounting_holes` 与 SVG 均记 **H3=(26.1,36.1)**，而**已裁决且已落板**的 H3=**(45.1,75.1)**（`k2/docs/K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md`：「按裁**重解孔位** H3 (26.1,36.1)→(45.1,75.1)，位移 43.38mm；H1/H2/H4 不动」）。
   **该裁决的域归属已在册**：`#K2-19 §一-3` = 「**H3 = L2 热机械 = 自裁域**（owner #14）」，并附几何证明「H3 无解于左缘（x 带被 5 排针列占满，Ø6.0 净空在任何 6.0mm 空窗中均不可得）」⇒ **孔位值本身不是待裁项**（L2 已自裁）；本件所求仅为**载体刷新放行**（见 §1 末）。**本件独立复算**：图纸值对最近排针 pad（`J12.1 @(26.67,35.32)`）中心距 **0.966mm** ⇒ 对孔壁净距 **−1.384mm**、对 6.0mm keepout 净距 **−2.784mm**（**重叠**）；板值最近 pad 距 **16.514mm**（净距 +14.164mm）。⇒ 图纸 H3 是**裁决前**值。
2. **②keepout 台账**：板权威 8 个 = **4 个固定孔回避区**（全层、bbox 6.00×6.00 **精确居中于 H1–H4**，d=0.00mm ⇒ 即图纸 KO-1..4）+ **4 个 F.Cu 铺铜回避区**（U6 pad 区 / MCIO J3 区 / MCIO J4 区 / SlimSAS J2 区）。后者与图纸 `keepouts` 的 **KO-5（count=1）· KO-6（count=1）不 1:1** ⇒ 图纸 keepout 枚举亦陈旧。
3. **③有网铜区**（板权威 **10** 个，**10/10 全填充**）：`In1/In3/In6 = GND`（3 平面）+ `In4` **7 区**：`12V_IN ×2 · P3V3_AUX ×2 · P3V3 ×2 · MCU_VDD ×1`。
4. **元结论（本会话第三例同型）**：**L3 图纸/SPEC 族相对 P4 落板普遍陈旧** ——
   ① `SPEC.components.pin_headers.column_x = 26.5`（权威 `27.94`，inc48）；② 图纸 H3 为裁决前值（本件 §1）；③ 图纸 keepout 枚举与板不 1:1（本件 §2）。
   ⇒ **G9/G10 的共同前置不是「放行改生成器」，而是「先定权威源」**：或**刷新 L3 图纸族/SPEC 至 P4 后真值**（版本 bump），或**明示以受审板为准**（并说明这不构成「用被验对象当判据真源」的 C-1 例外，因生成器消费的是**冻结输入**而非产物——此点**须监理裁**）。**只放行改生成器不足以闭 G-ROOT。**

## 1. 固定孔候选表（板权威；请监理逐座标确认）

板实测（`np_thru_hole`，Ø3.2 drill，footprint `MountingHole_3.2mm_M3`）：

| ref | 板实测 (x,y) | 图纸记载 | 差异 | 最近排针 pad 中心距 | 孔壁净距 | 结论 |
|---|---|---|---|---|---|---|
| `H1` | (26.10, 75.60) | (26.1, 75.6) | 一致 | — | — | ✅ |
| `H2` | (139.60, 39.60) | (139.6, 39.6) | 一致 | — | — | ✅ |
| **`H3`** | **(45.10, 75.10)** | **(26.1, 36.1)** | **位移 43.38mm** | 图纸值 **0.966mm** / 板值 16.514mm | 图纸值 **−1.384mm（重叠）** / 板值 +14.164mm | ⚠️ **图纸陈旧**；板值已有裁决支撑 |
| `H4` | (114.60, 36.10) | (114.6, 36.1) | 一致 | — | — | ✅ |

- 其它权威参数（图纸 `mounting_holes`）：`count=4` · `drill_mm=3.2` · `keepout_dia_mm=6.0` · `edge_material_min_mm=1.5`；板实测 drill=3.2、keepout bbox 6.00×6.00 ⇒ **一致**。
- 图纸注记（仍有效）：`"右下角不可放孔（In5 PCIe 布线占用 y≥74.5 ∧ x≥86）⇒ 右侧不对称（审计 §10.2 诚实披露）"`。
- **请监理裁（仅载体刷新，非重裁座标）**：(a) 确认 H3 以**板值 (45.1,75.1)** 为准（= 复述 `#K2-19 §一-3` + `K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` 的已裁结论，ENG **未**主张新裁决）；
  (b) **放行图纸/SPEC 族的刷新方式**（新 L3 rev，或在 `mounting_holes` 加「H3 已由 L2-3 重解，以板为准」的具名注记），使 G10 生成器的孔位来源**不再是裁决前值**。**此二项均属放行范围（§11），ENG 不擅改图纸/SPEC。**

## 2. keepout 台账（板权威 8 个）

| # | 层集 | bbox (x0,y0,x1,y1) | 尺寸 | 开关 | 判定 |
|---|---|---|---|---|---|
| 5–8（4 个） | **全层** F.Cu…In6.Cu | 各 **6.00×6.00**，中心 = H1/H2/H3/H4（d=**0.00mm**） | 6.00×6.00 | tracks/vias/`copperpour` **not_allowed**；pads/footprints allowed | **固定孔回避区 = 图纸 KO-1..4**（Ø6.0 ✓） |
| 1 | F.Cu | (82.10, 49.11, 105.34, 58.29) | 23.24×9.18 | `copperpour` not_allowed；tracks/vias/pads allowed | `U6` ReDriver pad 区（对齐 `keepout_geometry.u6_pads_bbox_mm=[82.6,49.61,104.84,57.79]`） |
| 2 | F.Cu | (53.45, 42.40, 65.55, 46.60) | 12.10×4.20 | 同上 | MCIO `J3` 区 |
| 3 | F.Cu | (53.45, 60.60, 65.55, 64.80) | 12.10×4.20 | 同上 | MCIO `J4` 区 |
| 4 | F.Cu | (131.50, 42.23, 136.15, 65.17) | 4.65×22.95 | 同上 | SlimSAS `J2` 区 |

**与图纸的差异（须监理裁）**：图纸 `keepouts` 列 `KO-5 escape_transition_zone (count=1)` · `KO-6 ac_pad_gnd_cutout (count=1)` · `KO-7 board edge (count=4)`；板侧 F.Cu 铺铜回避区为 **4 个**且**不对应** KO-5/KO-6 的单件计数，**亦未见 KO-7 独立的边带回避 zone**（边铜约束改由 `edge_copper_min=0.3` 规则承载）。
⇒ 板为准还是图纸为准 + 是否需补 KO-7 实体 zone，**请监理裁**。

## 3. 有网铜区台账（板权威 10 个，全填充）

| 层 | 网 | 数量 | 备注 |
|---|---|---|---|
| `In1.Cu` | `GND` | 1 | 图纸 `pour.gnd_planes` 一致 |
| `In3.Cu` | `GND` | 1 | 一致 |
| `In6.Cu` | `GND` | 1 | 一致 |
| `In4.Cu` | `12V_IN` | **2** | 图纸 `pour.power_plane=In4` 一致；分区粒度**细于**图纸 `power_partition`（图纸只列 P3V3 / P3V3_AUX+MCU_VDD 两区） |
| `In4.Cu` | `P3V3_AUX` | **2** | 同上 |
| `In4.Cu` | `P3V3` | **2** | 同上 |
| `In4.Cu` | `MCU_VDD` | **1** | 同上 |
| 合计 | | **10**（filled **10/10**） | 与 #K2-21 §二 ⑥ 中的「`zone_filled` 有网非 keepout 铜区 10/10」一致 |

## 4. G10 生成段草案要点（**不新增检查齿**；收敛判据沿用已裁维度）

- **① NPTH pad 生成**：按 §1 确认后的 4 组座标生成 `np_thru_hole circle` Ø3.2（`drill=3.2`，`layers *.Cu *.Mask`），并在每处生成 §2 的 6.0mm 全层回避区。
  **禁**：从锚板/产物读孔位（同 G-ROOT-1 循环依赖）；**禁**擅移孔位（孔位属机械接口座标）。
  前置机检（复用）：`drill_count: npth >= 4`（冻结 manifest 已列）。
- **② keepout zone 生成**：按 §2 的层集/开关/bbox 生成；`ESC_*` 类须**至少 1 个开关 `not_allowed`**。
  前置机检（复用）：`keepout_active`（草案已实现）。
- **③ 有网铜区生成 + 强制填充**：按 §3 生成 10 区（`In1/In3/In6=GND`，`In4` 4 网 7 区），出图前**强制 `ZONE_FILLER` 填充**。
  前置机检（复用）：`zone_filled`（注意分母口径 = **有网非 keepout**，见 #K2-21 §一-1）。
- **口径边界（重要）**：本件**未**提出任何新判据/新阈值；`npth>=4`/`zone_filled`/`keepout_active` 均为**已裁维度**。若 G10 实施需要新的「孔位逐座标一致性」判据，**须先经监理**（owner ② 禁新增检查齿）。

## 5. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 板侧 4 孔 + 16 排针 pad（权威落地值）
python3 - <<'PY'
import re,pathlib
tok=re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
def parse(t):
    ts=tok.findall(t); pos=0
    def rd():
        nonlocal pos
        x=ts[pos]; pos+=1
        if x=='(':
            out=[]
            while ts[pos]!=')': out.append(rd())
            pos+=1; return out
        return x[1:-1] if x.startswith('"') else x
    return rd()
def kids(n,k): return [c for c in n if isinstance(c,list) and c and c[0]==k]
root=parse(pathlib.Path('k2/hw/k2_v4_8L.l5.kicad_pcb').read_text(encoding='utf-8'))
for fp in kids(root,'footprint'):
    for pad in kids(fp,'pad'):
        if len(pad)>2 and pad[2]=='np_thru_hole':
            print(' NPTH', fp[1], kids(fp,'at')[0][1:3], kids(pad,'size')[0][1:3], 'drill=', kids(pad,'drill')[0][1])
PY
# ② 图纸孔位（期望 H3 为裁决前值）
python3 -c "import json;print(json.load(open('k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json'))['mounting_holes'])"
grep -oE 'H[1-4] \([0-9.]+, ?[0-9.]+\)' k2/pm_gate/artifacts/k2_v4/L3/drawings/01_board_frame_and_holes.svg
# ③ H3 裁决依据
grep -n 'H3' k2/docs/K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md | head -4
# ④ 板侧 keepout/铜区结构（8 keepout + 10 有网，含层集/开关/bbox）
#    见本件 §2 §3 的内联解析；keepout bbox 中心与 H1..H4 距离 = 0.00mm
```

## 6. 边界

本件**只读**：未改板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/SPEC/图纸/真源/`criteria/**`/`_shared/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 图纸 `p3_drawings.json` / `01_board_frame_and_holes.svg`
