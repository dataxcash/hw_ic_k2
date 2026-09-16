#!/usr/bin/env python3
"""k2_p4_build_l5_v1 — **P4 施工执行器**（#K2-18 §五 U3 / §九-3）。

零设计决策：几何/层/封装/落位全部来自冻结输入；本件纯执行 + 自检，自检不过即 raise（不写盘）。

输入（只读）：
  hw/k2_v4_8L.l4.kicad_pcb            交付板（冻结 d4e81f647be7f980，永不改）
  hw/k2_sch.errata-1.yaml             真源网表（经 pm_gate/project.yaml:nets_yaml）
  L3/SPEC_k2_v4.spec-rev-25.json      canonical SPEC（经 pm_gate.config 解析）
  L3/drawings/p3_placement_solution.json   落位解（15/15）
  hw/lib/ForgeOS.pretty               land pattern（PinHeader_1x02/1x04、MCU_STM32G0_LQFP48）
   AppDir/share/kicad/footprints/MountingHole.pretty   固定孔 land pattern

本轮已落地 IN（**增量 1**）：
  IN-4  U1 补齐 pad `34..48` + `EP(49)→GND`（换 land pattern，按 pad 号迁网）
  IN-11 5 件接口件 16 pad 补齐（J6/J9/J11/J12/J13）
  IN-8  排针列 `column_x = 27.94`（26.5 → 27.94，守 P3-4 余量 0.08）
  IN-6  4×Ø3.2 NPTH + Ø6.0 keepout（8 铜层 rule area）
  IN-7  4 个无网 `ESC_*` rule area：开关落 ≥1 非 allowed（`zone_fills = disallow`）
  IN-3  9 铜区填充（C7）
未落地（**下一增量**，须网表赋网 + 布线，属耦合任务）：IN-5 13 件补件落板 + C73/C86 移位

输出：
  K2_P4_OUT（默认 /tmp/opencode/p4/k2_v4_8L.l5.kicad_pcb）新 revision 板
  K2_P4_LEDGER（默认同目录 k2_p4_construction.json）机读施工台账 + 自检
"""
from __future__ import annotations
import json, os, sys, hashlib, uuid as _uuid

K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(K2)
os.environ.setdefault("PM_GATE_PROJECT_ROOT", K2)   # 官方解析链（禁硬编码 SPEC 路径）
sys.path.insert(0, os.path.join(K2, "_shared"))
SRC = os.path.join(K2, "hw/k2_v4_8L.l4.kicad_pcb")
OUT = os.environ.get("K2_P4_OUT", "/tmp/opencode/p4/k2_v4_8L.l5.kicad_pcb")
LEDGER = os.environ.get("K2_P4_LEDGER", os.path.join(os.path.dirname(OUT), "k2_p4_construction.json"))
FORGEOS = os.path.join(K2, "hw/lib/ForgeOS.pretty")
MH_LIB = os.path.join(ROOT, "AppDir/share/kicad/footprints/MountingHole.pretty")
MH_FP = "MountingHole_3.2mm_M3"
COLUMN_X = 27.94                      # IN-8（P3-4 余量 0.08 ⇒ 守值）
NPTH_DRILL = 3.2                      # IN-6
KEEPOUT_DIA = 6.0
STAGE = os.environ.get("K2_P4_STAGE", "/tmp/opencode/p4/stage_pretty")   # 暂存确定性 UUID 库
CU_LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def spec_load():
    from pm_gate import config as cfg, artifacts as art
    name = cfg.spec_name("k2_v4")
    return name, art.path("L3", name), json.load(open(art.path("L3", name), encoding="utf-8"))


def stage_lib(libdir, name, tag):
    """把库封装**复制到 /tmp 暂存 .pretty**，并把其中所有 `(uuid ...)` 换成按 `tag` 确定性派生的 UUID。

    目的：`FootprintLoad(preserveUUID=True)` + 写盘顺序均依赖 UUID ⇒ 不固定 UUID 则两次跑 sha 不同
    （KiCad 绑定无 UUID setter）。固定后：**复跑逐字节一致**。
    """
    import re as _re
    src = os.path.join(libdir, name + ".kicad_mod")
    txt = open(src, encoding="utf-8").read()
    ns = _uuid.uuid5(_uuid.NAMESPACE_URL, f"k2-l5-{tag}")
    cnt = [0]

    def _sub(m):
        u = str(_uuid.uuid5(ns, f"item{cnt[0]}"))
        cnt[0] += 1
        return f'(uuid "{u}")'
    txt = _re.sub(r'\(uuid "[0-9a-fA-F-]+"\)', _sub, txt)
    outp = os.path.join(STAGE, f"{tag}.pretty")
    os.makedirs(outp, exist_ok=True)
    open(os.path.join(outp, name + ".kicad_mod"), "w", encoding="utf-8").write(txt)
    return outp


def load_fp(libdir, name, preserve=True):
    """载入库封装。**preserveUUID=True** ⇒ 复用库内 UUID（复跑确定性；随机 UUID 会破坏两次跑 sha 相同）。"""
    import pcbnew
    fp = pcbnew.FootprintLoad(libdir, name, preserve)
    if fp is None:
        raise ValueError(f"FootprintLoad 失败: {libdir}:{name}")
    return fp


def lib_of(fpid):
    """SPEC/落位解的 lib id → (libdir, name)。"""
    lib, _, nm = fpid.partition(":")
    cand = [os.path.join(K2, "hw/lib", f"{lib}.pretty"),
            os.path.join(ROOT, "AppDir/share/kicad/footprints", f"{lib}.pretty")]
    for c in cand:
        if os.path.isdir(c):
            return c, nm
    raise ValueError(f"lib dir 未找到: {fpid}")


def yaml_path():
    """真源网表路径：经 project.yaml:nets_yaml 指针（#K2-16 §五.1；无指针回退冻结件）。"""
    import yaml as _y
    pp = os.path.join(K2, "pm_gate/project.yaml")
    cfg = _y.safe_load(open(pp, encoding="utf-8")) or {}
    rel = cfg.get("nets_yaml")
    cand = os.path.join(K2, rel) if rel else os.path.join(K2, "hw/data/k2_sch.yaml")
    return cand if os.path.isfile(cand) else os.path.join(K2, "hw/data/k2_sch.yaml")


def in5_pad_nets(refs):
    """IN-5：从**真源网表 + 符号引脚号**派生 ref → {pad 号: 网名}（禁猜：A→1/B→2 等一律由符号 pins 决定）。"""
    import yaml as _y
    y = _y.safe_load(open(yaml_path(), encoding="utf-8"))
    syms = {s["name"]: s for s in y["symbols"]}
    ref2sym, ref2val = {}, {}
    for sheet in y["sheets"]:
        for pl in sheet.get("placements", []):
            ref2sym[pl["ref"]] = pl["symbol"]
            ref2val[pl["ref"]] = syms.get(pl["symbol"], {}).get("value", "")
    pin_num = {}
    for nm, sd in syms.items():
        d = {}
        for side in ("right", "left"):
            for pin in sd.get("pins", {}).get(side, []):
                d[str(pin[0])] = str(pin[1])
        pin_num[nm] = d
    pin_net = {}
    for net, mem in (y["nets"] or {}).items():
        for item in mem:
            r, pin = item.split("/", 1)
            pin_net.setdefault(r, {})[pin] = net
    out = {}
    for ref in refs:
        pm, nm = pin_num.get(ref2sym.get(ref), {}), pin_net.get(ref, {})
        pad2net, unmapped = {}, []
        for pin, net in nm.items():
            if pin in pm:
                pad2net[pm[pin]] = net
            else:
                unmapped.append([pin, net])
        out[ref] = {"pad2net": pad2net, "unmapped": unmapped, "value": ref2val.get(ref, ""),
                    "symbol": ref2sym.get(ref)}
    return out


def _block_at(txt, i):
    """返回包含位置 i 的顶层 s-expr 块（含括号匹配，跳过字符串）。"""
    j = txt.rfind("(", 0, i + 1)
    d = 0
    k = j
    while k < len(txt):
        c = txt[k]
        if c == '"':
            k += 1
            while txt[k] != '"':
                k += 2 if txt[k] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                break
        k += 1
    return j, k + 1


def sort_footprints(path):
    """写盘后**规范化 footprint 顺序**（按 Reference 排序）。

    KiCad 的写盘顺序随 UUID 变化 ⇒ 逐字节不可复跑。本件把 footprint 区段按 ref 重排（其余段不动）。
    """
    import re as _re
    txt = open(path, encoding="utf-8").read()
    spans = []
    i = 0
    while True:
        j = txt.find("\t(footprint ", i)
        if j < 0:
            break
        a, b = _block_at(txt, txt.find("(", j))   # 从 footprint 自身的 '(' 起算（rfind 会抓到前一件的括号）
        m = _re.search(r'\(property "Reference" "([^"]*)"', txt[a:b])
        spans.append((a, b, m.group(1) if m else ""))
        i = b
    if len(spans) < 2:
        return 0
    head = txt[:spans[0][0]]
    tail = txt[spans[-1][1]:]
    blocks = [txt[a:b] for a, b, _r in spans]
    blocks.sort(key=lambda blk: (_re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)))
    open(path, "w", encoding="utf-8").write(head + "\n\t".join(blocks) + tail)
    return len(blocks)


def sort_new_keepout_zones(path, marker="K2_HOLE_KEEPOUT"):
    """写盘后把**本件新增的 4 个 keepout zone** 按名排序（zone 写盘顺序亦随 UUID 变化 ⇒ 逐字节不可复跑）。

    只重排这 4 个新块（互不相交、同 priority ⇒ 无语义影响）；既有 zone 顺序不动。
    """
    import re as _re
    txt = open(path, encoding="utf-8").read()
    spans = []
    i = 0
    while True:
        j = txt.find("\t(zone", i)
        if j < 0:
            break
        a, b = _block_at(txt, txt.find("(", j))
        if marker in txt[a:b]:
            spans.append((a, b, txt[a:b]))
        i = b
    if len(spans) < 2:
        return 0
    if spans[-1][0] - spans[0][1] > len(txt) // 10:
        return -1                     # 不连续 ⇒ 不重排（保守）
    head, tail = txt[:spans[0][0]], txt[spans[-1][1]:]
    blocks = sorted((blk for _a, _b, blk in spans), key=lambda blk: _re.search(r'\(name "([^"]*)"', blk).group(1))
    open(path, "w", encoding="utf-8").write(head + "\n\t".join(blocks) + tail)
    return len(blocks)


def canonicalize_uuids(path, refs=("U1", "J6", "J9", "J11", "J12", "J13", "H1", "H2", "H3", "H4")):
    """写盘后规范化**新增件**的 UUID ⇒ 复跑确定性（pcbnew 绑定无 UUID setter）。

    仅改这 4 个固定孔 footprint 块内的 `(uuid ...)`（footprint 自身 + 其 pad）；不触碰其余件。
    """
    import re as _re
    txt = open(path, encoding="utf-8").read()
    n = 0
    # ① 新增 keepout zone：按标记名定位，UUID 由标记名确定性派生
    for i in range(1, 9):
        mk = f"K2_HOLE_KEEPOUT_H{i}"
        j = txt.find(mk)
        if j < 0:
            continue
        z0 = txt.rfind("\t(zone", 0, j)          # 该 zone 块起点（避免 rfind("(") 抓到前一件的括号）
        a, bb = _block_at(txt, txt.find("(", z0))
        zblock = txt[a:bb]
        ns = _uuid.uuid5(_uuid.NAMESPACE_URL, f"k2-l5-{mk}")
        u = str(_uuid.uuid5(ns, "zone"))
        nb = _re.sub(r'\(uuid "[0-9a-fA-F-]+"\)', f'(uuid "{u}")', zblock, count=1)
        if nb != zblock:
            txt = txt[:a] + nb + txt[bb:]
            n += 1
    # ② 固定孔 footprint：按 ref 定位
    for ref in refs:
        idx = txt.find(f'(property "Reference" "{ref}"')      # 注意：KiCad 该行后仍有子节点 ⇒ 不带右括号
        if idx < 0:
            continue
        f0 = txt.rfind("\t(footprint ", 0, idx)              # 该 footprint 块起点（避免 rfind("(") 抓错层）
        a, b = _block_at(txt, txt.find("(", f0))
        block = txt[a:b]
        ns = _uuid.uuid5(_uuid.NAMESPACE_URL, f"k2-l5-{ref}")
        cnt = [0]

        def _sub(m):
            u = str(_uuid.uuid5(ns, f"item{cnt[0]}"))
            cnt[0] += 1
            return f'(uuid "{u}")'
        nb = _re.sub(r'\(uuid "[0-9a-fA-F-]+"\)', _sub, block)
        if nb != block:
            txt = txt[:a] + nb + txt[b:]
            n += 1
    open(path, "w", encoding="utf-8").write(txt)
    return n


def main():
    import pcbnew
    spec_name, spec_path, spec = spec_load()
    DRAW = os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/drawings")
    sol = json.load(open(os.path.join(DRAW, "p3_placement_solution.json"), encoding="utf-8"))
    drw = json.load(open(os.path.join(DRAW, "p3_drawings.json"), encoding="utf-8"))
    mh = drw["mounting_holes"]                       # P4 输入 = P3 图纸（L2-2）
    holes = [(mh["positions"][k][0], mh["positions"][k][1]) for k in sorted(mh["positions"])]
    if abs(mh["drill_mm"] - NPTH_DRILL) > 1e-9 or abs(mh["keepout_dia_mm"] - KEEPOUT_DIA) > 1e-9:
        raise ValueError(f"图纸与 IN-6 常量不符: {mh['drill_mm']}/{mh['keepout_dia_mm']}")
    b = pcbnew.LoadBoard(SRC)
    board_src_sha = sha16(SRC)
    ledger = {"stage": "P4", "increment": 1, "src_board": os.path.relpath(SRC, ROOT),
              "src_sha16": board_src_sha, "spec": spec_name, "spec_sha16": sha16(spec_path),
              "column_x": COLUMN_X, "IN": {}}

    def by_ref(ref):
        return [f for f in b.GetFootprints() if f.GetReference() == ref]

    # ── 阶段 1：只读捕获 + 库封装准备（**不做 board 变更**；pcbnew 代理在 Remove/Add 后会退化）
    META, PRE, PRE_STATS, OLD = {}, {}, {}, {}
    for ref in ("U1", "J6", "J12", "J9", "J11", "J13"):
        OLD[ref] = by_ref(ref)[0]        # 先捕获旧件对象（载库封装后 board 代理会退化）
    for ref in ("U1", "J6", "J12", "J9", "J11", "J13"):
        ft = OLD[ref]
        _pp = ft.GetPosition()
        _nets = {x.GetNumber(): x.GetNetname() for x in ft.Pads() if x.GetNetname()}
        META[ref] = {"x": pcbnew.ToMM(_pp.x), "y": pcbnew.ToMM(_pp.y),
                     "rot": ft.GetOrientationDegrees(), "value": ft.GetValue(),
                     "pads_before": len(list(ft.Pads())), "nets": _nets}
        _lib, _nm = lib_of(drw["devices"][ref]["footprint"])       # land pattern 经图纸解析（禁硬编码）
        new = load_fp(stage_lib(_lib, _nm, ref), _nm)              # 确定性 UUID 暂存库
        new.SetReference(ref)
        new.SetValue(META[ref]["value"])
        if ref in ("J6", "J12", "J9", "J11", "J13"):               # IN-8：排针列 column_x = 27.94
            new.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(COLUMN_X), pcbnew.FromMM(META[ref]["y"])))
        else:
            new.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(META[ref]["x"]), pcbnew.FromMM(META[ref]["y"])))
        new.SetOrientationDegrees(META[ref]["rot"])
        _plist = list(new.Pads())
        for x in _plist:                                            # 按 pad 号迁网（原板 pad 集）
            nn = _nets.get(x.GetNumber())
            if nn:
                x.SetNet(b.FindNet(nn))
        if ref == "U1":                                             # IN-4：EP(49) → GND
            for x in _plist:
                if x.GetNumber() == "49":
                    x.SetNet(b.FindNet("GND"))
        PRE[ref] = new
        PRE_STATS[ref] = {"npads": len(_plist), "nums": sorted(x.GetNumber() for x in _plist)}
    PRE_MH = []
    for _i in range(4):
        _fp = load_fp(stage_lib(MH_LIB, MH_FP, f"H{_i + 1}"), MH_FP)
        _fp.SetReference(f"H{_i + 1}")
        _fp.SetValue(MH_FP)
        _fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(holes[_i][0]), pcbnew.FromMM(holes[_i][1])))
        PRE_MH.append(_fp)      # UUID 由写盘后 canonicalize_uuids() 规范化（本版绑定无 UUID setter）

    # ── IN-12/13/14：**真源补网**（U1 新 pad 34..48 / 5 接口件 pad / U6 侧带球）──
    SUPP_REFS = ("U1", "J6", "J9", "J11", "J12", "J13", "U6")
    SUPP = in5_pad_nets(SUPP_REFS)          # ref → {pad:net}（引脚名→pad 号取符号定义）
    supp_log = {}
    for ref in SUPP_REFS:
        want = SUPP[ref]["pad2net"]
        target = PRE.get(ref) or (by_ref(ref)[0] if by_ref(ref) else None)
        if target is None:
            continue
        n = 0
        for pp in target.Pads():
            num = pp.GetNumber()
            if pp.GetNetname() or num not in want:
                continue
            net = b.FindNet(want[num])
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, want[num])
                b.Add(net)
            pp.SetNet(net)
            n += 1
        supp_log[ref] = {"assigned": n, "candidates": len(want),
                         "note": "U6 = 侧带/未连球（gap E 闭合）" if ref == "U6" else ""}

    # ── IN-5 准备：15 件（13 补件落板 + C73/C86 移位）+ 真源赋网 ───────────
    IN5 = in5_pad_nets(sorted(sol["placed"]))
    NEW_FP, MOVE_FP = {}, {}
    for ref, spec_v in sorted(sol["placed"].items()):
        at, rot = spec_v["at"], float(spec_v.get("rot") or 0.0)
        if by_ref(ref):                                   # 板上已有 ⇒ 移位（C73/C86）
            MOVE_FP[ref] = {"old": by_ref(ref)[0], "at": at, "rot": rot,
                            "pads_before": len(list(by_ref(ref)[0].Pads())),
                            "pad2net": IN5[ref]["pad2net"]}
            continue
        _lib, _nm = lib_of(spec_v["footprint"])            # 封装经落位解解析（禁硬编码）
        fp = load_fp(stage_lib(_lib, _nm, ref), _nm)
        fp.SetReference(ref)
        fp.SetValue(IN5[ref]["value"] or spec_v["footprint"].split(":")[-1])
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(at[0]), pcbnew.FromMM(at[1])))
        fp.SetOrientationDegrees(rot)
        _pl = list(fp.Pads())
        _missing_net = []
        for pp in _pl:
            nn = IN5[ref]["pad2net"].get(pp.GetNumber())
            if not nn:
                continue
            net = b.FindNet(nn)
            if net is None:                                # 板上尚未声明的网 ⇒ 新建
                net = pcbnew.NETINFO_ITEM(b, nn)
                b.Add(net)
            pp.SetNet(net)
        NEW_FP[ref] = fp
        IN5[ref]["npads"] = len(_pl)
        IN5[ref]["pad_nums"] = sorted(x.GetNumber() for x in _pl)

    # ── 阶段 2：board 变更（Remove 旧件 / Add 新件） ──────────────────────
    for ref in ("U1", "J6", "J12", "J9", "J11", "J13"):
        b.Remove(OLD[ref])
        b.Add(PRE[ref])
    u1_pads = set(PRE_STATS["U1"]["nums"])
    missing = sorted(set(str(i) for i in range(1, 50)) - u1_pads, key=lambda x: int(x))
    if missing:
        raise ValueError(f"IN-4 自检 FAIL：U1 仍缺 pad {missing}")
    ledger["IN"]["IN-4"] = {"ref": "U1", "pads_before": META["U1"]["pads_before"],
                            "pads_after": PRE_STATS["U1"]["npads"],
                            "added": [str(i) for i in range(34, 49)], "ep_net": "GND",
                            "nets_migrated": len(META["U1"]["nets"])}
    conn_rows = [{"ref": r, "fp": drw["devices"][r]["footprint"], "pads": PRE_STATS[r]["npads"],
                  "pads_before": META[r]["pads_before"], "x_before": round(META[r]["x"], 3),
                  "x_after": COLUMN_X, "y": round(META[r]["y"], 3)}
                 for r in ("J6", "J12", "J9", "J11", "J13")]
    for ref, fp in sorted(NEW_FP.items()):
        b.Add(fp)
    for ref, mv in sorted(MOVE_FP.items()):
        mv["old"].SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(mv["at"][0]), pcbnew.FromMM(mv["at"][1])))
        mv["old"].SetOrientationDegrees(mv["rot"])
    ledger["IN"]["IN-12"] = {"U1 新 pad 赋网": SUPP["U1"]["pad2net"],
                             "log": supp_log.get("U1")}
    ledger["IN"]["IN-13"] = {"接口件赋网": {r: SUPP[r]["pad2net"] for r in ("J6", "J9", "J11", "J12", "J13")},
                             "log": {r: supp_log.get(r) for r in ("J6", "J9", "J11", "J12", "J13")}}
    ledger["IN"]["IN-14"] = {"U6 侧带球赋网": {"candidates": len(SUPP["U6"]["pad2net"]),
                                              "log": supp_log.get("U6")}}
    ledger["IN"]["IN-5"] = {
        "placed_new": sorted(NEW_FP), "moved": sorted(MOVE_FP),
        "rows": [{"ref": r, "at": sol["placed"][r]["at"], "rot": sol["placed"][r].get("rot", 0.0),
                  "footprint": sol["placed"][r]["footprint"], "pads": IN5[r].get("npads", MOVE_FP.get(r, {}).get("pads_before")),
                  "pad2net": IN5[r]["pad2net"], "unmapped": IN5[r]["unmapped"]} for r in sorted(sol["placed"])],
        "nets_created": [r for r in sorted(IN5) if IN5[r]["unmapped"]]}
    ledger["IN"]["IN-11"] = {"rows": conn_rows, "pads_added": sum(r["pads"] for r in conn_rows)}
    ledger["IN"]["IN-8"] = {"column_x": COLUMN_X, "moved": [r["ref"] for r in conn_rows]}

    # ── IN-6：4×Ø3.2 NPTH + Ø6.0 keepout（8 铜层 rule area） ───────────────
    rows = []
    for i, (hx, hy) in enumerate(holes, start=1):
        fp = PRE_MH[i - 1]
        fp.SetReference(f"H{i}")
        fp.SetValue(MH_FP)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        b.Add(fp)
        rows.append({"hole": f"H{i}", "at": [hx, hy]})
    ledger["IN"]["IN-6"] = {"npth": rows, "drill_mm": NPTH_DRILL, "keepout_dia": KEEPOUT_DIA}

    # 6.1 Ø6.0 keepout rule area（圆，8 铜层；开关：zone_fills/vias/tracks/pads = disallow）
    for i, (hx, hy) in enumerate(holes, start=1):
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        _mk = f"K2_HOLE_KEEPOUT_H{i}"
        if hasattr(z, "SetZoneName"):
            z.SetZoneName(_mk)
        z.SetLayerSet(pcbnew.LSET(pcbnew.LSET.AllCuMask()) if hasattr(pcbnew.LSET, "AllCuMask") else z.GetLayerSet())
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowPads(True)
        import math as _m
        r = pcbnew.FromMM(KEEPOUT_DIA / 2.0)
        c = pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy))
        z.Outline().NewOutline()
        _pts = [(int(c.x + r * _m.cos(_m.radians(a))), int(c.y + r * _m.sin(_m.radians(a))))
                for a in range(0, 360, 10)]
        _pts.append(_pts[0])                      # 显式闭合（本版 SHAPE_POLY_SET 无 CloseLastContour）
        for _x, _y in _pts:
            z.Outline().Append(_x, _y)
        b.Add(z)

    # ── IN-7：4 个无网 ESC_* rule area 开关 ≥1 非 allowed ───────────────────
    esc = []
    for z in b.Zones():
        if z.GetIsRuleArea() and not z.GetNetname() and len(z.GetLayerSet().Seq()) == 1 \
           and b.GetLayerName(z.GetFirstLayer()) == "F.Cu":
            if z.GetDoNotAllowZoneFills():
                continue
            z.SetDoNotAllowZoneFills(True)          # ESC 逃逸区：禁铺铜（其余开关保持 allowed）
            esc.append({"zone": (z.GetZoneName() if hasattr(z, "GetZoneName") else ""), "zone_fills": "disallow"})
    ledger["IN"]["IN-7"] = {"esc_zones_set": len(esc), "rows": esc}

    # ── IN-3：9 铜区填充（C7） ─────────────────────────────────────────────
    b.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    filled, unfilled = [], []
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        n = z.GetFilledPolysList(z.GetFirstLayer()).OutlineCount()
        (filled if n > 0 else unfilled).append({"net": z.GetNetname(),
                                                "layer": b.GetLayerName(z.GetFirstLayer()), "outlines": n})
    ledger["IN"]["IN-3"] = {"copper_zones": len(filled) + len(unfilled), "filled": len(filled),
                            "unfilled": unfilled, "rows": filled}
    if unfilled:
        raise ValueError(f"IN-3 自检 FAIL：未填充铜区 {unfilled}")

    # ── 自检（结构） ───────────────────────────────────────────────────────
    zero_pad = [f.GetReference() for f in b.GetFootprints() if len(list(f.Pads())) == 0]
    npth = sum(1 for f in b.GetFootprints() for p in f.Pads()
               if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)
    ledger["selfcheck"] = {"footprints": len(b.GetFootprints()), "footprints_without_pads": sorted(zero_pad),
                           "npth": npth, "zones_total": len(b.Zones()),
                           "copper_zones_filled": len(filled)}
    if zero_pad:
        raise ValueError(f"自检 FAIL：0 焊盘器件 {zero_pad}")
    _bad = []
    for ref in sorted(sol["placed"]):
        want = IN5[ref]["pad2net"]
        _ft = by_ref(ref)
        if not _ft:
            _bad.append([ref, "missing"])
            continue
        got = {pp.GetNumber(): pp.GetNetname() for pp in _ft[0].Pads()}
        for pn, nn in want.items():
            if got.get(pn) != nn:
                _bad.append([ref, pn, nn, got.get(pn)])
    if _bad:
        raise ValueError(f"自检 FAIL：IN-5 赋网不符 {_bad[:6]}")
    ledger["selfcheck"]["in5_refs"] = len(sol["placed"])
    ledger["selfcheck"]["in5_pad_net_ok"] = True
    if npth < 4:
        raise ValueError(f"自检 FAIL：NPTH = {npth} < 4")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pcbnew.SaveBoard(OUT, b)
    ledger["footprints_sorted"] = sort_footprints(OUT)
    ledger["keepout_zones_sorted"] = sort_new_keepout_zones(OUT)
    _canon_refs = ("U1", "J6", "J9", "J11", "J12", "J13", "H1", "H2", "H3", "H4") + tuple(sorted(NEW_FP))
    ledger["uuid_canonicalized_blocks"] = canonicalize_uuids(OUT, refs=_canon_refs)
    ledger["out_board"] = os.path.relpath(OUT, ROOT) if OUT.startswith(ROOT) else OUT
    ledger["out_sha16"] = sha16(OUT)
    json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in ledger.items() if k in ("selfcheck", "out_board", "out_sha16")},
                     ensure_ascii=False))
    print("IN:", json.dumps({k: (v if k != "IN-6" else {"drill_mm": v["drill_mm"], "n": len(v["npth"])})
                             for k, v in ledger["IN"].items()}, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
