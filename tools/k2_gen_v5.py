#!/usr/bin/env python3
"""k2_gen_v5 — K2 转换卡 (k2_v4, 120×38mm) 单一权威 PCB 布局生成器.

PCIe Gen4 转换卡卡2-K2 权威生成器。取代旧多脚本拼接
(k2_build_v4.py + k2_aux_fill.py + k1_mcu_swap.py + k2_eco22/23_pipe.py),
从冻结输入 (YAML 网表 / SPEC 几何 / L2 冻结决策 / 产物坐标锚点) 生成完整 PCB。

宪法要求: 生成器零运行时自由度。所有设计决策在冻结输入里,
本脚本纯执行, 不做任何挪器件/换层/fallback。自检 FAIL 即 raise ValueError 阻断写盘。

输入 (全部只读):
  project.yaml::nets_yaml             — 网表权威 (symbols 引脚图 + nets 网表 + sheets refdes 清单, K2 卡子集)
                                        [G-ROOT-3] 配置驱动，禁 symlink 兜底
  pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json — 几何权威 (板框/走廊/电容墙/components)
  pm_gate/artifacts/k2_v4/L2/frozen/L2_STRUCTURE_v1.0.md — 冻结决策 (ECN-004)
  hw/lib/ForgeOS.refmap.json         — 库快照↔板 ref 名集（⑦ #K2-26 §3-1）
  pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json — canonical 布局解（坐标**唯一来源**）
  hw/lib/ForgeOS.pretty/<mod>.kicad_mod — pad 几何**唯一来源**（具名外部源；G-ROOT-1）
                                        [G-ROOT-1] ref 清单取自**真源 YAML**；pad 几何取自**库快照**
                                        ⇒ 生成器**零板依赖**（#K2-26 §3-2③）

输出:
  K2_OUT_PCB 环境变量指定 (默认 /tmp/opencode/boards/k2_v5.kicad_pcb)
    (KiCad 20260206 格式, property Reference + pad uuid + 无编号 net)
  K2_OUT_JSON 环境变量指定 (默认 /tmp/opencode/k2_v5_layout.json)
    ({ref: {at, footprint, value}} 供验证)

用法: python3 k2/tools/k2_gen_v5.py
"""

import json
import math
import os
import re
import sys
import uuid

import yaml

# ─────────────────────────────────────────────────────────────────────────
# 冻结路径 (只读)
# ─────────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# G2(§五④): SPEC 路径经 pm_gate.config 解析（禁硬编码 SPEC 名；根因 F-14/N-05）
sys.path.insert(0, os.path.join(ROOT, "_shared"))
os.environ.setdefault("PM_GATE_PROJECT_ROOT", ROOT)   # 自定位：不依赖调用方 cwd
from pm_gate import artifacts as _ARTIFACTS, config as _PMCFG   # noqa: E402
SPEC_PATH = _ARTIFACTS.path("L3", _PMCFG.spec_name())
# G-ROOT-3（#K2-23 §二-3）：真源网表路径**配置驱动**（同 SPEC_PATH 口径），**去 symlink 兜底**。
#   值 = project.yaml::nets_yaml（现行 = hw/data/k2_sch.errata-2.yaml；owner ⑤ 授权 #K2-24 仅删 C89/PWR_5V_KEY，未夹带 105 NC——#K2-28 §2.4 更正）。
#   缺配置 / 文件不存在 ⇒ fail-closed（禁回落 boards/k2_sch.yaml 之类隐式兜底）。
_NETS_REL = _PMCFG.project_config().get("nets_yaml")
if not _NETS_REL:
    raise SystemExit("[G-ROOT-3] project.yaml 缺 nets_yaml ⇒ fail-closed（禁 symlink 兜底）")
YAML_PATH = os.path.join(ROOT, _NETS_REL)
if not os.path.isfile(YAML_PATH):
    raise SystemExit("[G-ROOT-3] 真源网表不存在: %s ⇒ fail-closed" % YAML_PATH)
# G-ROOT-1（#K2-26 §3-2③）：**不读任何板** —— ref 清单取自真源 YAML，pad 几何取自库快照 mod，
# 坐标取自 refmap 冻结锚点。原 `PCB_REF_PATH`（锚板）已整体移除。
LIB_DIR = os.path.join(ROOT, "hw/lib/ForgeOS.pretty")
REFMAP_PATH = os.path.join(ROOT, "hw/lib/ForgeOS.refmap.json")
# P3（#K2-27 §五）：坐标来源 = canonical 布局解（非任何板）。
PLACEMENT_PATH = _ARTIFACTS.path("L2", "PLACEMENT_SOLUTION_v1.json")
# 输出路径可经 K2_OUT_PCB / K2_OUT_JSON 环境变量覆盖（默认 v5 路径，
# 行为零变化）；M13 v8 板重建经覆盖产出 k2_v6，保留 v5 证据不覆盖。
OUT_PCB = os.environ.get("K2_OUT_PCB", "/tmp/opencode/boards/k2_v5.kicad_pcb")
OUT_JSON = os.environ.get("K2_OUT_JSON", "/tmp/opencode/k2_v5_layout.json")

BOARD = {"x": [23.0, 143.0], "y": [33.0, 79.0]}   # G1(§五②): 板框 46mm [33,79]

# ─────────────────────────────────────────────────────────────────────────
# K2 refdes 权威清单 (MUST DO #2: YAML sheets K2 子集 + ECN-004 补齐器件)
# 与旧产物 k2_v4.kicad_pcb 的 80 个已验证器件 + 21 个补齐器件一一对应 (共 101)。
# U7 为上行 ReDriver (YAML 语义), 产物旧命名 "U3"@(93.825,44.7)。
# ─────────────────────────────────────────────────────────────────────────
# G-ROOT-1（#K2-26 §3-2①）: ref 清单取自**真源 YAML sheets placements**（禁取锚板）
def _derive_k2_refs_from_true_source(path: str):
    spec = yaml.safe_load(open(path, encoding="utf-8"))
    refs = {pl["ref"] for sh in spec.get("sheets", [])
            for pl in sh.get("placements", [])}
    if not refs:
        raise ValueError(f"[G-ROOT-1] 真源 {path} 未解析到任何 refdes")
    return refs


K2_REFS = sorted(_derive_k2_refs_from_true_source(YAML_PATH))
K2_REFS_SET = set(K2_REFS)

# K1 DNP / 不生成 (MUST DO #2)
K1_DNP = {"U6", "J1", "J7", "J10", "U8", "U9", "U10", "E1", "R16", "R30",
          "R35", "R36", "R37", "C91"}

# ─────────────────────────────────────────────────────────────────────────
# E4 判据（§五⑥ + #K2-13 O2 口径登记）
#   P2 起：产物 refs == **真源 YAML 54**（#K2-26 §3-2②）+ 边框 46mm [33,79]
#   + 两次连跑 sha 相同。**不得**把「refs 相等」读成终局合格（pad 几何仍须对账）。
# ─────────────────────────────────────────────────────────────────────────
E4_STAGE_REFS = 54          # = 真源 YAML placements（#K2-24 ⑤ 执行后 55→54）
E4_FINAL_TARGET_REFS = 54   # @P4

# ECN-004 补齐器件 (MUST DO #4/#5)
MISSING_REFS = []   # G-ROOT-1 附带：K2_REFS 取自真源 YAML，无「补齐」概念

def _scan_block(text: str, i: int) -> int:
    """i 指向 '('；返回配平括号之后的下标（exclusive）。"""
    depth, instr, j = 1, False, i + 1
    while j < len(text) and depth > 0:
        c = text[j]
        if instr:
            if c == "\\":
                j += 2
                continue
            if c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
        j += 1
    return j


def load_refmap():
    """⑦ 库↔板名集（#K2-26 §3-1）。失败即 fail-closed（禁隐式兜底）。"""
    if not os.path.isfile(REFMAP_PATH):
        raise SystemExit("[G-ROOT-1] 库↔板名集不存在: %s ⇒ fail-closed" % REFMAP_PATH)
    return json.load(open(REFMAP_PATH, encoding="utf-8"))["ref_to_mod"]


def load_placement():
    """canonical 布局解（L2「真源 layout 方案」）——坐标**唯一来源**，**不读任何板**。

    #K2-27 §五-2：来源具名 + sha（见该件 `_basis` 与 `provenance_gap`）。
    """
    if not os.path.isfile(PLACEMENT_PATH):
        raise SystemExit("[P3] 布局解不存在: %s ⇒ fail-closed" % PLACEMENT_PATH)
    d = json.load(open(PLACEMENT_PATH, encoding="utf-8"))
    missing = [r for r in K2_REFS if r not in d["refs"]]
    if missing:
        raise SystemExit("[P3] 布局解缺 ref（fail-closed）: %s" % missing)
    return {r: tuple(v["at"]) for r, v in d["refs"].items()}


def load_mod_pads(mod_name: str):
    """pad 几何**唯一来源**：hw/lib/ForgeOS.pretty/<mod>.kicad_mod。

    仅取**带号** pad（无号 F.Paste 阵列 = 非电气性；带号口径见 D 待裁登记）。
    """
    path = os.path.join(LIB_DIR, mod_name + ".kicad_mod")
    if not os.path.isfile(path):
        raise SystemExit("[G-ROOT-1] 库件缺失: %s ⇒ fail-closed" % path)
    txt = open(path, encoding="utf-8").read()
    pads = {}
    for m in re.finditer(r'\(pad\s+"([^"]*)"', txt):
        num = m.group(1)
        if num == "":
            continue
        blk = txt[m.start():_scan_block(txt, m.start())]
        mt = re.search(r'\(pad\s+"[^"]*"\s+(\w+)\s+(\w+)\s+'
                       r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)\s+'
                       r'\(size\s+([-\d.]+)\s+([-\d.]+)\)', blk)
        if not mt:
            raise ValueError("[G-ROOT-1] 库件 %s pad %r 解析失败" % (mod_name, num))
        md = re.search(r"\(drill\s+([-\d.]+)", blk)
        ml = re.search(r"\(layers\s+([^)]*)\)", blk)
        mrr = re.search(r"\(roundrect_rratio\s+([-\d.]+)\)", blk)
        pads[num] = {
            "type": mt.group(1), "shape": mt.group(2),
            "at": (float(mt.group(3)), float(mt.group(4))),
            "size": (float(mt.group(6)), float(mt.group(7))),
            "drill": float(md.group(1)) if md else None,
            "layers": ml.group(1).strip(),
            "rratio": float(mrr.group(1)) if mrr else None,
        }
    if not pads:
        raise ValueError("[G-ROOT-1] 库件 %s 无带号 pad" % mod_name)
    return pads


# ─────────────────────────────────────────────────────────────────────────
# 解析输入
# ─────────────────────────────────────────────────────────────────────────
def parse_yaml():
    spec = yaml.safe_load(open(YAML_PATH))
    symbols = {}
    for s in spec["symbols"]:
        pinmap = {}
        for side, pins in s.get("pins", {}).items():
            for p in pins:
                if len(p) >= 2:
                    pinmap.setdefault(p[0], []).append(str(p[1]))
        symbols[s["name"]] = {
            "value": s.get("value", ""),
            "footprint": s.get("footprint", ""),
            "pins": pinmap,
            "ref_prefix": s.get("ref_prefix", ""),
        }
    placements = {}   # ref -> {symbol, nc}
    for sheet in spec.get("sheets", []):
        for pl in sheet.get("placements", []):
            ref = pl["ref"]
            placements[ref] = {
                "symbol": pl["symbol"],
                "nc": list(pl.get("nc", [])),
            }
    return symbols, spec["nets"], placements


def parse_spec():
    return json.load(open(SPEC_PATH))


def _strip_card_suffix(value):
    """去掉 value 中的 C1/C2 装配标记后缀 (K1/K2 共享符号), 保留真实值."""
    return re.sub(r"_C[12]_(SMT|DNP)", "", value)


# ─────────────────────────────────────────────────────────────────────────
# refdes → symbol / footprint / value / 位置 / pad 几何
# ─────────────────────────────────────────────────────────────────────────
def build_device_table(symbols, placements, ref_pos, ref_mod):
    """构造每个 K2 器件的完整定义.

    坐标 = canonical 布局解（L2，非板）· pad 几何 = 库快照 mod（G-ROOT-1）
    """
    dev = {}
    for ref in K2_REFS:
        pl = placements[ref]
        sym = symbols[pl["symbol"]]
        pos = ref_pos[ref]            # canonical 布局解（唯一坐标来源）
        mod = ref_mod[ref]
        fp = "ForgeOS:" + mod
        # ── value ──
        if ref == "J13":
            value = "J_SWD"          # SWD 调试口 (与 J9 OOB 区分)
        elif ref == "J9":
            value = "J_OOB_HEADER"
        else:
            value = _strip_card_suffix(sym["value"])
        dev[ref] = {
            "ref": ref,
            "symbol": pl["symbol"],
            "footprint": fp,
            "mod": mod,
            "value": value,
            "at": pos,
            "nc": pl["nc"],
            "pin_map": sym["pins"],   # pin_name -> pad number
            "pads": {},               # pad_number -> 几何（assign_nets 由库件装载）
        }
    return dev


def mcio_pad_name(pin_num):
    """MCIO_4i 符号脚号(1-38) → 物理 pad 名 (A1-A19/B1-B19)."""
    n = int(pin_num)
    if n % 2 == 1:
        return f"A{(n + 1) // 2}"
    return f"B{n // 2}"


def assign_nets(dev, nets):
    """从 YAML nets 权威推导每个 pad 的 net；pad 几何一律取自库快照 mod。"""
    dev_nets = {ref: {} for ref in dev}
    for net, pins in nets.items():
        for rp in pins:
            if "/" not in rp:
                continue
            ref, pin = rp.split("/")
            if ref in dev_nets:
                dev_nets[ref][pin] = net

    for ref, d in dev.items():
        # nc 引脚显式 NO_CONNECT (防误连)
        for pin in d["nc"]:
            dev_nets[ref].setdefault(pin, "NO_CONNECT")
        pad_net = {}
        for pin_name, pad_nums in d["pin_map"].items():
            net = dev_nets[ref].get(pin_name, "NO_CONNECT")
            for pad_num in pad_nums:
                if d["symbol"] == "MCIO_4i":
                    pad_num = mcio_pad_name(pad_num)
                if pad_num in pad_net and pad_net[pad_num] != net:
                    raise ValueError(f"[NETS] {ref} pad {pad_num} 多 pin 冲突: "
                                     f"{pad_net[pad_num]} vs {net}")
                pad_net[pad_num] = net
        d["pad_net"] = pad_net
        # ── pad 几何：库快照（唯一来源；缺件/缺号 ⇒ fail-closed）──
        d["pads"] = load_mod_pads(d["mod"])
        absent = sorted(set(pad_net) - set(d["pads"]))
        if absent:
            raise ValueError(f"[G-ROOT-1] {ref} 库件 {d['mod']} 缺 pad: {absent}")


# ─────────────────────────────────────────────────────────────────────────
# 输出序列化 (KiCad 20260206 格式, 与产物 k2_v4.kicad_pcb 结构一致)
# ─────────────────────────────────────────────────────────────────────────
def _fmt_rot(rot):
    r = round(rot, 3)
    if r == int(r):
        return str(int(r))
    return f"{r:g}"


def _fmt_mm(v) -> str:
    """mm 坐标发射：1 nm 分辨率（%.6f）后去尾零。

    #K2-34 §一-6 (i-a′)：库侧坐标以 nm 整数存储，`%.3f` 会把非 µm 对齐值
    量化到 0.5 µm（U-03/M-09/J-7 根因）；µm 对齐值文本不变。
    """
    s = f"{float(v):.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _u5(kind: str, *parts: str) -> str:
    """确定性 uuid5: 固定 namespace + 元素类型前缀 + 键部分 (ref/pad/net 等).
    零运行时自由度: 同输入必得同 uuid, 与随机 uuid4 等效唯一 (全局不冲突)."""
    key = ":".join([kind] + [str(p) for p in parts])
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


def gen_footprint(d):
    x, y, rot = d["at"]
    lines = [f'\t(footprint "{d["footprint"]}"', '\t\t(layer "F.Cu")',
             f'\t\t(uuid "{_u5("fp", d["ref"])}")',
             f'\t\t(at {x:.3f} {y:.3f} {_fmt_rot(rot)})']
    # Reference / Value 属性 (property 而非 fp_text)
    lines.append(f'\t\t(property "Reference" "{d["ref"]}"')
    lines.append('\t\t\t(at 0 -2 0)')
    lines.append('\t\t\t(layer "F.SilkS")')
    lines.append(f'\t\t\t(uuid "{_u5("refprop", d["ref"])}")')
    lines.append('\t\t\t(effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "{d["value"]}"')
    lines.append('\t\t\t(at 0 2 0)')
    lines.append('\t\t\t(layer "F.Fab")')
    lines.append(f'\t\t\t(uuid "{_u5("valprop", d["ref"])}")')
    lines.append('\t\t\t(effects (font (size 1 1) (thickness 0.15))))')
    lines.append('\t\t(duplicate_pad_numbers_are_jumpers no)')
    for pnum in sorted(d["pads"].keys(), key=lambda n: (len(n), n)):
        p = d["pads"][pnum]
        net = d["pad_net"].get(pnum, "NO_CONNECT")
        px, py = p["at"]
        w, h = p["size"]
        if p["type"] == "thru_hole":
            drill = p.get("drill", 0.8)
            pad = (f'\t\t(pad "{pnum}" thru_hole circle (at {_fmt_mm(px)} {_fmt_mm(py)}) '
                   f'(size {w:.3f} {h:.3f}) (drill {drill:.3f}) '
                   f'(layers {p["layers"]}) (net "{net}") '
                   f'(uuid "{_u5("pad", d["ref"], pnum, net)}"))')
        else:
            rr = f' (roundrect_rratio {p["rratio"]:g})' if p.get("rratio") else ""
            pad = (f'\t\t(pad "{pnum}" smd {p["shape"]} (at {_fmt_mm(px)} {_fmt_mm(py)}) '
                   f'(size {w:.3f} {h:.3f}){rr} '
                   f'(layers {p["layers"]}) (net "{net}") '
                   f'(uuid "{_u5("pad", d["ref"], pnum, net)}"))')
        lines.append(pad)
    lines.append('\t)')
    return "\n".join(lines)


HEADER = """(kicad_pcb
\t(version 20260206)
\t(generator "k2_gen_v5")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
	(layers
		(0 "F.Cu" signal)
		(4 "In1.Cu" signal)
		(6 "In2.Cu" signal)
		(8 "In3.Cu" signal)
		(10 "In4.Cu" signal)
		(12 "In5.Cu" signal)
		(14 "In6.Cu" signal)
		(2 "B.Cu" signal)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t)
 	\t(setup
 	\t\t(pad_to_mask_clearance 0.05)
 	\t\t(solder_mask_min_width 0.05)
 	\t\t(allow_soldermask_bridges_in_footprints no)
	\t\t(tenting
\t\t\t(front yes)
\t\t\t(back yes)
\t\t)
\t\t(covering
\t\t\t(front no)
\t\t\t(back no)
\t\t)
\t\t(plugging
\t\t\t(front no)
\t\t\t(back no)
\t\t)
\t\t(capping no)
\t\t(filling no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00000000_00000000_55555555_5755f5ff)
\t\t\t(plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12)
\t\t\t(dashed_line_gap_ratio 3)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(pdf_metadata yes)
\t\t\t(pdf_single_document no)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plot_black_and_white yes)
\t\t\t(sketchpadsonfab no)
\t\t\t(plotpadnumbers no)
\t\t\t(hidednponfab no)
\t\t\t(sketchdnponfab yes)
\t\t\t(crossoutdnponfab yes)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
			(outputdirectory "")
		)
	)"""


# ─────────────────────────────────────────────────────────────────────────
# G10 emit 段（G-ROOT-2；#K2-23 §二-3/§二-4）—— **消费 SPEC 输入层，不读板**（避 C-1）
#   源：`keepout_geometry.zones`（8 keepout）· `pd.zone_defs.board_realized_zones`（10 有网铜区）
#       · `mounting_holes.holes`（4 NPTH）；数据经 SPEC rev-49 落库（逐条 verbatim 自受审板实测）。
#   生成段逐字取自已 KiCad 级验证的草案：Z2 `emit_zone`（inc62 §2 `8a31ad20ec520e32`）
#   · NPTH `emit_footprint`（inc63 §2 `56cdbef1e48e8b1e`）；填充仍由出图前 ZONE_FILLER 承担。
# ─────────────────────────────────────────────────────────────────────────
_KEEPOUT_SW = ("tracks", "vias", "pads", "copperpour", "footprints")
NPTH_FP_NAME = "MountingHole_3.2mm_M3"
NPTH_NS = uuid.UUID("6f5f1c3e-0000-4000-8000-000000000000")


def _layers_expr(z):
    return f'(layer "{z["layers"][0]}")' if len(z["layers"]) == 1 else \
        "(layers " + " ".join(f'"{l}"' for l in z["layers"]) + ")"


def emit_zone(z: dict) -> str:
    u = str(uuid.uuid5(uuid.NAMESPACE_URL,
                       f'k2/g10/{z["kind"]}/{z["name"]}/{z["net"]}/{z["pts"][:1]}'))
    pts = " ".join(f"(xy {a} {b})" for a, b in z["pts"])
    if z["kind"] == "keepout":
        sw = "\n".join(f"\t\t\t({s} {z['keepout'][s]})" for s in _KEEPOUT_SW)
        return (f'(zone\n\t\t{_layers_expr(z)}\n\t\t(uuid "{u}")\n\t\t(name "{z["name"]}")\n\t\t(hatch edge 0.5)\n'
                f'\t\t(connect_pads\n\t\t\t(clearance 0)\n\t\t)\n\t\t(min_thickness 0.25)\n\t\t(keepout\n{sw}\n\t\t)\n'
                f'\t\t(placement\n\t\t\t(enabled no)\n\t\t\t(sheetname "")\n\t\t)\n\t\t(fill\n\t\t\t(thermal_gap 0.5)\n'
                f'\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{pts}\n\t\t\t)\n\t\t)\n\t)')
    prio = f'\n\t\t(priority {z["priority"]})' if z["priority"] else ""
    return (f'(zone\n\t\t(net "{z["net"]}")\n\t\t{_layers_expr(z)}\n\t\t(uuid "{u}")\n\t\t(hatch edge 0.5)\n'
            f'\t\t(connect_pads yes\n\t\t\t(clearance {z["connect_pads_clearance"]})\n\t\t)\n\t\t(min_thickness {z["min_thickness"]}){prio}\n'
            f'\t\t(fill yes\n\t\t\t(thermal_gap 0.2)\n\t\t\t(thermal_bridge_width 0.3)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
            f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{pts}\n\t\t\t)\n\t\t)\n\t)')


def _npth_uuid(ref: str) -> str:
    return str(uuid.uuid5(NPTH_NS, f"k2/g10/npth/{ref}"))


def _emit_npth_pad(h: dict) -> str:
    d = h["drill"]
    return (f'\t\t(pad "" np_thru_hole circle\n'
            f'\t\t\t(at 0 0)\n'
            f'\t\t\t(size {d:g} {d:g})\n'
            f'\t\t\t(drill {d:g})\n'
            f'\t\t\t(layers "*.Cu" "*.Mask")\n'
            f'\t\t)')


def emit_npth_footprint(h: dict) -> str:
    x, y = h["at"]; d = h["drill"]
    return (f'\t(footprint "{NPTH_FP_NAME}"\n'
            f'\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{_npth_uuid(h["ref"])}")\n'
            f'\t\t(at {x:g} {y:g})\n'
            f'\t\t(descr "Mounting Hole 3.2mm, M3, no annular")\n'
            f'\t\t(property "Reference" "{h["ref"]}"\n'
            f'\t\t\t(at 0 -4.15 0)\n'
            f'\t\t\t(layer "F.SilkS")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n'
            f'\t\t)\n'
            f'\t\t(property "Value" "{NPTH_FP_NAME}"\n'
            f'\t\t\t(at 0 4.15 0)\n'
            f'\t\t\t(layer "F.Fab")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n'
            f'\t\t)\n'
            f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
            f'\t\t(fp_circle (center 0 0) (end {d:g} 0)\n'
            f'\t\t\t(stroke (width 0.15) (type solid)) (fill no) (layer "Cmts.User")\n'
            f'\t\t)\n'
            f'\t\t(fp_circle (center 0 0) (end {d + 0.25:g} 0)\n'
            f'\t\t\t(stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd")\n'
            f'\t\t)\n'
            f'{_emit_npth_pad(h)}\n'
            f'\t)')


def load_g10_inputs(spec: dict):
    """G-ROOT-2：从 SPEC **输入层**取 G10 三块数据（不读板）；缺件即 fail-closed。"""
    ko = (spec.get("keepout_geometry") or {}).get("zones") or []
    bz = ((spec.get("pd") or {}).get("zone_defs") or {}).get("board_realized_zones") or {}
    cu = bz.get("zones") or []
    hl = (spec.get("mounting_holes") or {}).get("holes") or []
    if (len(ko), len(cu), len(hl)) != (8, 10, 4):
        raise SystemExit(
            "[G-ROOT-2] SPEC 输入层缺件/计数异常 keepout=%d copper=%d npth=%d（期望 8/10/4）"
            " ⇒ fail-closed（禁读板兜底；须先有 SPEC rev-49 输入层）" % (len(ko), len(cu), len(hl)))
    return ko, cu, hl


def gen_edge_cuts():
    x0, x1 = BOARD["x"]
    y0, y1 = BOARD["y"]
    segs = [
        ((x0, y0), (x1, y0)),
        ((x0, y1), (x0, y0)),
        ((x1, y0), (x1, y1)),
        ((x1, y1), (x0, y1)),
    ]
    out = []
    for (ax, ay), (bx, by) in segs:
        out.append("\t(gr_line")
        out.append(f"\t\t(start {ax:g} {ay:g})")
        out.append(f"\t\t(end {bx:g} {by:g})")
        out.append("\t\t(stroke")
        out.append("\t\t\t(width 0.1)")
        out.append("\t\t\t(type solid)")
        out.append("\t\t)")
        out.append('\t\t(layer "Edge.Cuts")')
        out.append(f'\t\t(uuid "{_u5("edge", ax, ay, bx, by)}")')
        out.append("\t)")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────
# fail-fast 自检 (写盘前全 PASS; 任一 FAIL → raise ValueError 阻断写盘)
# ─────────────────────────────────────────────────────────────────────────
def pad_bboxes(dev):
    """每个 pad 的绝对 AABB (KiCad 旋转约定: x'=x·cosφ+y·sinφ, y'=-x·sinφ+y·cosφ)."""
    bboxes = []  # (ref, pad, (minx,miny,maxx,maxy))
    for ref, d in dev.items():
        fx, fy, rot = d["at"]
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        for pnum, p in d["pads"].items():
            px, py = p["at"]
            w, h = p["size"]
            cxp = px * ca + py * sa
            cyp = -px * sa + py * ca
            corners = [(-w / 2, -h / 2), (w / 2, -h / 2),
                       (w / 2, h / 2), (-w / 2, h / 2)]
            xs, ys = [], []
            for cx, cy in corners:
                rx = cx * ca + cy * sa + cxp
                ry = -cx * sa + cy * ca + cyp
                xs.append(rx + fx)
                ys.append(ry + fy)
            bboxes.append((ref, pnum, (min(xs), min(ys), max(xs), max(ys))))
    return bboxes


def check_pad_overlap(dev, tol=0.01):
    bb = pad_bboxes(dev)
    n = len(bb)
    for i in range(n):
        ri, pi, (ax0, ay0, ax1, ay1) = bb[i]
        for j in range(i + 1, n):
            rj, pj, (bx0, by0, bx1, by1) = bb[j]
            dx = min(ax1, bx1) - max(ax0, bx0)
            dy = min(ay1, by1) - max(ay0, by0)
            if dx > tol and dy > tol:
                raise ValueError(
                    f"[S1 PAD_OVERLAP] {ri}/{pi} ({ax0:.3f},{ay0:.3f})-"
                    f"({ax1:.3f},{ay1:.3f}) 与 {rj}/{pj} "
                    f"({bx0:.3f},{by0:.3f})-({bx1:.3f},{by1:.3f}) "
                    f"重叠 dx={dx:.3f} dy={dy:.3f} (容差 {tol})")
    return True


def check_refdes(dev):
    got = set(dev.keys())
    if got != K2_REFS_SET:
        extra = sorted(got - K2_REFS_SET)
        missing = sorted(K2_REFS_SET - got)
        raise ValueError(
            f"[S2 REFDES] 生成 refdes 集合 != K2 清单: "
            f"多余={extra} 缺失={missing}")
    # 交叉验证: 每个 K2 ref 必须存在于 YAML sheets placements
    return True


def check_missing_devices(dev):
    for r in MISSING_REFS:
        if r not in dev:
            raise ValueError(f"[S4 MISSING] 补齐器件 {r} 未生成")
    return True


def check_board_bounds(dev):
    x0, x1 = BOARD["x"]
    y0, y1 = BOARD["y"]
    for ref, d in dev.items():
        x, y, _ = d["at"]
        if not (x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6):
            raise ValueError(
                f"[S5 BOUNDS] {ref}@({x},{y}) 超出板框 "
                f"x∈[{x0},{x1}] y∈[{y0},{y1}]")
    return True


def check_nets(dev, nets):
    valid = set(nets.keys()) | {"NO_CONNECT"}
    for ref, d in dev.items():
        for pnum, net in d["pad_net"].items():
            if net not in valid:
                raise ValueError(
                    f"[S6 NETS] {ref} pad {pnum} net '{net}' "
                    f"不在 YAML nets (160 网名) 且非 NO_CONNECT")
    return True


# ─────────────────────────────────────────────────────────────────────────
# SPEC 冻结几何覆盖 (2026-08-16 更新: 排针列重排 + AC 电容墙最小中心距)
# 纯消费冻结值, 零运行时设计决策。
# ─────────────────────────────────────────────────────────────────────────
def apply_spec_overrides(dev, spec):
    """1) 排针坐标覆盖产物锚点 (components.pin_headers.positions).
       2) 锚点修正覆盖产物坐标 (components.anchor_fixes, 优先级最高).
       3) 下行 AC 墙 C17-C32 同 y 行 x 间距扩到 min_center_pitch_mm,
          超出 lower_band_y 的行 y 移入带内 (上行 C49-C64 已满足, 不动)."""
    ph = spec.get("components", {}).get("pin_headers", {})
    for ref, pos in ph.get("positions", {}).items():
        if ref not in dev:
            raise ValueError(f"[SPEC] pin_headers 含未知 ref {ref}")
        dev[ref]["at"] = (float(pos[0]), float(pos[1]), float(ph["rot"]))

    af = spec.get("components", {}).get("anchor_fixes", {})
    for ref, fix in af.items():
        if not isinstance(fix, dict) or "pos" not in fix:
            continue
        if ref not in dev:
            raise ValueError(f"[SPEC] anchor_fixes 含未知 ref {ref}")
        pos = fix["pos"]
        dev[ref]["at"] = (float(pos[0]), float(pos[1]), dev[ref]["at"][2])

    # G7(§五③): capacitor_walls 段已移除（AC 墙对象不存在）；anchor_fixes 严格校验保留
    return dev


def check_pin_headers(dev, spec):
    """S8: 排针坐标 == SPEC components.pin_headers.positions (精确匹配)."""
    ph = spec.get("components", {}).get("pin_headers", {})
    for ref, pos in ph.get("positions", {}).items():
        x, y, _ = dev[ref]["at"]
        ex, ey = float(pos[0]), float(pos[1])
        if abs(x - ex) > 1e-6 or abs(y - ey) > 1e-6:
            raise ValueError(
                f"[S8 PIN_HEADER] {ref}@({x},{y}) != 冻结坐标 ({ex},{ey})")
    return True


def classify_net(net: str) -> str:
    """网名 → net_class 归类 (通用命名约定, 供 netclass_assignments 注入)."""
    if net == "GND":
        return "Default"
    if net.startswith("PCIE_"):
        return "PCIe85"
    if any(k in net for k in ("P3V3", "MCU_VDD", "VREG", "PWR_5V",
                              "12V_IN", "3V3_DCDC")):
        return "POWER"
    return "LOW_SPEED"


def inject_netclasses(pro_path: str, spec: dict, dev: dict) -> None:
    """把 SPEC net_classes 注入 .kicad_pro 的 net_settings (KiCad 10 唯一合法位置).

    KiCad 10 实证 (2026-08-18): .kicad_pcb 顶层 (net_class ...) 非合法 token,
    pcbnew Save 也不保留; 规则必须落在 .kicad_pro 的 net_settings.classes +
    netclass_assignments, kicad-cli DRC 才按网名取用。
    """
    with open(pro_path) as f:
        pro = json.load(f)
    ns = pro.setdefault("net_settings", {})
    classes = ns.setdefault("classes", [])
    have = {c["name"] for c in classes}
    for name, meta in spec.get("net_classes", {}).items():
        if name in have:
            continue
        base = {"diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2, "line_style": 0,
                "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 2147483647,
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "tuning_profile": "", "via_diameter": 0.35,
                "via_drill": 0.2, "wire_width": 6, "bus_width": 12}
        base.update({"name": name,
                     "track_width": meta.get("width", 0.2),
                     "clearance": meta.get("clearance", 0.2)})
        dp = meta.get("diff_pair", {})
        if dp:
            base["diff_pair_width"] = dp.get("p_width", base["diff_pair_width"])
            base["diff_pair_gap"] = dp.get("p_gap", base["diff_pair_gap"])
        classes.append(base)
    nets = sorted({net for d in dev.values() for net in d["pad_net"].values()}
                  - {"NO_CONNECT"})
    ns["netclass_assignments"] = {net: [classify_net(net)] for net in nets}
    with open(pro_path, "w") as f:
        json.dump(pro, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────────
def main():
    symbols, nets, placements = parse_yaml()
    spec = parse_spec()
    g10_ko, g10_cu, g10_holes = load_g10_inputs(spec)   # G-ROOT-2
    ref_mod = load_refmap()
    ref_pos = load_placement()

    # SPEC 板框交叉校验
    sx = spec["board"]["outline_x"]
    sy = spec["board"]["outline_y"]
    if abs(sx[0] - BOARD["x"][0]) > 1e-6 or abs(sx[1] - BOARD["x"][1]) > 1e-6 \
            or abs(sy[0] - BOARD["y"][0]) > 1e-6 or abs(sy[1] - BOARD["y"][1]) > 1e-6:
        raise ValueError(f"[SPEC] SPEC_k2_v4.json 板框 {sx}/{sy} 与冻结板框 {BOARD} 不符")

    # K2 清单 ↔ YAML sheets 交叉验证
    yaml_refs = set(placements.keys())
    if not K2_REFS_SET.issubset(yaml_refs):
        raise ValueError(
            f"[YAML] K2 清单含 YAML sheets 不存在 ref: "
            f"{sorted(K2_REFS_SET - yaml_refs)}")

    dev = build_device_table(symbols, placements, ref_pos, ref_mod)
    apply_spec_overrides(dev, spec)
    assign_nets(dev, nets)

    # ── 8 项 fail-fast 自检 (全 PASS 才写盘) ──
    results = []
    results.append(("S1 焊盘重叠", check_pad_overlap(dev)))
    results.append(("S2 refdes 对齐", check_refdes(dev)))
    results.append(("S4 缺失器件", check_missing_devices(dev)))
    results.append(("S5 坐标范围", check_board_bounds(dev)))
    results.append(("S6 网表一致性", check_nets(dev, nets)))
    results.append(("S8 排针坐标冻结", check_pin_headers(dev, spec)))

    # ── 序列化 ──
    blocks = []
    for ref in K2_REFS:
        blocks.append(gen_footprint(dev[ref]))
    body = "\n".join(blocks)
    zone_text = "\n".join(emit_zone(z) for z in (g10_ko + g10_cu))
    hole_text = "\n".join(emit_npth_footprint(h) for h in g10_holes)
    full = (HEADER + "\n" + body + "\n" + gen_edge_cuts() + "\n"
            + hole_text + "\n" + zone_text + "\n)\n")

    os.makedirs(os.path.dirname(OUT_PCB), exist_ok=True)
    with open(OUT_PCB, "w") as f:
        f.write(full)

    # ── 复制 JLC 规则模板 (Board Setup, DRC 按板厂工艺而非 KiCad 默认) ──
    import shutil
    tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "k2_jlc_template.kicad_pro")
    dst = OUT_PCB.replace(".kicad_pcb", ".kicad_pro")
    shutil.copy(tmpl, dst)

    # ── 注入 SPEC net_classes + 网名→class 映射 ──
    # KiCad 10 实证: 规则只存 .kicad_pro 的 net_settings, .kicad_pcb 顶层 net_class 非法
    inject_netclasses(dst, spec, dev)

    layout = {ref: {"at": list(d["at"]), "footprint": d["footprint"],
                    "value": d["value"]}
              for ref, d in dev.items()}
    with open(OUT_JSON, "w") as f:
        json.dump(layout, f, indent=1)

    # ── 摘要 ──
    n_pads = sum(len(d["pads"]) for d in dev.values())
    n_nc = sum(1 for d in dev.values()
               for pnum in d["pads"] if d["pad_net"].get(pnum, "NO_CONNECT") == "NO_CONNECT")
    used_nets = sorted({net for d in dev.values() for net in d["pad_net"].values()}
                       - {"NO_CONNECT"})
    print("=" * 56)
    print(f"k2_gen_v5 自检结果 ({len(results)}/{len(results)}):")   # D-6: 声称须与实际一致
    for name, _ in results:
        print(f"  ✅ {name}: PASS")
    print("=" * 56)
    ph = spec["components"]["pin_headers"]["positions"]
    print("  排针坐标 (SPEC 冻结): " + ", ".join(
        f"{r}@({p[0]},{p[1]})" for r, p in sorted(ph.items())))
    # G6b/G8b: AC 墙摘要打印已随对象移除
    print(f"  器件数: {len(dev)}  (产物沿用 {len(dev) - len(MISSING_REFS)}, "
          f"补齐 {len(MISSING_REFS)})")
    print(f"  pads 总数: {n_pads}")
    print(f"  使用网名数: {len(used_nets)}  (YAML nets 共 {len(nets)})")
    print(f"  NO_CONNECT pads: {n_nc}")
    print(f"  G10 输入层: keepout={len(g10_ko)} copper={len(g10_cu)} npth={len(g10_holes)}  (源=SPEC 输入层，不读板)")
    print(f"  输出: {OUT_PCB}")
    print(f"  布局: {OUT_JSON}")
    return dev


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"❌ 写盘阻断 (fail-fast): {e}", file=sys.stderr)
        sys.exit(1)
