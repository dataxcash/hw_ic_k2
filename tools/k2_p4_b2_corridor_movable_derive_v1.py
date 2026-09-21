#!/usr/bin/env python3
"""K2 · B2 —— **走廊可腾挪集合「规则派生」器 v1**（#K2-71 §2.2 R-orc · 判据 ⑩）。

规则（**非名单** · 直击 #K2-68 O-2 / D-1 之手列病根）：
  走廊区 R = x∈[78,100] · y∈[45,66]（覆盖 F-3 实测阻塞者 x=83–85 + U6 扇出笼）。
  **movable = 区内全部「非冻结对象」**：
    ① 具名信号网之**铜线 + 过孔**（含 `DS320_STRAP_*` **全变体**） ⇒ 输出 `movable_nets`/`movable_copper`
    ② 参考面 **GND / P3V3 之缝合孔**（**仅孔可移 · 铜面不可动**） ⇒ 输出 `movable_stitch`
    ③ 32 条车道（被布线对象）自身之 `F–In5` 过渡孔 —— 由布线器 `--a-sites/--b-sites` 处理，**不入本表**
  **排除（冻结）**：车道网本体（`PCIE_{UP,DN}_OUT*`）· GND/P3V3 铜面 · 元件焊盘（球位/接口位）· 板框。

输出：JSON（名单 + sha16 + 复现命令 + 需求 2/4 之报件），**确定性**（全排序）。
用法：python3 tools/k2_p4_b2_corridor_movable_derive_v1.py --model <dump.json> --out <json>
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import is_lane  # noqa: E402

REGION = (78.0, 45.0, 100.0, 66.0)          # R-orc（#K2-71 §2.2）
REF_PLANE = ("GND", "P3V3", "P3V3_AUX", "PWR_", "MCU_VDD")   # 参考面/电源：仅缝合孔可移


def _seg_in_region(s, R):
    x0, y0, x1, y1 = R
    return (max(s[0], s[2]) >= x0 and min(s[0], s[2]) <= x1
            and max(s[1], s[3]) >= y0 and min(s[1], s[3]) <= y1)


def _pt_in_region(x, y, R):
    return R[0] <= x <= R[2] and R[1] <= y <= R[3]


def _is_refplane(net):
    return net in ("GND", "P3V3") or any(net.startswith(p) for p in ("P3V3", "PWR_", "MCU_VDD", "VREG"))


def _is_diffpair_like(net):
    """差分对 / 时钟 / 等长组成员之粗判（需求 4：移位须同报匹配/等长复核）。"""
    n = net
    return (n.endswith("_P") or n.endswith("_N") or "_P_" in n or "_N_" in n
            or n.startswith(("PCIE", "REFCLK", "USB", "SATA", "DS320")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--region", default=",".join(str(v) for v in REGION))
    a = ap.parse_args()
    R = tuple(float(v) for v in a.region.split(","))
    m = json.load(open(a.model))

    lanes = set()
    refplane_copper, sig_tracks, sig_vias, foreign, pads_in = {}, {}, {}, {}, {}
    for layer, ss in m["segs"].items():
        for s in ss:
            net = s[5]
            if is_lane(net):
                continue
            if not _seg_in_region(s, R):
                continue
            if _is_refplane(net):
                refplane_copper.setdefault(net, 0)
                refplane_copper[net] += 1        # 铜面不可动（仅登记）
                continue
            sig_tracks.setdefault(net, 0)
            sig_tracks[net] += 1
    refplane_stitch, refplane_mpad = {}, {}
    for v in m["vias"]:
        net = v["net"]
        if is_lane(net) or not _pt_in_region(v["x"], v["y"], R):
            continue
        if _is_refplane(net):
            refplane_stitch.setdefault(net, 0)
            refplane_stitch[net] += 1
            continue
        sig_vias.setdefault(net, 0)
        sig_vias[net] += 1
    for p in m["pads"]:
        net = p["net"]
        if is_lane(net) or not _pt_in_region(p["cx"], p["cy"], R):
            continue
        if _is_refplane(net):
            refplane_mpad.setdefault(net, 0)
            refplane_mpad[net] += 1
            continue
        pads_in.setdefault(net, 0)
        pads_in[net] += 1

    mov = sorted(n for n in set(sig_tracks) | set(sig_vias) if not _is_refplane(n))
    stitch = sorted(refplane_stitch)
    need_len = sorted(n for n in mov if _is_diffpair_like(n))
    # 需求 2：报区内「未列入本案」之非常规阻塞者（无网名铜 / 未分类）
    unclassified = {}
    for net in sorted(set(sig_tracks) | set(sig_vias)):
        if net == "" or net.startswith("Net-("):
            unclassified[net] = {"tracks": sig_tracks.get(net, 0), "vias": sig_vias.get(net, 0)}
    out = {
        "artifact": "k2_p4_b2_corridor_movable_derive_v1",
        "authority": "#K2-71 §2.2（R-orc 规则派生口径）· 判据 ⑩",
        "region": list(R),
        "rule": "movable = 区内全部非冻结对象：①具名信号网铜线+过孔 ②GND/P3V3 缝合孔（仅孔）③车道 F–In5 过渡孔（布线器侧）",
        "movable_nets": mov,
        "movable_copper": mov,
        "movable_stitch": stitch,
        "needs_length_recheck": need_len,
        "refplane_copper_census_not_movable": refplane_copper,
        "refplane_pads_in_region": refplane_mpad,
        "frozen": {"lane_nets": "PCIE_{UP,DN}_OUT*（被布线对象）", "refplane_copper": sorted(refplane_copper),
                   "component_pads": "元件终止（球位/接口位）· 冻结", "board_outline": "冻结"},
        "new_entries_required_by_rule": unclassified,
        "counts": {"mov_nets": len(mov), "mov_stitch": len(stitch), "tracks": sum(sig_tracks.values()),
                   "vias": sum(sig_vias.values()), "pads_frozen_in_region": sum(pads_in.values()),
                   "refplane_stitch": sum(refplane_stitch.values())},
        "cmd": ("python3 tools/k2_p4_b2_in5_lane_router_v3.py --model <dump.json> --out <wo.json> "
                "--cell 0.10 --a-sites <sites.json> --margin 0.100 "
                "--movable-nets \"%s\" --movable-copper \"%s\" --movable-stitch \"%s\""
                % (",".join(mov), ",".join(mov), ",".join(stitch))),
        "self_sha16": "见文件 sha256 前 16 位",
    }
    js = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True)
    open(a.out, "w").write(js)
    print("movable_nets(%d): %s" % (len(mov), ",".join(mov)))
    print("movable_stitch(%d): %s" % (len(stitch), ",".join(stitch)))
    print("needs_length_recheck(%d): %s" % (len(need_len), ",".join(need_len)))
    print("new_entries_required_by_rule:", unclassified)
    print("counts:", out["counts"])
    print("wrote", a.out, "sha16", hashlib.sha256(js.encode()).hexdigest()[:16])


if __name__ == "__main__":
    main()
