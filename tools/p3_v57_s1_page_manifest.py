#!/usr/bin/env python3
"""P3 v57 S1 — 图纸页清单派生（设计细案 m13_v57_s1_generator_design.md §0.1 机器落地）。

输出：m13_v57_s1_page_manifest.json —— 34 页：(base, segname) 键 / 差分对 P/N /
出逃侧 / 走廊与带 / 双端权威锚 / 源指纹。双跑逐字节一致（A0.1 同款纪律）。

输入（只读单向，authority-first；零 x-window / 零 max-x / 零板文件反猜）：
  1. m13_v57_s0_endpoint_model.json —— chip 锚(expect_xy/ball/ball_grid) + 连接器
     锚(at_global_est/pad_num)，以及 68 网两侧归属；
  2. k2_sch.yaml 网表 —— PCIE_REFCLK{k} 双连接器端（J2 与 J3/J4）成员（S0 模型只
     录 conn_pin 单侧；J2 侧补录用与 S0 完全相同的「网名→pad」join，非几何反猜）；
  3. 连接器 J2 的 REFCLK pad 位：以网名 join 板上 pad（S0 connector audit 同款
     「pad#↔网名 库/手册派生实现读取」；仅取 REFCLK 两网、不扫窗口）。

页键派生（判别只用网名 + 连接器侧，见 docstring 分类表）：
  PCIE_DN{k}_{P|N}            → base PCIE_DN{k} / segname input  (J2 TX ↔ chip A_PER, 东)
  PCIE_DN_OUT{k}_{P|N}_MCIO   → base PCIE_DN{k} / segname out_MCIO (chip A_PET ↔ J3/J4 RX, 西)
  PCIE_UP{k}_{P|N}            → base PCIE_UP{k} / segname input   (J3/J4 TX ↔ chip B_PER, 西)
  PCIE_UP_OUT{k}_{P|N}_J2     → base PCIE_UP{k} / segname out_J2  (chip B_PET ↔ J2 RX, 东)
  PCIE_REFCLK{k}_{P|N}        → base PCIE_REFCLK{k} / segname input (J2 ↔ J3|J4 直通)
"""
import hashlib
import json
import re
from pathlib import Path

import yaml  # noqa: E402

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
EP_MODEL = STEP2 / "m13_v57_s0_endpoint_model.json"
SCH = K2 / "boards" / "k2_sch.yaml"
BOARD = K2 / "k2_v4.kicad_pcb"
OUT = STEP2 / "m13_v57_s1_page_manifest.json"

# ---- 页键分类（纯网名判别） -------------------------------------------------
_P_N = re.compile(r"^PCIE_REFCLK(\d+)_([PN])$")
_DN = re.compile(r"^PCIE_DN(\d+)_([PN])$")
_DN_OUT = re.compile(r"^PCIE_DN_OUT(\d+)_([PN])_MCIO$")
_UP = re.compile(r"^PCIE_UP(\d+)_([PN])$")
_UP_OUT = re.compile(r"^PCIE_UP_OUT(\d+)_([PN])_J2$")


def classify(net: str):
    """→ (base, segname, kind, pol) | None。"""
    for rx, base_pat, seg, kind in (
            (_P_N, "PCIE_REFCLK", "input", "refclk_pass"),
            (_DN_OUT, "PCIE_DN", "out_MCIO", "data"),
            (_UP_OUT, "PCIE_UP", "out_J2", "data"),
            (_DN, "PCIE_DN", "input", "data"),
            (_UP, "PCIE_UP", "input", "data")):
        m = rx.match(net)
        if m:
            if base_pat == "PCIE_REFCLK":
                base = f"PCIE_REFCLK{m.group(1)}"
            else:
                base = f"{base_pat}{m.group(1)}"
            return base, seg, kind, m.group(2)
    return None


def rot90(lx, ly, rot):
    import math
    r = math.radians(-rot)
    return (lx * math.cos(r) - ly * math.sin(r),
            lx * math.sin(r) + ly * math.cos(r))


def block_at(s, start):
    depth, i = 0, start
    while i < len(s):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
        i += 1
    return s[start:]


def conn_pad_global(ref: str, net: str):
    """S0 同款「网名→连接器 pad」join：net 在 ref 上的 pad 全局坐标。
    仅用于 S0 模型缺失的 REFCLK J2 侧（连接器实现读取，非窗口反猜）。"""
    import re as _re
    txt = BOARD.read_text()
    for m in _re.finditer(r"\(footprint ", txt):
        blk = block_at(txt, m.start())
        props = dict(_re.findall(r'\(property "([^"]+)" "([^"]+)"', blk))
        if props.get("Reference") != ref:
            continue
        at = _re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", blk)
        ax, ay, arot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        for pm in _re.finditer(r"\(pad ", blk):
            pblk = block_at(blk, pm.start())
            num = _re.search(r'\(pad "([^"]*)"', pblk)
            pat = _re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", pblk)
            pnet = _re.search(r'\(net (?:\d+\s+)?"([^"]*)"\)', pblk)
            if num and pat and pnet and pnet.group(1) == net:
                gx, gy = rot90(float(pat.group(1)), float(pat.group(2)), arot)
                return {"num": num.group(1), "at_global": [round(ax + gx, 3),
                                                           round(ay + gy, 3)]}
    return None


def main() -> int:
    ep = json.load(open(EP_MODEL))
    chip = {d["net"]: d for d in ep["details"]["chip"] if d.get("kind") != "pass_through"}
    conn = {c["net"]: c for c in ep["details"]["connector"]}

    # 网表：REFCLK 双端 + 数据网 chip/conn 成员（cross-check 用）
    sch = yaml.safe_load(open(SCH))
    nets = sch["nets"]

    pages: dict = {}
    order = []

    def page_of(base, seg, kind):
        key = f"{base}/{seg}"
        if key not in pages:
            pages[key] = {"page_id": key, "base": base, "segname": seg,
                          "kind": kind, "nets": {}, "anchors": {}}
            order.append(key)
        return pages[key]

    # ---- 数据页（chip ↔ 连接器） ----
    for net, d in sorted(chip.items()):
        cl = classify(net)
        if cl is None or cl[2] != "data":
            continue
        base, seg, _, pol = cl
        c = conn.get(net)
        if c is None or not c.get("board_pad") or not c["board_pad"].get("at_global_est"):
            raise SystemExit(f"FAIL: 连接器锚缺失 {net}")
        pg = page_of(base, seg, "data")
        pg["nets"][pol] = net
        # 侧向/走廊：与设计细案表一致（网名 + 连接器 ref 判别）
        conn_ref = c["ref"]
        if base.startswith("PCIE_DN"):
            side, cid, band = ("east", "EAST_CHIP_TO_J2", "dn") if seg == "input" else \
                              ("west", "WEST_MCIO_TO_CHIP", "dn")
        else:
            side, cid, band = ("west", "WEST_MCIO_TO_CHIP", "up") if seg == "input" else \
                              ("east", "EAST_CHIP_TO_J2", "up")
        pg.setdefault("side", side)
        pg.setdefault("corridor", {"id": cid, "band": band})
        pg["anchors"].setdefault("chip", {})[pol] = {
            "net": net, "ball": d["ball"], "ball_grid": d["ball_grid"],
            "pad_global": d["expect_xy"], "source": "s0_endpoint_model.chip_audit"}
        pg["anchors"].setdefault("conn", {})[pol] = {
            "net": net, "ref": conn_ref, "pin": c["pin"], "pad_num": c["board_pad"]["num"],
            "pad_global": c["board_pad"]["at_global_est"],
            "source": "s0_endpoint_model.connector_audit"}

    # ---- REFCLK 页（双连接器直通） ----
    for net, c in sorted(conn.items()):
        cl = classify(net)
        if cl is None or cl[2] != "refclk_pass":
            continue
        base, seg, _, pol = cl
        pg = page_of(base, seg, "refclk_pass")
        pg["nets"][pol] = net
        pg.setdefault("side", "pass")
        pg.setdefault("corridor", {"id": "EAST+WEST_CHIP_TO_CONN", "band": "refclk"})
        # 该网另一连接器端 = 网表成员里 ref 不同于 audit 侧的那个
        members = nets.get(net) or []
        refs = [m.split("/")[0] for m in members if "/" in m]
        other_ref = next((r for r in refs if r != c["ref"]), None)
        other = None
        if other_ref:
            other = conn_pad_global(other_ref, net)
        if other is None:
            raise SystemExit(f"FAIL: REFCLK {net} 第二连接器端缺锚")
        pg["anchors"].setdefault("conn", {})[pol] = {
            "net": net, "ref": c["ref"], "pin": c["pin"], "pad_num": c["board_pad"]["num"],
            "pad_global": c["board_pad"]["at_global_est"],
            "source": "s0_endpoint_model.connector_audit"}
        pg["anchors"].setdefault("conn2", {})[pol] = {
            "net": net, "ref": other_ref, "pad_num": other["num"],
            "pad_global": other["at_global"],
            "source": "s0_method_net_join(REFCLK 第二端补录)"}

    # ---- 装配报告 ----
    manifest = {
        "artifact": "m13_v57_s1_page_manifest",
        "basis": "m13_v57_s1_generator_design.md §0.1",
        "inputs_sha": {
            "s0_endpoint_model": hashlib.sha256(EP_MODEL.read_bytes()).
            hexdigest(),
            "sch": hashlib.sha256(SCH.read_bytes()).hexdigest(),
        },
        "authority": ["S0 权威端点模型(网表×ballmap×放置)", "k2_sch 网表 REFCLK 双端成员"],
        "n_pages": len(pages),
        "tally": {"data_input": sum(1 for p in pages.values() if p["kind"] == "data"
                                    and p["segname"] == "input"),
                  "data_out_mcio": sum(1 for p in pages.values()
                                       if p["segname"] == "out_MCIO"),
                  "data_out_j2": sum(1 for p in pages.values()
                                     if p["segname"] == "out_J2"),
                  "refclk_pass": sum(1 for p in pages.values()
                                     if p["kind"] == "refclk_pass")},
        "pages": [pages[k] for k in sorted(order)],
    }
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")

    # 完整性断言
    assert len(pages) == 34, f"页数 {len(pages)} != 34"
    for k, pg in pages.items():
        assert pg["nets"].get("P") and pg["nets"].get("N"), f"{k} P/N 缺"
        if pg["kind"] == "data":
            assert pg["anchors"].get("chip", {}).get("P") and \
                pg["anchors"]["chip"].get("N"), f"{k} chip 锚缺"
            assert pg["anchors"].get("conn", {}).get("P") and \
                pg["anchors"]["conn"].get("N"), f"{k} conn 锚缺"
        else:
            assert pg["anchors"].get("conn", {}).get("P") and \
                pg["anchors"]["conn"].get("N") and \
                pg["anchors"].get("conn2", {}).get("P") and \
                pg["anchors"]["conn2"].get("N"), f"{k} REFCLK 双连接器锚缺"

    print(json.dumps({"n_pages": manifest["n_pages"], "tally": manifest["tally"],
                      "sha_inputs": manifest["inputs_sha"]}, indent=1,
                      ensure_ascii=False))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
