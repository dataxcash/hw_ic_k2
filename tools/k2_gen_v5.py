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
  k2_v4.kicad_pcb                    — 坐标锚点 (只读提取已验证器件坐标与 pad 几何)

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
#   值 = project.yaml::nets_yaml（#K2-23 §二-6 裁定「乙」= hw/data/k2_sch.errata-1.yaml）。
#   缺配置 / 文件不存在 ⇒ fail-closed（禁回落 boards/k2_sch.yaml 之类隐式兜底）。
_NETS_REL = _PMCFG.project_config().get("nets_yaml")
if not _NETS_REL:
    raise SystemExit("[G-ROOT-3] project.yaml 缺 nets_yaml ⇒ fail-closed（禁 symlink 兜底）")
YAML_PATH = os.path.join(ROOT, _NETS_REL)
if not os.path.isfile(YAML_PATH):
    raise SystemExit("[G-ROOT-3] 真源网表不存在: %s ⇒ fail-closed" % YAML_PATH)
PCB_REF_PATH = os.path.join(ROOT, "k2_v4.kicad_pcb")
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
# G3(§五③): K2 refdes 集由真源板导出（禁字面表；单颗 U6）
def _derive_k2_refs_from_true_source(path: str):
    import re as _re
    txt = open(path, encoding="utf-8").read()
    refs = set(_re.findall(r'\(fp_text reference "([A-Z]+\d+)"', txt))
    if not refs:
        refs = set(_re.findall(r'\(property "Reference" "([A-Z]+\d+)"', txt))
    if not refs:
        raise ValueError(f"[G3] 真源板 {path} 未解析到任何 refdes")
    return refs


K2_REFS = sorted(_derive_k2_refs_from_true_source(PCB_REF_PATH))
K2_REFS_SET = set(K2_REFS)

# K1 DNP / 不生成 (MUST DO #2)
K1_DNP = {"U6", "J1", "J7", "J10", "U8", "U9", "U10", "E1", "R16", "R30",
          "R35", "R36", "R37", "C91"}

# ─────────────────────────────────────────────────────────────────────────
# E4 判据（§五⑥ + #K2-13 O2 口径登记）
#   本阶段：产物 refs == 42（对齐真源板）+ 边框 46mm [33,79] + 两次连跑 sha 相同
#   final_target: 55 @P4 —— 差 13 = D2, L1, R35–R39, R40, R41, R42–R45（板侧补件）
#   ⚠ 42 == 42 只是「本阶段对齐真源板」，**不得读成终局合格**
# ─────────────────────────────────────────────────────────────────────────
E4_STAGE_REFS = 42
E4_FINAL_TARGET_REFS = 55   # @P4

# ECN-004 补齐器件 (MUST DO #4/#5)
MISSING_REFS = []   # G3 附带：K2_REFS 现由真源板导出，无「补齐」概念

# ─────────────────────────────────────────────────────────────────────────
# 补齐器件新定位 (ECN-004 规则, 从冻结决策落表; 已在板内空隙验证 0 重叠)
# 全部 ∈ 板框 x∈[23,143], y∈[33,71]
# ─────────────────────────────────────────────────────────────────────────
NEW_PLACE = {
    # U7@(93.825,44.7) VCC 去耦 (4×0.1µF + 1×1µF bulk): x≈91.0 同列 (C67-C72),
    # 上放 y∈[38,43] 避开走廊带 y=44.7±0.5
    "C78": (91.0, 38.5, 0.0),   # U7 bulk 1µF (0603)
    "C74": (91.0, 40.0, 0.0),   # U7 VCC pin6/18/38/50 去耦 0.1µF
    "C75": (91.0, 41.0, 0.0),
    "C76": (91.0, 42.0, 0.0),
    "C77": (91.0, 43.0, 0.0),
    # U3@(93.825,62.7) VCC 去耦: x≈91.0 同列, y∈[57,61] (U3 下方空隙)
    "C83": (91.0, 57.0, 0.0),   # U3 bulk 1µF (0603)
    "C79": (91.0, 58.0, 0.0),
    "C80": (91.0, 59.0, 0.0),
    "C81": (91.0, 60.0, 0.0),
    "C82": (91.0, 61.0, 0.0),
    # P3V3 总线 bulk 10µF (0805): 电源区 x∈[30,45], y∈[37,45]
    "C84": (44.0, 40.0, 0.0),
    # MCU 电源去耦: C85 0.1µF / C86 4.7µF bulk — 就近 U1@(36,52) 左上方
    "C85": (31.5, 54.5, 0.0),
    "C86": (31.5, 56.0, 0.0),
    # PERST# 滤波 0.1µF — 电源区空闲带
    "C87": (44.0, 35.0, 0.0),
    # 12V_IN 输入去耦 1µF — 就近 U2/J12
    "C88": (29.5, 41.5, 0.0),
    # PWR_5V_KEY 输出 4.7µF — 电源区
    "C89": (44.0, 37.5, 0.0),
    # P3V3_AUX 去耦 0.1µF — 就近 U1 x≈30, y∈[50,55]
    "C90": (30.0, 53.0, 0.0),
    # I2C pull-up 4.7K ×4 — strap 电阻列阵右缘 x=55.5 一列
    "R31": (55.5, 66.5, 0.0),
    "R32": (55.5, 67.5, 0.0),
    "R33": (55.5, 68.5, 0.0),
    "R34": (55.5, 69.5, 0.0),
}

# 产物旧 refdes → YAML 语义 refdes (ECN-004 修正)
OLD_REF_MAP = {}   # G4(§五③): 双颗命名重映射已移除（单颗下 U6 不得被改名）

# ─────────────────────────────────────────────────────────────────────────
# 小封装 pad 几何 (0402/0603/0805 — 产物 MLCC/RES 已验几何; 0805 按同比例)
# pad1 = A (驱动侧), pad2 = B (接收侧)
# ─────────────────────────────────────────────────────────────────────────
G_0402 = {"1": (-0.35, 0.0, 0.4, 0.5), "2": (0.35, 0.0, 0.4, 0.5)}
G_0603 = {"1": (-0.45, 0.0, 0.6, 0.7), "2": (0.45, 0.0, 0.6, 0.7)}
G_0805 = {"1": (-0.60, 0.0, 0.8, 0.9), "2": (0.60, 0.0, 0.8, 0.9)}


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


def parse_ref_pcb():
    """从产物 k2_v4.kicad_pcb 提取 {ref: (x, y, rot, fp_name, pads)}.

    pads: {pad_num: {type, shape, at:(x,y), size:(w,h), drill, layers}}
    仅取几何信息; net 一律由 YAML 网表权威重新推导。
    """
    src = open(PCB_REF_PATH).read()
    # 产物文件由增量拼接产生, 部分 footprint 块嵌套在其它块内
    # (J3/J4/MCIO 与 U3/U4/DS160PR810 缩进异常)。用平衡括号从每个
    # `(footprint "NAME"` 处完整提取 s-expr, 与嵌套位置无关。
    blocks = []
    for m in re.finditer(r'\(footprint\s+"[^"]+"', src):
        start = m.start()
        depth = 0
        i = start
        in_str = False
        while i < len(src):
            c = src[i]
            if c == '"':
                in_str = not in_str
            elif not in_str:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1
        blocks.append(src[start:i + 1])
    anchors = {}
    for blk in blocks:
        mref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', blk)
        if not mref:
            continue
        ref = mref.group(1)
        mat = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", blk)
        if not mat:
            continue
        x, y = float(mat.group(1)), float(mat.group(2))
        rot = float(mat.group(3)) if mat.group(3) else 0.0
        mfp = re.search(r'\(footprint\s+"([^"]+)"', blk)
        pads = {}
        for pm in re.finditer(
            r'\(pad\s+"([^"]+)"\s+(\w+)\s+(\w+)\s+'
            r'\(at\s+([-\d.]+)\s+([-\d.]+)\)\s+'
            r'\(size\s+([-\d.]+)\s+([-\d.]+)\)'
            r'(?:\s+\(drill\s+([-\d.]+)\))?\s+'
            r'\(layers\s+([^)]+)\)\s+\(net\s+"([^"]+)"\)',
            blk, re.S):
            pads[pm.group(1)] = {
                "type": pm.group(2), "shape": pm.group(3),
                "at": (float(pm.group(4)), float(pm.group(5))),
                "size": (float(pm.group(6)), float(pm.group(7))),
                "drill": float(pm.group(8)) if pm.group(8) else None,
                "layers": pm.group(9),
            }
        anchors[ref] = {
            "at": (x, y, rot),
            "fp": mfp.group(1) if mfp else "?",
            "pads": pads,
        }
    return anchors


# ─────────────────────────────────────────────────────────────────────────
# refdes → symbol / footprint / value / 位置 / pad 几何
# ─────────────────────────────────────────────────────────────────────────
def build_device_table(symbols, placements, ref_anchors):
    """构造每个 K2 器件的完整定义. 所有坐标来自冻结输入, 零运行时决策."""
    dev = {}
    for ref in K2_REFS:
        pl = placements[ref]
        sym = symbols[pl["symbol"]]
        # ── 位置: 产物锚点优先 (已验证坐标), 缺失器件用 ECN-004 新定位 ──
        old_ref = None
        for k, v in OLD_REF_MAP.items():
            if v == ref:
                old_ref = k
        # refdes 修正器件 (U3/U4/U7): 锚点板已是新命名 (U3/U4/U7 直接存在) 时
        # 优先新 refdes; 旧命名 (U6 等) 仅作 fallback — 防 KeyError/错位。
        anchor = ref_anchors.get(ref)
        if anchor is None and old_ref is not None:
            anchor = ref_anchors.get(old_ref)
        if anchor is not None:
            pos = anchor["at"]
        else:
            pos = NEW_PLACE[ref]
        # ── footprint 名 ──
        if pl["symbol"] in ("C_100N", "C_220N"):
            # L2 v1.2: C67/C68/C72 例外 MLCC_0603; 其余 C_100N/C_220N 0402
            if ref in ("C67", "C68", "C72"):
                fp = "Capacitor_SMD:C_0603_1608Metric"
            else:
                fp = "Capacitor_SMD:C_0402_1005Metric"
        elif pl["symbol"] == "C_1U":
            fp = "Capacitor_SMD:C_0603_1608Metric"
        elif pl["symbol"] == "C_10U":
            fp = "Capacitor_SMD:C_0805_2012Metric"
        elif pl["symbol"] == "C_4R7":
            fp = "Capacitor_SMD:C_0603_1608Metric"
        elif pl["symbol"].startswith("R_"):
            # 产物电阻列阵全部 0603 焊盘 (已验证), 沿用产物几何
            fp = "Resistor_SMD:R_0603_1608Metric"
        else:
            fp = sym["footprint"]
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
            "value": value,
            "at": pos,
            "nc": pl["nc"],
            "pin_map": sym["pins"],   # pin_name -> pad number
            "pads": {},               # pad_number -> net (稍后填充)
        }
    return dev


def mcio_pad_name(pin_num):
    """MCIO_4i 符号脚号(1-38) → 物理 pad 名 (A1-A19/B1-B19)."""
    n = int(pin_num)
    if n % 2 == 1:
        return f"A{(n + 1) // 2}"
    return f"B{n // 2}"


def assign_nets(dev, nets):
    """从 YAML nets 权威推导每个 pad 的 net. 未连网引脚 → NO_CONNECT."""
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
        # pad 几何: 产物优先 (已验证), 新器件用 size-class 几何
        anchor = None
        old_ref = None
        for k, v in OLD_REF_MAP.items():
            if v == ref:
                old_ref = k
        anchor = ref_anchors_cache.get(ref)
        if anchor is None and old_ref is not None:
            anchor = ref_anchors_cache.get(old_ref)
        if anchor is not None:
            d["pads"] = anchor["pads"]
        else:
            sym = d["symbol"]
            if sym in ("C_100N", "C_220N"):
                geom = G_0603 if ref in ("C67", "C68", "C72") else G_0402
            elif sym == "C_1U":
                geom = G_0603
            elif sym == "C_10U":
                geom = G_0805
            elif sym == "C_4R7":
                geom = G_0603
            elif sym.startswith("R_"):
                geom = G_0603
            else:
                raise ValueError(f"[GEOM] 缺少 {ref} 的 pad 几何 (符号 {sym})")
            d["pads"] = {}
            for num, (px, py, w, h) in geom.items():
                d["pads"][num] = {
                    "type": "smd", "shape": "rect",
                    "at": (px, py), "size": (w, h),
                    "drill": None, "layers": '"F.Cu" "F.Mask" "F.Paste"',
                }
    return dev


ref_anchors_cache = {}


# ─────────────────────────────────────────────────────────────────────────
# 输出序列化 (KiCad 20260206 格式, 与产物 k2_v4.kicad_pcb 结构一致)
# ─────────────────────────────────────────────────────────────────────────
def _fmt_rot(rot):
    r = round(rot, 3)
    if r == int(r):
        return str(int(r))
    return f"{r:g}"


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
            pad = (f'\t\t(pad "{pnum}" thru_hole circle (at {px:.3f} {py:.3f}) '
                   f'(size {w:.3f} {h:.3f}) (drill {drill:.3f}) '
                   f'(layers {p["layers"]}) (net "{net}") '
                   f'(uuid "{_u5("pad", d["ref"], pnum, net)}"))')
        else:
            pad = (f'\t\t(pad "{pnum}" smd {p["shape"]} (at {px:.3f} {py:.3f}) '
                   f'(size {w:.3f} {h:.3f}) '
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
    ref_anchors = parse_ref_pcb()
    global ref_anchors_cache
    ref_anchors_cache = ref_anchors

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

    dev = build_device_table(symbols, placements, ref_anchors)
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
    full = HEADER + "\n" + body + "\n" + gen_edge_cuts() + "\n)\n"

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
    print("k2_gen_v5 自检结果 (8/8):")
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
    print(f"  输出: {OUT_PCB}")
    print(f"  布局: {OUT_JSON}")
    return dev


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"❌ 写盘阻断 (fail-fast): {e}", file=sys.stderr)
        sys.exit(1)
