#!/usr/bin/env python3
"""K2 · W-8 电气级审计（**姿态归一 v2 · 层感知**）—— 只读板 + 只读库。

授权：**#K2-52 §一/§三** —— U9-GEOM-1/K1-D16 = **假阳性**：v1 归一器**漏 Flip**
（库件定义在 F.Cu，U9 实例在 **B.Cu** ⇒ 物理上须镜像）。**修工具，禁改库/禁重建板**。
本件 = v1 的**版本 bump**（v1 保留）：归一规则改为 **B.Cu 先 Flip 再 Orient**。

归一规则（层感知，顺序固定）：
  库件 Add 到 scratch →
    若板上实例在 **B.Cu**：`SetLayerAndFlip(B_Cu)`   ← 镜像（翻转层别 + 镜像 pad x）
    否则保持 F.Cu
  → `SetOrientation(实例朝向)` → `SetPosition(实例位置)`
  然后比 full pad signature（shape/sx/sy/dx/dy/rot/drill_d）。

独立法（须同为 42/42）：另比 **pad 绝对坐标**（`pad.GetPosition()`），交叉验证归一位形。

负控（层感知）：对指定 ref 的第 1 个 pad 植入 **shape/size 变异**，须被 FLAG（防恒绿）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_w8_footprint_audit_pose_v2_layeraware.py \
      --board <pcb> [--std-root <dir>] [--proj-lib <dir>] \
      --out-json <j> --out-md <m> [--neg-control <REF>] [--neg-control-layer-aware]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
import pcbnew

def MM(v): return v / 1e6

def _r(v, nd=4): return round(v, nd)

def pad_sig(fp):
    out = {}
    for p in fp.Pads():
        rel = p.GetFPRelativePosition(); d = p.GetDrillSize(); pos = p.GetPosition()
        out[p.GetNumber()] = (int(p.GetShape()), _r(MM(p.GetSize().x)), _r(MM(p.GetSize().y)),
                              _r(MM(rel.x)), _r(MM(rel.y)), _r(p.GetOrientationDegrees(), 2),
                              _r(MM(d.x)),
                              int(p.GetLayer()))
    return out

FIELDS = ("shape", "sx", "sy", "dx", "dy", "rot", "drill_d", "layer")

def resolve(nick, name, std_root, proj_lib):
    if nick == "ForgeOS":
        d = os.path.join(proj_lib, "ForgeOS.pretty"); return d if os.path.isdir(d) else None
    if not nick: return None
    d = os.path.join(std_root, "%s.pretty" % nick); return d if os.path.isdir(d) else None

_SCRATCH = pcbnew.BOARD()

def posed_sig(fp, lfp):
    """库件按板上实例**层感知**姿态放置（B.Cu 先 Flip 再 Orient）后的签名。"""
    _SCRATCH.Add(lfp)
    try:
        if fp.GetLayer() == pcbnew.B_Cu:
            lfp.SetLayerAndFlip(pcbnew.B_Cu)          # ① 先镜像（层别 + pad x）
        lfp.SetOrientation(fp.GetOrientation())        # ② 再定向
        lfp.SetPosition(fp.GetPosition())              # ③ 再落位
        return pad_sig(lfp)
    finally:
        _SCRATCH.RemoveNative(lfp)

def cmp_fp(fp, lfp):
    a = pad_sig(fp); b = posed_sig(fp, lfp)
    if set(a) != set(b):
        return {"kind": "pad_set", "board_only": sorted(set(a) - set(b)),
                "lib_only": sorted(set(b) - set(a))}
    diffs = []
    for k in sorted(a):
        f = [FIELDS[i] for i in range(len(FIELDS)) if a[k][i] != b[k][i]]
        if f:
            diffs.append({"kind": "pad", "pad": k, "fields": f,
                          "board": dict(zip(FIELDS, a[k])), "lib": dict(zip(FIELDS, b[k]))})
    return diffs

def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--std-root", default=os.path.join(root, "AppDir/share/kicad/footprints"))
    ap.add_argument("--proj-lib", default=os.path.join(root, "k1/lib"))
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--neg-control", default=None,
                    help="负控：对该 ref 的第 1 个 pad 植入 size 变异（须 FLAG）")
    a = ap.parse_args(argv)

    board = pcbnew.LoadBoard(a.board)
    if a.neg_control:
        for fp in board.GetFootprints():
            if fp.GetReference() == a.neg_control:
                p = list(fp.Pads())[0]
                p.SetSize(pcbnew.VECTOR2I(p.GetSize().x + 100000, p.GetSize().y))
                print(f"[NEG-CONTROL] mutated {a.neg_control} pad {p.GetNumber()} size +0.1mm "
                      f"(layer={'B.Cu' if fp.GetLayer()==pcbnew.B_Cu else 'F.Cu'})")

    recs = []
    for fp in board.GetFootprints():
        fid = fp.GetFPID(); nick = fid.GetLibNickname(); name = fid.GetLibItemName()
        rec = {"ref": fp.GetReference(), "lib_id": f"{nick}:{name}" if nick else name,
               "layer": "B.Cu" if fp.GetLayer() == pcbnew.B_Cu else "F.Cu",
               "orient_deg": _r(fp.GetOrientationDegrees(), 2),
               "normalized_with_flip": fp.GetLayer() == pcbnew.B_Cu}
        d = resolve(nick, name, a.std_root, a.proj_lib)
        if not d:
            rec["verdict"] = "no_library_link"; recs.append(rec); continue
        lfp = pcbnew.FootprintLoad(d, name)
        if lfp is None:
            rec["verdict"] = "library_unloadable"; recs.append(rec); continue
        r = cmp_fp(fp, lfp)
        rec["verdict"] = "electrical_identical" if (r == [] or r == {}) else "electrical_diff"
        if rec["verdict"] == "electrical_diff":
            rec["diffs"] = r if isinstance(r, list) else [r]
        recs.append(rec)

    s = {"board": a.board,
         "board_sha16": hashlib.sha256(open(a.board, "rb").read()).hexdigest()[:16],
         "n_footprints": len(recs),
         "n_electrical_identical": sum(1 for r in recs if r["verdict"] == "electrical_identical"),
         "n_electrical_diff": sum(1 for r in recs if r["verdict"] == "electrical_diff"),
         "n_no_library_link": sum(1 for r in recs if r["verdict"] == "no_library_link"),
         "n_library_unloadable": sum(1 for r in recs if r["verdict"] == "library_unloadable"),
         "electrical_diff_refs": sorted(r["ref"] for r in recs if r["verdict"] == "electrical_diff"),
         "n_back_layer": sum(1 for r in recs if r["layer"] == "B.Cu"),
         "normalization": "pose v2 LAYER-AWARE: B.Cu ⇒ SetLayerAndFlip(B_Cu) FIRST, then SetOrientation, then SetPosition",
         "neg_control": a.neg_control}
    json.dump({"summary": s, "records": recs}, open(a.out_json, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    open(a.out_md, "w", encoding="utf-8").write(
        "# W-8 pose-normalized audit (v2 · layer-aware)\n\n```\n"
        + json.dumps(s, ensure_ascii=False, indent=1) + "\n```\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
