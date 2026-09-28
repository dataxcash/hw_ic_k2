"""eda_eng 回归测试（#K2-358 §三：考题与判卷器＝CI 可重复执行，与 LLM 无关）。"""
import json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from eda_eng import eco, exams, netplan, place, ripup, route, verify   # noqa: E402

L2 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2")
REF = os.path.join(ROOT, verify.BASELINE_BOARD)
REF_DRC = os.path.join(L2, "REROUTE_EXAM_REF_L14_DRC.json")
A1 = os.path.join(ROOT, "hw", "k2_v4_8L.l15-H4CLEAR-attempt1-FAILED.kicad_pcb")
A1_DRC = os.path.join(L2, "H4CLEAR_ATTEMPT1_L15_DRC.json")
A2 = os.path.join(ROOT, "hw", "k2_v4_8L.l15-H4CLEAR-attempt2-FAILED.kicad_pcb")
A2_DRC = os.path.join(L2, "H4CLEAR_ATTEMPT2_L15_DRC.json")


class T(unittest.TestCase):
    def test_ref_artifacts_present(self):
        for p in (REF, REF_DRC, A1, A1_DRC, A2, A2_DRC):
            self.assertTrue(os.path.isfile(p), p)

    def test_sanity_selfgrade_never_passes(self):
        r = verify.judge(REF, REF_DRC, REF, REF_DRC)
        self.assertNotEqual(r["verdict"], "PASS", "a no-op must never PASS (C5 must bite)")
        self.assertFalse(r["criteria"]["C5_routing_changed"]["pass"])

    def test_attempt1_fails_drc_and_chamfer(self):
        r = verify.judge(A1, A1_DRC, REF, REF_DRC)
        self.assertEqual(r["verdict"], "FAIL")
        self.assertFalse(r["criteria"]["C2_drc_no_new_increase"]["pass"])
        self.assertIn("shorting_items", r["criteria"]["C2_drc_no_new_increase"]["new_classes"])

    def test_attempt2_fails_connectivity(self):
        r = verify.judge(A2, A2_DRC, REF, REF_DRC)
        self.assertEqual(r["verdict"], "FAIL")
        self.assertFalse(r["criteria"]["C1_connectivity"]["pass"])

    def test_drc_judging_needs_no_pcbnew(self):
        # C1/C2 come from the DRC json only -> always reproducible in CI
        r = verify.judge(REF, REF_DRC, REF, REF_DRC)
        self.assertIsInstance(r["criteria"]["C1_connectivity"]["pass"], bool)

    def test_exam_definitions(self):
        for k in ("A", "B"):
            e = exams.EXAMS[k]
            self.assertIn("scenario", e)
            self.assertTrue(e["affected_nets"])
        self.assertEqual(len(exams.EXAMS["B"]["affected_nets"]), 8)

    def test_eco_chain_form_complete(self):
        r = eco.check_all()
        self.assertEqual(r["verdict"], "PASS", r)
        self.assertTrue(all(e["registered"] for e in r["ecos"]))

    def test_eco_render_generates_a_conforming_doc(self):
        import tempfile
        spec = {"id": "ECO-K2-9999", "title": "t", "status": "草案", "date": "2026-09-28",
                "authority": "test", "what": "w", "why": "y", "nets": "`A/1`", "docs": "d",
                "rollback": "r", "criteria": "1. total <= 168", "plan": "p", "records": "| x | y | z | t | e |",
                "consistency": "n/a"}
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(eco.render(spec)); path = fh.name
        self.assertTrue(eco.check_form(path)["complete"], eco.check_form(path))
        os.remove(path)

    def test_docs_chain_status(self):
        from eda_eng import docs
        r = docs.chain_status()
        self.assertEqual(r["verdict"], "PASS")
        self.assertTrue(any(row["form_complete"] for row in r["rows"]))

    def test_place_is_declarative_and_never_touches_a_board(self):
        r = place.apply_scenario(["U1", "U2", "U4", "U5"], [5.0, 0.0])
        self.assertFalse(r["board_touched"])
        self.assertEqual(r["delta_mm"], [5.0, 0.0])

    # ---------------- M1 netplan (#K2-360) ----------------
    def test_M1_netplan_matches_the_frozen_expectation_exactly(self):
        exp = json.load(open(os.path.join(L2, "EDA_ENG_NETPLAN_EXPECTATION_U1_v1.json"), encoding="utf-8"))
        r = netplan.plan(REF, ["U1"], [5.0, 0.0])
        self.assertEqual(r["affected_nets"], exp["affected_nets"], "affected net list must match exactly")
        self.assertEqual(r["teardown_totals"], exp["teardown_totals"], "segment/via totals must match exactly")
        counts = {k: {"tracks": len(v["tracks"]), "vias": len(v["vias"])} for k, v in r["teardown"].items()}
        self.assertEqual(counts, exp["teardown_counts_per_net"], "per-net inventory must match exactly")
        self.assertEqual(r["moved_pads"], exp["moved_pads"], "moved pad list must match exactly")

    def test_M1_zero_extra_zero_missing(self):
        exp = json.load(open(os.path.join(L2, "EDA_ENG_NETPLAN_EXPECTATION_U1_v1.json"), encoding="utf-8"))
        r = netplan.plan(REF, ["U1"], [5.0, 0.0])
        got, want = set(r["affected_nets"]), set(exp["affected_nets"])
        self.assertEqual(got - want, set(), "no extra nets")
        self.assertEqual(want - got, set(), "no missing nets")
        self.assertEqual(set(r["teardown"]), want, "teardown must cover exactly the affected nets")

    def test_M1_is_deterministic(self):
        a = netplan.plan(REF, ["U1", "U2"], [5.0, 0.0])
        b = netplan.plan(REF, ["U1", "U2"], [5.0, 0.0])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_M1_delta_is_applied_to_every_moved_pad(self):
        r = netplan.plan(REF, ["U1"], [5.0, 0.0])
        self.assertGreater(r["n_moved_pads"], 0)
        for p_ in r["moved_pads"]:
            self.assertAlmostEqual(p_["new"][0] - p_["old"][0], 5.0, places=4)
            self.assertAlmostEqual(p_["new"][1] - p_["old"][1], 0.0, places=4)

    def test_M1_cluster_plan_is_superset_of_the_single_ref_plan(self):
        one = set(netplan.plan(REF, ["U1"], [5.0, 0.0])["affected_nets"])
        cl = set(netplan.plan(REF, ["U1", "U2", "U4", "U5"], [5.0, 0.0])["affected_nets"])
        self.assertTrue(one.issubset(cl), "the cluster plan must contain the single-ref nets")

    def test_M2_M3_are_not_implemented_yet(self):
        self.assertEqual(ripup.run()["status"], "NOT_IMPLEMENTED")
        import contextlib, io
        from eda_eng import cli
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["route"])                      # M3 subcommand
        self.assertEqual(rc, 2)
        self.assertIn("NOT_IMPLEMENTED", buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["ripup"])                      # M2 subcommand
        self.assertEqual(rc, 2)
        self.assertIn("NOT_IMPLEMENTED", buf.getvalue())

    def test_regen_is_implemented_and_plans_five_stages(self):
        r = route.run(exam="A", work="/tmp/eda_eng_selftest_plan", dry=True)
        self.assertEqual(r["state"], "PLANNED")
        self.assertEqual(r["stages"], ["place", "gen", "route", "polish", "drc"])
        self.assertTrue(all(k in r["commands"] for k in ("gen", "route", "polish", "drc")))

    def test_shadow_root_never_touches_the_real_tree(self):
        from eda_eng import shadow
        import shutil
        w = "/tmp/opencode/eda_eng/selftest_shadow"
        shutil.rmtree(w, ignore_errors=True)
        sh = shadow.build(w + "/shadow")
        r = shadow.edit_placement_at(sh["shadow_root"], ["U1"], [1.0, 0.0])
        self.assertTrue(r["real_source_untouched"])
        self.assertTrue(os.path.islink(os.path.join(sh["shadow_root"], "pm_gate/artifacts/k2_v4/L3"))
                        or os.path.isdir(os.path.join(sh["shadow_root"], "pm_gate/artifacts/k2_v4/L3")))

    def test_placement_edit_preserves_rotation(self):
        from eda_eng import shadow
        import shutil
        w = "/tmp/opencode/eda_eng/selftest_shadow2"
        shutil.rmtree(w, ignore_errors=True)
        sh = shadow.build(w + "/shadow")
        r = shadow.edit_placement_at(sh["shadow_root"], ["U1"], [1.0, 0.0])
        self.assertTrue(all(len(m["new"]) >= 3 for m in r["moves"]), "at must keep (x,y,rot,...)")


if __name__ == "__main__":
    unittest.main()
