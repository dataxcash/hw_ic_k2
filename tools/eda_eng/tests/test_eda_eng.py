"""eda_eng 回归测试（#K2-358 §三：考题与判卷器＝CI 可重复执行，与 LLM 无关）。"""
import json, math, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from eda_eng import eco, exams, netplan, place, regen, ripup, route, verify   # noqa: E402

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

    # ---------------- M2 ripup (#K2-360) ----------------
    # 注：删改板件会破坏同进程的 SWIG 类型态（已诊断过）=> M2 的一切**板面改写**都在**子进程**里做；
    # 测试进程只比对 JSON（`eda_eng dump` 的只读清册 + kicad-cli 的 DRC）。
    def _cli(self, *args):
        import subprocess
        k2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        p = subprocess.run([os.path.join(k2, "tools", "eda_eng.sh"), *args], cwd=k2,
                           capture_output=True, text=True, timeout=1200)
        out = p.stdout
        j = None
        if "{" in out:
            try:   # pcbnew flushes SWIG leak notices to STDOUT at exit -> decode the FIRST json value only
                j = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]
            except Exception:
                j = None
        return p.returncode, j, p.stderr

    def _rip(self, tmpname):
        import tempfile
        plan = netplan.plan(REF, ["U1"], [5.0, 0.0])
        pj = os.path.join(tempfile.mkdtemp(), "plan.json")
        json.dump(plan, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
        out = os.path.join("/tmp/opencode/eda_eng_m2", tmpname)
        os.makedirs("/tmp/opencode/eda_eng_m2", exist_ok=True)
        rc, r, _ = self._cli("ripup", "--board", REF, "--plan", pj, "--out", out)
        self.assertEqual(rc, 0, r)
        return plan, out, r

    def test_M2_removes_exactly_the_plan_and_touches_nothing_else(self):
        plan, out, r = self._rip("t_m2_exact.kicad_pcb")
        self.assertEqual(r["status"], "RIPPED")
        self.assertEqual(r["removed"], {"tracks": plan["teardown_totals"]["tracks"],
                                        "vias": plan["teardown_totals"]["vias"]})
        _, a, _ = self._cli("dump", "--board", REF, "--json-out", "")
        _, b, _ = self._cli("dump", "--board", out, "--json-out", "")
        before, after = a["inventory"], b["inventory"]
        affected = set(plan["affected_nets"])
        for n in set(before) | set(after):
            if n in affected:
                self.assertEqual(after.get(n, {"tracks": [], "vias": []}), {"tracks": [], "vias": []},
                                 "affected net %s must be fully ripped" % n)
            else:
                self.assertEqual(before.get(n, {"tracks": [], "vias": []}), after.get(n, {"tracks": [], "vias": []}),
                                 "net %s was touched but must not be" % n)

    def test_M2_is_deterministic(self):
        _, o1, r1 = self._rip("t_m2_det1.kicad_pcb")
        _, o2, r2 = self._rip("t_m2_det2.kicad_pcb")
        self.assertEqual(r1["out_sha16"], r2["out_sha16"])

    def test_M2_unconnected_appears_only_in_affected_nets(self):
        import re, subprocess
        plan, out, _ = self._rip("t_m2_drc.kicad_pcb")
        cli = os.environ.get("EDA_ENG_CLI", "kicad-cli")
        sj = out + ".drc.json"
        subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "-o", sj, out],
                       capture_output=True, timeout=1200)
        un = json.load(open(sj, encoding="utf-8")).get("unconnected_items", [])
        self.assertGreater(len(un), 0, "ripping an affected net must create disconnections")
        allowed = set(plan["affected_nets"])
        for u in un:
            nets = set(re.findall(r"\[([A-Za-z0-9_+#/.-]+)\]", json.dumps(u, ensure_ascii=False)))
            self.assertTrue(nets & allowed, "unconnected outside the affected nets: %r" % (nets,))

    def test_M2_refuses_a_stale_plan(self):
        import tempfile
        plan = netplan.plan(REF, ["U1"], [5.0, 0.0])
        plan["teardown"]["NOT_A_REAL_NET"] = {"tracks": [{"layer": "F.Cu", "a": [0.0, 0.0], "b": [1.0, 1.0],
                                                         "width_mm": 0.2}], "vias": []}
        pj = os.path.join(tempfile.mkdtemp(), "bad.json")
        json.dump(plan, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
        rc, r, _ = self._cli("ripup", "--board", REF, "--plan", pj, "--out", "/tmp/opencode/eda_eng_m2/nope.kicad_pcb")
        self.assertEqual(r["status"], "REFUSED_STALE_PLAN")

    # ---------------- M4 verify (#K2-360 / #K2-361) ----------------
    def test_M4_judging_table_is_the_sole_source_and_matches_the_ECOs(self):
        import re
        tbl = verify.judging_table()
        self.assertEqual(tbl["thresholds"]["C2_drc_no_new_increase"]["value"], 168)
        self.assertEqual(tbl["thresholds"]["C3_skew"]["value"], 0.15)
        self.assertEqual(tbl["thresholds"]["C4_chamfer_preserved"]["value"], 2637)
        self.assertIn("C4_threshold_unification", tbl["thresholds"]["C4_chamfer_preserved"])
        ecc = open(os.path.join(ROOT, "docs", "ECO", "ECO-K2-0002-reroute-engine-exam-A.md"), encoding="utf-8").read()
        sec6 = ecc[ecc.index("## 6 验收判据"):ecc.index("## 6b")]
        self.assertIn("168", sec6); self.assertIn("0.15", sec6); self.assertIn("2637", sec6)
        self.assertIn("C5", sec6)
        # judge() must consume the table (thresholds_used echoes it)
        r = verify.judge(REF, REF_DRC, REF, REF_DRC)
        self.assertEqual(r["thresholds_used"]["chamfer_ref"], 2637)
        self.assertEqual(r["thresholds_used"]["drc_total"], 168)

    def test_M4_class_delta_attributes_every_rise(self):
        r = verify.class_delta(REF_DRC, REF_DRC)
        self.assertEqual(r["total_delta"], 0)
        self.assertEqual(r["by_class"], {})
        if os.path.isfile(A1_DRC):
            d = verify.class_delta(A1_DRC, REF_DRC)
            self.assertGreater(d["total_delta"], 0)
            self.assertTrue(d["by_class"], "a rise must be attributed class by class")

    # ---------------- M3 route (#K2-360) : toy cases first ----------------
    def test_M3_toy_1_single_net_free_space(self):
        r = route.route_pair([0, 0], [10, 0], "F.Cu", [], net="N1")
        self.assertEqual(r["status"], "ROUTED")
        self.assertEqual(r["poly"][0], [0, 0])
        self.assertEqual(r["poly"][-1], [10, 0])

    def test_M3_toy_2_two_nets_respect_each_other(self):
        a = route.route_pair([0, 0], [10, 0], "F.Cu", [], net="N1")
        self.assertEqual(a["status"], "ROUTED")
        obs = [{"id": "N1", "kind": "copper", "net": "N1",
                "bbox": [min(p[0] for p in a["poly"]) - 0.1, min(p[1] for p in a["poly"]) - 0.1,
                         max(p[0] for p in a["poly"]) + 0.1, max(p[1] for p in a["poly"]) + 0.1]}]
        b = route.route_pair([0, 5], [10, 5], "F.Cu", obs, net="N2")
        self.assertEqual(b["status"], "ROUTED")
        self.assertEqual(route.poly_violations(b["poly"], obs), [], "N2 must clear N1")

    def test_M3_toy_3_blocked_is_named(self):
        wall = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [4.5, -5, 5.5, 5]}]
        r = route.route_pair([0, 0], [10, 0], "F.Cu", wall, net="N1")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertTrue(any(v["obstacle"] == "wall" for v in r["violations"]))

    def test_M3_toy_4_keepout_is_respected(self):
        ko = [{"id": "KO", "kind": "keepout", "bbox": [4.5, -1, 5.5, 1]}]
        r = route.route_pair([0, 0], [10, 0], "F.Cu", ko, net="N1")
        self.assertEqual(r["status"], "BLOCKED", "a keepout across the straight line must block the trivial candidate")
        self.assertIn("keepout", [v["kind"] for v in r["violations"]])

    def test_M3_is_deterministic(self):
        a = route.route_pair([0, 0], [9, 3], "F.Cu", [])
        b = route.route_pair([0, 0], [9, 3], "F.Cu", [])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_M3_region_case_on_l14_with_immediate_connectivity_check(self):
        """区域用例：真板 l14 上挑一对**同网相邻 pad**，布一段，落板（子进程）后**即时**查连通与 DRC。"""
        import subprocess, tempfile
        # 障碍必须**排除待布网自身**（同网铜是它自己的，不是障碍）
        pads = route.pads_by_net(REF, "F.Cu")
        pick = None
        for net in sorted(pads):
            if net == "GND" or len(pads[net]) < 2:
                continue
            pts = sorted(pads[net])
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    if math.dist(pts[i], pts[j]) > 5.0:
                        continue
                    # 区域用例 = 真板上**确有可行走法**的一对（直段无违规）=> 引擎必须给出见证
                    obs_n, _b = route.obstacles_from_board(REF, {net}, "F.Cu")
                    if not route.poly_violations([list(pts[i]), list(pts[j])], obs_n):
                        pick = (net, list(pts[i]), list(pts[j])); break
                if pick:
                    break
            if pick:
                break
        self.assertIsNotNone(pick, "no same-net pad pair within 5 mm found")
        net, p1, p2 = pick
        obs, bounds = route.obstacles_from_board(REF, {net}, "F.Cu")
        r = route.route_pair(p1, p2, "F.Cu", obs, bounds=bounds, net=net)
        self.assertEqual(r["status"], "ROUTED", "region case must route: %r" % (r.get("violations"),))
        self.assertEqual(route.poly_violations(r["ploy"] if False else r["poly"], obs), [],
                         "the routed witness must clear every obstacle")
        plan = os.path.join(tempfile.mkdtemp(), "plan.json")
        json.dump(r, open(plan, "w", encoding="utf-8"), ensure_ascii=False)
        out = os.path.join("/tmp/opencode/eda_eng_m3", "region_%s.kicad_pcb" % net)
        os.makedirs("/tmp/opencode/eda_eng_m3", exist_ok=True)
        rc, ap, _ = self._cli("route", "--apply", plan, "--board", REF, "--out", out)
        self.assertEqual(rc, 0, ap)
        self.assertGreaterEqual(ap["segments_added"], 1)
        cli = os.environ.get("EDA_ENG_CLI", "kicad-cli")
        sj = out + ".drc.json"
        subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "-o", sj, out],
                       capture_output=True, timeout=1200)
        d = json.load(open(sj, encoding="utf-8"))
        shorts = [v for v in d.get("violations", []) if v.get("type") == "shorting_items"
                  and net in json.dumps(v, ensure_ascii=False)]
        self.assertEqual(shorts, [], "the added copper must not short net %s" % net)
        un = [u for u in d.get("unconnected_items", []) if net in json.dumps(u, ensure_ascii=False)]
        self.assertEqual(un, [], "net %s must be fully connected after the route" % net)
        # #K2-361 sec.2.5: the board-level rise must be attributed AND resolved (the apply step must not
        # perturb the board beyond the added segments - the engine fix is to carry the project config)
        cd = verify.class_delta(sj, REF_DRC)
        self.assertEqual(cd["total_delta"], 0,
                         "apply must not perturb the board config; attribution was %r" % (cd,))

    def test_C29_preflight_refuses_a_mechanically_illegal_scenario(self):
        """C29 关闭判据（#K2-361 sec.4）：非法场景被 preflight 拦下、**零重活运行**。"""
        from eda_eng import regen
        pf = regen.preflight("A", "/tmp/eda_eng_selftest_pf")
        self.assertFalse(pf["ok"], "the +X 4.000 mm scenario must be refused by the strengthened gate")
        self.assertTrue(pf["P1_scenario_legality"]["ok"], "it is pad-legal ...")
        self.assertTrue(pf["P1b_mechanical_legality"]["new_mechanical_violations"],
                        "... but mechanically illegal (zero heavy runs spent); P1b is BASELINE-RELATIVE and the "
                        "probe includes the crtyd stage (both defects were found by the scenario sweep)")

    def test_regen_is_implemented_and_plans_five_stages(self):
        r = regen.run(exam="A", work="/tmp/eda_eng_selftest_plan", dry=True)
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
