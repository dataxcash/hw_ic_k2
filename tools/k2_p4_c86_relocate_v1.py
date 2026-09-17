#!/usr/bin/env python3
"""K2 P4 · **C86 重落位 + 平面接入 v1**（L2：placement/机械 + 布线/过孔策略）—— 清除 C86 ⊂ U2 实体碰撞。

依据：`k2/docs/K2-P4-C86-COLLISION-DEFECT-v1.md`（D-1）。落位解 `p3_placement_solution.json` 的
`selfcheck` 未把「既有封装本体」列为障碍，导致 C86 落在 U2（SOIC-8 双排）本体之内。
本工具按「原约束（inset 0.3 / pad 净距 0.2 / 件间距 0.5 / 孔禁布 φ6）+ **既有封装本体不重叠**」重落 C86：
  ① 移 C86 到合法位；② 每 pad 加 1 支**同网通孔**（复制板内既有同类 via）+ 1 段 0/45/90° 引线接平面；
  ③ 清理原 pad 处的孤立走线；④ `ZONE_FILLER` 重填 + `kicad-cli` DRC 复算（复用 W-7 `delta_ok`）+ 嵌套扫描须 0。
默认只写 work-dir；`--apply` 才写仓库板（此时走 T-22 备份 + 同名 pro 逐字节校验）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_c86_relocate_v1.py \
    --board <板> --pro <同名 pro> --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/c86 [--x 31.55 --y 58.85]
"""
import argparse
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W

NM = 1_000_000
SEED = 20260918
REF = "C86"
TRACE_W = 200_000
VIA_OFF = 775_000
END_TOL = 2_000


def v2(x, y):
    return pcbnew.VECTOR2I(int(round(x)), int(round(y)))


def delta_ok_nonregress(rep_b, rep_a):
    """本增量闸：无新类型 / 无类型增量 / error 0 / unconnected 0（**不要求总量下降**）。"""
    bad = []
    hb, ha = W.type_hist(rep_b), W.type_hist(rep_a)
    for t in sorted(set(hb) | set(ha)):
        if ha.get(t, 0) > hb.get(t, 0):
            bad.append(f"{t}:{hb.get(t, 0)}->{ha.get(t, 0)}")
    for v in rep_a.get("violations", []):
        if v["severity"] == "error":
            bad.append(f"error:{v['type']}")
    if W.unconn(rep_a) > 0:
        bad.append(f"unconnected:{W.unconn(rep_a)}")
    return bad


def make_via(bd, net, pos):
    """优先复制板内同网通孔（保证孔类/盘径/层跨与板内既有完全一致）。"""
    tmpl = None
    for t in bd.GetTracks():
        if W.is_via(t) and t.GetNetname() == net:
            layers = [l for l in t.GetLayerSet().Seq()]
            if pcbnew.F_Cu in layers and pcbnew.B_Cu in layers:
                tmpl = t
                break
    if tmpl is not None:
        nv = tmpl.Duplicate()
        nv.SetPosition(v2(*pos))
        bd.Add(nv)
        return nv, "cloned"
    nv = pcbnew.PCB_VIA(bd)
    nv.SetPosition(v2(*pos))
    nv.SetDrill(200_000)
    nv.SetWidth(350_000)
    nv.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    nv.SetNet(bd.FindNet(net))
    bd.Add(nv)
    return nv, "constructed"


def mutate(bd, target, drop_stubs=True, via_off=None, silk_idx=None):
    fp = next((f for f in bd.GetFootprints() if f.GetReference() == REF), None)
    if fp is None:
        raise RuntimeError(f"{REF} not found")
    old = [(p.GetPadName(), p.GetPosition().x, p.GetPosition().y, p.GetNetname()) for p in fp.Pads()]
    fp.SetPosition(v2(*target))
    made = {"moved": {"ref": REF, "to": [int(target[0]), int(target[1])]}, "vias": [], "traces": []}
    for p in fp.Pads():
        pp, net = p.GetPosition(), p.GetNetname()
        # 方向 = 远离本体中心（pad1 西 / pad2 东）
        cx = fp.GetPosition().x
        dirn = -1 if pp.x <= cx else 1
        vpos = (pp.x + dirn * (VIA_OFF if via_off is None else via_off), pp.y)
        nv, how = make_via(bd, net, vpos)
        made["vias"].append({"pad": p.GetPadName(), "net": net, "at": [vpos[0], vpos[1]],
                             "drill_nm": int(nv.GetDrillValue()), "how": how})
        tr = pcbnew.PCB_TRACK(bd)
        tr.SetStart(pcbnew.VECTOR2I(pp.x, pp.y))
        tr.SetEnd(v2(*vpos))
        tr.SetWidth(TRACE_W)
        tr.SetLayer(pcbnew.F_Cu)
        tr.SetNet(bd.FindNet(net))
        bd.Add(tr)
        made["traces"].append({"pad": p.GetPadName(), "net": net,
                               "from": [pp.x, pp.y], "to": [vpos[0], vpos[1]]})
    if drop_stubs:
        killed = []
        for t in list(bd.GetTracks()):
            if not W.is_track(t):
                continue
            s, e = t.GetStart(), t.GetEnd()
            for name, px, py, net in old:
                if t.GetNetname() != net:
                    continue
                if ((abs(s.x - px) <= END_TOL and abs(s.y - py) <= END_TOL)
                        or (abs(e.x - px) <= END_TOL and abs(e.y - py) <= END_TOL)):
                    killed.append([W.uid(t)[:8], pcbnew.LayerName(t.GetLayer())])
                    bd.RemoveNative(t)
                    break
        made["dropped_stubs"] = killed
    if silk_idx is not None:
        fu = None
        for fl in fp.GetFields():
            try:
                if fl.GetName() == "Reference":
                    fu = W.uid(fl)
                    break
            except Exception:
                pass
        if fu is None:
            raise RuntimeError("C86 Reference field not found")
        cands, meta = W.silk_plan(bd, fu)
        if not cands:
            raise RuntimeError("no silk candidate for C86 Reference")
        cfg = cands[min(silk_idx, len(cands) - 1)]
        W.mutate_silk_cfg(fu, cfg)(bd, None)
        made["silk"] = {"n_cands": len(cands), "idx": silk_idx,
                        "text_mm": cfg["text_mm"], "angle": cfg["angle_deg"],
                        "pos": list(cfg["pos"]), "shift_nm": cfg["shift_nm"]}
    return made


def nested_hits(bd, ref=None):
    def env(f):
        xs, ys = [], []
        for p in f.Pads():
            pp, sz = p.GetPosition(), p.GetSize()
            xs += [pp.x - sz.x / 2, pp.x + sz.x / 2]
            ys += [pp.y - sz.y / 2, pp.y + sz.y / 2]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None
    fps = list(bd.GetFootprints())
    E = {f.GetReference(): env(f) for f in fps}
    P = {f.GetReference(): len(list(f.Pads())) for f in fps}
    out = []
    for f in fps:
        ea = E[f.GetReference()]
        if not ea:
            continue
        for g in fps:
            eb = E[g.GetReference()]
            if not eb or f is g or P[g.GetReference()] < 4:
                continue
            if eb[0] < ea[0] and eb[1] < ea[1] and eb[2] > ea[2] and eb[3] > ea[3]:
                out.append({"inner": f.GetReference(), "outer": g.GetReference()})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--x", type=float, default=31.55)
    ap.add_argument("--y", type=float, default=58.85)
    ap.add_argument("--silk-idx", default="0,1,2,3",
                    help="逗号分隔：对 C86 位号施加 silk 候选的序号（-1 = 不改位号）")
    ap.add_argument("--positions", default=None,
                    help="分号分隔 x,y 候选（默认用内置候选表）")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    try:
        pcbnew.KIID.SeedGenerator(SEED)
    except Exception:
        pass
    board_src, pro_src = os.path.abspath(a.board), os.path.abspath(a.pro)
    work = os.path.abspath(a.work_dir)
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(board_src))[0]
    if a.apply:
        src_pro_bytes = open(pro_src, "rb").read()
        shutil.copy2(board_src, os.path.join(work, stem + ".src-backup.kicad_pcb"))
        shutil.copy2(pro_src, os.path.join(work, stem + ".pro-backup.kicad_pro"))
    base = W.stage(board_src, pro_src, work, stem)
    probe = os.path.join(work, stem + ".kicad_pro")
    r0 = W.run_drc(a.kicad_cli, base, os.path.join(work, "drc_before.json"))
    rep_out = {"src": {"board": board_src, "board_sha16": W.sha16(board_src),
                       "pro": pro_src, "pro_sha16": W.sha16(pro_src)},
               "target_mm": [a.x, a.y],
               "before": {"counts": W.counts(r0), "unconnected": W.unconn(r0),
                          "nested": nested_hits(pcbnew.LoadBoard(base), REF)},
               "attempts": []}
    if a.positions:
        cand_pos = [tuple(float(t) for t in z.split(",")) for z in a.positions.split(";") if z]
    else:
        cand_pos = [(a.x, a.y)]
    ok_done = False
    silk_idxs = [None if int(x) < 0 else int(x) for x in a.silk_idx.split(",") if x != ""]
    combos = []
    for pos in cand_pos:
        for si in silk_idxs:
            combos.append((pos, VIA_OFF, True, si))
    combos += [(cand_pos[0], VIA_OFF, False, si) for si in silk_idxs[:2]]
    for pos, off, drop, si in combos:
        bd = pcbnew.LoadBoard(base)
        try:
            rec = mutate(bd, (pos[0] * NM, pos[1] * NM), drop_stubs=drop, via_off=off, silk_idx=si)
        except Exception as e:
            rep_out["attempts"].append({"drop_stubs": drop, "via_off_nm": off, "target_mm": list(pos), "silk_idx": si, "error": str(e)})
            continue
        W.refill(bd)
        tag = f"cand_{pos[0]:.2f}_{pos[1]:.2f}_off{off//1000}_d{int(drop)}_s{si}".replace(".", "p")
        cand = os.path.join(work, "_" + tag + ".kicad_pcb")
        W.save_with_pro(bd, cand, probe)
        rc = W.run_drc(a.kicad_cli, cand, cand + ".json")
        bad = delta_ok_nonregress(r0, rc)
        nest = nested_hits(pcbnew.LoadBoard(cand), REF)
        if nest:
            bad = list(bad) + [f"nested:{[h['inner']+'<'+h['outer'] for h in nest]}"]
        rec["drop_stubs"] = drop
        rec["via_off_nm"] = off
        rec["target_mm"] = [pos[0], pos[1]]
        rec["silk_idx"] = si
        rec["after_counts"] = W.counts(rc)
        rec["unconnected"] = W.unconn(rc)
        rec["nested"] = nest
        rec["rejected"] = bad
        rep_out["attempts"].append(rec)
        if not bad:
            final = os.path.join(work, stem + ".c86-relocated.kicad_pcb")
            shutil.copy2(cand, final)
            shutil.copy2(cand.replace(".kicad_pcb", ".kicad_pro"),
                         os.path.splitext(final)[0] + ".kicad_pro")
            rep_out["after"] = {"counts": W.counts(rc), "unconnected": W.unconn(rc),
                                "nested": nest, "board": final, "board_sha16": W.sha16(final)}
            ok_done = True
            break
    if not ok_done:
        rep_out["after"] = None
    if a.apply and ok_done:
        shutil.copy2(rep_out["after"]["board"], board_src)
        if open(pro_src, "rb").read() != src_pro_bytes:
            shutil.copy2(os.path.join(work, stem + ".pro-backup.kicad_pro"), pro_src)
            raise RuntimeError("pro 字节被改动，已回滚")
        rep_out["applied"] = {"board_sha16": W.sha16(board_src),
                              "pro_sha16": W.sha16(pro_src), "pro_unchanged": True}
    out = a.report or os.path.join(work, "c86_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep_out, fh, indent=1, ensure_ascii=False)
    print(json.dumps({k: rep_out[k] for k in ("before", "after") if k in rep_out}, indent=1, ensure_ascii=False))
    for at in rep_out["attempts"]:
        print("attempt at=%s off=%s drop=%s silk=%s -> %s" % (at.get("target_mm"), at.get("via_off_nm"), at.get("drop_stubs"), at.get("silk_idx"), at.get("rejected") or "ACCEPT"))
    print("report:", out)
    return 0 if ok_done else 1


if __name__ == "__main__":
    sys.exit(main())
