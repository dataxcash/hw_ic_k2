# K2 · P4 · 「铜到板边」在内层盲孔上的口径缺口（实测）· v1 · 2026-09-17

> 性质：ENG 只读取证 + 判定性探针。**未改板 / SPEC / 判据 / 真源**。判定权归监理。
> 结论一句话：**JLC 能力合规（≥0.2，实测最小 0.256）⇒ 不阻断交付**；但**板规 0.30 在「内层盲孔铜环」上未被强制**（kicad-cli 对该类按**钻孔**判边距），属**口径登记项**，ENG **不建议**为此加齿或改板。

## 1. 应然值（三处）

| 出处 | 值 | 备注 |
|---|---|---|
| JLC 能力（`L2/L2_DFM_DETERMINATION_vs_JLC_HDI_v1.md` 第 13 项「铜到板边」） | **≥ 0.2 mm** | 该项判 **PASS** |
| 板规（`k2/hw/k2_v4_8L.l5.kicad_pro → rules.min_copper_edge_clearance`，severity = `error`） | **0.30 mm** | 与 `drc_rules.json` 一致 |
| 冻结 `drc_rules.json → manufacturing.min_copper_edge_clearance` | **0.30 mm** | **自注**：「track_width/annular_width/**copper_edge_clearance 属 DRC 独立类型，M10 对齐以 clearance/hole_clearance 为主，本组先声明后深化**」 |

## 2. 全板实测（只读，板边 = `Edge.Cuts` 矩形 `x[23,143] y[33,79]`，四条 `gr_line`，无圆角）

| 对象 | 到板边最小（铜边缘） |
|---|---|
| 走线段 | **0.431 mm** |
| 焊盘（pad） | **0.350 mm**（`D2` @(36.7,34.6)/(40.7,34.6)） |
| 过孔（via） | **0.256 mm** ← 4 支，均为 **`In2.Cu–In5.Cu` 盲孔**：`(93.7,78.569)` · `(136.0,78.569)`（=0.256）· `(54.4,33.45)` · `(88.9,33.45)`（=0.275） |

⇒ 4 支盲孔**铜环**低于板规 0.30（但仍 **≥ JLC 能力 0.2**）。

## 3. 为何 DRC 零违规：三类对象三种度量（判定性探针，实测）

在 /tmp 变体上注入/改动后跑 `kicad-cli pcb drc`（T-8 口径：同名 pro + `fp-lib-table` + `lib/`）：

| 探针 | 注入 | kicad-cli 报的「实际」 | 推出的度量基准 |
|---|---|---|---|
| P1 | 走线 @y=78.8（铜边到边应 0.12） | 0.1200 | 段：按**铜边缘**判 ✓ |
| P2 | 通孔 via `size 0.35/drill 0.2` @y=78.55 | **0.2750** | 通孔：按 **pad 半径 0.175** 判 |
| P3 | 内层盲孔 `size 0.35/drill 0.2` @y=78.8 | **0.1000** | 盲孔：按 **钻孔半径 0.1** 判 |
| P4 | 把**现存**盲孔 `(93.7,78.569)` 的 `drill 0.2→0.3` | **0.2810**（=79−78.569−0.15） | 盲孔：确认按**钻孔半径**判 |

⇒ **kicad-cli 对「内层盲孔到板边」用钻孔半径度量**，故现存 4 支（钻孔边 0.331 / 0.350）**合规放行**，而其**铜环**（0.256 / 0.275）不受 0.30 约束。
⇒ 与冻结 `drc_rules.json` 的自注一致：`copper_edge_clearance` 属**「先声明后深化」**的类型。

## 4. 判定与建议（ENG）

1. **对 JLC 能力：PASS**（4 支盲孔铜环 0.256/0.275 ≥ 0.2；其余对象 0.350/0.431）⇒ **不构成交付阻断**，无需改板。
2. **口径缺口（登记项）**：DFM 第 13 项记「铜到板边 ≥0.2 / **板规 0.30** / 违规 = 0」——建议补一句实况：**「内层盲孔按钻孔判（kicad-cli 口径），其铜环实测最小 0.256mm；板规 0.30 未在内层盲孔铜环上强制」**。建议把该事实**登记入 manifest 备注**（本件未改 manifest 草案；若监理采纳，ENG 随后一并落并复跑正/负控）。
3. **ENG 不建议**：(a) 为「内层盲孔铜环 ≥0.30」**新增检查齿**（owner 常设政策②：禁新增检查齿；且 JLC 已 PASS）；(b) 为满足 0.30 而把这 4 支盲孔内移 —— 它们位于**南侧 In5 长距离走廊（T-32）**，位移会牵动 `PCIE_DN7_P/N` 等**对内等长（冻结判据 ≤0.15，现 max 0.0788）**与走廊占用 ⇒ 收益（0.30 → 0.05mm 富余）远低于风险。
4. 若监理**要求**全层满足 0.30 ⇒ 属 L2 自裁域，ENG 可按增量执行（内移 ≥0.05mm + 逐段 0/45/90 + 对内等长守恒复算 + 复跑 sha），但请以书面口径为凭。

## 5. 复跑命令（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 全板最小铜到板边（只读）
python3 - <<'PY'
import re
t = open('k2/hw/k2_v4_8L.l5.kicad_pcb', encoding='utf-8').read()
X0, X1, Y0, Y1 = 23.0, 143.0, 33.0, 79.0
d = lambda x, y: min(x - X0, X1 - x, y - Y0, Y1 - y)
worst = []
for m in re.finditer(r'\n\t\(via( blind)?\n', t):
    s = m.start() + 1; e = t.find('\n\t)\n', s); b = t[s:e + 4]
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b); sz = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', b)
    if not at: continue
    vx, vy = float(at.group(1)), float(at.group(2)); r = float(sz.group(1)) / 2 if sz else 0.175
    worst.append((d(vx, vy) - r, vx, vy, 'blind' if m.group(1) else 'through'))
for w in sorted(worst)[:4]: print('铜环到边 %.3fmm @(%s,%s) %s' % w)
PY
#   期望: 0.256 @(93.7,78.569) blind · 0.256 @(136.0,78.569) blind · 0.275 @(54.4,33.45) blind · 0.275 @(88.9,33.45) blind
# ② 度量基准探针（/tmp 变体；勿动仓库板）
#    走线 @y=78.8 → 0.1200 | 通孔via @y=78.55 → 0.2750 | 盲孔 @y=78.8 → 0.1000 | 现存盲孔 drill 0.2→0.3 → 0.2810
#    AppDir/bin/kicad-cli pcb drc --format json --severity-error --severity-warning --output /tmp/p.json <变体板>
```

—— ENG（ARCHER）· 2026-09-17 · 只读取证；本件不改任何件
