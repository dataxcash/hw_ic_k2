#!/usr/bin/env python3
"""k2_sch_gen_v1 — 由真源再生 K2 原理图（R1 路径 (ii) 的薄 driver）。

- 授权链：监理 #K2-12 §三（先交 (ii) 可行性论证）→ `k2/docs/K2-P2-R1-path-ii-feasibility-v1.md`
  （端到端冒烟通过）→ 监理 **#K2-13 一、U2/S2/S3 裁定**后实施（安装为独立批准步）。
- 真源：`k2/hw/data/k2_sch.yaml`（+ 已存 root 元数据，只读）。
- 输出：`K2_OUT_SCH`（默认 `/tmp/opencode/sch_v1/`）；**绝不直写 `hw/sch`**。

显式规则（禁隐式默认；按可行性论证 §5「规则先报监理备案」）：
  P1 纸张     = 真源 `sheets[].paper`（ReDriver 页经 #K2-13 S2 改为 A0）
  P2 布局     = 列数自适应（越界即增列），列内 gap 8mm，网格 2.54mm
  P3 标签列   = col_x ± floor(min(60, spacing/2−5)/1.27)·1.27 —— **必须落 1.27mm 连接网格**，
                否则导线端点 off-grid（ERC endpoint_off_grid；已实测）
  P4 NC 标记  = `comp.nc_pins`（真源显式）+ 路由 isolated_pins；两者须一致（不一致即 fail-fast）
  P5 电源旗标 = 见 P9（#K2-13 S3 裁定后由「零旗标」改为「按需旗标」）
  P6 label shape = 由 net 上驱动脚的 Electrical 决定（output > input > bidirectional）
  P7 文件名   = `slug(sheet.title) + ".kicad_sch"`（旧 `v5_*` 名不承；sheet 分区由真源给）
  P8 root 元数据(title/paper/uuid) 真源未含 ⇒ 取自已存 `k2/hw/sch/k2_sch.kicad_sch`（只读）
  P9 电源旗标（**#K2-13 S3 采纳 (a)**）：凡「有 `power_in` 脚且无 `power_out` 脚」的网，各加
                **1 个 `PWR_FLAG`**（虚拟件：`in_bom no` / `on_board no`；Value 与内嵌库定义一致，
                以免 `lib_symbol_mismatch`），置于该网**首个标签锚点**；不得改真源引脚类型
  P10 确定性  = 全部 UUID 由 md5(seed) 派生、遍历序固定 ⇒ 同输入两次连跑逐字节相同

版本：v1（2026-09-16，R1 路径 (ii) 落地；规则变更须版本 bump + 留痕）。
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


def render_pwr_flag(x: float, y: float) -> str:
    """PWR_FLAG 实例 —— 虚拟件（不入 BOM、不上板），Value 与内嵌库定义一致。

    连接点 = (x, y)（与目标网的标签锚点重合）；引脚类型 power_out ⇒ ERC 视该网为「已被驱动」。
    """
    uid = _uuid4(f"pwrflag_{x}_{y}")
    return (
        '(symbol (lib_id "power:PWR_FLAG") (at %.3f %.3f 0) (unit 1) '
        '(in_bom no) (on_board no)\n'
        '      (property "Reference" "#FLG01" (at %.3f %.3f 0) (hide yes) '
        '(effects (font (size 1.27 1.27))) (id 0))\n'
        '      (property "Value" "PWR_FLAG" (at %.3f %.3f 0) (hide yes) '
        '(effects (font (size 1.27 1.27))) (id 1))\n'
        '      (property "Footprint" "" (at %.3f %.3f 0) (hide yes) '
        '(effects (font (size 1.27 1.27))) (id 2))\n'
        '      (instances (project "ioconvert" '
        '(path "/%s" (reference "#FLG01"))))\n'
        '      (uuid "%s"))'
        % (x, y, x, y + 6.35, x, y - 1.27, x, y,
           _uuid4(f"ip_pwrflag_{x}_{y}"), uid)
    )


def nets_needing_flag(nets, comps) -> list[str]:
    """P9 通用规则：有 power_in 脚且无 power_out 脚的网（禁硬编 GND）。"""
    out = []
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
        if Electrical.POWER_IN in elec and Electrical.POWER_OUT not in elec:
            out.append(name)
    return out


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


FLAG_NEEDED = {"nets": None, "done": set()}   # P9：全工程各网仅 1 个旗标


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
    # ── P9（#K2-13 S3(a)）：本 sheet 上「需旗标且尚未放」的网，各在首个标签锚点放 1 个虚拟 PWR_FLAG
    power_flags = []
    for net_name in FLAG_NEEDED["nets"]:
        if net_name in FLAG_NEEDED["done"]:
            continue
        lbl = next((l for l in res.labels if l.name == net_name), None)
        if lbl is None:
            continue
        power_flags.append(render_pwr_flag(lbl.x, lbl.y))
        FLAG_NEEDED["done"].add(net_name)
    if power_flags:
        lib.insert(0, KiCadRenderer.render_power_symbol("GND"))
    txt = KiCadRenderer.render_sheet(
        title, paper, lib, inst,
        [KiCadRenderer.render_wire(x) for x in res.wires],
        [KiCadRenderer.render_label(x) for x in res.labels],
        power_flags, ncs)

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
    FLAG_NEEDED["nets"] = nets_needing_flag(nets, comps)   # P9 通用规则（禁硬编）
    only = os.environ.get("K2_SHEETS")
    keep = set(only.split(",")) if only else None
    report = {"yaml": YAML, "out": OUT, "yaml_nets": len(nets),
              "yaml_components": len(comps), "sheets": [], "skipped": []}
    if FLAG_NEEDED["nets"]:
        report["flags_needed"] = sorted(FLAG_NEEDED["nets"])

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
    missing = sorted(set(FLAG_NEEDED["nets"] or []) - FLAG_NEEDED["done"])
    if missing:
        raise ValueError(f"[P9] 需旗标的网未落地: {missing}")
    report["flags_placed"] = sorted(FLAG_NEEDED["done"])
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
