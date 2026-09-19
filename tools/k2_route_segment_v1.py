#!/usr/bin/env python3
"""k2_route_segment_v1.py — K2 P4 · #K2-31 §二 (A) **段2 驱动器 v1**（链内路由器段）。

链位：段1(`k2_gen_v5.py` 产物) → **[本件：段2a 图纸直构 + 段2b PDN 连接施加]** → 段2c(P4 收敛族) → 段3(ZONE_FILLER) → 段4(落件)

依据：监理 #K2-31 §二（裁 (A)：链自己产出布线）+ §2.1 硬要求：
  1. 输入 = **链内中间产物**（本件只读 `--in`，**不读** l4/l5/设计源板/锚板）；
  2. 确定性：段2a 复用 `p3_v57_l4_apply_drawing.apply_board` 的 canonicalize（排序 + uuid5）；段2b 坐标逐字取自 SPEC ⇒ 两次连跑逐字节同；
  3. 只增不改既有铜（除图纸/PDN 声明网按 purge-then-add 幂等重发）。

段2a = W3 图纸直构（`m13_v57_w3_joint_assignment.json` 34 页 nodes/vias + REFCLK path；宽度口径 = SPEC `impedance.width_mm_by_layer`）
段2b = PDN **仅 connect 段**（`gnd_stitch_via` + `power_pad_connect` 的 stub/via；**不取 zone 段** —— zone 集以段1 产物为准）

CLI: AppDir/usr/bin/python3.11 k2/tools/k2_route_segment_v1.py --in <段1 产物.kicad_pcb> --out <段2 产物.kicad_pcb> [--spec-rev19 PATH] [--skip-2b]
输出：stdout JSON（逐段 sha/段数/网数/track 直方图）；`--out` 板就地写出（两段累计）。
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
K2 = HERE.parent


def _load(name: str, fn: str):
    sp = importlib.util.spec_from_file_location(name, str(HERE / fn))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha16(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]


UUID_NS = "6f5f1c3e-0000-4000-8000-0000000000ff"


def canon_sort_tracks(path, loader):
    """把 segment/via/zone 根块**全局**排序（P3 canonicalize 只排「连续同类 run」⇒
    pcbnew 保存顺序一变，run 切分就变 ⇒ 仍漂移，实测 975 行）。排序键 = (类序, 去 uuid 文本)。"""
    import re
    txt = path.read_text(encoding="utf-8")
    ch = loader._root_children(txt)
    head, tail = txt[:ch[0][0]], txt[ch[-1][1]:]
    blocks = [txt[s:e] for s, e in ch]
    KINDS = ("segment", "via", "zone")
    m_kind = re.compile(r'\s*\(\s*([a-z_]+)')
    u_mid = re.compile(r'\(uuid "[^"]*"\)')

    def kind(b):
        m = m_kind.match(b); return m.group(1) if m else ""
    tr = [b for b in blocks if kind(b) in KINDS]
    keep = [b for b in blocks if kind(b) not in KINDS]
    tr.sort(key=lambda b: (KINDS.index(kind(b)), u_mid.sub("(uuid)", b)))
    first = next(i for i, b in enumerate(blocks) if kind(b) in KINDS)
    out = blocks[:first] + tr + [b for b in blocks[first:] if kind(b) not in KINDS]
    path.write_text(head + "\n".join(out) + tail, encoding="utf-8")
    return len(tr)


def canon_all_uuids(path, loader):
    """把整板 **所有** `(uuid "...")` 归一为内容派生 uuid5（确定性）。

    背景：`p3_v57_l4_apply_drawing.canonicalize_board` 只归一 `_CANON_TYPES=(segment,via,zone)`
    三类；footprint/pad/net 等的 uuid 来自 pcbnew 随机 uuid4 ⇒ 两次连跑漂移（实测 1115 行）。
    做法：按**根块**取内容（去 uuid 后的文本）为键 + 同类出现序号，块内 uuid 依序替换。
    （不改 P3 件；本件为 #K2-31 §2.1 硬要求 2「两次连跑逐字节同」。）
    """
    import re, uuid
    txt = path.read_text(encoding="utf-8")
    ch = loader._root_children(txt)
    head, tail = txt[:ch[0][0]], txt[ch[-1][1]:]
    u_mid = re.compile(r'\(uuid "[^"]*"\)')
    seen, out_blocks, n = {}, [], 0
    for (s, e) in ch:
        blk = txt[s:e]
        key = u_mid.sub("(uuid)", blk)
        i = seen.get(key, 0); seen[key] = i + 1
        base = key + "#%d" % i
        c = [0]

        def sub(_m):
            c[0] += 1
            return '(uuid "%s")' % uuid.uuid5(uuid.UUID(UUID_NS), base + "|%d" % c[0])
        nb = u_mid.sub(sub, blk)
        n += c[0]
        out_blocks.append(nb)
    path.write_text(head + "\n".join(out_blocks) + tail, encoding="utf-8")
    return n


def run_drc(board, workdir, kicad_cli):
    """链内 DRC（#K2-31 §2.1 硬要求）：新建 work-dir + 补齐 fp-lib-table/lib 环境，
    返回 (json_path, counts)。**禁用复用旧目录**（E-3 §4 具名坑：69 vs 73 假绿）。"""
    import json as _j, pathlib as _p, shutil as _s, subprocess as _sp
    wd = _p.Path(workdir); wd.mkdir(parents=True, exist_ok=True)
    stem = "k2_v4_8L.l6cand"
    b = wd / (stem + ".kicad_pcb"); _s.copy2(board, b)
    pro = _p.Path(str(board).replace(".kicad_pcb", ".kicad_pro"))
    if pro.exists(): _s.copy2(pro, wd / (stem + ".kicad_pro"))
    for pat in ("fp-lib-table", "lib"):
        s = K2 / "hw" / pat; d = wd / pat
        if s.exists() and not d.exists():
            (_s.copytree if s.is_dir() else _s.copy2)(s, d)
    out = wd / "drc.json"
    _sp.run([kicad_cli, "pcb", "drc", "--format", "json", "--severity-all", "--output", str(out), str(b)],
            capture_output=True, text=True, timeout=1800)
    d = _j.loads(out.read_text())
    # 确定性：违规条目 + 条目内 items 全序化（工具侧按文件序遍历 ⇒ 候选序随 kicad 输出序漂移，
    # 实测 2c-B 两条不同锚点重布位、差 ~0.176mm）。输入侧固化序 = 不改工具件、保可追溯。
    for v in d.get("violations", []):
        if isinstance(v.get("items"), list):
            v["items"] = sorted(v["items"], key=lambda x: _j.dumps(x, sort_keys=True, ensure_ascii=False))
    d["violations"] = sorted(d.get("violations", []),
                             key=lambda v: (str(v.get("type")), _j.dumps(v.get("items"), sort_keys=True, ensure_ascii=False),
                                            _j.dumps(v.get("description", ""), ensure_ascii=False)))
    for kk in ("unconnected_items",):
        if isinstance(d.get(kk), list):
            d[kk] = sorted(d[kk], key=lambda x: _j.dumps(x, sort_keys=True, ensure_ascii=False))
    out.write_text(_j.dumps(d, sort_keys=True), encoding="utf-8")
    vs = d.get("violations", [])
    return str(out), {"violations": len(vs), "errors": sum(1 for v in vs if v["severity"] == "error"),
                      "unconnected": len(d.get("unconnected_items", [])),
                      "types": {k: sum(1 for v in vs if v["type"] == k) for k in sorted({v["type"] for v in vs})}}


STEP_ORDER = ["2b", "2cA", "2cB"]


def _ord(x: str) -> int:
    return len(STEP_ORDER) if x == "all" else STEP_ORDER.index(x)


def track_hist(p) -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(p)); h = {}
    for t in b.GetTracks():
        k = 'via' if t.Type() == pcbnew.PCB_VIA_T else str(t.GetLayerName())
        h[k] = h.get(k, 0) + 1
    return {"total": sum(h.values()), "by": h, "nets": b.GetNetCount(), "fps": len(b.GetFootprints())}


def main() -> int:
    ap = argparse.ArgumentParser(description="#K2-31 §二 (A) 段2 驱动器（2a 图纸直构 + 2b PDN connect）")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec-rev19", default=str(K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"))
    ap.add_argument("--skip-2b", action="store_true")
    ap.add_argument("--drc-cli", default=str(K2.parent / "AppDir/bin/kicad-cli"))
    ap.add_argument("--upto", default="2b", choices=["2b", "2cA", "2cB", "all"], help="链步截止（默认 2b）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    src, out = pathlib.Path(a.src).resolve(), pathlib.Path(a.out).resolve()
    if not src.exists():
        print(json.dumps({"error": f"输入不存在: {src}"})); return 2
    rec = {"src": str(src), "src_sha16": sha16(src), "steps": []}

    # ── 段2a：图纸直构（底 = 段1 产物）────────────────────────────────
    la = _load("k2_l4apply", "p3_v57_l4_apply_drawing.py")
    la.K2 = pathlib.Path("/")                # 仅影响返回值的 relative_to（模块常量 MAIN/SPEC 等已绑定）
                                             # ⇒ build() 与 apply_board() 的 relative_to 均不抛错
    art = json.loads(la.MAIN.read_text(encoding="utf-8"))
    manifest = json.loads(la.MANIFEST.read_text(encoding="utf-8"))
    dr = la.build(art, manifest)
    if a.dry_run:
        rec["steps"].append({"step": "2a", "segs": dr["tally"]["n_segments"], "vias": dr["tally"]["n_vias"], "dry_run": True})
    else:
        shutil.copy2(src, out)
        _sp = src.with_suffix(".kicad_pro"); _op = out.with_suffix(".kicad_pro")
        if _sp.exists(): shutil.copy2(_sp, _op)   # pro 随链传导（段4 再打规则强度/sheets 补丁）
        app = la.apply_board(dr, src, out, None)
        rec["steps"].append({"step": "2a", "segs": dr["tally"]["n_segments"], "vias": dr["tally"]["n_vias"],
                             "sha16": sha16(out), **track_hist(out)})

    # ── 段2b：PDN connect（只 stub/via，不动 zone）─────────────────────
    if not a.skip_2b:
        co = _load("k2_co102", "p3_v57_co102_pdn_apply_local.py")
        if a.dry_run:
            rec["steps"].append({"step": "2b", "dry_run": True})
        else:
            st = co.apply(a.spec_rev19, str(out), "connect")
            rec["steps"].append({"step": "2b", "spec": pathlib.Path(a.spec_rev19).name,
                                 "stub_w": st["stub_width_mm"], "vias": st["vias"], "tracks": st["tracks"],
                                 "blocked": len(st["blocked"]), "sha16": sha16(out), **track_hist(out)})
    # ── 段2c 第一步：converge_v1 阶段 A（A1 NC 语义 ⇒ 消 NO_CONNECT；A2 keepout pad；A3 丝印镜像）──
    if _ord(a.upto) >= _ord("2cA"):
        cv = _load("k2cv", "k2_p4_converge_v1.py")
        tmpc = str(out) + ".2cA_tmp.kicad_pcb"
        import contextlib, io
        _buf = io.StringIO()
        with contextlib.redirect_stdout(_buf):
            rc = cv.main(["--stage", "A", "--in", str(out), "--out", tmpc, "--ledger", str(out) + ".2cA_ledger.json"])
        if rc != 0:
            print(json.dumps({"error": f"converge A rc={rc}"})); return 3
        shutil.copy2(tmpc, out)
        rec["steps"].append({"step": "2c-A", "rc": rc, "tool_stdout": _buf.getvalue().strip(),
                             "sha16": sha16(out), **track_hist(out)})

    # ── 段2c 第二步：converge_v1 阶段 B（旧铜避让新 pad；需链内即时 DRC）──
    if _ord(a.upto) >= _ord("2cB"):
        cvb = _load("k2cv", "k2_p4_converge_v1.py")
        dj, cnt = run_drc(out, str(out) + ".drc_b", a.drc_cli)
        tmpb = str(out) + ".2cB_tmp.kicad_pcb"
        import contextlib, io
        _bb = io.StringIO()
        with contextlib.redirect_stdout(_bb):
            rcb = cvb.main(["--stage", "B", "--in", str(out), "--drc", dj, "--out", tmpb,
                            "--ledger", str(out) + ".2cB_ledger.json"])
        if rcb != 0:
            rec["steps"].append({"step": "2c-B", "rc": rcb, "drc_before": cnt}); print(json.dumps(rec, ensure_ascii=False, indent=1)); return 3
        shutil.copy2(tmpb, out)
        rec["steps"].append({"step": "2c-B", "rc": rcb, "drc_before": cnt, "tool_stdout": _bb.getvalue().strip(),
                             "sha16": sha16(out), **track_hist(out)})

    if not a.dry_run:
        n_s = canon_sort_tracks(out, la)
        n_u = canon_all_uuids(out, la)
        rec["steps"].append({"step": "canon-sort", "blocks_sorted": n_s, "sha16": sha16(out)})
        rec["steps"].append({"step": "canon", "uuids_remapped": n_u, "sha16": sha16(out), **track_hist(out)})
    rec["out"] = str(out); rec["out_sha16"] = sha16(out) if not a.dry_run else None
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
