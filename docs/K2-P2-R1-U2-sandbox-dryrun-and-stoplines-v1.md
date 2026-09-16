# R1 路径 (ii) · U2 沙箱干跑证据 + 停机项（**须监理裁 2 项 + 观察 1 项**）v1

- **依据**：#K2-12 §三（(ii) 可行性论证后**监理批后实施**；未批前**禁止改图**）、§五（停机条款）、handoff §7。
- **性质**：**沙箱证据，未安装**。driver 草案仅存 `/tmp/opencode`；**未写** `hw/sch`、未动生成器/SPEC/图/板/`criteria/`、未派 WORKER。
- **结论（一句话）**：薄 driver **能跑通**，且**全 5 sheet + root 可产出**、C1 确定性成立、网表 101 网中 **100 网逐名一致**；但真源自带 **2 项缺口**（纸张/表征、GND 驱动）**须监理一句话裁定**后才能真正安装。

## 1. 沙箱结论（全 5 sheet；驱动 = `K2_PAPER_OVERRIDE="ReDriver DS320PR1601 & Sideband Strap=A0"`）

| 判据 | 结果 | 说明 |
|---|---|---|
| **C1 确定性** | ✅ **PASS** | 两次独立连跑：5 件 `.kicad_sch` + root + `IOCONVERT.kicad_sym` **逐字节相同**（sha16 见 §6）；`sandbox_report.json` 仅 `out` 路径字段不同 |
| **C2 网表等同** | ⚠ **100/101** | 55 件全生成、101 网。**网名一致 100/101**；分区等价（剔除 `unconnected-`）**仅 1 项差异** = `PWR_5V_KEY`（见 §4）；NC 口径 yaml 104 vs netlist `unconnected` 105，差项**同**为 `C89/A` |
| **C3 ERC** | ⚠ **1 error / 522 warning** | 现行（未改）图基线 = **0 error / 421 warning** ⇒ 差异需逐条归因：**1 条真 error** = §3；452 `endpoint_off_grid`、55 `lib_symbol_issues`、15 `footprint_link_issues` 均为**同型/环境**（§5）；`isolated_pin_label` 在 4/5 sheet 时 64 条、**全 5 sheet 后 0 条**（已证为部分构建假象） |
| **C4 结构** | ✅ **PASS** | 括号平衡差 0；每 sheet 实例数 == yaml placements（3/10/21/12/9 = 55）；root 5 sheet、page 2–6 |
| model ERC / crosspage | ✅ 0 / 0 | `schlib.validate.erc` + `crosspage`（全 55 件、101 网） |

## 2. 停机项 **S2**（须监理裁）：ReDriver sheet 的**纸张 vs 符号几何**冲突

- **事实**：真源 `k2_sch.yaml` 该 sheet `paper = A2`；而 `U6 = DS320PR1601` 符号 = **单符号 R=136 / L=218 脚**（2.54mm 栅格）
  ⇒ `pin_extent = 551.18mm`、`total_height = 556.26mm`、`half_height = 281.43mm`。`Page` 边界（margin 15mm）实测：

  | 纸张 | 尺寸 | 结果 |
  |---|---|---|
  | A2（真源声明） | 594×420 | ❌ 需 y∈[296.4, 123.6] = **空集** |
  | A1 | 841×594 | ❌ 实测 bbox y 上界 579.1 > 579.0（**仅差 0.1mm**，且符号占满整页，其余 9 件无处放） |
  | **A0** | 1189×841 | ✅ 可行 |

- **非新问题之源**：现行 v5 图用**旧符号** `REDR_DS160PR810`（手维库中已作废），其实测下行 sheet 在 A2 内（y∈[-44.5, 231.1]）；冲突是 **8L 单颗全 354 球表征**新引入。
- **选项**（三选一）：
  - **(a) ★建议：真源该 sheet `paper: A2 → A0`**（1 字段；**实测**：全 5 sheet + root 生成成功、C1 成立）。属"图纸表征"级改动。
  - **(b) 把 `DS320PR1601` 拆 unit / 多页表征** —— 需**新工具**（`SymbolShape` 无 unit 概念）+ 跨页归属策略；若牵动**球↔脚表征**，按 owner 指令 #14 属 **L1（球重映射）⇒ 须 owner**。
  - **(c) 允许越界绘制**（KiCad 容忍，但图纸不可用）—— **不推荐**。
- **停机声明**：本项裁定前，driver 不安装、不改真源。

## 3. 停机项 **S3**（须监理裁）：GND 网**无 POWER_OUT 驱动** ⇒ 唯一 ERC error

- **报告原文**：`[power_pin_not_driven] ; error @ U6 引脚 AC4 [电源输入]`（Sheet `/ReDriver DS320PR1601 & Sideband Strap/`），全图**仅此 1 条 error**。
- **根因（精确计数）**：`U6 = DS320PR1601` 共 **354 脚**，其中 **152 脚 `power_in` 且全部挂在 GND**；真源 **GND 网共 211 节点 = `power_in` 152（全 U6）+ `passive` 54 + `input` 5 ⇒ 网内无任何 `power_out`** ⇒ KiCad 判「电源输入无驱动」（报代表脚 `AC4`）。现行图 **0 error** 说明旧符号把地脚记为 `passive`。
- **选项**：
  - **(a) driver 侧加电源旗标**（GND/电源网 `PWR_FLAG`）—— 即**变更现行 P5 策略**（沿用 v5 = 零电源旗标），须备案；
  - **(b) 真源侧把 U6 地脚类型 `power_in → passive`**（或指定某脚 `power_out`）—— 改真源 yaml；
  - **(c) 其它**（如仅对 GND 加旗标、或接受该 error 并登记豁免）。

## 4. 观察项 **O1**：`PWR_5V_KEY` 是**单节点网**（不进网表网名）

- 真源 `PWR_5V_KEY = {C89/A}` **仅 1 脚**；路由按既定策略（"单脚本地网 ⇒ `no_connect`"，共享库 `wirerouter` 内注释所载，为规避 `isolated_pin_label`/`pin_not_connected`）⇒ 网表出现 `unconnected-(C89-A-Pad1)`，**网名丢失**。
- 这是 101 网中**唯一**的 C2 差异项，且与 NC 口径差异为同一脚。**须确认**：真源**漏了一个节点**，还是有意留 1 脚占位（后者则网名不可保留，需登记）。

## 5. ERC 差异归因（证明**非 driver 回归**）

| 类型 | 生成件（全 5 sheet） | 现行图基线 | 判定 |
|---|---|---|---|
| `endpoint_off_grid` | 452 | 304 | 同型。根因 = 真源符号 `body_width` 多处非 1.27 倍数（19.8 / 23.3 / 32.7…）+ 354 脚符号；**pin tip 天然 off-grid**，wire 与 pin tip 坐标精确重合 ⇒ 连接不受影响 |
| `lib_symbol_issues` | 55 | 103 | **环境**：沙箱未注册 `IOCONVERT` 到 sym-lib-table（现行仓靠全局注册） |
| `footprint_link_issues` | 15 | 14 | **环境**：沙箱无 fp-lib-table |
| `isolated_pin_label` | **0** | 0 | 4/5 sheet 时的 64 条已证为"另一端在未生成 sheet"的**部分构建假象**，全量构建后归零 |
| `power_pin_not_driven` | **1** | 0 | **真 error**，见 §3 |

## 6. 复现（沙箱，只写 `/tmp/opencode`）

```bash
cd /home/fila/jqdDev_2025/ic_hw
export K2_SHEETS=...            # 可选：sheet 子集
export K2_PAPER_OVERRIDE="ReDriver DS320PR1601 & Sideband Strap=A0"   # S2(a) 沙箱试验
K2_OUT_SCH=/tmp/opencode/full_a AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/k2_sch_gen_v1.draft.py
AppDir/bin/kicad-cli sch export netlist --format kicadsexpr -o /tmp/opencode/full_a/board.net /tmp/opencode/full_a/k2_sch.kicad_sch
AppDir/bin/kicad-cli sch erc --severity-all -o /tmp/opencode/erc_full.rpt /tmp/opencode/full_a/k2_sch.kicad_sch
K2_ALL=1 K2_SCHDIR=/tmp/opencode/full_a AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/u2_c2_refined.draft.py
```

- 沙箱产物 sha16：`connectors 58b53dbe51e95be9` · `redriver…strap 1825b3f0ad655c9d` · `mcu_sideband cdf94bc84d068838` · `power_decoupling… a3eadcd0f4d30329` · `power_12v… cb3c2134de77cfd6` · `root a7cbb7a7aa54d4c3` · `IOCONVERT.kicad_sym 84ffb7de31fbcd82` · `board.net 77ead4c536b9a4e3` · `erc_full.rpt b044ef436b6f6a46`（基线 `erc_legacy.rpt 095417395227d024`）
- driver 草案：`/tmp/opencode/k2p1/k2_sch_gen_v1.draft.py` sha16 **`9aa52762444851b8`**（217 行）—— **全文附于 §7**，防 `/tmp` 丢失。

## 7. 附：driver 草案全文（`k2_sch_gen_v1.draft.py`，sha16 `9aa52762444851b8`）

```python
#!/usr/bin/env python3
"""k2_sch_gen_v1 (DRAFT, 沙箱) — 路径(ii)「由真源再生」薄 driver 草案。

真源: k2/hw/data/k2_sch.yaml  →  原理图套件（每 sheet 一件 .kicad_sch + IOCONVERT.kicad_sym + root）
输出: 仅 K2_OUT_SCH（默认 /tmp/opencode/sch_v1）；**绝不写 hw/sch**。

显式策略（禁隐式默认；须报监理备案）:
  P1 纸张      = 真源 sheets[].paper（A4/A3/A2/A1/A0）
  P2 布局      = 列数自适应（网格 NxM 竖向堆叠；越界即增列），列内 gap 8mm，网格 2.54mm
  P3 标签列    = 每列 col_x ± min(60mm, spacing/2-5mm)
  P4 NC 标记   = comp.nc_pins（真源显式）+ 路由 isolated_pins；两者须一致（不一致即 fail-fast）
  P5 电源旗标  = 无（沿用 v5 现行件：power:GND 计 0）；GND/电源网按普通网路由（global_label）
  P6 label shape = 由 net 上驱动脚的 Electrical 决定（output>input>bidirectional）
  P7 文件名    = slug(sheet.title) + ".kicad_sch"（旧 v5_* 名不承；sheet 分区已由真源给）
  P8 root 元数据(title/paper/uuid) 真源未含 ⇒ 取自已存 k2/hw/sch/k2_sch.kicad_sch（只读）
"""
from __future__ import annotations
import hashlib, json, math, os, re, sys

ROOT = "/home/fila/jqdDev_2025/ic_hw"
sys.path.insert(0, os.path.join(ROOT, "_shared"))

from schlib.loader.yamlloader import load_board_spec
from schlib.kernel.net import NetKind
from schlib.kernel.pin import Electrical
from schlib.layout.page import Page
from schlib.layout.wirerouter import WireRouter
from schlib.renderer.kicad import KiCadRenderer, _uuid4

YAML = os.environ.get("K2_SCH_YAML", os.path.join(ROOT, "k2/hw/data/k2_sch.yaml"))
OUT = os.environ.get("K2_OUT_SCH", "/tmp/opencode/sch_v1")
EXISTING_ROOT = os.path.join(ROOT, "k2/hw/sch/k2_sch.kicad_sch")
PAPER = {"A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0),
         "A1": (841.0, 594.0), "A0": (1189.0, 841.0)}
GAP = 8.0
LABEL_OFF_MAX = 60.0


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def net_shapes(nets, comps) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, net in nets.items():
        elec = set()
        for ref, pin_name in net.pins:
            c = comps.get(ref)
            if c is None:
                continue
            for p in list(c.symbol.right_pins) + list(c.symbol.left_pins):
                if p.name == pin_name:
                    elec.add(p.electrical)
                    break
        if Electrical.OUTPUT in elec or Electrical.POWER_OUT in elec:
            out[name] = "output"
        elif Electrical.INPUT in elec or Electrical.POWER_IN in elec:
            out[name] = "input"
        else:
            out[name] = "bidirectional"
    return out


def layout(w: float, h: float, comps: list):
    """P2: 列数自适应布局；返回 (page, col_xs, spacing)。"""
    n = len(comps)
    for ncols in range(1, n + 1):
        page = Page(w, h)
        spacing = (w - 2 * page.margin) / ncols
        col_xs = [page.snap(page.margin + (i + 0.5) * spacing) for i in range(ncols)]
        try:
            for i, c in enumerate(comps):
                page.place_auto(c, "VERTICAL", column=i % ncols,
                                col_x=col_xs[i % ncols], gap=GAP)
            return page, col_xs, spacing
        except RuntimeError:
            continue
    raise RuntimeError(
        f"布局失败：{n} 件在 {w}x{h}mm 上任何列数均越界/碰撞"
    )


def pin_name_set_not_netted(comp) -> set[str]:
    return {p.name for p in list(comp.symbol.right_pins) + list(comp.symbol.left_pins)
            if p.name not in comp.nets}


def nc_points(page, comp, pl) -> list[tuple[float, float]]:
    """P4: 显式 NC 脚的 pin tip 坐标（逐 occurrence）。"""
    pts = []
    nc = set(comp.nc_pins)
    for side in ("R", "L"):
        pins = comp.symbol.right_pins if side == "R" else comp.symbol.left_pins
        for i, p in enumerate(pins):
            if p.name in nc:
                pts.append((pl.x + comp.symbol.pin_tip_x(side),
                            pl.y - comp.symbol.pin_y(side, i)))
    return pts


PAPER_OVERRIDE = dict(
    kv.split("=", 1) for kv in os.environ.get("K2_PAPER_OVERRIDE", "").split(";") if kv)


def build_sheet(sheet, comps, nets, nshapes, out_dir, report):
    title = sheet["title"]
    paper = PAPER_OVERRIDE.get(title, sheet["paper"])
    w, h = PAPER[paper]
    pls = [comps[p["ref"]] for p in sheet["placements"]]
    fname = slug(title) + ".kicad_sch"

    # P4 fail-fast: 真源 nc 显式表 vs 内核「未归网」派生集，必须一致
    for pl_d, c in zip(sheet["placements"], pls):
        yaml_nc = set(pl_d.get("nc") or [])
        kern_nc = set(c.nc_pins)
        derived = pin_name_set_not_netted(c)
        if yaml_nc != kern_nc or kern_nc != derived:
            raise ValueError(
                f"[NC 口径不一致] {c.reference}: yaml={sorted(yaml_nc)} "
                f"kernel={sorted(kern_nc)} derived={sorted(derived)}")

    page, col_xs, spacing = layout(w, h, pls)
    # P3: 标签列偏移必须落在 1.27mm 连接网格上（否则导线端点 off-grid → ERC
    # endpoint_off_grid；实测：col_x(2.54 网格) - 60mm 不在 1.27 网格上）
    off = math.floor(min(LABEL_OFF_MAX, spacing / 2.0 - 5.0) / 1.27) * 1.27
    if off < 2.54:
        raise ValueError(f"[布局] {title}: 标签列偏移 {off}mm 过小")
    lc = {x: (x + off, x - off) for x in col_xs}
    res = WireRouter.route(page.placements, nets, lc, nshapes)

    ncs = [KiCadRenderer.render_no_connect(x, y) for x, y in res.isolated_pins]
    for pl_d, c in zip(sheet["placements"], pls):
        pl = next(p for p in page.placements if p.comp.reference == c.reference)
        ncs += [KiCadRenderer.render_no_connect(x, y) for x, y in nc_points(page, c, pl)]

    seen, lib = set(), []
    for c in pls:
        if c.symbol.name not in seen:
            seen.add(c.symbol.name)
            lib.append(KiCadRenderer.render_symbol(c.symbol))
    inst = [KiCadRenderer.render_placement(p.comp, p.x, p.y) for p in page.placements]
    txt = KiCadRenderer.render_sheet(
        title, paper, lib, inst,
        [KiCadRenderer.render_wire(x) for x in res.wires],
        [KiCadRenderer.render_label(x) for x in res.labels],
        [], ncs)

    bal = txt.count("(") - txt.count(")")
    if bal != 0:
        raise ValueError(f"[结构] {title}: 括号平衡差 {bal}")
    if len(inst) != len(sheet["placements"]):
        raise ValueError(f"[结构] {title}: 实例数 {len(inst)} != yaml {len(sheet['placements'])}")
    open(os.path.join(out_dir, fname), "w", encoding="utf-8").write(txt)
    report["sheets"].append({
        "title": title, "paper": paper, "file": fname, "ncols": len(col_xs),
        "components": len(inst), "wires": len(res.wires), "labels": len(res.labels),
        "global_labels": sum(1 for x in res.labels if x.cross_sheet),
        "no_connect": len(ncs), "bytes": len(txt.encode()),
        "sha256_16": hashlib.sha256(txt.encode()).hexdigest()[:16],
    })
    return fname


def build_root(files, report, out_dir):
    cur = open(EXISTING_ROOT, encoding="utf-8").read()
    title = re.search(r'\(title "([^"]*)"\)', cur).group(1)
    paper = re.search(r'\(paper "([^"]*)"\)', cur).group(1)
    root_uuid = re.search(r'\(uuid "([0-9a-fA-F-]{36})"\)', cur).group(1)
    blocks = [(t, f, _uuid4(f"sheet_{t}"), [], i + 2)
              for i, (t, f) in enumerate(files)]
    txt = KiCadRenderer.render_root_sheet(title, paper, root_uuid, blocks,
                                          project="ioconvert")
    if txt.count("(") - txt.count(")") != 0:
        raise ValueError("[结构] root: 括号不平衡")
    open(os.path.join(out_dir, "k2_sch.kicad_sch"), "w", encoding="utf-8").write(txt)
    report["root"] = {"file": "k2_sch.kicad_sch", "title": title, "paper": paper,
                      "sheets": len(blocks), "bytes": len(txt.encode()),
                      "sha256_16": hashlib.sha256(txt.encode()).hexdigest()[:16]}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    spec = load_board_spec(YAML)
    comps = {c.reference: c for c in spec["components"]}
    nets = {n.name: n for n in spec["nets"]}
    nshapes = net_shapes(nets, comps)
    only = os.environ.get("K2_SHEETS")
    keep = set(only.split(",")) if only else None
    report = {"yaml": YAML, "out": OUT, "yaml_nets": len(nets),
              "yaml_components": len(comps), "sheets": [], "skipped": []}

    files = []
    for sheet in spec["sheets"]:
        if keep and slug(sheet["title"]) not in keep and sheet["title"] not in keep:
            continue
        try:
            files.append((sheet["title"], build_sheet(sheet, comps, nets, nshapes, OUT, report)))
        except Exception as e:                       # 沙箱：记录后继续，最后统一报
            report["skipped"].append({"title": sheet["title"],
                                      "paper": sheet["paper"],
                                      "error": f"{type(e).__name__}: {e}"})
    if files and not report["skipped"]:
        build_root(files, report, OUT)               # 全 sheet 成功才出 root

    lib = KiCadRenderer.render_symbol_library(
        list({id(c.symbol): c.symbol for c in comps.values()}.values()))
    open(os.path.join(OUT, "IOCONVERT.kicad_sym"), "w", encoding="utf-8").write(lib)
    report["symbol_lib"] = {"file": "IOCONVERT.kicad_sym", "bytes": len(lib.encode()),
                            "sha256_16": hashlib.sha256(lib.encode()).hexdigest()[:16]}
    open(os.path.join(OUT, "sandbox_report.json"), "w", encoding="utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["skipped"] else 2


if __name__ == "__main__":
    sys.exit(main())
```
