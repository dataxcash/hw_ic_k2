#!/usr/bin/env python3
"""eda_eng CLI --- K2 独立确定性 EDA 工程软件（#K2-358）。无 LLM 在场可完整运行。"""
from __future__ import annotations
import argparse, json, os, subprocess, sys

from . import block as block_mod, eco as eco_mod, exams as exams_mod, netplan as netplan_mod, place as place_mod, regen as regen_mod, ripup as ripup_mod, route as route_mod, verify as verify_mod

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L2 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2")
REF_BOARD = os.path.join(ROOT, verify_mod.BASELINE_BOARD)
REF_DRC = os.path.join(L2, "REROUTE_EXAM_REF_L14_DRC.json")


def _emit(o, path=None, code=0):
    print(json.dumps(o, ensure_ascii=False, indent=1))
    if path:
        json.dump(o, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(prog="eda_eng", description="#K2-358 product CLI (LLM-free)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify", help="grade a board against the reference (5 criteria)")
    p.add_argument("--board", required=True); p.add_argument("--drc", required=True)
    p.add_argument("--ref", default=REF_BOARD); p.add_argument("--ref-drc", default=REF_DRC)
    p.add_argument("--json-out"); p.add_argument("--no-touch-l1", action="store_true",
                                                 help="(always true: verify never writes a board)")
    p = sub.add_parser("exam", help="run an exam's regression (definition, or --run to build+grade)")
    p.add_argument("which", choices=["A", "B"])
    p.add_argument("--board"); p.add_argument("--drc")
    p.add_argument("--run", action="store_true", help="build with the engine then grade")
    p.add_argument("--chain", default="product", choices=["product", "legacy"],
                   help="product = M1->M2->M3->M4 (C30); legacy = the old composed pipeline")
    p.add_argument("--max-nets", type=int, default=None)
    p.add_argument("--work", default=None)
    p = sub.add_parser("eco", help="validate the ECO chain form")
    p.add_argument("--json-out")
    p = sub.add_parser("docs", help="document-chain status (#K2-357 five links)")
    p.add_argument("--json-out")
    p = sub.add_parser("place", help="declarative placement (scenario applied to the placement source)")
    p.add_argument("--refs", required=True, help="comma-separated refs")
    p.add_argument("--delta", required=True, help="dx,dy in mm")
    p.add_argument("--out"); p.add_argument("--json-out")
    p = sub.add_parser("netplan", help="M1: teardown plan (affected nets + segments/vias to remove)")
    p.add_argument("--board", required=True)
    p.add_argument("--refs", required=True)
    p.add_argument("--delta", required=True, help="dx,dy in mm")
    p.add_argument("--json-out")
    p = sub.add_parser("relocate", help="#K2-366: relocate parts (6 steps: move -> M1 -> M2 -> maze reconnect -> refill -> M4)")
    p.add_argument("--refs", required=True, help="comma-separated refdes (or refdes=x,y pairs to set absolute positions)")
    p.add_argument("--delta", default=None, help="dx,dy applied to every listed ref")
    p.add_argument("--work", required=True)
    p.add_argument("--max-nets", type=int, default=None)
    p = sub.add_parser("block", help="M0: BLOCK census (frame -> three-way class census -> N* inflated predicate)")
    p.add_argument("--board"); p.add_argument("--rect", help="x0,y0,x1,y1 (mm)")
    p.add_argument("--refs", default=None, help="declared block members (comma-separated)")
    p.add_argument("--margin", type=float, default=0.5, help="margin when the frame is derived from refs")
    p.add_argument("--delta", default="0,0", help="dx,dy (mm) - used for swept + N*")
    p.add_argument("--clearance", type=float, default=None)
    p.add_argument("--json-out")
    p = sub.add_parser("relocate-block",
                       help="#K2-369: BLOCK relocation (M0 census -> move_block(+M2 clip) -> M3 in-block reconnect -> refill -> M4)")
    p.add_argument("--rect", help="x0,y0,x1,y1 (mm)")
    p.add_argument("--refs", default=None, help="declared block members (comma-separated)")
    p.add_argument("--margin", type=float, default=0.5)
    p.add_argument("--delta", required=True, help="dx,dy in mm")
    p.add_argument("--work", required=True)
    p.add_argument("--clearance", type=float, default=None)
    p.add_argument("--max-jobs", type=int, default=None)
    p.add_argument("--json-out")
    p = sub.add_parser("dump", help="read-only per-net track/via inventory (QA/test helper)")
    p.add_argument("--board", required=True)
    p.add_argument("--json-out")
    p = sub.add_parser("ripup", help="M2: execute the M1 teardown plan")
    p.add_argument("--board"); p.add_argument("--plan", help="M1 netplan JSON")
    p.add_argument("--out"); p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("route", help="M3: re-route (deterministic closed-form candidate family + oracle)")
    p.add_argument("--p1"); p.add_argument("--p2"); p.add_argument("--net", default="__route__")
    p.add_argument("--layer", default="F.Cu"); p.add_argument("--board")
    p.add_argument("--apply", help="apply a ROUTED plan JSON to the board")
    p.add_argument("--apply-batch", help="apply a batch of ROUTED plans (list) to the board")
    p.add_argument("--out"); p.add_argument("--json-out")
    p = sub.add_parser("regen", help="composed deterministic pipeline (place->gen->route->polish->drc), shadow root")
    p.add_argument("--exam", dest="exam_id", choices=["A", "B"], default=None)
    p.add_argument("--work", default=None)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("selftest", help="run the regression test suite (CI entry)")
    a = ap.parse_args(argv)

    if a.cmd == "verify":
        r = {"artifact": "eda_eng_verify", "board": a.board, "ref": a.ref}
        r.update(verify_mod.judge(a.board, a.drc, a.ref, a.ref_drc))
        return _emit(r, a.json_out, 0 if r["verdict"] == "PASS" else 1)

    if a.cmd == "exam":
        spec = exams_mod.EXAMS[a.which]
        out = {"artifact": "eda_eng_exam", "exam": spec, "judging_table": exams_mod.JUDGING_TABLE,
               "state": "DEFINED"}
        if a.run and a.chain == "product":
            preset = exams_mod.EXAMS[a.which]
            refs = preset.get("refs") or []
            delta = preset.get("delta_mm") or [0.0, 0.0]
            W = a.work or os.path.join("/tmp/opencode/eda_eng", "exam" + a.which)
            pr = regen_mod.preflight(a.which, W)
            if not pr["ok"]:
                return _emit({"artifact": "eda_eng_exam", "exam": a.which, "state": "REFUSED_BY_PREFLIGHT",
                              "preflight": pr}, None, 2)
            rp = regen_mod.exam_a_chain(refs, delta, W, max_nets=a.max_nets)
            graded = bool(rp.get("M4"))
            v = (rp.get("M4") or {}).get("verdict") or ("FAIL" if str(rp.get("state", "")).endswith("FAILED") else None)
            out = {"artifact": "eda_eng_exam", "exam": a.which, "preflight": pr, "route": rp,
                   "state": rp.get("state"), "criteria": (rp.get("M4") or {}).get("criteria"), "verdict": v}
            if not graded:
                out["blocked_at"] = rp.get("state")          # 链条未能到 M4 ⇒ 具名 FAIL（不许 None 静默）
            return _emit(out, None, 0 if v == "PASS" else 1)
        if a.run:
            rp = regen_mod.run(exam=a.which, work=a.work or os.path.join("/tmp/opencode/eda_eng", "exam" + a.which))
            out["route"] = rp
            if rp.get("state") == "RAN":
                out.update(verify_mod.judge(rp["final_board"], rp["drc"], REF_BOARD, REF_DRC))
                out["state"] = "GRADED"
            else:
                out["state"] = "BUILD_" + str(rp.get("state"))
            return _emit(out, None, 0 if out.get("verdict") == "PASS" else 1)
        if a.board and a.drc:
            out.update(verify_mod.judge(a.board, a.drc, REF_BOARD, REF_DRC))
            out["state"] = "GRADED"
        else:
            out["note"] = ("definition only; to grade, pass --board/--drc of the engine's output. "
                           "The engine is NOT implemented yet (see route), so the plan step is unavailable "
                           "and the exam cannot be passed today.")
            out["engine"] = regen_mod.STATUS
        return _emit(out, None, 0 if out.get("verdict") == "PASS" else 1)

    if a.cmd == "eco":
        r = eco_mod.check_all()
        return _emit(r, a.json_out, 0 if r["verdict"] == "PASS" else 1)

    if a.cmd == "docs":
        r = __import__("eda_eng.docs", fromlist=["chain_status"]).chain_status()
        return _emit(r, a.json_out, 0 if r["verdict"] == "PASS" else 1)

    if a.cmd == "place":
        refs = [x.strip() for x in a.refs.split(",") if x.strip()]
        dx, dy = [float(v) for v in a.delta.split(",")]
        r = place_mod.apply_scenario(refs, [dx, dy], out=a.out)
        return _emit(r, a.json_out, 0 if not r["missing"] else 1)

    if a.cmd == "netplan":
        refs = [x.strip() for x in a.refs.split(",") if x.strip()]
        dx, dy = [float(v) for v in a.delta.split(",")]
        r = netplan_mod.plan(a.board, refs, [dx, dy])
        return _emit(r, a.json_out, 0)

    if a.cmd == "relocate":
        moves = []
        for item in [x.strip() for x in a.refs.split(",") if x.strip()]:
            if "=" in item:
                r, xy = item.split("=")
                moves.append((r, [float(v) for v in xy.split(":")]))
            else:
                moves.append((item, None))
        if a.delta:
            dx, dy = [float(v) for v in a.delta.split(",")]
            if any(m[1] is None for m in moves):
                import pcbnew as P
                b = P.LoadBoard(os.path.join(ROOT, "hw/k2_v4_8L.l14.kicad_pcb"))
                pos = {fp.GetReference(): [P.ToMM(fp.GetPosition().x), P.ToMM(fp.GetPosition().y)]
                       for fp in b.GetFootprints()}
                moves = [(r, tgt if tgt else [round(pos[r][0] + dx, 4), round(pos[r][1] + dy, 4)])
                         for r, tgt in moves]
        r = regen_mod.relocate_chain(moves, a.work, max_nets=a.max_nets)
        return _emit(r, None, 0 if r.get("state") == "GRADED" and (r.get("M4") or {}).get("verdict") == "PASS" else 1)

    if a.cmd == "block":
        from . import route as _rt
        board = a.board or REF_BOARD
        members = [x.strip() for x in a.refs.split(",") if x.strip()] if a.refs else None
        rect = [float(v) for v in a.rect.split(",")] if a.rect else None
        if rect is None:
            pb = block_mod.pad_rect(board, members)
            if pb is None:
                return _emit({"artifact": "eda_eng_block", "error": "no pads for the given refs"}, a.json_out, 2)
            rect = block_mod.inflate(pb, a.margin)
        dx, dy = [float(v) for v in a.delta.split(",")]
        clear = a.clearance if a.clearance is not None else _rt.CLEAR
        r = block_mod.census(board, rect, [dx, dy], clearance=clear, members=members)
        return _emit(r, a.json_out, 0 if r["frame_ok"] else 1)

    if a.cmd == "relocate-block":
        from . import route as _rt
        members = [x.strip() for x in a.refs.split(",") if x.strip()] if a.refs else None
        rect = [float(v) for v in a.rect.split(",")] if a.rect else None
        if rect is None:
            pb = block_mod.pad_rect(REF_BOARD, members)
            if pb is None:
                return _emit({"artifact": "eda_eng_relocate_block", "error": "no pads for the given refs"}, None, 2)
            rect = block_mod.inflate(pb, a.margin)
        dx, dy = [float(v) for v in a.delta.split(",")]
        clear = a.clearance if a.clearance is not None else _rt.CLEAR
        r = regen_mod.relocate_block_chain(rect, [dx, dy], a.work, members=members,
                                           clearance=clear, max_jobs=a.max_jobs)
        return _emit(r, a.json_out, 0 if r.get("state") == "GRADED" and (r.get("M4") or {}).get("verdict") == "PASS" else 1)

    if a.cmd == "dump":
        return _emit({"artifact": "eda_eng_dump", "board": a.board,
                      "inventory": netplan_mod.inventory(a.board)}, a.json_out, 0)

    if a.cmd == "ripup":
        if not (a.board and a.plan and a.out):
            r = {"artifact": "eda_eng_ripup", "status": "NEED_ARGS",
                 "usage": "ripup --board <pcb> --plan <netplan.json> --out <pcb> [--dry-run]"}
            return _emit(r, None, 2)
        plan = json.load(open(a.plan, encoding="utf-8"))
        r = ripup_mod.execute(a.board, plan, a.out, dry=a.dry_run)
        return _emit(r, None, 0 if r["status"] in ("RIPPED", "DRY_RUN_OK") else 2)

    if a.cmd == "route":
        if a.apply_batch:
            plans = json.load(open(a.apply_batch, encoding="utf-8"))
            r = route_mod.apply_routes(a.board, plans, a.out)
            return _emit(r, None, 0)
        if a.apply:
            plan = json.load(open(a.apply, encoding="utf-8"))
            r = route_mod.apply_route(a.board, plan, a.out)
            return _emit(r, None, 0)
        if not (a.p1 and a.p2):
            r = {"artifact": "eda_eng_route_m3", "status": "NEED_ARGS", "module": "M3",
                 "usage": "route --p1 x,y --p2 x,y --layer F.Cu [--board PCB] [--net NAME]  |  "
                          "route --apply plan.json --board PCB --out PCB",
                 "scope_v1": ["deterministic closed-form candidate family (straight / L / Z, 45-degree chamfered)",
                              "clearance+keepout oracle", "SINGLE layer", "via insertion and multi-layer are the next scope step"]}
            return _emit(r, None, 2)
        p1 = [float(v) for v in a.p1.split(",")]; p2 = [float(v) for v in a.p2.split(",")]
        obs, bounds = ([], None)
        if a.board:
            import pcbnew as P
            bb = P.LoadBoard(a.board).GetBoardEdgesBoundingBox()
            obs, bounds = route_mod.obstacles_from_board(a.board, {a.net}, a.layer)
        r = route_mod.route_pair(p1, p2, a.layer, obs, bounds=bounds, net=a.net)
        r.update({"artifact": "eda_eng_route_m3", "module": "M3",
                  "constraints": {"clearance_mm": route_mod.CLEAR, "bounds": bounds, "n_obstacles": len(obs)}})
        return _emit(r, a.json_out, 0 if r["status"] == "ROUTED" else 1)

    if a.cmd == "regen":
        r = regen_mod.run(exam=a.exam_id, work=a.work, dry=a.dry_run)
        code = 0 if r.get("state") in ("RAN", "PLANNED") else 2
        return _emit(r, None, code)

    if a.cmd == "selftest":
        # in-process so it also works under a frozen/packaged KiCad python (no PYTHONPATH games)
        import unittest
        suite = unittest.TestLoader().discover(os.path.join(ROOT, "tools", "eda_eng", "tests"))
        res = unittest.TextTestRunner(verbosity=2).run(suite)
        print(json.dumps({"artifact": "eda_eng_selftest", "tests": res.testsRun,
                          "failures": len(res.failures), "errors": len(res.errors),
                          "skipped": len(res.skipped),
                          "verdict": "PASS" if res.wasSuccessful() else "FAIL"}, ensure_ascii=False))
        return 0 if res.wasSuccessful() else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
