#!/usr/bin/env python3
"""eda_eng CLI --- K2 独立确定性 EDA 工程软件（#K2-358）。无 LLM 在场可完整运行。"""
from __future__ import annotations
import argparse, json, os, subprocess, sys

from . import eco as eco_mod, exams as exams_mod, place as place_mod, route as route_mod, verify as verify_mod

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
    p = sub.add_parser("exam", help="run an exam's regression definition")
    p.add_argument("which", choices=["A", "B"])
    p.add_argument("--board"); p.add_argument("--drc")
    p = sub.add_parser("eco", help="validate the ECO chain form")
    p.add_argument("--json-out")
    p = sub.add_parser("docs", help="document-chain status (#K2-357 five links)")
    p.add_argument("--json-out")
    p = sub.add_parser("place", help="declarative placement (scenario applied to the placement source)")
    p.add_argument("--refs", required=True, help="comma-separated refs")
    p.add_argument("--delta", required=True, help="dx,dy in mm")
    p.add_argument("--out"); p.add_argument("--json-out")
    p = sub.add_parser("route", help="rip-up & reroute engine (status)")
    p.add_argument("--exam", dest="exam_id", choices=["A", "B"], default=None)
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
        if a.board and a.drc:
            out.update(verify_mod.judge(a.board, a.drc, REF_BOARD, REF_DRC))
            out["state"] = "GRADED"
        else:
            out["note"] = ("definition only; to grade, pass --board/--drc of the engine's output. "
                           "The engine is NOT implemented yet (see route), so the plan step is unavailable "
                           "and the exam cannot be passed today.")
            out["engine"] = route_mod.STATUS
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

    if a.cmd == "route":
        r = {"artifact": "eda_eng_route", **route_mod.run(exam=a.exam_id)}
        return _emit(r, None, 2)          # explicit non-zero: the capability does not exist yet

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
