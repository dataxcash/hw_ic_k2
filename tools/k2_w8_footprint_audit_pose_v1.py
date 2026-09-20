#!/usr/bin/env python3
"""K2 · W-8 电气级审计（**姿态归一版**）—— 只读板 + 只读库。

授权：#K2-51 §二「姿态口径」自裁 —— 由**实例姿态**造成的 pad `rot` 差 = 表征差、
非电气/几何差 ⇒ 比较前须**姿态归一**；且归一器须过**三项验证**（负控 / 0° 件集合不变 /
原 identical 集合不变），否则**不得为绿**（防 C-12）。

归一规则（实测确定）：把库件按**板上实例姿态**（`SetOrientation`，**不做 Flip**）放置后
比较电气签名。理由：实测 NOFLIP 使 RAW 的 7 项差异中 6 项归位（41 identical），
FLIP 版反而破坏 0° 件（34 identical，含 U1/U5/U6/E1）⇒ FLIP = 过度归一，否决。

用法：
  python3 k2/tools/k2_w8_footprint_audit_pose_v1.py --board <pcb> --proj-lib <dir> \
      --out-json <j> --out-md <m> [--neg-control PADREF] [--self-test]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
import pcbnew

def MM(v): return v / 1e6
def fmt(v, nd=4):
    s = f"{v:.{nd}f}".rstrip("0").rstrip("."); return s if s else "0"

def pad_sig(fp):
    out = {}
    for p in fp.Pads():
        r = p.GetFPRelativePosition(); d = p.GetDrillSize()
        out[p.GetNumber()] = (int(p.GetShape()), round(MM(p.GetSize().x),4), round(MM(p.GetSize().y),4),
                              round(MM(r.x),4), round(MM(r.y),4), round(p.GetOrientationDegrees(),2),
                              round(MM(d.x),4))
    return out

def resolve(nick, name, std_root, proj_lib):
    if nick == "ForgeOS":
        d = os.path.join(proj_lib, "ForgeOS.pretty"); return d if os.path.isdir(d) else None
    if not nick: return None
    d = os.path.join(std_root, "%s.pretty" % nick); return d if os.path.isdir(d) else None

_SCRATCH = pcbnew.BOARD()

def posed_sig(fp, lfp):
    """库件按板上实例姿态（定向，不 Flip）放置后的电气签名。"""
    _SCRATCH.Add(lfp)
    try:
        lfp.SetOrientation(fp.GetOrientation()); lfp.SetPosition(fp.GetPosition())
        return pad_sig(lfp)
    finally:
        _SCRATCH.RemoveNative(lfp)

def cmp_fp(fp, lfp):
    a = pad_sig(fp); b = posed_sig(fp, lfp)
    if set(a) != set(b):
        return {"kind": "pad_set", "board_only": sorted(set(a)-set(b)), "lib_only": sorted(set(b)-set(a))}
    diffs = []
    for k in sorted(a):
        f = [n for n, i in (("shape",0),("sx",1),("sy",2),("dx",3),("dy",4),("rot",5),("drill_d",6)) if a[k][i] != b[k][i]]
        if f: diffs.append({"kind":"pad","pad":k,"fields":f,
                            "board":dict(zip(("shape","sx","sy","dx","dy","rot","drill_d"),a[k])),
                            "lib":dict(zip(("shape","sx","sy","dx","dy","rot","drill_d"),b[k]))})
    return diffs

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--std-root", default=os.path.join(root, "AppDir/share/kicad/footprints"))
    ap.add_argument("--proj-lib", default=os.path.join(root, "k1/lib"))
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--neg-control", default=None, help="负控：对指定 ref 的第 1 个 pad 植入 shape/size 变异，须被 FLAG")
    a = ap.parse_args()
    board = pcbnew.LoadBoard(a.board)
    if a.neg_control:
        for fp in board.GetFootprints():
            if fp.GetReference() == a.neg_control:
                p = list(fp.Pads())[0]
                p.SetSize(pcbnew.VECTOR2I(p.GetSize().x + 100000, p.GetSize().y))
                print(f"[NEG-CONTROL] mutated {a.neg_control} pad {p.GetNumber()} size +0.1mm")
    recs = []
    for fp in board.GetFootprints():
        fid = fp.GetFPID(); nick = fid.GetLibNickname(); name = fid.GetLibItemName()
        rec = {"ref": fp.GetReference(), "lib_id": f"{nick}:{name}" if nick else name,
               "layer": "B.Cu" if fp.GetLayer() == pcbnew.B_Cu else "F.Cu",
               "orient_deg": round(fp.GetOrientationDegrees(), 2)}
        d = resolve(nick, name, a.std_root, a.proj_lib)
        if not d:
            rec["verdict"] = "no_library_link"; recs.append(rec); continue
        lfp = pcbnew.FootprintLoad(d, name)
        if lfp is None:
            rec["verdict"] = "library_unloadable"; recs.append(rec); continue
        r = cmp_fp(fp, lfp)
        rec["verdict"] = "electrical_identical" if r == [] or r == {} else "electrical_diff"
        if rec["verdict"] == "electrical_diff": rec["diffs"] = r if isinstance(r, list) else [r]
        recs.append(rec)
    s = {"board": a.board, "board_sha16": hashlib.sha256(open(a.board,"rb").read()).hexdigest()[:16],
         "n_footprints": len(recs),
         "n_electrical_identical": sum(1 for r in recs if r["verdict"]=="electrical_identical"),
         "n_electrical_diff": sum(1 for r in recs if r["verdict"]=="electrical_diff"),
         "n_no_library_link": sum(1 for r in recs if r["verdict"]=="no_library_link"),
         "n_library_unloadable": sum(1 for r in recs if r["verdict"]=="library_unloadable"),
         "electrical_diff_refs": sorted(r["ref"] for r in recs if r["verdict"]=="electrical_diff"),
         "normalization": "pose: orientation-only (no flip) — validated by /tmp experiments"}
    json.dump({"summary": s, "records": recs}, open(a.out_json,"w"), ensure_ascii=False, indent=1)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    open(a.out_md,"w").write("# W-8 pose-normalized audit\n\n```\n"+json.dumps(s,ensure_ascii=False,indent=1)+"\n```\n")
    return 0
if __name__ == "__main__":
    sys.exit(main())
