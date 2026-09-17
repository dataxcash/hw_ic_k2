#!/usr/bin/env python3
"""K2 P4 · ⑦ **库侧收口：以板为准的封装库快照 + 全板 `lib_id` 重指** v1（默认 dry-run）。

依据（监理 #K2-21 §二⑦，权威原文）：
  「**裁定：以板为准** …… 判据**容忍图形级差异**，**电气级必须 0**（pad 数/名/尺寸/旋转/位置逐件比）；
    35 件**逐条登记**。**同时建 `fp-lib-table`**（F-12 收口）」
处置路线（`K2-P4-COURTYARD-AND-LIB-REGISTER-v1.md` §3-3/§4-3）：
  「以板为准 + **库侧待按板重建并让 board `lib_id` 指向项目库**」。

本器做三件事，全部**确定性**、**默认只写 `--work-dir`**：
  ① 把板上 59 颗 footprint 按 **land pattern**（pad/图形/模型/其它字段；忽略 `Reference`/`Value`
     文本与位号—数值字段实例差异、忽略 uuid）去重，重建项目库 `lib/ForgeOS.pretty` 快照；
  ② 把板上每颗 footprint 的 `lib_id` 改指 `ForgeOS:<快照名>`（无 nickname / 错 nickname 一并收敛）；
  ③ 复算硬闸 + 守恒闸，出候选板（**落件须监理放行**）。

硬闸（任一不达 ⇒ 退出码 1，禁缩口径）：DRC `error` = 0 · `unconnected` = 0 ·
`lib_footprint_mismatch` = 0 · `lib_footprint_issues` = 0 · 无违规类型增量。
守恒闸：footprint/pad/net 数不变 · `track`/`via` 几何集合逐条相同 · zone 数不变 ·
非 45° = 0 · 文本差异**仅** footprint 头行 · `column_x` 不变。
纪律：T-22（备份 + dst pro 逐字节校验）· T-38（种子）· T-41（写仓库须 `--apply --confirm-repo-write`）。

用法（dry-run）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_lib_snapshot_v1.py \
    --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
    --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/lib7/run
（落件）追加 `--apply --confirm-repo-write`（**须监理放行**）
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import pcbnew

NM = 1_000_000
SEED = 20260918
LIB_NICK = "ForgeOS"
RULES9 = ["copper_sliver", "footprint_filters_mismatch", "footprint_type_mismatch",
          "tuning_profile_track_geometries", "missing_courtyard", "silk_over_copper",
          "silk_overlap", "track_not_centered_on_via", "via_dangling"]
SAFE = re.compile(r"[^A-Za-z0-9._+\-]")


# ------------------------------------------------------------------ 基础工具
def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def scan_block(text: str, i: int) -> int:
    """i 指向 '('；返回配平括号之后的下标（exclusive）。"""
    j, depth, instr = i + 1, 1, False
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


def strip_props(text: str, names) -> str:
    """删除顶层 `(property "<names>" ...)` 块（连同其后换行）。"""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith('(property "', i):
            j = scan_block(text, i)
            blk = text[i:j]
            m = re.match(r'\(property "([^"]+)"', blk)
            if m and m.group(1) in names:
                i = j
                while i < n and text[i] in "\r\n":
                    i += 1
                continue
            out.append(blk)
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def land_pattern_sig(text: str) -> str:
    """land pattern 指纹：去 Reference/Value 块 + 归一 uuid（跨实例可比）。"""
    t = strip_props(text, {"Reference", "Value"})
    t = re.sub(r'\(uuid "[^"]*"\)', '(uuid "U")', t)
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def build_props(side: str, value: str) -> str:
    f = ("\t\t(layer \"%s\")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n"
         "\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n")
    return ('\t(property "Reference" "REF**"\n\t\t(at 0 0 0)\n' + f % (side + ".SilkS")
            + '\t(property "Value" "%s"\n\t\t(at 0 0 0)\n' % value + f % (side + ".Fab"))


def render_mod(text: str, name: str, value: str) -> str:
    body = strip_props(text, {"Reference", "Value"})
    body = re.sub(r'^\(footprint "[^"]*"', '(footprint "%s"' % name, body, count=1)
    m = re.search(r'\n\t\(layer "([^"]+)"\)\n', body)
    if not m:
        raise RuntimeError("mod: no layer line")
    side = "B" if m.group(1).startswith("B.") else "F"
    return body[:m.end()] + build_props(side, value) + body[m.end():]


# ------------------------------------------------------------- 板/Drc/项目副件
def probe_pro(pro_src: str, dest: str) -> None:
    data = json.load(open(pro_src, encoding="utf-8"))
    sev = data["board"]["design_settings"]["rule_severities"]
    for r in RULES9:
        sev[r] = "warning"          # 探针：把 ignore 抬到 warning（非安装）
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def run_drc(kicad_cli: str, board: str, out_json: str) -> dict:
    p = subprocess.run([kicad_cli, "pcb", "drc", "--format", "json", "--severity-all",
                        "--output", out_json, board], capture_output=True, text=True)
    if p.returncode != 0 or not os.path.exists(out_json):
        raise RuntimeError("drc rc=%d\n%s\n%s" % (p.returncode, p.stdout, p.stderr))
    with open(out_json, encoding="utf-8") as fh:
        return json.load(fh)


def counts(rep: dict) -> dict:
    c = collections.Counter((v["severity"], v["type"]) for v in rep.get("violations", []))
    return {"%s:%s" % k: v for k, v in sorted(c.items())}


def unconn(rep: dict) -> int:
    return len(rep.get("unconnected_items", []))


def copper_sig(bd) -> dict:
    """铜几何集合（守恒用；与 lib_id 无关）。"""
    tracks, vias = [], []
    for t in bd.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.Type() == pcbnew.PCB_VIA_T:
            vias.append((t.GetLayer(), t.GetPosition().x, t.GetPosition().y,
                         t.GetDrillValue(), t.GetFrontWidth(), t.GetNetname()))
        else:
            tracks.append((t.GetLayer(), s.x, s.y, e.x, e.y, t.GetWidth(), t.GetNetname()))
    return {"tracks": sorted(tracks), "vias": sorted(vias),
            "zones": len(list(bd.Zones())), "nets": bd.GetNetCount(),
            "fps": len(list(bd.GetFootprints())),
            "pads": sum(f.GetPadCount() for f in bd.GetFootprints())}


def non45(bd) -> list:
    out = []
    for t in bd.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        dx = t.GetEnd().x - t.GetStart().x
        dy = t.GetEnd().y - t.GetStart().y
        if dx and dy and abs(abs(dx) - abs(dy)) > 2_000:
            out.append((t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y))
    return out


def column_x(bd, refs=("J6", "J9", "J11", "J12", "J13")) -> dict:
    return {f.GetReference(): round(f.GetPosition().x / NM, 4)
            for f in bd.GetFootprints() if f.GetReference() in refs}


def placement_equiv(bd, libdir: str) -> list:
    """独立等价证明：把库件按板上位姿（位置/朝向/侧别）放置后，逐 pad 比绝对几何。
    —— 与 KiCad 的 `lib_footprint_mismatch` 互补，可识别「旋转/背面镜像」类约定差异。"""
    scratch = pcbnew.BOARD()
    bad = []
    for fp in bd.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        lfp = pcbnew.FootprintLoad(libdir, name)
        if lfp is None:
            bad.append("%s:library_item_missing" % fp.GetReference())
            continue
        scratch.Add(lfp)
        lfp.SetOrientation(fp.GetOrientation())
        lfp.SetPosition(fp.GetPosition())
        if fp.GetLayer() == pcbnew.B_Cu:
            lfp.Flip(fp.GetPosition(), False)

        def m(f):
            return {p.GetNumber(): (p.GetPosition().x, p.GetPosition().y,
                                    round(p.GetOrientationDegrees(), 2), int(p.GetShape()),
                                    p.GetSize().x, p.GetSize().y, p.GetDrillSize().x)
                    for p in f.Pads()}
        a, b = m(fp), m(lfp)
        if set(a) != set(b):
            bad.append("%s:pad_name_set" % fp.GetReference())
        else:
            d = [n for n in a if a[n] != b[n]]
            if d:
                bad.append("%s:pads:%s" % (fp.GetReference(), ",".join(sorted(d)[:4])))
        scratch.RemoveNative(lfp)
    return bad


def diff_lines(a: str, b: str):
    la, lb = open(a, encoding="utf-8").read().splitlines(), open(b, encoding="utf-8").read().splitlines()
    if len(la) != len(lb):
        return None, None
    ch = [(x, y) for x, y in zip(la, lb) if x != y]
    return len(ch), ch


# ------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    if a.apply and not a.confirm_repo_write:
        print("REFUSE: --apply 需 --confirm-repo-write（T-41）", file=sys.stderr)
        return 2
    try:
        pcbnew.KIID.SeedGenerator(SEED)
    except Exception:
        pass

    board_src = os.path.abspath(a.board)
    pro_src = os.path.abspath(a.pro)
    pro_dir = os.path.dirname(board_src)
    lib_src = os.path.join(pro_dir, "lib", LIB_NICK + ".pretty")
    work = os.path.abspath(a.work_dir)
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(board_src))[0]
    work_lib = os.path.join(work, "lib", LIB_NICK + ".pretty")
    scratch = os.path.join(work, "scratch.pretty")
    for d in (work_lib, scratch):
        os.makedirs(d, exist_ok=True)
    rep = {"src": {"board": board_src, "board_sha16": sha16(board_src),
                   "pro": pro_src, "pro_sha16": sha16(pro_src),
                   "lib": lib_src, "lib_present": os.path.isdir(lib_src)}}

    r0 = run_drc(a.kicad_cli, board_src, os.path.join(work, "drc_before.json"))
    bd = pcbnew.LoadBoard(board_src)
    rep["before"] = {"counts": counts(r0), "unconnected": unconn(r0),
                     "copper": {k: (len(v) if isinstance(v, list) else v)
                                for k, v in copper_sig(bd).items()},
                     "non45": len(non45(bd)), "column_x": column_x(bd)}
    sig0 = copper_sig(bd)

    # ① 采样：每颗 footprint 存 scratch，算 land pattern 指纹
    io = pcbnew.PCB_IO_KICAD_SEXPR()
    recs = {}
    for fp in sorted(bd.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        item = SAFE.sub("_", str(fp.GetFPID().GetLibItemName()))
        if not item:
            raise RuntimeError("empty item name: %s" % ref)
        fp.SetFPID(pcbnew.LIB_ID(LIB_NICK, item))
        io.FootprintSave(scratch, fp)
        p = os.path.join(scratch, item + ".kicad_mod")
        txt = open(p, encoding="utf-8").read()
        recs[ref] = {"ref": ref, "item": item, "sig": land_pattern_sig(txt), "text": txt}
    # ② 按 (item, land pattern) 分组 → 快照名（去重；同名不同版才加序号）
    groups = collections.defaultdict(list)
    for ref, d in recs.items():
        groups[(d["item"], d["sig"])].append(ref)
    per_item = collections.defaultdict(list)
    for (item, sig), refs in sorted(groups.items()):
        per_item[item].append((sig, sorted(refs)))
    name_of = {}
    for item, lst in per_item.items():
        for k, (sig, refs) in enumerate(lst, 1):
            nm = item if len(lst) == 1 else "%s__%d" % (item, k)
            for r in refs:
                name_of[r] = nm
    # ③ 写快照库
    written = {}
    for (item, sig), refs in sorted(groups.items()):
        refs = sorted(refs)
        nm = name_of[refs[0]]
        txt = render_mod(recs[refs[0]]["text"], nm, item)
        with open(os.path.join(work_lib, nm + ".kicad_mod"), "w", encoding="utf-8") as fh:
            fh.write(txt)
        written[nm] = {"members": refs, "sha16": hashlib.sha256(txt.encode()).hexdigest()[:16]}
    with open(os.path.join(work, "fp-lib-table"), "w", encoding="utf-8") as fh:
        fh.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") '
                 '(uri "${KIPRJMOD}/lib/%s.pretty") (options "") '
                 '(descr "IC_HW K2 project footprints (board-authoritative snapshot; F-12/J-7a)"))\n)\n'
                 % (LIB_NICK, LIB_NICK))
    # ④ 重指 lib_id 并出候选板
    for fp in bd.GetFootprints():
        fp.SetFPID(pcbnew.LIB_ID(LIB_NICK, name_of[fp.GetReference()]))
    probe_pro(pro_src, os.path.join(work, stem + ".kicad_pro"))
    out = os.path.join(work, stem + ".libsnap.kicad_pcb")
    pcbnew.SaveBoard(out, bd)
    rc = run_drc(a.kicad_cli, out, out + ".json")
    bd2 = pcbnew.LoadBoard(out)
    sig1 = copper_sig(bd2)
    ndiff, chlines = diff_lines(board_src, out)
    lib_src_existing = sorted(f[:-10] for f in os.listdir(lib_src)
                              if f.endswith(".kicad_mod")) if os.path.isdir(lib_src) else []
    rep["snapshot"] = {"lib_src_existing_mods": lib_src_existing,
                       "stale_mods": sorted(set(lib_src_existing) - set(written)),
                       "n_footprints": len(recs), "n_land_patterns": len(groups),
                       "n_mods": len(written), "mods": written,
                       "lib_ids": sorted({"%s:%s" % (LIB_NICK, v) for v in name_of.values()})}
    rep["after"] = {"counts": counts(rc), "unconnected": unconn(rc),
                    "copper": {k: (len(v) if isinstance(v, list) else v) for k, v in sig1.items()},
                    "non45": len(non45(bd2)), "column_x": column_x(bd2),
                    "board": out, "board_sha16": sha16(out),
                    "text_diff_lines": ndiff}
    # ⑤ 闸
    bad = []
    hb, ha = counts(r0), counts(rc)
    for t in sorted(set(hb) | set(ha)):
        if ha.get(t, 0) > hb.get(t, 0) and t not in ("missing_courtyard",):
            bad.append("vios+:%s %s->%s" % (t, hb.get(t, 0), ha.get(t, 0)))
    for v in rc.get("violations", []):
        if v["severity"] == "error":
            bad.append("error:%s" % v["type"])
    if unconn(rc) != 0:
        bad.append("unconnected:%d" % unconn(rc))
    for t in ("lib_footprint_mismatch", "lib_footprint_issues"):
        if ha.get("warning:" + t, 0) or ha.get("error:" + t, 0):
            bad.append("%s:%s" % (t, ha.get("warning:" + t, 0) + ha.get("error:" + t, 0)))
    # 守恒
    for key in ("tracks", "vias"):
        if sig0[key] != sig1[key]:
            bad.append("copper_%s_changed" % key)
    for key in ("zones", "nets", "fps", "pads"):
        if sig0[key] != sig1[key]:
            bad.append("%s:%s->%s" % (key, sig0[key], sig1[key]))
    if rep["before"]["non45"] != rep["after"]["non45"]:
        bad.append("non45:%s->%s" % (rep["before"]["non45"], rep["after"]["non45"]))
    if rep["before"]["column_x"] != rep["after"]["column_x"]:
        bad.append("column_x_changed")
    if ndiff is None:
        bad.append("text_line_count_changed")
    elif any(not y.lstrip().startswith('(footprint "') for x, y in chlines):
        bad.append("text_change_outside_footprint_header")
    elif not 0 < ndiff <= len(recs):
        bad.append("text_diff_lines:%d out of (0,%d]" % (ndiff, len(recs)))
    rep["placement_equiv"] = {"n_footprints": len(list(bd2.GetFootprints())),
                              "mismatches": placement_equiv(bd2, work_lib)}
    if rep["placement_equiv"]["mismatches"]:
        bad.append("placement_equiv:%s" % rep["placement_equiv"]["mismatches"][:5])
    rep["gates"] = {"passed": not bad, "failures": bad}
    # 落件（须 --apply --confirm-repo-write；监理放行后）
    if a.apply and not bad:
        bak = os.path.join(work, stem + ".repo-backup")
        os.makedirs(bak, exist_ok=True)
        shutil.copy2(board_src, os.path.join(bak, os.path.basename(board_src)))
        if os.path.isdir(lib_src):
            shutil.copytree(lib_src, os.path.join(bak, LIB_NICK + ".pretty"), dirs_exist_ok=True)
        src_pro_bytes = open(pro_src, "rb").read()
        stale = sorted(f for f in os.listdir(lib_src)
                       if f.endswith(".kicad_mod") and f[:-10] not in written) \
            if os.path.isdir(lib_src) else []
        shutil.copytree(work_lib, lib_src, dirs_exist_ok=True)   # 只增/改，不删（删除须监理另裁）
        shutil.copy2(out, board_src)
        if open(pro_src, "rb").read() != src_pro_bytes:
            raise RuntimeError("pro 字节被改动，已中止（备份在 %s）" % bak)
        rep["applied"] = {"board_sha16": sha16(board_src), "pro_sha16": sha16(pro_src),
                          "pro_unchanged": True, "lib": lib_src,
                          "n_mods": len([f for f in os.listdir(lib_src) if f.endswith(".kicad_mod")]),
                          "stale_mods_not_deleted": stale, "backup": bak}
    elif a.apply:
        rep["applied"] = {"refused": "gates failed"}
    outrep = a.report or os.path.join(work, "lib_snapshot_report.json")
    with open(outrep, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("before:", json.dumps(rep["before"]["counts"], ensure_ascii=False))
    print("after :", json.dumps(rep["after"]["counts"], ensure_ascii=False))
    print("snapshot: fps=%d land_patterns=%d mods=%d" % (len(recs), len(groups), len(written)))
    print("candidate:", out, "sha16", rep["after"]["board_sha16"], "| text_diff_lines", ndiff)
    print("placement_equiv:", rep["placement_equiv"]["n_footprints"], "fps, mismatches",
          len(rep["placement_equiv"]["mismatches"]))
    print("gates:", json.dumps(rep["gates"], ensure_ascii=False))
    print("report:", outrep)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
