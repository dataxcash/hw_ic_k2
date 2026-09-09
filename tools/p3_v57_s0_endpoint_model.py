#!/usr/bin/env python3
"""P3 v57 S0 — 权威端点模型 + 单向审计（图纸层铁律 L4 落地第一步）。

权威链（上游→下游，只此方向）：
  k2_sch 网表（连接性：68 网 × 双端 connector-pin / chip-ball）
  + DS320 ballmap（芯片球局部几何，数据手册派生）
  + placement（U6/J2/J3/J4 板上 at/rot）
  + 连接器 SFF/MCIO pad 布局（板上 pad# ↔ 网名，库/手册派生）
  → 权威双端几何（板坐标系）

单向审计（派生一致性报告，不产生正确性）：
  - 芯片侧：期望球位 = transform(ballmap, U6 placement) vs 板上该网 pad 实测位
  - 连接器侧：网表 pin 网名 vs 板上 pad 网名/pad#（旁证）
  - escape_spec / 既有图纸行不在本模型输入内（它们是被审对象，另步审）

输出：m13_v57_s0_endpoint_model.json（机器可复现，含来源指纹）。
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
SCH = K2 / "boards" / "k2_sch.yaml"
BOARD = K2 / "k2_v4.kicad_pcb"
BALLMAP = STEP2 / "ds320pr1601_ballmap.json"
OUT = STEP2 / "m13_v57_s0_endpoint_model.json"
import yaml  # noqa: E402


def block_at(s: str, start: int) -> str:
    depth = 0
    i = start
    while i < len(s):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
        i += 1
    return s[start:]


def fp_blocks(txt: str):
    """(footprint ...) 顶层块迭代，返回 (block, header_dict)。"""
    for m in re.finditer(r"\(footprint ", txt):
        blk = block_at(txt, m.start())
        props = dict(re.findall(r'\(property "([^"]+)" "([^"]+)"', blk))
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", blk)
        yield blk, props, at


def parse_pads(blk: str):
    """footprint 块内 pads: 每 pad → {num, at(local x,y), net}。"""
    out = []
    for pm in re.finditer(r"\(pad ", blk):
        pblk = block_at(blk, pm.start())
        num = re.search(r'\(pad "([^"]*)"', pblk)
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", pblk)
        net = re.search(r'\(net (?:\d+\s+)?\"([^"]*)\"\)', pblk)
        if num and at:
            out.append({"num": num.group(1),
                        "x": float(at.group(1)), "y": float(at.group(2)),
                        "rot": float(at.group(3) or 0.0),
                        "net": net.group(1) if net else None})
    return out


def rot90(lx, ly, rot):
    # KiCad 存储 rot(如 90) ↔ 数学约定 −rot（已用 A_PERP0 球实证）
    import math
    r = math.radians(-rot)
    return (lx * math.cos(r) - ly * math.sin(r),
            lx * math.sin(r) + ly * math.cos(r))


def main() -> int:
    # 1. 网表连接性（权威）
    sch = yaml.safe_load(open(SCH))
    nets = sch["nets"]
    sig = sorted(k for k in nets
                 if k.startswith(("PCIE", "REFCLK"))
                 and isinstance(nets[k], list) and len(nets[k]) == 2)
    conn = []
    for k in sig:
        a, b = nets[k]
        conn.append({"net": k, "conn_pin": a if a.split("/")[0].startswith("J")
                     else b, "chip_ball": b if b.split("/")[0].startswith("U")
                     else a})

    # 2. ballmap（权威芯片局部几何）
    bm = json.load(open(BALLMAP))
    balls = {b["signal"]: b for b in bm["ballmap"]}

    # 3. 板文件 footprint（placement 是既定输入；pad 几何=库派生实现）
    txt = BOARD.read_text()
    fps = {}
    for blk, props, at in fp_blocks(txt):
        ref = props.get("Reference")
        if ref in ("U6", "J2", "J3", "J4"):
            fps[ref] = {"at": (float(at.group(1)), float(at.group(2)),
                               float(at.group(3) or 0.0)),
                        "pads": parse_pads(blk),
                        "footprint": props.get("Value", "?")}

    def pad_of(ref, net):
        for p in fps[ref]["pads"]:
            if p["net"] == net:
                return p
        return None

    audit = {"chip": [], "connector": []}
    for c in conn:
        net = c["net"]
        conn_ref = c["conn_pin"].split("/")[0]
        pin = c["conn_pin"].split("/")[1]
        cpad = pad_of(conn_ref, net)
        audit["connector"].append({"net": net, "ref": conn_ref,
                                   "pin": pin,
                                   "board_pad": cpad and {
                                       "num": cpad["num"],
                                       "at_global_est": None},
                                   "net_on_board": cpad is not None})
        if cpad is not None:
            ax, ay, arot = fps[conn_ref]["at"]
            gx, gy = rot90(cpad["x"], cpad["y"], arot)
            audit["connector"][-1]["board_pad"]["at_global_est"] = [
                round(ax + gx, 3), round(ay + gy, 3)]
        ball = c["chip_ball"].split("/")[1]
        if net.startswith("PCIE_REFCLK"):
            # REFCLK 直通不经芯片（网表 J2↔J3/J4）：无芯片球，属 pass-through
            audit["chip"].append({"net": net, "kind": "pass_through",
                                  "conn_pin": c["conn_pin"]})
            continue
        bl = balls.get(ball)
        chip_pad = pad_of("U6", net)
        chip_ok = None
        num_ok = None
        if bl is not None and chip_pad is not None:
            ax, ay, arot = fps["U6"]["at"]
            ex, ey = rot90(bl["x_mm"], bl["y_mm"], arot)
            exb, eyb = round(ax + ex, 3), round(ay + ey, 3)
            pxb, pyb = rot90(chip_pad["x"], chip_pad["y"], arot)
            pxb, pyb = round(ax + pxb, 3), round(ay + pyb, 3)
            chip_ok = (abs(exb - pxb) <= 0.05 and abs(eyb - pyb) <= 0.05)
            num_ok = chip_pad["num"] == bl["name"]
            audit["chip"].append({"net": net, "ball": ball,
                                  "ball_grid": bl["name"],
                                  "ballmap_xy": [bl["x_mm"], bl["y_mm"]],
                                  "expect_xy": [exb, eyb],
                                  "board_pad_xy": [pxb, pyb],
                                  "match": chip_ok,
                                  "pad_num_matches_ball": num_ok})
        else:
            audit["chip"].append({"net": net, "ball": ball,
                                  "missing": (bl is None, chip_pad is None)})

    report = {
        "artifact": "m13_v57_s0_endpoint_model",
        "authority": ["k2_sch 网表连接性", "ds320pr1601_ballmap(数据手册)",
                      "U6/J2/J3/J4 placement(既定输入)",
                      "板上 pad# ↔ 网名(库/手册派生，仅作实现读取)"],
        "inputs_sha": {
            "sch": hashlib.sha256(SCH.read_bytes()).hexdigest()[:12],
            "ballmap": hashlib.sha256(BALLMAP.read_bytes()).hexdigest()[:12],
            "board": hashlib.sha256(BOARD.read_bytes()).hexdigest()[:12],
        },
        "connectivity": {"n_nets": len(conn)},
        "board_footprints": {r: {"at": fps[r]["at"],
                                 "footprint": fps[r]["footprint"],
                                 "n_pads": len(fps[r]["pads"])}
                             for r in ("U6", "J2", "J3", "J4")},
        "chip_audit": {
            "data_checked": sum(1 for a in audit["chip"]
                                if not a.get("kind") == "pass_through"),
            "data_match": sum(1 for a in audit["chip"]
                              if a.get("match") is True),
            "pad_num_match": sum(1 for a in audit["chip"]
                                 if a.get("pad_num_matches_ball") is True),
            "pass_through": sum(1 for a in audit["chip"]
                                if a.get("kind") == "pass_through"),
            "mismatch_or_missing":
                [a for a in audit["chip"]
                 if a.get("kind") != "pass_through"
                 and not a.get("match")],
        },
        "connector_audit": {
            "checked": len(audit["connector"]),
            "net_present": sum(1 for a in audit["connector"]
                               if a.get("net_on_board")),
            "missing_net": [a for a in audit["connector"]
                            if not a.get("net_on_board")],
        },
        "details": audit,
    }
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    chip_ok = (report["chip_audit"]["data_checked"] > 0
               and report["chip_audit"]["data_match"] ==
               report["chip_audit"]["data_checked"])
    conn_ok = (report["connector_audit"]["missing_net"] == [])
    print(json.dumps({
        "connectivity": report["connectivity"],
        "board_footprints": report["board_footprints"],
        "chip_audit": {k: report["chip_audit"][k] for k in
                       ("data_checked", "data_match", "pad_num_match",
                        "pass_through")},
        "chip_all_match": chip_ok,
        "connector_net_present": report["connector_audit"]["net_present"],
        "connector_ok": conn_ok,
    }, indent=1, ensure_ascii=False))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
