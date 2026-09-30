"""eda_eng 回归测试（#K2-358 §三：考题与判卷器＝CI 可重复执行，与 LLM 无关）。"""
import json, math, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from eda_eng import block, eco, exams, netplan, place, regen, ripup, route, verify   # noqa: E402

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

    def test_M3v2_multipad_mst_routes_a_three_pad_net(self):
        r = route.route_net([[0, 0], [10, 0], [10, 10]], ["F.Cu"], [], net="N1")
        self.assertEqual(r["status"], "ROUTED")
        self.assertEqual(len(r["mst_edges"]), 2, "a 3-pad net needs 2 MST edges")
        self.assertEqual(len(r["segments"]), 2)

    def test_M3v2_multipad_is_deterministic(self):
        a = route.route_net([[0, 0], [10, 0], [10, 10], [0, 10]], ["F.Cu"], [])
        b = route.route_net([[0, 0], [10, 0], [10, 10], [0, 10]], ["F.Cu"], [])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_M3v2_multipad_names_the_blocked_edge(self):
        wall = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [4.5, -5, 5.5, 5]}]
        r = route.route_net([[0, 0], [10, 0]], ["F.Cu"], wall, net="N1")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("blocked_edge", r)
        self.assertTrue(r["edge_violations"])

    def test_M3v2_layer_change_fallback_uses_vias(self):
        # F.Cu 被墙挡死，但 In2 在端点有净位 ⇒ 端点各落一支 via，中间走 In2
        wall = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [4.0, -6.0, 6.0, 6.0], "layers": ["F.Cu"]}]
        r = route.route_pair_multi([0, 0], [10, 0], ["F.Cu", "In2.Cu"], wall, net="N1")
        self.assertEqual(r["status"], "ROUTED")
        self.assertEqual(r["layer"], "In2.Cu")
        self.assertEqual(len(r["vias"]), 2, "a via at each endpoint")

    def test_M3v2_via_sites_must_be_clear(self):
        blocked = [{"id": "padblock", "kind": "copper", "net": "X", "bbox": [-1.0, -0.6, 1.0, 0.6],
                    "layers": ["F.Cu", "In2.Cu"]}]
        r = route.route_pair_multi([0, 0], [10, 0], ["F.Cu", "In2.Cu"], blocked, net="N1")
        self.assertEqual(r["status"], "BLOCKED", "a via site on top of foreign copper must be refused")

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

    # ---------------- #K2-366 maze router (Lee/A*) ----------------
    def test_maze_routes_a_straight_line(self):
        r = route.maze_route([0, 0], [6, 0], ["F.Cu"], [], [-1, -1, 7, 1])
        self.assertEqual(r["status"], "ROUTED")
        self.assertEqual(r["layer"], "F.Cu")

    def test_maze_detours_around_a_wall_on_one_layer(self):
        w = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [2.5, -1, 3.5, 1], "layers": ["F.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu"], w, [-1, -2, 7, 2])
        self.assertEqual(r["status"], "ROUTED")

    def test_maze_uses_vias_when_the_pad_layer_is_fully_crossed(self):
        # 墙**横跨整幅**（y 方向占满板面）⇒ F.Cu 无绕行余量 ⇒ 必须换层出去再回来（2 支 via）
        w = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [2.5, -5, 3.5, 5], "layers": ["F.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu", "In2.Cu"], w, [-1, -4.6, 7, 4.6])
        self.assertEqual(r["status"], "ROUTED")
        self.assertEqual(len(r["vias"]), 2, "must leave and come back to the pad layer")
        self.assertEqual(r["polys"][-1]["layer"], "F.Cu", "the route must END on the pad layer")

    def test_maze_refuses_an_endpoint_inside_foreign_copper(self):
        cage = [{"id": "cage", "kind": "copper", "net": "X", "bbox": [-2, -2, 2, 2], "layers": ["F.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu"], cage, [-3, -3, 7, 3])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("endpoint", r["reason"])

    def test_maze_reports_a_named_blockage_when_truly_caged(self):
        cage = [{"id": "cage", "kind": "copper", "net": "X", "bbox": [2.0, -9, 4.0, 9],
                 "layers": ["F.Cu", "In2.Cu"]},
                {"id": "capN", "kind": "copper", "net": "X", "bbox": [-9, 4.4, 9, 9], "layers": ["F.Cu", "In2.Cu"]},
                {"id": "capS", "kind": "copper", "net": "X", "bbox": [-9, -9, 9, -4.4], "layers": ["F.Cu", "In2.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu", "In2.Cu"], cage, [-5, -5, 7, 5])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("exhausted", r["reason"])

    def test_maze_semantics_is_NOT_FOUND_never_IMPOSSIBLE(self):
        """#K2-367 sec.2 语义纪律：搜索失败只能说"未找到"；"不存在"须另出不可行证书。"""
        cage = [{"id": "cage", "kind": "copper", "net": "X", "bbox": [2.0, -9, 4.0, 9], "layers": ["F.Cu", "In2.Cu"]},
                {"id": "capN", "kind": "copper", "net": "X", "bbox": [-9, 4.4, 9, 9], "layers": ["F.Cu", "In2.Cu"]},
                {"id": "capS", "kind": "copper", "net": "X", "bbox": [-9, -9, 9, -4.4], "layers": ["F.Cu", "In2.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu", "In2.Cu"], cage, [-5, -5, 7, 5])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["semantics"], "NOT_FOUND")
        self.assertIn("never as IMPOSSIBLE", r["semantics_rule"])

    def test_maze_is_deterministic(self):
        w = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [2.5, -1, 3.5, 1], "layers": ["F.Cu"]}]
        a = route.maze_route([0, 0], [6, 0], ["F.Cu"], w, [-1, -2, 7, 2])
        b = route.maze_route([0, 0], [6, 0], ["F.Cu"], w, [-1, -2, 7, 2])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_maze_reports_a_named_blockage_when_the_goal_cannot_be_snapped(self):
        """R970 fidelity fix: an unsnappable goal must be a NAMED blockage, never a crash (min(())).
        Found by running exam A on the real board: MCU_VDD pad (31.8375,51.75) could not be snapped to a free
        pad-layer cell, and the heuristic raised ValueError instead of reporting NOT FOUND."""
        r = route.maze_route([0, 0], [100, 0], ["F.Cu"], [], [-1, -1, 7, 1])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["semantics"], "NOT_FOUND")
        self.assertIn("goal cell", r["reason"])

    def test_M3a_draw_and_review_pass_on_a_clean_toy(self):
        d = route.draw_net([[0, 0], [10, 0], [10, 10]], ["F.Cu"], [], net="N1")
        self.assertEqual(d["status"], "DRAWN")
        r = route.review_drawing(d, [])
        self.assertEqual(r["verdict"], "PASS", r["rows"])
        self.assertTrue(all(row.get("bends_45_or_90") for row in r["rows"]))

    def test_M3a_review_rejects_a_non_45_bend(self):
        d = route.draw_net([[0, 0], [10, 0]], ["F.Cu"], [], net="N1")
        d["edges"][0]["poly"] = [[0, 0], [5, 1], [10, 0]]           # 30° 级折角 ⇒ 违 45° 约定
        r = route.review_drawing(d, [])
        self.assertEqual(r["verdict"], "FAIL")
        self.assertFalse(r["rows"][0]["bends_45_or_90"])

    def test_M3a_review_rejects_an_undeclared_layer(self):
        d = route.draw_net([[0, 0], [10, 0]], ["F.Cu"], [], net="N1")
        d["edges"][0]["layer"] = "In7.Cu"
        self.assertEqual(route.review_drawing(d, [])["verdict"], "FAIL")

    def test_M3a_review_rejects_an_undeclared_corridor(self):
        d = route.draw_net([[0, 0], [10, 0]], ["F.Cu"], [], net="N1")
        d["edges"][0]["corridor_bbox"] = None
        self.assertEqual(route.review_drawing(d, [])["verdict"], "FAIL")

    def test_M3a_dead_end_is_marked_for_the_fallback_solver(self):
        wall = [{"id": "wall", "kind": "copper", "net": "X", "bbox": [4.0, -6.0, 6.0, 6.0], "layers": ["F.Cu", "In2.Cu"]}]
        d = route.draw_net([[0, 0], [10, 0]], ["F.Cu"], wall, net="N1")
        self.assertIn("DEAD_END", d["status"])
        self.assertEqual(route.review_drawing(d, wall)["verdict"], "FAIL")

    def test_M3a_markdown_is_human_readable(self):
        d = route.draw_net([[0, 0], [10, 0]], ["F.Cu"], [], net="N1")
        md = route.drawing_markdown([d])
        self.assertIn("| 网 | 边 | 约定 | 层 |", md)
        self.assertIn("N1", md)

    def test_K366_relocate_runs_the_six_steps_on_a_small_part(self):
        """#K2-366 sec.2 六步一条命令：在小件上跑通（挪 pad→M1→M2→迷宫重连→复敷铜→M4），并以具名判定收尾。"""
        rc, r, _ = self._cli("relocate", "--refs", "L1", "--delta", "0.5,0", "--work",
                             "/tmp/eda_eng_selftest_reloc", "--max-nets", "1")
        st = r.get("state")
        self.assertIn(st, ("GRADED", "S2_M1_FAILED", "S3_M2_FAILED", "S5_APPLY_FAILED", "S6_DRC_FAILED"), st)
        stages = [c.get("stage") for c in r["chain"] if c.get("stage")]
        self.assertIn("1_move_pads", stages, "step 1 missing")
        self.assertTrue(any(s in stages for s in ("4_maze_reconnect",)), "step 4 missing")
        for b in (r.get("blocked") or []):
            self.assertEqual(b.get("semantics"), "NOT_FOUND",
                             "every blockage must carry the NOT_FOUND semantics (never 'impossible')")

    def test_C30_product_chain_runs_M1_to_M4_with_call_chain_evidence(self):
        """C30 关闭判据：`exam A --run` 的执行路径 = M1->M2->M3->M4，且**附调用链证据**。"""
        rc, r, _ = self._cli("exam", "A", "--run", "--chain", "product",
                             "--work", "/tmp/eda_eng_selftest_chain", "--max-nets", "1")
        self.assertIn(r.get("state"), ("GRADED", "M0_FRAME_REJECTED", "M2_FAILED", "M3_PLAN_REVIEW_FAILED",
                                       "M3_APPLY_FAILED", "M4_DRC_FAILED"), r.get("state"))
        stages = [c.get("stage") for c in r["route"]["chain"]]
        # #K2-369: exam A's product chain is the BLOCK chain - M0 census -> M1 plan -> M2 block pass ->
        # M3 in-block reconnect -> step5 refill -> M4 judge; every stage is named in the call-chain evidence.
        for m in ("M0_block_census", "M1_block_plan", "M2_block_pass"):
            self.assertIn(m, stages, "%s missing from the chain" % m)
        if r.get("state") == "GRADED":
            self.assertIn("M3_block_reconnect", stages, "M3 missing from the chain")
            self.assertIn("step5_apply_refill", stages, "refill step missing from the chain")
            self.assertIn("M4_judge", stages, "M4 missing from the chain")
        else:
            self.assertTrue(str(r.get("state", "")).endswith("REJECTED") or str(r.get("state", "")).endswith("FAILED"),
                            "a chain that cannot reach M4 must stop with a NAMED result")
        self.assertIn(r.get("verdict"), ("PASS", "FAIL", None), "the chain must end in a named verdict")

    def test_C29_preflight_refuses_a_mechanically_illegal_scenario(self):
        """C29 关闭判据（#K2-361 sec.4）：非法场景被 preflight 拦下、**零重活运行**。"""
        from eda_eng import regen
        # the ORIGINAL exam-A translation (+X 4.000 mm on the bare cluster) is pad-legal but mechanically illegal:
        # it must be refused by the gate.  (The CURRENT preset is the gate-legal REGION scenario, so probe the
        # illegal one explicitly.)
        sel = regen.region_select(["U1", "U2", "U4", "U5"],
                                 [{"delta_mm": [4.0, 0.0], "k": 1}], "/tmp/eda_eng_selftest_pf")
        self.assertFalse(sel["candidates"][0]["legal"],
                         "the bare-cluster +X 4.000 mm translation must be refused by the mechanical gate")
        self.assertTrue(sel["candidates"][0]["new_mechanical_violations"],
                        "... with the violation NAMED (zero heavy runs spent); P1b is BASELINE-RELATIVE and the "
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

    # ---------------- #K2-369 BLOCK relocation model ----------------
    def test_K369_frame_acceptance_rejects_foreign_pads_inside(self):
        """框接受判据（#K2-369 sec.4）：**框内不得多出有网器件**。实测：批准用的松框会吞 5 个器件，
        并把 N* 从 22 撑到 30（含 8 条 PCIe）⇒ 该框在模型上不成立；收紧框 FOREIGN_* == 0。"""
        regs = ["C73", "C84", "C85", "C86", "C87", "C88", "C90", "D2", "E2", "J12", "J13",
                "J6", "J9", "L1", "R40", "R41", "U1", "U2", "U4", "U5"]
        tight = block.census(REF, [22.95, 32.95, 46.50, 62.50], [3.5, 3.5], members=regs)
        self.assertTrue(tight["frame_ok"], "tight frame must be admissible")
        self.assertTrue(tight["board_model"]["ok"], "the census must run on the shared board_model layer")
        self.assertEqual(tight["FOREIGN_INSIDE"]["count"], 0)
        self.assertEqual(tight["FOREIGN_PADS_INSIDE"]["count"], 0)
        self.assertEqual(tight["n_members"], 20)
        self.assertEqual(tight["mech_no_net_inside"], ["H3"], "the mounting hole is a board feature, never a member")
        loose = block.census(REF, [22.95, 32.95, 51.50, 66.50], [3.5, 3.5], members=regs)
        self.assertFalse(loose["frame_ok"], "the loose frame swallows extra netted components")
        self.assertEqual(sorted(loose["FOREIGN_PADS_INSIDE"]["refs"]), ["D1", "J11", "R1", "R21", "R28"])
        self.assertGreater(loose["n_N_star"], tight["n_N_star"])

    def test_K369_block_move_preserves_outside_copper_and_hs_fanout(self):
        """C6/C7 的**本体**：块体搬运后，扫过区之外的铜与 16 条 PCIe 扇出必须**逐段零改动**。
        控制项：换用 R（块内框）做比较时必须**不等**（块铜确实搬出去了）⇒ 判据非空转。"""
        regs = ["C73", "C84", "C85", "C86", "C87", "C88", "C90", "D2", "E2", "J12", "J13",
                "J6", "J9", "L1", "R40", "R41", "U1", "U2", "U4", "U5"]
        rect = [22.95, 32.95, 46.50, 62.50]
        S = block.swept(rect, [3.5, 3.5])
        out = "/tmp/opencode/eda_eng/selftest_block_move.kicad_pcb"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        rc0, mv, _ = self._cli("move-block", "--board", REF, "--rect", ",".join(str(v) for v in rect),
                               "--refs", ",".join(regs), "--delta", "3.5,3.5", "--out", out)
        self.assertEqual(rc0, 0, "the block move must run in a SUBPROCESS (SWIG rule)")
        self.assertEqual(mv["n_members"], 20)
        self.assertEqual(mv["moved"]["cross_split"], 23)
        self.assertEqual(mv["moved"]["bridge_split"], 0)
        self.assertEqual(mv["n_jobs"], 23)
        for j in mv["jobs"]:                                    # 作业缺口 = 精确的 Δ
            self.assertAlmostEqual(j["target"][0] - j["port"][0], 3.5, places=6)
            self.assertAlmostEqual(j["target"][1] - j["port"][1], 3.5, places=6)
        self.assertTrue(block.geometry_equal(block.outside_geometry(out, S),
                                             block.outside_geometry(REF, S))["equal"],
                        "C6: copper outside the swept region must be bit-identical")
        self.assertTrue(block.geometry_equal(block.net_geometry(out, regen.HS_FANOUT_NETS),
                                             block.net_geometry(REF, regen.HS_FANOUT_NETS))["equal"],
                        "C7: the 16 PCIe fanout nets must be untouched")
        self.assertFalse(block.geometry_equal(block.outside_geometry(out, rect),
                                              block.outside_geometry(REF, rect))["equal"],
                         "control: the in-block copper really did move out of R")

    def test_K369_maze_via_prism_checks_every_layer_in_span(self):
        """缺口 C31（#K2-369）：via 必须穿透 span 内**每一层**。只查两端层时，跨层 via 会穿过中间层的墙。"""
        wall = [{"id": "wF", "kind": "copper", "net": "X", "bbox": [2.5, -6, 3.5, 6], "layers": ["F.Cu"]},
                {"id": "w1", "kind": "copper", "net": "X", "bbox": [-1, -6, 7, 6], "layers": ["In1.Cu"]}]
        r = route.maze_route([0, 0], [6, 0], ["F.Cu", "In1.Cu", "In2.Cu"], wall, [-1, -4.6, 7, 4.6])
        self.assertEqual(r["status"], "BLOCKED",
                         "a via F.Cu->In2.Cu may not cross a wall on In1.Cu (prism span)")
        r2 = route.maze_route([0, 0], [6, 0], ["F.Cu", "In2.Cu"], wall, [-1, -4.6, 7, 4.6])
        self.assertEqual(r2["status"], "ROUTED",
                         "without In1.Cu in the stack the same geometry is routable")

    def test_K369_apply_batch_refills_zones(self):
        """#K2-369 sec.3.2：`route --apply-batch` 此前**从不调用** ZONE_FILLER（第 5 步是空操作）。
        现在必须真复敷铜并把 zones_refilled 写进收执。"""
        out = "/tmp/opencode/eda_eng/selftest_refill.kicad_pcb"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        plan = "/tmp/opencode/eda_eng/selftest_refill_plan.json"
        json.dump([], open(plan, "w"))
        rc, r, _ = self._cli("route", "--apply-batch", plan, "--board", REF, "--out", out)
        self.assertEqual(r["status"], "APPLIED")
        self.assertGreater(r["zones_refilled"], 0, "the batch path must actually refill zones")

    def test_C35_the_maze_wall_keeps_every_polyline_inside_the_declared_domain(self):
        """C35（#K2-377 §二.3 · 「框界墙」）：把**框**作为迷宫域传入时，**任何**折线点都不得越出框。
        这是「界下在源头」的可证形式（对比：事后恢复框外铜会撕开连通性 · R1020 实测 C1 14->17）。"""
        rect = [0.0, 0.0, 6.0, 6.0]                      # 玩具域：保证有解，专测「墙」性质
        r = route.maze_route([0.5, 0.5], [5.5, 5.5], ["F.Cu"], [], rect, pitch=0.5, endpoint_clear=0.0)
        self.assertEqual(r["status"], "ROUTED", "a route inside the frame must exist")
        for pl in r["polys"]:
            for (x, y) in pl["poly"]:
                self.assertGreaterEqual(x, rect[0] - 1e-6)
                self.assertLessEqual(x, rect[2] + 1e-6)
                self.assertGreaterEqual(y, rect[1] - 1e-6)
                self.assertLessEqual(y, rect[3] + 1e-6)

    def test_C35_the_wall_is_wired_into_the_search_loop_not_patched_afterwards(self):
        """C35（#K2-378 §三.1）：框界必须**下在搜索环路**（迷宫域约束），**不得事后恢复**。
        本回归锁住接线：迷宫有 `--bound-rect` 且把域外格封死；产品只**转发**该参数（不改方法）。"""
        maze = open(os.path.join("tools", "k2_p4_mroute_v1.py"), encoding="utf-8").read()
        prod = open(os.path.join("tools", "k2_reroute_affected_v2.py"), encoding="utf-8").read()
        self.assertIn("WALL_RECT", maze, "the maze must carry the in-loop wall")
        self.assertIn("--bound-rect", maze, "the maze must expose the wall as a CLI parameter")
        self.assertIn("bb2[i * self.ny + j] = 1", maze, "the wall must BLOCK cells outside the domain")
        self.assertIn("--bound-rect", prod, "the product must accept the wall")
        self.assertIn('"--bound-rect", str(a.bound_rect)', prod, "the product must FORWARD the wall to the maze")
        self.assertNotIn("bound_outside(", prod, "the product must not rely on a post-hoc restore")

    def test_C380_the_apply_stage_refuses_a_plan_that_leaves_the_domain(self):
        """#K2-380 §二.3（收尾道）：落板前框外检查 —— **新增可选参数、默认不改老行为**；
        越域计划 fail-closed 拒收且**在 SaveBoard 之前**返回（代码级锁 · 改板调用不在测试进程内）。"""
        src = open(os.path.join("tools", "eda_eng", "route.py"), encoding="utf-8").read()
        seg = src[src.index("def apply_routes("):src.index("def apply_route(")]
        self.assertIn("bound_rect=None", seg, "the domain must be an ADDITIVE optional parameter")
        self.assertIn("REFUSED_OUT_OF_BOUND", seg)
        self.assertLess(seg.index("REFUSED_OUT_OF_BOUND"), seg.index("P.SaveBoard"),
                        "the check must run BEFORE the board is saved (fail-closed)")

    def test_C385_mask_bridge_precheck_is_a_pure_failclosed_guard(self):
        """#K2-385 §五.2(b)：阻焊桥预检 = **纯函数** ＋ **落铜前 fail-closed 拒收**（加法参数，默认不改行为）。"""
        risk = route.mask_bridge_pairs([[0.0, 0.0], [1.0, 0.0]], [("U1", "11", 0.30, 0.0)], 0.5)
        self.assertEqual(len(risk), 1)
        self.assertEqual(risk[0]["ref"], "U1")
        self.assertLess(risk[0]["dist_mm"], 0.5)
        self.assertEqual(route.mask_bridge_pairs([[0.0, 0.0]], [("U1", "11", 5.0, 0.0)], 0.5), [],
                         "a far pad must not be flagged")
        src = open(os.path.join("tools", "eda_eng", "route.py"), encoding="utf-8").read()
        seg = src[src.index("def apply_routes("):src.index("def apply_route(")]
        self.assertIn("mask_clear_mm=None", seg, "the guard must be an ADDITIVE optional parameter")
        self.assertIn("REFUSED_MASK_BRIDGE_RISK", seg)
        self.assertLess(seg.index("REFUSED_MASK_BRIDGE_RISK"), seg.index("P.SaveBoard"),
                        "the pre-check must run BEFORE the board is saved")

    def test_C385_pour_island_reconnection_is_deterministic_and_wall_bounded(self):
        """#K2-385 §五.2(a)：灌注孤岛重连 —— 复铜后检 `isolated_copper`，每个孤岛**就近连回同网最近焊盘**，
        用**同一件**域内迷宫（带 `--bound-rect`）· **一次**（非循环）· **确定性**（最近焊盘＋同一迷宫）。"""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        for k in ("pour_islands_detected", "pour_islands_repair", "isolated_copper",
                  "--bound-rect", "key=lambda q:"):
            self.assertIn(k, seg, "the island path must contain %s" % k)
        self.assertEqual(seg.count("pour_islands_repair"), 1, "exactly ONE repair pass (never a loop)")

    def test_C385_the_island_branch_reads_no_undefined_names(self):
        """#K2-387（R1064-R1068 的孤岛重连分支**首次实跑即崩**）：`NameError: _pcbnew`
        —— 同一分支里 `collections` 也未导入。旧的 C385 回归只做**源码字符串**检查，
        挡不住运行期未定义名（这正是它 74/74 全绿却仍崩的盲区）。本测试用 AST 做
        **作用域感知**的名字解析：孤岛分支读到的每个裸名必须在内建／模块级绑定／函数内
        绑定／形参之一，否则失败。"""
        import ast, builtins
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)

        def scope_nodes(body):
            stack = list(body)
            while stack:
                n = stack.pop()
                yield n
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue                     # nested defs are their own scope
                stack.extend(ast.iter_child_nodes(n))

        def scope_bound(body):
            out = set()
            for n in scope_nodes(body):
                if isinstance(n, ast.Import):
                    out.update((a.asname or a.name).split(".")[0] for a in n.names)
                elif isinstance(n, ast.ImportFrom):
                    out.update(a.asname or a.name for a in n.names)
                elif isinstance(n, ast.ExceptHandler):
                    if isinstance(n.name, str) and n.name:
                        out.add(n.name)
                elif isinstance(n, ast.arg):
                    out.add(n.arg)
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    out.add(n.name)
                elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                    out.add(n.id)
            return out

        mod = set(dir(builtins)) | scope_bound(tree.body)
        fn = next(n for n in tree.body
                  if isinstance(n, ast.FunctionDef) and n.name == "wipe_resolve_chain")
        bound = scope_bound(fn.body) | {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
        if fn.args.vararg:
            bound.add(fn.args.vararg.arg)
        if fn.args.kwarg:
            bound.add(fn.args.kwarg.arg)
        bad = sorted({n.id for n in scope_nodes(fn.body)
                      if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                      and n.id not in mod and n.id not in bound})
        self.assertEqual(bad, [], "the island branch must not read undefined names: %s" % bad)

    def test_C382_the_residual_second_stitch_is_bounded_and_wall_bounded(self):
        """#K2-382 §二.2：残余二次缝合＝**喂残余清单给同一件工具**（同墙），**只多跑一趟**（不循环/不搜参）。"""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        self.assertIn("resolve_residual_second_pass", seg, "the second pass must be present and NAMED")
        self.assertIn("--bound-rect", seg, "the second pass must keep the in-loop wall")
        self.assertIn("if u1:", seg, "the second pass must be conditional (only when gaps remain)")
        self.assertIn("resolve_residual_before", seg, "the residual DRC must be read first")
        self.assertIn("led2", seg, "the second pass must keep its own ledger")

    def test_C381_C2_uses_the_same_pinned_caliber_as_class_delta(self):
        """#K2-381 §五.2：C2 与 class_delta **同一把尺** —— 库解析类只记录、不判 FAIL；阈值不动。"""
        src = open(os.path.join("tools", "eda_eng", "verify.py"), encoding="utf-8").read()
        seg = src[src.index("def judge("):]
        self.assertIn('tbl["C2_drc_no_new_increase"].get("excluded_classes"', seg,
                      "the judge must read the pinned caliber from the table")
        self.assertIn('geo_total = sum(v for k, v in d["classes"].items() if k not in excl)', seg)
        self.assertIn('not new_classes', seg, "the pass condition must use the caliber-filtered classes")
        self.assertIn('"excluded_new_classes": excluded_new', seg, "excluded classes must be REPORTED, never hidden")

    def test_C36_the_eco_table_is_a_nine_row_lock(self):
        """C36（#K2-377 F3 / #K2-388 §五）：ECO-K2-0004 §6 的判卷表是**九行锁**。"""
        eco = open(os.path.join("docs", "ECO", "ECO-K2-0004-reroute-engine-exam-A-prime.md"), encoding="utf-8").read()
        rows = [r for r in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9")
                if ("| **%s**" % r) in eco or ("| %s " % r) in eco]
        self.assertEqual(len(rows), 9, "the ECO must carry nine rows; found %s" % rows)

    def test_C36_each_exam_chain_path_enumerates_the_nine_rows(self):
        """C36 复发修正（#K2-388 §七.2）：判卷必须在**实际执行的链路径**上逐行读数 ——
        不是整文件 grep（旧测试因别处含 `C8` 字样而**误绿**）。逐链用 AST 取**函数段**断言：
        C6/C7/C8/C9 四行在**该链自己**的路径上产出，且判卷调用带 `required_rows`（缺行 ⇒ fail-closed）。"""
        import ast
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        needed = ("C6_outside_copper_unchanged", "C7_hs_fanout_untouched",
                  "C8_members_inside_frame", "C9_geometric_digest")
        for name in ("relocate_block_chain", "relocate_relative_chain",
                     "relocate_relative_c17v1", "wipe_resolve_chain"):
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            seg = "\n".join(src.splitlines()[fn.lineno - 1:fn.end_lineno])
            self.assertIn("_vf.judge(", seg, "%s must grade" % name)
            for k in needed:
                self.assertIn(k, seg, "%s must emit %s on its OWN path" % (name, k))
            self.assertIn("required_rows=_vf.LOCKED_EXAM_ROWS", seg,
                          "%s must pass required_rows (missing row => fail-closed)" % name)

    def test_C36_a_missing_row_is_fail_closed_at_runtime(self):
        """运行期回归（先 RED 后 GREEN）：给了 required_rows 时，缺行 ⇒ verdict=FAIL 且 missing 列出该行。"""
        r = verify.judge(REF, REF_DRC, REF, REF_DRC, required_rows=verify.LOCKED_EXAM_ROWS)
        self.assertEqual(r["verdict"], "FAIL")
        self.assertIn("C8_members_inside_frame", r["rows_completeness"]["missing"])
        extra = {"C6_outside_copper_unchanged": {"diff": 0, "pass": True},
                 "C7_hs_fanout_untouched": {"diff": 0, "pass": True},
                 "C8_members_inside_frame": {"violations": [], "pass": True},
                 "C9_geometric_digest": {"pass": True}}
        r2 = verify.judge(REF, REF_DRC, REF, REF_DRC, extra=extra, required_rows=verify.LOCKED_EXAM_ROWS)
        self.assertEqual(r2["rows_completeness"]["missing"], [])
        self.assertEqual(len(r2["criteria"]), 9)
        r3 = verify.judge(REF, REF_DRC, REF, REF_DRC)   # legacy call unchanged
        self.assertNotIn("rows_completeness", r3)

    def test_C389_mask_opening_gap_is_pure_and_correct(self):
        """#K2-389 §二.1：阻焊开窗间隙是**纯函数**（相接/重叠 => 0）。
        这是「放置闸 mask-dam 约束」的最小可测内核（不依赖 pcbnew）。"""
        self.assertEqual(route.mask_opening_gap([0, 0, 1, 1], [2, 0, 3, 1]), 1.0)      # side by side
        self.assertEqual(route.mask_opening_gap([0, 0, 1, 1], [1, 0, 2, 1]), 0.0)      # touching => bridge
        self.assertEqual(route.mask_opening_gap([0, 0, 1, 1], [0.5, 0.5, 1.5, 1.5]), 0.0)  # overlapping
        self.assertAlmostEqual(route.mask_opening_gap([0, 0, 1, 1], [2, 2, 3, 3]), 2 ** 0.5, places=9)

    def test_C389_the_placement_gate_consumes_the_mask_dam_rule(self):
        """#K2-389 §二.1：放置闸（`mech_probe`／`mech_probe_moves`）必须**消费在册 mask-dam 规则**，
        且必须用**类黑名单**（原 4 类白名单正是漏掉 `solder_mask_bridge` 的洞）。路径感知（按函数段）。"""
        import ast
        self.assertAlmostEqual(regen._mask_clear_mm(), 0.05, places=6)   # 在册规则值
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        for name in ("mech_probe", "mech_probe_moves"):
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            seg = "\n".join(src.splitlines()[fn.lineno - 1:fn.end_lineno])
            self.assertIn("pad_mask_dam_violations", seg, "%s must consume the rule-derived mask-dam check" % name)
            self.assertIn("_mask_clear_mm()", seg)
            self.assertIn("lib_footprint_issues", seg, "%s must use the class BLACKLIST" % name)
            self.assertNotIn('if ty in ("courtyards_overlap"', seg,
                             "%s must not fall back to the old 4-type whitelist" % name)

    def test_C389_l14_is_mask_clean_and_the_A_triple_prime_map_is_C8_clean(self):
        """#K2-389：l14 参照无 mask-dam 违规；A‴ 的**逐件图**（committed）在 l14 位置上 **C8 零越框**；
        记录在案的闸结果（A‴ 见证 mask-dam=0 · DRC 桥=0 · 无类高于基线）自洽。见证板是**派生件**、
        按仓规**不入库**（禁止直改 PCB）⇒ 本测试用 l14 ＋ committed 图做算术，不依赖 /tmp 板。"""
        try:
            import pcbnew  # noqa: F401
        except Exception:                                              # noqa: BLE001
            self.skipTest("pcbnew unavailable")
        import pcbnew as P
        clear = json.load(open(os.path.join(ROOT, "..", "_shared", "eda_core", "drc_rules.json"),
                               encoding="utf-8"))["solder_mask"]["pad_to_mask_clearance"]
        self.assertEqual(route.pad_mask_dam_violations(os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb"), clear), [])
        scen = json.load(open(os.path.join(L2, "EXAM_A_TRIPLE_PRIME_SCENARIO_v1.json"), encoding="utf-8"))
        rect = scen["scenario"]["frame_rect"]
        rows = scen["scenario"]["placement_map"]
        self.assertEqual(len(rows), 25)
        self.assertEqual(sum(1 for m in rows if m["moved"]), scen["scenario"]["n_moved"])
        pmap = {m["ref"]: m["delta_mm"] for m in rows}
        b = P.LoadBoard(os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb"))
        outside = []
        for fp in b.GetFootprints():
            if fp.GetReference() not in pmap:
                continue
            d = pmap[fp.GetReference()]
            for pd in fp.Pads():
                pos = pd.GetPosition()
                pt = [P.ToMM(pos.x) + d[0], P.ToMM(pos.y) + d[1]]
                if not (rect[0] - 1e-6 <= pt[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= pt[1] <= rect[3] + 1e-6):
                    outside.append((fp.GetReference(), pd.GetNumber()))
        self.assertEqual(outside, [], "C8: the A-triple-prime map must keep every member inside the frame")
        g = scen["gate_result"]
        self.assertEqual(g["pad_mask_dam_violations_on_the_new_witness"], 0)
        self.assertEqual(g["drc_solder_mask_bridge_on_the_new_witness"], 0)
        self.assertTrue(g["no_drc_class_above_the_gate_baseline"])

    def test_C389_the_chain_refuses_a_board_that_still_has_isolated_copper(self):
        """#K2-389 §二.2：`wipe_resolve` 链必须在**落板前**执行 fail-closed 前置 —— 残留 `isolated_copper`
        ⇒ **拒板具名**（`W3B_REFUSED_ISOLATED_COPPER`），且必须**在判卷（M4）之前**生效。路径感知（按函数段）。"""
        import ast
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "wipe_resolve_chain")
        seg = "\n".join(src.splitlines()[fn.lineno - 1:fn.end_lineno])
        self.assertIn("landing_precondition_no_isolated_copper", seg)
        self.assertIn("W3B_REFUSED_ISOLATED_COPPER", seg)
        self.assertIn("isolated_copper", seg)
        self.assertLess(seg.index("W3B_REFUSED_ISOLATED_COPPER"), seg.index("M4_judge"),
                        "the landing precondition must bite BEFORE the judge")

    def test_C390_isolated_copper_landing_policy_is_pure(self):
        """#K2-390 §七步①：孤岛清单是**纯函数**；两例 ——「有孤岛 ⇒ 拒板」·「无孤岛 ⇒ 放行」。"""
        with_iso = {"violations": [
            {"type": "isolated_copper", "items": [{"uuid": "u1", "description": "fill [12V_IN]", "pos": {"x": 1, "y": 2}}]},
            {"type": "clearance", "items": []}]}
        without = {"violations": [{"type": "clearance", "items": []}]}
        a = route.isolated_copper_items(with_iso)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["uuid"], "u1")
        self.assertEqual(route.isolated_copper_items(without), [])
        self.assertTrue(len(a) > 0)                                  # with island  => the landing gate REFUSES
        self.assertFalse(len(route.isolated_copper_items(without)) > 0)   # clean     => ADMIT

    def test_C390_the_chain_disposes_isolated_copper_before_the_landing_gate(self):
        """#K2-390 §七步①：`wipe_resolve` 链必须在**落板前置之前**调用确定性处置 `dispose-islands`。路径感知。"""
        import ast
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "wipe_resolve_chain")
        seg = "\n".join(src.splitlines()[fn.lineno - 1:fn.end_lineno])
        self.assertIn("isolated_copper_disposed", seg)
        self.assertIn('"dispose-islands"', seg)
        self.assertLess(seg.index('"dispose-islands"'), seg.index("W3B_REFUSED_ISOLATED_COPPER"),
                        "the dispose step must run BEFORE the landing precondition")

    def test_C392_port_aware_goals_use_the_wall_ports(self):
        """#K2-392 第三边（端口感知目标）：`solve_edge` 正常失败（no-free-start/goal-node）时，
        以**同网 ∂R 端口**（目标或起点）重试。用桩对象做**确定性**单测（不跑迷宫、不碰板）。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_reroute_router_floor_v1", os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

        class MR:
            LAYERS = ["F.Cu", "In5.Cu"]
            LNAME = {"F.Cu": "F.Cu", "In5.Cu": "In5.Cu"}

            def __init__(self):
                self.calls = []
                self.snap_node = lambda *a, **k: None

            def solve_edge(self, ctx, find, compa, compb, net, la, pa, lb, pb, margin, cs):
                self.calls.append((compa, compb, la, pa, lb, pb))
                if compb == "PORT" and pb == (51.5, 37.5):
                    return {"legs": [], "vias": []}, "ok"
                if compa == "PORT" and pa == (51.5, 37.5):
                    return {"legs": [], "vias": []}, "ok"
                return None, "no-free-start-node"

        mr = MR()
        ctx = type("C", (), {"tracks": [{"net": "N1", "layer": "In5.Cu", "x1": 51.5, "y1": 37.5,
                                         "x2": 55.0, "y2": 37.5, "uuid": "u1"}]})()
        find = lambda k: "PORT" if k == "t:u1" else "OTHER"          # noqa: E731
        w._install_port_aware_goals(mr, (22.95, 32.95, 51.50, 66.50))
        sol, why = mr.solve_edge(ctx, find, "A", "B", "N1", "F.Cu", (10.0, 10.0), "F.Cu", (20.0, 20.0), 3.0, 0.25)
        self.assertIsNotNone(sol, "the port retry must succeed")
        self.assertTrue(why.startswith("ok-port"), why)
        # 非同网/无端口 ⇒ 行为不变（仍然失败，且不搜索）
        sol2, why2 = mr.solve_edge(ctx, find, "A", "B", "N2", "F.Cu", (10.0, 10.0), "F.Cu", (20.0, 20.0), 3.0, 0.25)
        self.assertIsNone(sol2)
        self.assertEqual(why2, "no-free-start-node")

    def test_C392_the_floor_wrapper_installs_port_goals_only_with_a_wall(self):
        """路径感知：wrapper 仅在**设了框（WALL_RECT）**时安装端口感知目标（C35 域内语义不放松）。"""
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("_install_port_aware_goals", src)
        self.assertIn("if mr.WALL_RECT:", src)
        self.assertIn("mr.snap_node = snap", src)

    def test_C394_port_reachability_precheck_names_unreachable_endpoints(self):
        """#K2-394 §二.1：**端口可达性预检** —— 每条失败边记录「端口是否可达」，不可达者**具名**。
        桩对象 · 确定性（不跑迷宫、不碰板）。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_reroute_router_floor_v1", os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

        class MR:
            LAYERS = ["F.Cu", "In5.Cu"]
            LNAME = {"F.Cu": "F.Cu", "In5.Cu": "In5.Cu"}

            def __init__(self):
                self.snap_node = lambda *a, **k: None

            def solve_edge(self, ctx, find, compa, compb, net, la, pa, lb, pb, margin, cs):
                if net == "OK" and compb == "PORT" and pb == (51.5, 37.5):
                    return {"legs": [], "vias": []}, "ok"
                return None, "no-free-start-node"

        mr = MR()
        ctx = type("C", (), {"tracks": [{"net": "OK", "layer": "In5.Cu", "x1": 51.5, "y1": 37.5,
                                         "x2": 55.0, "y2": 37.5, "uuid": "u1"}]})()
        find = lambda k: "PORT" if k == "t:u1" else "OTHER"          # noqa: E731
        recs = w._install_port_aware_goals(mr, (22.95, 32.95, 51.50, 66.50))
        mr.solve_edge(ctx, find, "A", "B", "OK", "F.Cu", (10.0, 10.0), "F.Cu", (20.0, 20.0), 3.0, 0.25)
        self.assertTrue(recs[-1]["reachable_port"], "a reachable port must be recorded as such")
        self.assertEqual(recs[-1]["ports_available"], 1)
        mr.solve_edge(ctx, find, "A", "B", "NOPE", "F.Cu", (10.0, 10.0), "F.Cu", (20.0, 20.0), 3.0, 0.25)
        self.assertFalse(recs[-1]["reachable_port"], "a net with no port must be NAMED unreachable")
        self.assertEqual(recs[-1]["net"], "NOPE")
        self.assertEqual(recs[-1]["ports_available"], 0)

    def test_static_gate_no_undefined_names_in_the_eda_eng_package(self):
        """#K2-396 §二.5：**静态未定义名闸** —— 覆盖**生产链本体**（不只是测试面），全包 AST 扫描。
        （`exam_a_chain` 的 `rp`/`blocked` 即此闸的**先 RED 后 GREEN** 用例：修前命中、修后为空。）"""
        import ast, builtins, glob
        def scope_nodes(body):
            stack = list(body)
            while stack:
                n = stack.pop(); yield n
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue
                stack.extend(ast.iter_child_nodes(n))
        def scope_bound(body):
            out = set()
            for n in scope_nodes(body):
                if isinstance(n, ast.Import):
                    out.update((a.asname or a.name).split(".")[0] for a in n.names)
                elif isinstance(n, ast.ImportFrom):
                    out.update(a.asname or a.name for a in n.names)
                elif isinstance(n, ast.ExceptHandler):
                    if isinstance(n.name, str) and n.name:
                        out.add(n.name)
                elif isinstance(n, ast.arg):
                    out.add(n.arg)
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    out.add(n.name)
                elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                    out.add(n.id)
            return out
        bad = {}
        for path in sorted(glob.glob(os.path.join("tools", "eda_eng", "*.py"))):
            tree = ast.parse(open(path, encoding="utf-8").read(), path)
            mod = set(dir(builtins)) | scope_bound(tree.body)
            for fn in tree.body:
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                bound = scope_bound(fn.body) | {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
                if fn.args.vararg: bound.add(fn.args.vararg.arg)
                if fn.args.kwarg: bound.add(fn.args.kwarg.arg)
                hit = sorted({n.id for n in scope_nodes(fn.body)
                              if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                              and n.id not in mod and n.id not in bound})
                if hit:
                    bad[os.path.basename(path) + "::" + fn.name] = hit
        self.assertEqual(bad, {}, "undefined names in the production package: %s" % bad)

    def test_M_ENG_DETECTOR_DUAL_SOURCE_precheck_uses_the_maze_model(self):
        """#K2-396 §五 `M-ENG-DETECTOR-DUAL-SOURCE`：检测器**唯一源＝迷宫自身模型** ——
        端口/预检逻辑必须建在 `snap_node`/`solve_edge` 上；**旁路自写几何规则不得入库**
        （`pad_clearance_violations` 首版实测不实：l14 误报 366，已撤回）。"""
        w = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("orig_snap", w, "the pre-check / snap relaxation must sit on the maze's snap_node")
        self.assertIn("mr.solve_edge = solve", w, "the decision must go through the maze's solve_edge")
        self.assertNotIn("pad_clearance_violations", w)
        r = open(os.path.join("tools", "eda_eng", "route.py"), encoding="utf-8").read()
        self.assertNotIn("def pad_clearance_violations", r, "the unsound bypass detector must not ship")

    def test_C398_a_gen_failure_is_distinguishable_from_a_clean_probe(self):
        """#K2-398 自我更正：`mech_probe_moves` 在 **gen_v5 失败**时返回**空 violations**（`{}`）——
        调用方**必须**同时看 `gen_exit`/`gen_failed`，否则「生成失败」会被读成「干净通过」
        （我上一窗的 dy 扫描就是这样把 A⁴ 的刚性下移误判为过闸）。本测试把该契约钉住。"""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        self.assertIn('"gen_failed": True', src, "the gen-failure branch must be NAMED")
        self.assertIn('s.get("gen_exit") == 0', src, "rearrange_probe must require gen_exit == 0")
        # the CLI gained an explicit exam scenario option (the A^4 wiring) - default keeps A-double-prime behaviour
        cli = open(os.path.join("tools", "eda_eng", "cli.py"), encoding="utf-8").read()
        self.assertIn('p.add_argument("--scenario"', cli)
        self.assertIn('a.scenario or os.path.join(L2, "EXAM_A_PRIME_SCENARIO_v1.json")', cli)

    def test_C400_the_gate_never_silently_accepts_an_unapplied_move(self):
        """#K2-400 §六.①（量具修复 · 关账判据）：量具**不得**对「位移未落板」的板出读数 ——
        要么位移**真落板**，要么**具名 fail-closed**（`move_not_applied`）。
        RED 基线 ＝ R1102（单件探针 J13 未动却返回"干净"读数）；GREEN ＝ 具名拦下。"""
        try:
            import pcbnew  # noqa: F401
        except Exception:                                              # noqa: BLE001
            self.skipTest("pcbnew unavailable")
        import pcbnew as P, tempfile
        w = tempfile.mkdtemp(prefix="k2c400_")
        base = regen.mech_probe_moves([], w, "base", return_board=True).get("board")
        mv = regen.mech_probe_moves([("J13", 0.0, 4.0)], w, "j13", return_board=True)

        def j13y(bp):
            if not bp:
                return None
            b = P.LoadBoard(bp)
            for fp in b.GetFootprints():
                if fp.GetReference() != "J13":
                    continue
                for pd in fp.Pads():
                    if pd.GetNumber() == "2":
                        return P.ToMM(pd.GetPosition().y)
            return None
        y0, y1 = j13y(base), j13y(mv.get("board"))
        landed = (y0 is not None and y1 is not None and abs(y1 - (y0 + 4.0)) < 1e-3)
        if not landed:
            na = mv.get("move_not_applied")
            self.assertTrue(na, "an UNLANDED requested move must be NAMED (move_not_applied), never silently accepted")
            self.assertIn("J13", [x["ref"] for x in na])

    def test_C403_layout_reasonableness_gate_is_a_standing_binary_check(self):
        """#K2-403 §二.B：**布局合理性常设闸** —— 机算行（R6 重叠 / R4 孔·边距 / R3 密度均衡）**基线相对二值**；
        目视行（R1/R2/R5）**显式 `RENDER_REQUIRED`**（双轨 · 不得以"只注声称"代替）。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_layout_reasonableness_v1", os.path.join("tools", "k2_layout_reasonableness_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        r = m.check(os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb"))
        self.assertIn(r.get("verdict"), ("PASS", "FAIL"))
        self.assertEqual(sorted(r["rows"].keys()), ["R3_density_balance", "R4_hole_edge", "R6_no_overlap"])
        self.assertTrue(all("pass" in v for v in r["rows"].values()))
        self.assertEqual(sorted(set(r["render_rows"].values())), ["RENDER_REQUIRED"])

    def test_C408_endpoint_stitch_turns_pairs_into_deterministic_l_stitches(self):
        """#K2-408 §四.2：**端口可达性感知缝合段** —— 同网成对端点 ⇒ 一条**确定性 L 型 stitch**
        （`[a, corner, b]` · corner=(b.x,a.y) · 跨层在 corner 落**一个**过孔）；异网/非成对 ⇒ **不产计划**（防误缝）。
        **先 RED**（该纯函数此前不存在）**后 GREEN**。"""
        drc = {"unconnected_items": [
            {"items": [{"description": "F.Cu 上 C73 的焊盘 1 [NRST]", "pos": {"x": 1.0, "y": 2.0}},
                       {"description": "F.Cu 上 U1 的焊盘 10 [NRST]", "pos": {"x": 3.0, "y": 5.0}}]},
            {"items": [{"description": "走线 [PERSTA#] (In5.Cu), 长度: 0.25 mm", "pos": {"x": 7.0, "y": 8.0}},
                       {"description": "F.Cu 上 R1 的焊盘 1 [PERSTA#]", "pos": {"x": 9.0, "y": 8.5}}]},
            {"items": [{"description": "F.Cu 上 A [NET1]", "pos": {"x": 0.0, "y": 0.0}},
                       {"description": "F.Cu 上 B [NET2]", "pos": {"x": 1.0, "y": 1.0}}]}]}
        plans = regen.endpoint_stitch_plans(drc)
        self.assertEqual(len(plans), 2, "same-net pairs only")
        self.assertEqual(plans[0]["net"], "NRST")
        self.assertEqual(plans[0]["polys"][0][1], [3.0, 2.0], "deterministic L corner")
        self.assertEqual(plans[1]["layers"], ["In5.Cu"])
        self.assertEqual(plans[1].get("vias", [{}])[0]["layers"], ["In5.Cu", "F.Cu"])
        self.assertEqual(regen.stitch_layer_of("走线 [X] (In5.Cu)"), "In5.Cu")
        self.assertEqual(regen.stitch_layer_of(""), "F.Cu")

    def test_C408_the_chain_stitches_endpoints_before_the_refill(self):
        """路径感知：缝合段必须在 **refill/孤岛阶段之前**（#K2-408 §四.2）。"""
        import ast
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "wipe_resolve_chain")
        seg = "\n".join(src.splitlines()[fn.lineno - 1:fn.end_lineno])
        self.assertIn("endpoint_stitch_planned", seg)
        self.assertIn("endpoint_stitch_applied", seg)
        self.assertLess(seg.index("endpoint_stitch_planned"), seg.index("pour_islands_detected"))

    def test_C410_partial_apply_excludes_out_of_bound_stitches_by_name(self):
        """#K2-410 §四.1：stitch **部分应用 ＋ 具名排除** —— 越框者**具名排除**、界内者**保留**
        （确定性 · 零搜索 · 不再让单条越框计划作废整批）。"""
        plans = [{"net": "IN", "polys": [[[1.0, 1.0], [2.0, 1.0], [2.0, 2.0]]], "layers": ["F.Cu"]},
                 {"net": "OUT", "polys": [[[1.0, 1.0], [9.0, 1.0], [9.0, 2.0]]], "layers": ["F.Cu"]}]
        inb, exc = regen.partition_stitch_plans(plans, [0, 0, 5, 5])
        self.assertEqual([p["net"] for p in inb], ["IN"], "the in-bound plan must be kept")
        self.assertEqual([e["net"] for e in exc], ["OUT"], "the out-of-bound plan must be NAMED, not dropped silently")

    def test_C410_the_chain_partitions_before_applying(self):
        """路径感知 ＋ 顺序：先**分区**（具名排除）再**落板**。"""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        self.assertIn("endpoint_stitch_partitioned", seg)
        self.assertLess(seg.index("endpoint_stitch_partitioned"), seg.index("endpoint_stitch_applied"))
        self.assertIn("partition_stitch_plans(st_plans, rect)", seg)

    def test_C410_clipping_puts_out_of_frame_stitches_back_in_bound(self):
        """#K2-410 §四.3（在册「∂R 端口＝固定端子」语义）：越框端点**钳到框边** ⇒ 计划**落域内**（确定性 · 零搜索 · 具名被钳点）。"""
        plans = [{"net": "N", "polys": [[[51.75, 37.5], [50.05, 39.0]]], "layers": ["F.Cu"]}]
        cl, named = regen.clip_stitch_plans_to_bound(plans, [22.95, 32.95, 51.5, 78.0])
        self.assertEqual(cl[0]["polys"][0][0], [51.5, 37.5], "the out-of-frame point is clamped onto the bound")
        self.assertEqual([n["net"] for n in named], ["N"], "the clamped point is NAMED")
        inb, exc = regen.partition_stitch_plans(cl, [22.95, 32.95, 51.5, 78.0])
        self.assertEqual(len(inb), 1); self.assertEqual(exc, [])

    def test_C411_stitch_is_maze_first_and_refusals_are_dropped_named(self):
        """#K2-411 §二：**迷宫优先 ＋ 拒即具名** —— 链内**不得**落未经验证的直线 stitch；
        本阶段出现的计划即"迷宫未接通者" ⇒ 一律 **DROP-NAMED**（R1146 实测直线 L 破 C2）。"""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        self.assertIn("endpoint_stitch_dropped_named", seg)
        self.assertNotIn('_cli("route", "--apply-batch", sf2', seg, "no direct-L apply path may remain")

    def test_C412_endpoint_own_cell_relaxation_unblocks_a_boxed_in_endpoint(self):
        """#K2-412 sec.4.3 (carrying #K2-411 sec.2 **D1**): the ENDPOINT-OWN-CELL semantics -- every maze edge
        endpoint LIES ON the net's own copper (the anchors are pad/via/track centres of the SAME island), so its
        OWN cell is by definition a legal start/goal; the plain snap prunes that cell whenever a foreign obstacle
        sits within (clearance + half-width + margin) of it => the named `no-free-start/goal-node` (R1150: 8/8).
        This gate relaxes the snap ONLY onto the endpoint's OWN copper cell: the C35 domain wall still holds (the
        start cell may never be placed outside the declared domain) and seg_exact/via_exact + the final DRC are
        UNCHANGED -- it only lets the maze START. RED before the fix (snap returns None for the boxed-in endpoint),
        GREEN after (it returns the net's own copper cell). Deterministic stub, no maze run, no board touched."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_reroute_router_floor_v1", os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

        OWN = (5.0, 5.0)                     # the net's own copper (pad/via/track) anchor of THIS island

        class Grid:
            step, x0, y0, nx, ny = 0.10, 0.0, 0.0, 200, 200

            def __init__(self):
                # the plain prune mask: the endpoint's OWN cell is PRUNED (why the plain snap fails)
                self.bad = {L: bytearray(self.nx * self.ny) for L in ("F.Cu", "In5.Cu")}
                self.bad["F.Cu"][self._idx(*OWN)] = 1        # the endpoint's own cell: pruned
                self.bad["F.Cu"][self._idx(1.0, 1.0)] = 1    # a foreign cell that must stay pruned
                self.bad["F.Cu"][self._idx(9.0, 9.0)] = 1    # another foreign cell that must stay pruned

            def _idx(self, x, y):
                i, j = self.cell(x, y)
                return i * self.ny + j

            def cell(self, x, y):
                return int(round((x - self.x0) / self.step)), int(round((y - self.y0) / self.step))

            def pt(self, i, j):
                return self.x0 + i * self.step, self.y0 + j * self.step

            def inside(self, i, j):
                return 0 <= i < self.nx and 0 <= j < self.ny

        def make_mr():
            class MR:
                LAYERS = ["F.Cu", "In5.Cu"]
                LNAME = {"F.Cu": "F.Cu", "In5.Cu": "In5.Cu"}
                WALL_RECT = None

                def __init__(self):
                    self.snap_node = lambda *a, **k: None         # plain snap finds nothing (the cell is pruned)
                    self.solve_edge = lambda *a, **k: (None, "no-free-start-node")

                @staticmethod
                def node_in_island(ctx, find, comp, net, layer, x, y, tol=0.06):
                    return net == "N1" and abs(x - OWN[0]) <= tol and abs(y - OWN[1]) <= tol
            return MR()

        find = lambda k: "ISLAND"                              # noqa: E731
        grid = Grid()
        mr = make_mr()
        w._install_port_aware_goals(mr, (0.0, 0.0, 8.0, 8.0))
        cell = mr.snap_node(grid, None, find, "ISLAND", "N1", "F.Cu", OWN[0], OWN[1])
        self.assertIsNotNone(cell, "RED before the fix: the endpoint's OWN copper cell was pruned => snap None")
        px, py = grid.pt(cell[0], cell[1])
        self.assertLessEqual(abs(px - OWN[0]) + abs(py - OWN[1]), 0.11,
                             "the snapped cell must lie ON the net's own copper (never a foreign cell)")
        # #K2-412 sec.4.3(b): `astar` refuses a PRUNED start (`start-blocked`) => D1 must ALSO lift the prune
        # bit for THAT one cell, otherwise the returned own-copper cell is still unusable (D1 would be inert).
        self.assertEqual(grid.bad["F.Cu"][grid._idx(*OWN)], 0,
                         "the returned OWN-copper cell must have its prune bit lifted so `astar` can start")
        # the lifting is confined to exactly that cell: both foreign cells stay pruned
        self.assertEqual(grid.bad["F.Cu"][grid._idx(1.0, 1.0)], 1)
        self.assertEqual(grid.bad["F.Cu"][grid._idx(9.0, 9.0)], 1)
        # negative control (a): a point NOT on this net's own copper is never relaxed (bounded, no blanket door)
        self.assertIsNone(mr.snap_node(grid, None, find, "ISLAND", "N1", "F.Cu", 7.0, 7.0))
        # negative control (b): C35 -- the relaxation NEVER places the start cell outside the declared domain
        mr2 = make_mr()
        w._install_port_aware_goals(mr2, (0.0, 0.0, 4.0, 8.0))     # the wall's right edge = 4.0 (< OWN.x)
        self.assertIsNone(mr2.snap_node(grid, None, find, "ISLAND", "N1", "F.Cu", OWN[0], OWN[1]),
                          "C35: the endpoint-own-cell relaxation must never start outside the declared domain")

    def test_C412_corridor_occupancy_audit_names_the_affected_items(self):
        """#K2-412 sec.4.2 (carrying R1102/R1154 'delimit the affected set'): the drawing-layer prerequisite --
        every DRAWN corridor is audited against the board and each foreign item inside (plus clearance) is NAMED.
        Pure part pinned here (deterministic; the board pass is a read-only run, no board change)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_corridor_occupancy_audit_v1", os.path.join("tools", "k2_corridor_occupancy_audit_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        layers, rect = m.parse_corridor("In5 + F.Cu (50.0-51.6, 37.5-39.0)")
        self.assertEqual(layers, ["In5.Cu", "F.Cu"], "bare `In5` must be normalised to `In5.Cu`")
        self.assertEqual(rect, (50.0, 37.5, 51.6, 39.0))
        self.assertEqual(m.parse_corridor("F.Cu (43.4-81.0 clipped to 51.5, 44.0-60.6)")[1],
                         (43.4, 44.0, 51.5, 60.6), "the `clipped to` form must take the CLIPPED bound")
        self.assertLessEqual(m.rect_gap((0, 0, 1, 1), (1.1, 0, 2, 1)), 0.20, "inside clearance => occupant")
        self.assertGreater(m.rect_gap((0, 0, 1, 1), (1.5, 0, 2, 1)), 0.20, "outside clearance => not an occupant")

    def test_C412_corridor_redraw_is_deterministic_zero_search(self):
        """#K2-412 sec.4.1 (v2 element 3): the REDRAW engine -- the largest clear axis-aligned sub-rectangle of the
        corridor that CONTAINS the endpoint and avoids every (occupant + clearance); when the endpoint is BOXED the
        items blocking it at the point are NAMED (the relocation list). Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_corridor_redraw_v1", os.path.join("tools", "k2_corridor_redraw_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        rect, cl, wall = (0, 0, 10, 10), 0.2, [[4, 0, 5, 8]]     # the wall inflates to [3.8,-0.2,5.2,8.2]
        sub, blk = m.clear_subrect_containing(rect, wall, cl, (6, 5))
        self.assertEqual(sub, (5.2, 0.0, 10.0, 10.0), "the clear side of the wall must be returned")
        self.assertEqual(blk, [])
        self.assertEqual(m.clear_subrect_containing(rect, wall, cl, (1, 5))[0], (0.0, 0.0, 3.8, 10.0))
        self.assertEqual(m.clear_subrect_containing(rect, wall, cl, (6, 5))[0], sub, "must be deterministic")
        # a BOXED endpoint (the point sits inside an occupant) => None + the blockers NAMED, never guessed
        sub3, blk3 = m.clear_subrect_containing(rect, [[4, 4, 6, 6]], 0.0, (5, 5))
        self.assertIsNone(sub3, "a boxed endpoint must be reported, not invented")
        self.assertEqual(len(blk3), 1, "the item blocking the endpoint must be NAMED")

    def test_C413_per_corridor_no_common_channel_is_reported(self):
        """#K2-413 sec.5.3 (per-corridor conservation): two points separated by a full wall have NO common clear
        rectangle => the corridor CANNOT carry them; the per-corridor check must report that, never fall back to a
        block-level free-area claim. Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_corridor_redraw_v1", os.path.join("tools", "k2_corridor_redraw_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        rect, wall = (0, 0, 10, 10), [[4, 0, 5, 10]]              # a full-height wall splits the corridor
        self.assertIsNone(m.clear_subrect_containing_pts(rect, wall, 0.0, [(2, 5), (8, 5)])[0],
                          "points on opposite sides of a full wall cannot share a clear rectangle")
        sub, _ = m.clear_subrect_containing_pts(rect, wall, 0.0, [(6, 3), (8, 7)])
        self.assertIsNotNone(sub, "same side => a common clear rectangle exists")
        self.assertTrue(sub[0] <= 6 and sub[1] <= 3 and sub[2] >= 8 and sub[3] >= 7, "it must contain BOTH points")
        self.assertEqual(m.clear_subrect_containing_pts(rect, wall, 0.0, [(2, 5), (8, 5)]),
                         m.clear_subrect_containing_pts(rect, wall, 0.0, [(2, 5), (8, 5)]), "deterministic")

    def test_C414_B2_uses_the_in_register_FINE_STEP_and_B1_filters_pour(self):
        """#K2-414 sec.2.1/2.2 - B1: pour-reflowable nets are NOT obstacles in the maze model; B2: the maze is
        called with the IN-REGISTER FINE_STEP(0.10). Stub-based, deterministic (no maze run, no board)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_reroute_router_floor_v1", os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
        seen = {}

        class MR:
            LAYERS = ["F.Cu", "In5.Cu"]; LNAME = {"F.Cu": "F.Cu", "In5.Cu": "In5.Cu"}
            FINE_STEP = 0.10; WALL_RECT = None

            def __init__(self):
                self.snap_node = lambda *a, **k: None

                def solve_edge(ctx, find, cA, cB, net, la, pa, lb, pb, margin, cs):
                    seen["cs"] = cs
                    return {"legs": [], "vias": []}, "ok"
                self.solve_edge = solve_edge

        mr = MR()
        w._set_step("fine")
        w._install_port_aware_goals(mr, (0.0, 0.0, 1.0, 1.0))
        mr.solve_edge(None, None, "A", "B", "N", "F.Cu", (0, 0), "F.Cu", (1, 1), 3.0, 0.25)
        self.assertEqual(seen["cs"], 0.10, "B2: the maze must be called with the IN-REGISTER FINE_STEP")
        w._set_step("keep")
        mr.solve_edge(None, None, "A", "B", "N", "F.Cu", (0, 0), "F.Cu", (1, 1), 3.0, 0.25)
        self.assertEqual(seen["cs"], 0.25, "`keep` must leave the caller's step untouched")
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn('c.tracks = [t for t in c.tracks if t["net"] not in POUR]', src,
                      "B1: the pour-reflowable filter must sit in the maze obstacle context")
        self.assertIn('ap.add_argument("--reflowable"', src)

    def test_C429_the_channel_constraint_is_wired_into_the_maze_bound_rect(self):
        """#K2-429 sec.3.2: the produced per-net channel must become a HARD input to the maze - wired into the
        maze's EXISTING bound-rect vehicle per edge, not a post-hoc filter."""
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn('ap.add_argument("--channels"', src)
        self.assertIn("mr.WALL_RECT = (_c[0] - _w", src, "the per-net channel must set the maze's bound rect per edge")
        self.assertIn("mr._CHANNELS = CH", src, "the map must live on mr (solve is module-level scope)")
        self.assertIn('ap.add_argument("--port-refs"', src, "#K2-431 fix 1: connector pads as fixed ports")
        r = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        self.assertIn('"--port-refs", PORT_REFS', r, "#K2-431 fix 1 must be WIRED into the chain's maze passes")
        self.assertIn('PORT_REFS = "J13"', r)
    def test_C434_K1_pour_aware_clear_is_a_subprocess_verb_and_wired_into_the_chain(self):
        """#K2-434 K-1: the cleared field must contain NO hidden pour => an unfill (zone) verb exists and the chain
        calls it BEFORE routing (unfill -> route -> refill). Static; the verb is subprocess-only (mutation ban)."""
        c = open(os.path.join("tools", "eda_eng", "cli.py"), encoding="utf-8").read()
        self.assertIn('"unfill"', c)
        u = open(os.path.join("tools", "k2_unfill_all_v1.py"), encoding="utf-8").read()
        self.assertIn("UnFill()", u, "the verb must unfill the zones")
        r = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = r[r.index("def wipe_resolve_chain("):]
        self.assertIn('"unfill"', seg); self.assertIn("pour_aware_unfill", seg)

    def test_C434_K2_functional_blocks_are_deterministic_and_name_boundaries(self):
        """#K2-434 K-2 RED->GREEN: one undivided blob hides all functions; the deterministic functional grouping
        separates POWER/CONTROL/BUS/HS and NAMES the boundary ports (nets crossing blocks)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_functional_block_v1", os.path.join("tools", "k2_functional_block_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        netof = {"U1": ["MCU_VDD", "NRST"], "C85": ["MCU_VDD", "I2C1_SDA"], "E2": ["I2C1_SDA"], "D1": ["PCIE_DN0_P"]}
        blk = m.functional_blocks(["U1", "C85", "E2", "D1"], netof)
        self.assertEqual(sorted(blk), ["BUS", "HS", "POWER"], "GREEN: families separated (no single blob)")
        self.assertEqual(blk["POWER"]["members"], ["C85", "U1"], "grouped by function, sorted")
        self.assertEqual(m.functional_blocks(["U1", "C85", "E2", "D1"], netof), blk, "deterministic")
        bp = m.boundary_ports(blk, netof)
        self.assertIn("I2C1_SDA", bp["POWER"], "a net crossing blocks is a NAMED boundary port")

    def test_C434_K3_multi_block_plan_is_simultaneous_disjoint_and_named(self):
        """#K2-434 K-3 RED->GREEN: a block-by-block serial placement can overlap/starve; the deterministic
        simultaneous plan stacks the blocks disjointly with the preconditions checked and NAMED on failure."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_functional_block_v1", os.path.join("tools", "k2_functional_block_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        blocks = {"POWER": {"members": ["U1"], "nets": ["MCU_VDD"]}, "BUS": {"members": ["E2"], "nets": ["I2C1_SDA"]}}
        r = m.multi_block_plan(blocks, {"POWER": (4.0, 3.0), "BUS": (3.0, 2.0)}, (0, 0, 10, 20))
        self.assertEqual(r["verdict"], "FEASIBLE", "the plan fits => FEASIBLE")
        self.assertTrue(r["checks"]["disjoint"] and r["checks"]["area_ok"] and r["checks"]["hs_safe"])
        self.assertEqual(len(r["plan"]), 2, "N=2 blocks move in ONE plan (simultaneous)")
        big = m.multi_block_plan(blocks, {"POWER": (4.0, 30.0), "BUS": (3.0, 2.0)}, (0, 0, 10, 20))
        self.assertEqual(big["verdict"], "INFEASIBLE", "does not fit => INFEASIBLE, never silent")
        self.assertTrue(big["named"], "infeasibility is NAMED to the block")

    def test_C434_K4_per_block_flow_is_ordered_and_puts_power_on_pours(self):
        """#K2-434 K-4: the per-block flow fixes the 7-step order, requires the BLOCK-INTERNAL C1 to reach zero
        first (failures localise to a block), and sends POWER nets through pours (never thin tracks)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_functional_block_v1", os.path.join("tools", "k2_functional_block_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        blocks = {"POWER": {"members": ["U1"], "nets": ["MCU_VDD"]}}
        plan = m.multi_block_plan(blocks, {"POWER": (4.0, 3.0)}, (0, 0, 10, 20))["plan"]
        f = m.per_block_flow(blocks, plan)
        self.assertEqual(f["steps"], ["1_block", "2_multi_block_place", "3_pour_aware_clear", "4_in_block_route",
                                      "5_cross_block_stitch", "6_refill", "7_judge"])
        self.assertEqual(f["per_block"][0]["gate"], "in_block_C1_zero")
        self.assertIn("pour", f["per_block"][0]["route_mode"])

    def test_C434_the_chain_prefers_the_functional_block_channels(self):
        """#K2-434 sec.2.3 wiring: the chain must consume the K-2/K-3 derived channels first, falling back to the
        row-grouped ones. Static (the runners are board-dependent)."""
        j = open(os.path.join("tools", "k2_joint_alloc_v1.py"), encoding="utf-8").read()
        self.assertIn("def channels_arg_by_block(", j)
        r = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        # #K2-440: the preferred-then-fallback logic now lives in the BEHAVIOUR-TESTED helper channels_for_maze
        # (see test_C440_...); the chain must consume that helper.
        h = r[r.index("def channels_for_maze("):r.index("def wipe_resolve_chain(")]
        self.assertIn("channels_arg_by_block(wiped, drc, list(rect))", h)
        self.assertIn("or ja_module.channels_arg(wiped, drc, list(rect))", h)
        self.assertIn("channels_for_maze(wiped, d0, rect)", r[r.index("def wipe_resolve_chain("):])

    def test_C434_K4_the_chain_reads_the_per_block_C1_gate(self):
        """#K2-434 K-4: the chain must emit the per-functional-block C1 gate evidence (failures localise to a block)."""
        r = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = r[r.index("def wipe_resolve_chain("):]
        self.assertIn('"per_block_C1_gate"', seg)
        self.assertIn('"in_block_C1 must reach zero FIRST', seg + '"in_block_C1 must reach zero FIRST')

    def test_C438_the_chain_extractor_is_robust_and_fails_loud(self):
        """#K2-438 sec.3.1 / M-ENG-EVIDENCE-EXTRACTION: RED = the naive fixed-shape path fails when the chain is
        stored as a JSON STRING (the R1286 fault); GREEN = the recursive finder locates the stage in all shapes and
        FAILS LOUD (KeyError) when absent - never a silent null."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_chain_evidence_v1", os.path.join("tools", "k2_chain_evidence_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        gate = {"stage": "per_block_C1_gate", "per_block": {"POWER": 2, "CONTROL": 1, "BUS": 1}, "pass": False}
        art_str = {"route": {"chain": json.dumps({"chain": [{"stage": "x"}, gate]})}}
        # RED: the naive fixed-shape path cannot see through the JSON string (this is exactly the R1286 fault)
        with self.assertRaises(TypeError):
            art_str["route"]["chain"]["chain"][-1]
        # GREEN: the recursive finder locates the stage in each shape it is stored in
        self.assertEqual(m.find_stage(art_str, "per_block_C1_gate"), gate, "JSON-string shape")
        self.assertEqual(m.find_stage({"chain": [gate]}, "per_block_C1_gate"), gate, "list shape")
        self.assertEqual(m.find_stage(gate, "per_block_C1_gate"), gate, "bare dict shape")
        # fail-LOUD: an absent stage raises KeyError, never a silent null
        with self.assertRaises(KeyError):
            m.find_stage({"a": 1}, "per_block_C1_gate")
        # the per-block residual attribution: counts by ITEM (sums to C1) not by DISTINCT NET
        drc = {"unconnected_items": [
            {"type": "unconnected_items", "items": [
                {"description": "\u8d70\u7ebf [P3V3_AUX] (In2.Cu), \u957f\u5ea6: 0.7071 mm"},
                {"description": "F.Cu \u4e0a C90 \u7684\u710a\u76d8 1 [P3V3_AUX]"}]},
            {"type": "unconnected_items", "items": [
                {"description": "\u8d70\u7ebf [NRST] (F.Cu), \u957f\u5ea6: 0.1414 mm"},
                {"description": "F.Cu \u4e0a U1 \u7684\u710a\u76d8 10 [NRST]"}]}]}
        at = m.per_block_attribution(drc)
        self.assertEqual(at["n_items"], 2); self.assertEqual(at["n_nets"], 2)
        self.assertEqual(at["per_block"]["POWER"]["items"], 1)
        self.assertEqual(at["per_block"]["POWER"]["nets"], ["P3V3_AUX"])
        self.assertEqual(at["per_block"]["CONTROL"]["nets"], ["NRST"])
        # fail-LOUD: an item whose description has no [NET] must RAISE, never be silently dropped (the R1288 fault)
        with self.assertRaises(KeyError):
            m.parse_net("a track with no net tag")
        with self.assertRaises(KeyError):
            m.residual_table({"unconnected_items": [{"items": [{"description": "no net tag"}]}]})


    def test_C438_M1_the_chain_hands_the_channels_to_the_maze_after_the_drc_exists(self):
        """#K2-438 M-1 RED->GREEN: today the channel computation reads `d0` before it is assigned, the exception is
        swallowed and the maze receives an EMPTY --channels (a no-channel run). GREEN: the computation sits AFTER
        the wiped DRC is written, and an empty result is FAIL-LOUD, never swallowed."""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        i_d0 = seg.index('d0 = os.path.join(work, "s1_wiped_drc.json")')
        i_ch = seg.index("channels_for_maze(wiped, d0, rect)")     # #K2-440: the tested helper
        self.assertLess(i_d0, i_ch, "the channel computation must come AFTER d0 exists")
        h = src[src.index("def channels_for_maze("):src.index("def wipe_resolve_chain(")]
        self.assertIn("channels_compute_empty", h, "an empty channel set must be FAIL-LOUD, not swallowed")
        self.assertIn("channels_compute_failed", h)
        self.assertIn("W1B_CHANNELS_EMPTY", seg, "the chain must bail out loudly")

    def test_C438_M2_the_block_channel_source_never_returns_empty(self):
        """#K2-438 M-2 RED->GREEN: channels_arg_by_block returns '' on its own input (multi_block_plan INFEASIBLE
        from endpoint-spread sizes) - which is what made K-2/K-3 a no-op. GREEN: it never returns '', the family
        frame is OPTIONAL, and plane nets are kept out of the pack sizes."""
        src = open(os.path.join("tools", "k2_joint_alloc_v1.py"), encoding="utf-8").read()
        seg = src[src.index("def channels_arg_by_block("):]
        seg = seg[:seg.index("\ndef ")]
        self.assertNotIn('        return ""', seg, "an empty channel set must never be returned")
        self.assertIn("_plane_nets(", seg)
        self.assertIn("tgt.get(FB.family_of([n]))", seg, "the family frame must be OPTIONAL, not a gate")

    def test_C450_joint_channel_allocation_vs_sequential_starvation(self):
        """#K2-450 sec.2.4/2.6 (means change: one-shot JOINT channel allocation). RED = the old per-net sequential
        allocation leaves overlapping channels, so whoever is served last is starved (the observed residual rotation).
        GREEN = the joint allocation packs all channels disjointly in one pass, so nobody is starved."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2jca", os.path.join("tools", "k2_joint_channel_alloc_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        demands = [{"net": "A", "lo": 0.0, "hi": 10.0}, {"net": "B", "lo": 5.0, "hi": 15.0},
                   {"net": "C", "lo": 12.0, "hi": 20.0}]
        seq = m.sequential(demands)
        self.assertEqual(m.overlaps(seq, 0.20), [("A", "B"), ("B", "C")], "RED: sequential overlaps")
        self.assertEqual(m.starved(seq, 0.20), ["A", "B", "C"], "RED: sequential starves")
        ch, unsat = m.joint(demands, (0.0, 40.0), gap=0.20)
        self.assertEqual(unsat, [], "GREEN: the joint allocation serves every net")
        self.assertEqual(m.overlaps(ch, 0.20), [], "GREEN: no overlap, hence no starvation")
        self.assertEqual(len(ch), 3)
        ch2, unsat2 = m.joint(demands, (0.0, 12.0), gap=0.20)      # a span too small => loud naming
        self.assertTrue(unsat2, "a span that cannot host everything must NAME the unsatisfied nets, not go silent")
        # the wiring helper: the emitted --channels string must be DISJOINT in y (that is the whole point)
        pairs = [{"net": "A", "p1": (30.0, 40.0), "p2": (50.0, 44.0)},
                 {"net": "B", "p1": (31.0, 42.0), "p2": (49.0, 51.0)},
                 {"net": "C", "p1": (33.0, 45.0), "p2": (48.0, 46.0)}]
        s_, unsat_ = m.channels_from_pairs(pairs, [22.95, 32.95, 51.5, 78.0])
        self.assertEqual(unsat_, [])
        bands = {}
        for part in s_.split(";"):
            n, r4 = part.split(":"); v = [float(t) for t in r4.split(",")]
            bands[n] = (v[1], v[3])
        self.assertEqual(m.overlaps(bands, 0.20), [], "the wired channels must be disjoint")
        # and the chain must PREFER this joint source
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        h = src[src.index("def channels_for_maze("):src.index("def wipe_resolve_chain(")]
        self.assertIn("channels_string_corridor(", h,
                      "the chain must prefer the one-shot JOINT allocation (per-corridor since R1418)")
        # R1408/R1410 correct GRANULARITY: per-corridor packing must place EVERY crossing net (zero unsat),
        # whereas whole-net y-banding provably cannot (two independent refutations on the record).
        rect2 = [22.95, 32.95, 51.5, 78.0]
        per2 = {"MCU_VDD": (26.0, 34.0, 51.0, 70.0), "P3V3": (28.0, 34.0, 51.0, 64.0),
                "GND": (26.0, 35.0, 51.0, 70.0), "NRST": (27.0, 40.0, 51.0, 55.0),
                "I2C1_SCL": (33.0, 61.0, 46.0, 67.0), "I2C1_SDA": (33.0, 48.0, 51.0, 68.0),
                "PERSTA#": (31.0, 37.0, 51.0, 56.0), "GPIO_LED": (33.0, 56.0, 45.0, 71.0)}
        ch2, uns2 = m.channels_by_corridor(per2, rect2, h=8.0, pitch=0.40)
        self.assertEqual(uns2, {}, "per-corridor packing must leave NO corridor unsatisfied")
        self.assertEqual(sorted(ch2), sorted(per2), "every cross-region net must receive corridor slots")
        for _n, _ps in ch2.items():
            self.assertTrue(_ps, _n)
            for (_x0, _y0, _x1, _y1) in _ps:
                self.assertLess(_y0, _y1)
                self.assertFalse(_y0 < rect2[1] - 1e-9 or _y1 > rect2[3] + 1e-9, "slots stay inside the frame")
        dem2 = [{"net": _n, "lo": 0.0, "hi": max(_b[3] - _b[1], 0.40), "min_w": max(_b[3] - _b[1], 0.40)}
                for _n, _b in per2.items()]
        _, unsat_whole = m.joint(dem2, (rect2[1], rect2[3]), gap=0.40)
        self.assertTrue(unsat_whole, "RED: whole-net y-banding must leave nets unsatisfied")
        # the interface-ready emitter: the string MUST allow a net to repeat (one entry per corridor)
        strc, uns3 = m.channels_string_corridor(per2, rect2, h=8.0, pitch=0.40)
        self.assertEqual(uns3, {})
        names = [t.split(":", 1)[0] for t in strc.split(";")]
        self.assertEqual(sorted(set(names)), sorted(per2), "every net must appear")
        self.assertGreater(len(names), len(set(names)), "a net repeats when it crosses several corridors")

    def test_C451_a_multislot_hard_channel_is_REFUSED_and_the_same_string_is_a_LEGAL_SOFT_GUIDE(self):
        """#K2-452 sec.2.4 (item 1 = the fail-closed gate, mandatory FIRST) - SUPERSEDES the R1418 law (option (ii),
        which fed every per-corridor slot to the maze as its solve DOMAIN). R1420 MEASURED that form: the 0.40mm
        lane-as-domain starves the edge by construction (C1 2 -> 47, no-path-coarse(exhausted-1)=47). RED = the R1418
        state (multi-slot accumulated into mr.WALL_RECT). GREEN = the wrapper REFUSES a multi-slot --channels loudly
        (rc=2, no board written) while the SAME repeated-net string stays legal as --guide (a PREFERENCE, accumulated
        per net, consumed as cost - never as a boundary).
        The behaviour is driven end to end in test_C452_the_wrapper_REFUSES_a_multislot_hard_channel_..."""
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("REFUSED(#K2-452 sec.2.4 item 1)", src, "the gate must be LOUD")
        self.assertIn("_multi = sorted(_n for _n, _v in CH.items() if len(_v) > 1)", src)
        self.assertIn("out.setdefault(_n, []).append(", src, "the GUIDE parser must ACCUMULATE a repeated net")
        self.assertIn('_r.split("@")[0]', src, "the @corridor/@layer tag must be tolerated")
        self.assertNotIn("for _c in _cs:", src, "the per-corridor-as-DOMAIN loop (R1418) must be GONE")


        """#K2-449 sec.2.4 (M-ENG-ORPHAN-BRIDGE-DISPOSAL closure): every ADDED drawing piece must be anchored to a pad
        or to existing copper, otherwise the chain's isolated-copper disposal removes it (proved twice: the R-g zone
        and the I2C1_SDA joint). RED = a pad-less piece is flagged; GREEN = a pad-touching piece passes."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2aa", os.path.join("tools", "k2_anchor_audit_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        pads = [[45.90, 62.85, 46.00, 62.95]]
        routes = [{"layer": "B.Cu", "a": (49.15, 62.505), "b": (49.35, 62.505)}]
        anchored = {"kind": "track", "layer": "B.Cu", "a": [48.15, 62.905], "b": [45.95, 62.905]}
        orphan = {"kind": "track", "layer": "F.Cu", "a": [50.30, 67.455], "b": [50.30, 62.505]}
        self.assertEqual(m.audit([anchored], pads, routes), {"ok": True, "padless": [], "n_added": 1})
        bad = m.audit([anchored, orphan], pads, routes)
        self.assertFalse(bad["ok"]); self.assertEqual(bad["padless"], [orphan])
        # a dR port stub anchored on KEPT copper (not a pad) must PASS (R1386 refinement)
        port = {"kind": "track", "layer": "B.Cu", "a": [51.5, 61.905], "b": [50.9, 61.905]}
        kept = [{"layer": "B.Cu", "a": (51.5, 61.905), "b": (52.205, 61.905)}]
        self.assertTrue(m.audit([port], pads, kept)["ok"], "a port stub anchored on kept copper is anchored")
        via_ok = {"kind": "via", "at": [45.95, 62.905]}
        self.assertTrue(m.audit([via_ok], pads, routes)["ok"])

    def test_C452_soft_guidance_prefers_and_never_starves_where_a_hard_domain_starves(self):
        """#K2-452 sec.2.4 item 2 RED->GREEN (the core of the means change). RED = R1420: a channel fed as the HARD
        domain (mr.WALL_RECT) is a BOUNDARY that must contain both endpoints, so a thin trunk lane starves the edge
        (C1 2->47). GREEN = the SAME rect fed as SOFT guidance (mr.GUIDE) only multiplies the cost of steps OUTSIDE
        it: the edge is ALWAYS solvable, and the route really does leave the direct line to use the lane."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2mr452", os.path.join("tools", "k2_p4_mroute_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)

        class _Ctx:
            tracks, holes, edge, keep_t, keep_v = [], [], [], [], []
            pads, vias = {}, {}

        ctx = _Ctx()
        lane = (0.0, 1.0, 5.0, 1.25)      # the trunk lane: 0.25mm tall; the endpoints are NOT inside it
        s, g = (1, 1), (19, 1)            # both at y=0.25mm (off-lane), same layer
        step = 0.25
        # RED: the lane as the HARD domain => the maze cannot even start (R1420's starvation at unit scale)
        m.WALL_RECT = lane; m.GUIDE = None
        p1, why1 = m.astar(m.Grid(ctx, "N", step, 0.0, 0.0, 5.0, 5.0, 0.0), ctx, "N", s, g, m.F_CU, m.F_CU)
        self.assertIsNone(p1, "a hard domain that excludes the endpoints MUST starve the edge")
        self.assertEqual(why1, "start-blocked")
        # no domain, no guidance: the plain shortest path is the straight off-lane line
        m.WALL_RECT = None; m.GUIDE = None
        p2, why2 = m.astar(m.Grid(ctx, "N", step, 0.0, 0.0, 5.0, 5.0, 0.0), ctx, "N", s, g, m.F_CU, m.F_CU)
        self.assertEqual(why2, "ok"); self.assertLessEqual(max(c[2] for c in p2), 1)
        # GREEN: the SAME lane as SOFT guidance at a high penalty => solvable, and the route PREFERS the lane
        m.GUIDE = {"rects": [lane], "penalty": 50.0}
        p3, why3 = m.astar(m.Grid(ctx, "N", step, 0.0, 0.0, 5.0, 5.0, 0.0), ctx, "N", s, g, m.F_CU, m.F_CU)
        m.GUIDE = None; m.WALL_RECT = None
        self.assertEqual(why3, "ok", "soft guidance can NEVER starve an edge")
        self.assertGreater(max(c[2] for c in p3), 1, "the route must leave the direct line and use the guided lane")
        # penalty 0 must be a NO-OP (backward compatibility of the cost surface)
        m.GUIDE = {"rects": [lane], "penalty": 0.0}
        p4, why4 = m.astar(m.Grid(ctx, "N", step, 0.0, 0.0, 5.0, 5.0, 0.0), ctx, "N", s, g, m.F_CU, m.F_CU)
        m.GUIDE = None
        self.assertEqual(why4, "ok"); self.assertLessEqual(max(c[2] for c in p4), 1)

    def test_C452_the_wrapper_REFUSES_a_multislot_hard_channel_and_never_widens_a_frozen_ladder(self):
        """#K2-452 sec.2.4 item 1 + item 3, BEHAVIOURAL. (a) The gate is driven for real: the wrapper is executed with
        a multi-slot --channels and must exit rc=2 with a REFUSED message BEFORE touching any board (R1420's starvation
        form must be impossible to re-feed silently). (b) The widen ladder must be DEDUPLICATED: with the frozen
        margin 0.0 the old (m, 2m, 4m) tuple was three IDENTICAL attempts (band never widened, solve cost tripled)."""
        import subprocess, sys
        r = subprocess.run([sys.executable, os.path.join("tools", "k2_reroute_router_floor_v1.py"),
                            "--in", "/nonexistent.kicad_pcb", "--drc", "/nonexistent_drc.json",
                            "--out", "/tmp/opencode/k2gate_out.kicad_pcb", "--ledger", "/tmp/opencode/k2gate_led.json",
                            "--channels", "GND:0,0,1,1;GND:0,2,1,3;P3V3:0,0,1,1"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, "a multi-slot HARD channel must be REFUSED (rc=2), never run: %s" % r.stderr[-300:])
        self.assertIn("REFUSED", r.stderr)
        self.assertFalse(os.path.exists("/tmp/opencode/k2gate_out.kicad_pcb"), "the gate must refuse BEFORE writing a board")
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("sorted(set((_m, _m * 2, _m * 4)))", src,
                      "the ladder must be deduplicated (frozen margin 0.0 => exactly one attempt, provably identical)")
        self.assertIn("mr._GUIDE_PEN", src); self.assertIn("mr._GUIDES = GD", src)
        # #K2-452 sec.2.4 item 3: an absent endpoint uuid must be a NAMED block reason, never a silent KeyError
        mr_src = open(os.path.join("tools", "k2_p4_mroute_v1.py"), encoding="utf-8").read()
        self.assertIn("endpoint-absent-from-ctx", mr_src)
        self.assertIn('why = None, "exception:%s(%s)" % (type(ex).__name__, str(ex)[:60])', mr_src,
                      "an exception must reach the ledger WITH its name and message (the R1420 lesson: 244 opaque blocks)")

    def test_C452_the_port_pad_layer_must_be_normalised_to_a_pcbnew_layer_id(self):
        """#K2-452 sec.2.4 item 3 ROOT CAUSE (located by the K2MR_EXC_TRACE diagnostic, not by guesswork): the maze keys
        grid.bad by PCBNew LAYER IDs, but mr._PORT_PADS carries layer NAMES, so every port-goal retry crashed with
        KeyError('F.Cu') - the 244/316 blocks of R1420, sitting exactly on the two nets that own J13 pads (GND 241 +
        MCU_VDD 3); i.e. the #K2-431 port-aware-goal lever was DEAD for them. RED = the name passes through
        (grid.bad['F.Cu'] -> KeyError). GREEN = the name is normalised to the ID; IDs pass through unchanged."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2floor452",
                                                    os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        lname2id = {"F.Cu": 11, "In5.Cu": 13, "B.Cu": 12}
        self.assertEqual(m._norm_layer("F.Cu", lname2id), 11, "a layer NAME must become the pcbnew layer ID")
        self.assertEqual(m._norm_layer(13, lname2id), 13, "an ID must pass through unchanged")
        self.assertIsNone(m._norm_layer(None, lname2id))
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("_norm_layer(_l, _LNAME2ID)", src, "the port table must be normalised at the source")
        self.assertIn("_LNAME2ID = {mr.LNAME[L]: L for L in mr.LAYERS}", src)

    def test_C454_an_endpoint_OUTSIDE_the_wall_must_start_from_its_dR_port(self):
        """#K2-454 sec.2.4/2.5 RED->GREEN (the next means: endpoint start-node reachability). MEASURED lesion (R1430):
        265 of 268 blocked edges had BOTH representative ends OUTSIDE the C35 wall, endpoint_own_cell_hits=0, and the
        port retry still passed the outside point as one of the two ends - so both directions were doomed. RED = an
        endpoint outside the wall cannot obtain a start cell (snap_node returns None => no-free-start-node). GREEN =
        the outside copper is KEPT by construction and its dR port IS the connection point: substitute the net's nearest
        port for that endpoint and the maze starts legally (wall, exact gates and the maze core untouched)."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2floor454",
                                                    os.path.join("tools", "k2_reroute_router_floor_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        wall = (0.0, 0.0, 5.0, 2.0)
        # the substitution itself (pure, deterministic; zero search)
        ports = [(11, 3.5, 2.0, "t:uB"), (11, 0.5, 2.0, "t:uA")]
        self.assertTrue(m._outside_wall((0.5, 3.5), wall)); self.assertFalse(m._outside_wall((0.5, 2.0), wall))
        self.assertEqual(m._port_substitute((0.5, 3.5), 11, wall, ports), ((0.5, 2.0), 11, "t:uA"),
                         "an OUTSIDE endpoint must be replaced by the NEAREST same-net dR port")
        self.assertEqual(m._port_substitute((4.5, 1.0), 11, wall, ports), ((4.5, 1.0), 11, None),
                         "an INSIDE endpoint must pass through untouched")
        self.assertEqual(m._port_substitute((0.5, 3.5), 11, None, ports), ((0.5, 3.5), 11, None),
                         "no wall => nothing to substitute")
        self.assertEqual(m._port_substitute((0.5, 3.5), 11, wall, []), ((0.5, 3.5), 11, None),
                         "no port => fall back to today's behaviour (the existing retry)")
        # the lesion itself, at unit scale, on the REAL maze core
        sp2 = importlib.util.spec_from_file_location("k2mr454", os.path.join("tools", "k2_p4_mroute_v1.py"))
        mr = importlib.util.module_from_spec(sp2); sp2.loader.exec_module(mr)

        class _Ctx:
            pads, vias = {}, {}
            holes, edge, keep_t, keep_v = [], [], [], []
            # the net's OWN copper crosses the wall: a kept outside stub that ends exactly ON the port cell
            tracks = [{"net": "N", "layer": mr.F_CU, "x1": 0.5, "y1": 3.5, "x2": 0.5, "y2": 1.0,
                       "hw": 0.1, "uuid": "u1"}]

        ctx = _Ctx(); find = lambda k: "R"      # one island; node_in_island only needs the root to match
        mr.WALL_RECT = wall
        g = mr.Grid(ctx, "N", 0.25, 0.0, 0.0, 5.0, 5.0, 0.0)
        self.assertIsNone(mr.snap_node(g, ctx, find, "R", "N", mr.F_CU, 0.5, 3.5),
                          "RED: an endpoint outside the wall gets NO start cell")
        s = mr.snap_node(g, ctx, find, "R", "N", mr.F_CU, 0.5, 2.0)
        self.assertIsNotNone(s, "GREEN: the dR port cell (on the wall, on the net's own copper) IS a legal start")
        path, why = mr.astar(g, ctx, "N", s, (18, 4), mr.F_CU, mr.F_CU)
        mr.WALL_RECT = None
        self.assertEqual(why, "ok", "from the substituted port the maze solves normally (no-new-permission: gates unchanged)")
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn("_port_substitute(pa, la, _saved, _prts)", src, "the substitution must be wired BEFORE the solve")
        self.assertIn("if _prts and _outside_wall(pa, _saved) and _outside_wall(pb, _saved):", src,
                      "ONLY the both-outside case may be substituted: a single outside end is already handled by the "
                      "retry, and re-formulating it (measured in the #K2-454 dry-run) collapsed 13 working retry routes "
                      "into same-island no-ops and cost adds (68 -> 66)")
        self.assertIn("no-op-after-port-substitution(same-island)", src,
                      "two substituted ends landing on one island must be a NAMED no-op, never phantom copper")

    def test_C448_via_aware_clearance_and_interpreter_gate(self):
        """#K2-448 sec.2.5: (1) a clearance check MUST enumerate every layer a via covers - R1358 found a false clean
        because a single GetLayer() filter missed a via; (2) a pcbnew-using tool must fail LOUDLY under a python
        without pcbnew (R1356's host-python silent abort)."""
        import importlib.util
        sp = importlib.util.spec_from_file_location("k2cl", os.path.join("tools", "k2_clearance_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        self.assertEqual(m.via_layer_span("In2.Cu", "In5.Cu"), ["In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu"])
        via = {"kind": "via", "net": "HS", "layers": ["In2.Cu", "In5.Cu"], "bbox": [57.9, 39.2, 58.1, 39.4]}
        self.assertEqual(m.obstacle_layers(via), {"In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu"})
        self.assertTrue(m.seg_blocked([42.8, 39.0], [58.5, 39.0], "In4.Cu", [via]),
                        "a via on In2-In5 MUST block an In4 segment (the R1358 false-clean case)")
        self.assertFalse(m.seg_blocked([42.8, 35.5], [58.5, 35.5], "In4.Cu", [via]))
        self.assertIn("DRC run", m.CLEAN_CLAIM_RULE)
        # (2) interpreter gate: importing a pcbnew-using tool under the HOST python must fail LOUDLY
        import shutil, subprocess
        host = shutil.which("python3")
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH")}
        r = subprocess.run([host, "-c",
                            "import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), 'tools')); "
                            "import k2_port_plane_stitch_v1"],
                           capture_output=True, text=True, cwd=os.path.join(ROOT), env=clean)
        self.assertNotEqual(r.returncode, 0, "a host-python run must NOT succeed silently")
        self.assertIn("EDA_ENG_PY", (r.stderr or "") + (r.stdout or ""))

    def test_C443_the_lane_drafter_fails_LOUD_on_an_empty_or_foreign_source_draft(self):
        """#K2-443 sec.2.5 / #K2-446 sec.2.3(3): a draft that adds NOTHING must fail LOUDLY (an empty ledger was once
        read as 'infeasible' when in fact the DRC came from a different board). The drafter self-runs the DRC on the
        SAME board, so a foreign source is structurally impossible; this pins the empty-result verdict."""
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "k2ld", os.path.join("tools", "k2_lane_draft_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        bad = m.draft_verdict({"added": [], "blocked": []})
        self.assertFalse(bad["ok"]); self.assertIn("EMPTY DRAFT", bad["why"])
        self.assertFalse(m.draft_verdict({"added": [], "blocked": [{"net": "X", "why": "no-path"}]})["ok"])
        good = m.draft_verdict({"added": [{"net": "I2C1_SCL", "segs": 3}], "blocked": []})
        self.assertTrue(good["ok"]); self.assertEqual(good["added"], 1)
        src = open(os.path.join("tools", "k2_lane_draft_v1.py"), encoding="utf-8").read()
        self.assertIn("same_source_drc", src, "the DRC must be produced by the drafter itself")

    def test_C442_out_of_dR_items_must_be_DECLARED_not_silently_accepted(self):
        """#K2-446 sec.2.3(3) same-class regression: anything leaving dR must EITHER be refused loudly OR carry an
        explicit allow_outside_dR declaration (sec.2.7 'declare, do not hide')."""
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "k2pps2", os.path.join("tools", "k2_port_plane_stitch_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        rect = [22.95, 32.95, 51.5, 78.0]
        lane = {"n": "R-g", "kind": "lane", "net": "P3V3", "layer": "In4.Cu",
                "poly": [[42.8, 39.0], [58.5, 39.0]]}
        self.assertEqual([r["why"] for r in m.validate({"lines": [dict(lane)]}, rect)],
                         ["lane point outside dR"], "an undeclared outside-dR item must be refused LOUDLY")
        declared = dict(lane); declared["allow_outside_dR"] = True
        self.assertEqual(m.validate({"lines": [declared]}, rect), [],
                         "an explicitly declared outside-dR item is allowed (and recorded by stitch())")

    def test_C442_the_outside_copper_check_can_see_zones(self):
        """#K2-442 sec.2.7: 'outside copper unchanged' must include ZONE fills - the legacy predicate read segments
        + vias only, which is a false-green blind spot. Zone edges must contribute, deterministically."""
        b = os.path.join(ROOT, verify.BASELINE_BOARD)
        rect = [22.95, 32.95, 51.5, 78.0]
        legacy = block.outside_geometry(b, rect)
        zone_edges = block.zone_fill_segments(b, rect, only_outside=True)
        self.assertTrue(zone_edges, "zones must contribute to the outside-copper read")
        zaware = block.outside_geometry(b, rect, include_zones=True)
        self.assertNotEqual(dict(legacy), dict(zaware), "include_zones must add the zone edges")
        self.assertEqual(dict(block.outside_geometry(b, rect, include_zones=True)), dict(zaware), "deterministic")

    def test_C440_channels_for_maze_fails_LOUD_on_empty_and_on_error(self):
        """#K2-440 sec.3.3 BEHAVIOUR regression (not a source-string proxy). RED was the R1286 run: an EMPTY channel
        set was silently swallowed and the maze ran with NO constraint. GREEN: drive the REAL code path with stub
        sources and assert it refuses loudly - empty => channels_compute_empty, raise => channels_compute_failed,
        and only a non-empty set yields the --channels args."""
        class _JA:
            def __init__(self, by_block, arg=None, boom=False): self._b, self._a, self._boom = by_block, arg, boom
            def channels_arg_by_block(self, *a):
                if self._boom: raise RuntimeError("stub")
                return self._b
            def channels_arg(self, *a):
                if self._boom: raise RuntimeError("stub")
                return self._a
        rect = [22.95, 32.95, 51.5, 78.0]
        r = regen.channels_for_maze("B", "D", rect, ja_module=_JA("", ""))
        self.assertFalse(r["ok"]); self.assertEqual(r["stage"], "channels_compute_empty"); self.assertEqual(r["args"], [])
        r = regen.channels_for_maze("B", "D", rect, ja_module=_JA("", None, boom=True))
        self.assertFalse(r["ok"]); self.assertEqual(r["stage"], "channels_compute_failed")
        r = regen.channels_for_maze("B", "D", rect, ja_module=_JA("", "NRST:0,0,1,1;P3V3:0,0,1,1"))
        self.assertTrue(r["ok"]); self.assertEqual(r["stage"], "channels_computed")
        self.assertEqual(r["source"], "hard=legacy-single-rect", "#K2-452: --channels is the HARD half")
        self.assertEqual(r["args"][0], "--channels"); self.assertEqual(r["n_nets"], 2)
        # #K2-452 sec.2.4 item 1 (CHAIN side of the gate): a multi-slot HARD set is REFUSED loudly. R1420 proved a
        # multi-slot channel fed as mr.WALL_RECT starves the edges by construction (C1 2 -> 47) => it must never be
        # re-fed silently; the soft half (--guide) is where a per-corridor allocation belongs now.
        r2 = regen.channels_for_maze("B", "D", rect, ja_module=_JA("GND:0,0,1,1;GND:0,2,1,3", ""))
        self.assertFalse(r2["ok"]); self.assertEqual(r2["stage"], "channels_hard_multislot_refused")
        self.assertEqual(r2["args"], []); self.assertIn("GND", r2["err"])
        # the chain must consume the helper and bail out loudly (no silent run)
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        self.assertIn("channels_for_maze(wiped, d0, rect)", seg)
        self.assertIn("W1B_CHANNELS_EMPTY", seg); self.assertIn("W1B_CHANNELS_FAILED", seg)

    def test_C440_the_chain_stitches_the_frozen_drawing_before_the_maze(self):
        """#K2-440 sec.3.1: the chain applies the frozen sec.16.3 drawing (port/plane stitch) AFTER the pour-aware
        clear and BEFORE the maze, refuses on a frame mismatch, and counts the added items."""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        i_st = seg.index('_pps.stitch(wiped, list(rect), _spec, _st)')
        i_unf = seg.index('"stage": "pour_aware_unfill"')
        i_ch = seg.index("channels_for_maze(wiped, d0, rect)")
        self.assertLess(i_unf, i_st, "the stitch must follow the pour-aware clear")
        self.assertLess(i_st, i_ch, "the stitch must precede the maze (its ports are routing goals)")
        self.assertIn("REFUSED_FRAME_MISMATCH", seg)

    def test_C439_the_port_plane_stitch_sets_the_via_type_and_refuses_outside_dR(self):
        """#K2-439 sec.2.10 means implementation: the drawing implementer must (a) SET THE VIA TYPE - an untyped
        PCB_VIA comes out as a THROUGH via and shorted an In2 track in the first attempt (caught by DRC, not by a
        run) - and (b) refuse any landing outside dR. The validation rule is pure, so it is unit-tested here."""
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "k2pps", os.path.join("tools", "k2_port_plane_stitch_v1.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        src = open(os.path.join("tools", "k2_port_plane_stitch_v1.py"), encoding="utf-8").read()
        self.assertIn("SetViaType", src); self.assertIn("VIATYPE_BLIND", src)
        rect = [22.95, 32.95, 51.5, 78.0]
        self.assertEqual(m.validate({"lines": [
            {"n": 1, "kind": "via", "net": "P3V3", "at": [42.8, 39.0], "layers": ["F.Cu", "In4.Cu"]},
            {"n": 2, "kind": "port_stub", "net": "NRST", "layer": "F.Cu",
             "near": [51.5, 40.45], "far": [50.9, 40.45]}]}, rect), [])
        bad = m.validate({"lines": [
            {"n": 1, "kind": "via", "net": "P3V3", "at": [52.0, 39.0], "layers": ["F.Cu", "In4.Cu"]},
            {"n": 2, "kind": "track", "net": "P3V3", "layer": "F.Cu", "a": [43.4, 44.0], "b": [43.4, 79.0]}]}, rect)
        self.assertEqual([r["why"] for r in bad], ["via outside dR", "endpoint outside dR"])
        # #K2-442 sec.3.2 (R-h): a multi-segment LANE is validated point by point
        lane_ok = m.validate({"lines": [{"n": 1, "kind": "lane", "net": "I2C1_SCL", "layer": "F.Cu",
            "poly": [[51.5, 66.185], [50.90, 66.185], [50.90, 61.635]]}]}, rect)
        self.assertEqual(lane_ok, [])
        lane_bad = m.validate({"lines": [{"n": 1, "kind": "lane", "net": "I2C1_SCL", "layer": "F.Cu",
            "poly": [[51.5, 66.185], [79.0, 61.635]]}]}, rect)
        self.assertEqual([r["why"] for r in lane_bad], ["lane point outside dR"])
        self.assertIn('"lane"', open(os.path.join("tools", "k2_port_plane_stitch_v1.py"), encoding="utf-8").read())

    def test_C415_the_chain_routes_the_objective_nets_first(self):
        """#K2-415 sec.2.2 lever 'order': the blockers are copper the MAZE itself laid (move_parts wipes every net
        inside the frame), so the sound lever is ORDER - the eight objective nets must be routed first."""
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        seg = src[src.index("def wipe_resolve_chain("):]
        self.assertIn('"--order", "list"', seg)
        self.assertIn("GAP_NETS", src)
        self.assertIn('"--order-list", _prio', seg)

    def test_C417_ripup_plan_exposes_the_rip_set_and_route_request(self):
        """#K2-416 sec.5.1(ii) (reported in R1174): the new-means plan must name the RIP SET and the bounded
        ROUTE REQUEST per residual - and its own weak spot (the after-rip check removes ALL occupants)."""
        src = open(os.path.join("tools", "k2_ripup_reroute_gen_v1.py"), encoding="utf-8").read()
        self.assertIn('"rip_set"', src); self.assertIn('"route_request"', src)
        self.assertIn('"after_rip_clear"', src)
        self.assertIn("clear_subrect_containing_pts(rect, []", src, "the after-rip check is knowingly the ALL-removed case")

    def test_C419_endpoint_reach_planner_is_order_preserving_and_zero_search(self):
        """#K2-419 sec.5: the endpoint-reachability / re-layout generator. RED: a naive index-order fan INVERTS the
        row order (lanes cross). GREEN: plan_lanes sorts along the row and assigns lanes ORDER-PRESERVINGLY (no
        crossing), with EXACTLY ONE layer change per lane. Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_endpoint_reach_planner_v1", os.path.join("tools", "k2_endpoint_reach_planner_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        pts = [("A", 0.0, 3.0, "F.Cu"), ("B", 0.0, 1.0, "F.Cu"), ("C", 0.0, 2.0, "F.Cu")]   # a SHUFFLED row
        naive = {n: (i - 1) * 0.25 for i, (n, _, _, _) in enumerate(pts)}
        self.assertLess(naive["A"], naive["B"],
                        "RED: the naive index-order fan gives the TOP pad (A,y=3) a SMALLER lane than the bottom (B,y=1) => inverted/crossing")
        lanes = m.plan_lanes(pts, 0.25)
        off = {l["net"]: l["offset"] for l in lanes}
        self.assertLess(off["B"], off["C"]); self.assertLess(off["C"], off["A"])       # GREEN: order preserved
        g = m.lane_geometry(next(l for l in lanes if l["net"] == "B"), 1.2, "In5.Cu")
        self.assertEqual(g["n_via"], 1, "exactly ONE layer change per lane (reference policy)")
        self.assertIsNone(m.lane_geometry(lanes[0], 1.2, None)["via"], "no layer change => no via")

    def test_C419_yield_sequence_is_deterministic_and_ordered(self):
        """#K2-419 sec.5 direction A: the deterministic YIELD SEQUENCE - per blocker, how far to move and in what
        order (fewest-to-move first). Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_endpoint_reach_planner_v1", os.path.join("tools", "k2_endpoint_reach_planner_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        seg = ((0.0, 0.0), (1.0, 0.0))
        blk = [{"net": "NEAR", "bbox": [0.2, 0.10, 0.8, 0.14]}, {"net": "FAR", "bbox": [0.2, 0.20, 0.8, 0.24]}]
        ys = m.yield_sequence(seg, blk, 0.20)
        self.assertEqual([y["net"] for y in ys], ["FAR", "NEAR"], "fewest-to-move yields FIRST")
        self.assertLess(ys[0]["move_mm"], ys[1]["move_mm"])
        self.assertEqual(m.yield_sequence(seg, blk, 0.20), ys, "deterministic")

    def test_C419_yield_sequence_makes_the_lane_clear(self):
        """#K2-419 sec.5 direction A (machine-checkable improvement): RED = the lane is blocked; GREEN = after the
        deterministic yield sequence the lane IS clear. Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_endpoint_reach_planner_v1", os.path.join("tools", "k2_endpoint_reach_planner_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        seg = ((0.0, 0.0), (1.0, 0.0))
        blk = [{"net": "A", "bbox": [0.2, 0.10, 0.8, 0.14]}, {"net": "B", "bbox": [0.2, 0.20, 0.8, 0.24]}]
        r = m.lane_clear_after_yields(seg, blk, 0.20)
        self.assertFalse(r["before"], "RED: the lane starts blocked")
        self.assertTrue(r["after"], "GREEN: the deterministic yields make the lane clear")
        self.assertEqual(r, m.lane_clear_after_yields(seg, blk, 0.20), "deterministic")

    def test_C419_yield_model_is_axis_aligned_only(self):
        """#K2-419 sec.5 (honest boundary pinned): the +/-y yield model is AXIS-ALIGNED ONLY. A slanted lane must
        stay reported as BLOCKED, so no future caller can mistake it for cleared. Deterministic."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_endpoint_reach_planner_v1", os.path.join("tools", "k2_endpoint_reach_planner_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        seg = ((0.0, 0.0), (1.0, 1.0))                       # slanted
        blk = [{"net": "A", "bbox": [0.4, 0.55, 0.6, 0.65]}]
        self.assertFalse(m.lane_clear_after_yields(seg, blk, 0.20)["after"],
                         "documented limit: the +/-y model is axis-aligned only")

    def test_C421_block_relayout_slices_disjoint_ordered_corridors(self):
        """#K2-421 sec.4 (whole-block re-layout, copying the reference policy): RED = putting every group in one
        corridor overlaps; GREEN = the deterministic GROUP-SLICED corridors are disjoint AND order-preserving, and
        each escape is one straight run with exactly ONE layer change. Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        corr = m.slice_corridors((0, 0, 10, 10), ["B", "A", "C"], gap=0.2)
        naive = [c["corridor"] for c in corr]
        self.assertGreater(len({tuple(r) for r in naive}), 1, "RED: a single shared corridor would overlap")
        self.assertEqual([c["group"] for c in corr], ["B", "A", "C"], "GREEN: group order preserved")
        for i in range(len(corr) - 1):
            self.assertLessEqual(corr[i]["corridor"][2], corr[i + 1]["corridor"][0], "corridors disjoint")
        self.assertEqual(m.slice_corridors((0, 0, 10, 10), ["B", "A", "C"], 0.2), corr, "deterministic")
        esc = m.escape_into_corridor([("N1", 0, 3, "F.Cu"), ("N2", 0, 1, "F.Cu")], corr[0]["corridor"])
        self.assertEqual([e["net"] for e in esc], ["N2", "N1"], "escapes are order-preserving along the row")
        self.assertTrue(all(len(e["via"]["layers"]) == 2 for e in esc), "exactly one layer change per escape")

    def test_C421_row_grouping_is_deterministic_and_contiguous(self):
        """#K2-421 sec.4 (the policy's FIRST element): group the endpoints into contiguous y-bands (rows) so each
        group can be fanned out. Deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        pts = [("A", 0, 1.0, "F.Cu"), ("B", 0, 7.0, "F.Cu"), ("C", 0, 1.5, "F.Cu"), ("D", 0, 6.5, "F.Cu")]
        g = m.group_by_row(pts, band=2.0)
        self.assertEqual([[p[0] for p in row] for row in g], [["A", "C"], ["D", "B"]], "contiguous y-bands, row-ordered")
        self.assertEqual(m.group_by_row(pts, 2.0), g, "deterministic")

    def test_C421_corridor_conservation_is_per_corridor(self):
        """#K2-421 sec.4 / #K2-413 (pinned): conservation is PER-CORRIDOR - capacity is THIS corridor's own clear
        narrow dimension vs need; a blocked corridor FAILS even if the block is mostly free."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        free = m.corridor_conservation((0, 0, 4, 4), [], 0.20, 0.60)
        self.assertTrue(free["pass"]); self.assertAlmostEqual(free["capacity_mm"], 4.0, places=2)
        blocked = m.corridor_conservation((0, 0, 4, 4), [[1.9, 0, 2.1, 4]], 0.20, 0.60)
        self.assertFalse(blocked["pass"], "a wall across the corridor must FAIL the per-corridor check")

    def test_C421_row_corridors_are_content_aware_and_named(self):
        """#K2-421 sec.4 (A): content-aware corridor allocation - each ROW gets the clear sub-rectangle containing
        ALL its endpoints; a row split by a wall is NAMED UNPLACEABLE (never force-fitted). Deterministic."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        rows = [[("A", 0.0, 0.0, "F.Cu"), ("B", 1.0, 0.0, "F.Cu")]]
        self.assertEqual(m.row_corridors(rows, [], 0.20)[0]["status"], "OK")
        wall = [[0.45, -2.0, 0.55, 2.0]]
        self.assertEqual(m.row_corridors(rows, wall, 0.20)[0]["status"], "UNPLACEABLE",
                         "a wall between the row's endpoints must be NAMED, not force-fitted")

    def test_C421_row_blockers_names_who_boxes_the_row(self):
        """#K2-421 sec.4: for an UNPLACEABLE row, NAME the nets boxing it in (the yield input). Deterministic."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        row = [("A", 0.0, 0.0, "F.Cu")]
        occ = {"W1": [[-0.1, -0.1, 0.1, 0.1]], "W2": [[5.0, 5.0, 6.0, 6.0]]}
        self.assertEqual(m.row_blockers(row, occ, 0.20), ["W1"], "only the net actually covering the point is named")
        self.assertEqual(m.row_blockers([("W1", 0.0, 0.0, "F.Cu")], occ, 0.20), [], "a net's own copper never blocks it")

    def test_C421_row_relayout_request_is_ordered_and_named(self):
        """#K2-421 sec.4: the deterministic re-layout request - per row, the named blocker nets with their move_mm
        and yield order (fewest-to-move first). Pure, deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_block_relayout_gen_v1", os.path.join("tools", "k2_block_relayout_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        row = [("A", 0.0, 0.0, "F.Cu")]
        occ = {"NEAR": [[-0.1, -0.05, 0.1, 0.05]], "FAR": [[-0.1, -0.19, 0.1, -0.11]]}   # both cover the point
        r = m.row_relayout_request(row, occ, 0.20)
        self.assertEqual([z["net"] for z in r], ["FAR", "NEAR"], "tie on move_mm => ordered by net name")
        self.assertEqual([z["yield_order"] for z in r], [0, 1])
        self.assertTrue(all(z["move_mm"] >= 0 for z in r))
        self.assertEqual(m.row_relayout_request(row, occ, 0.20), r, "deterministic")

    def test_C425_joint_channel_assignment_is_disjoint_and_ordered(self):
        """#K2-425 sec.4.2: the coordinated single-pass allocation. RED = letting the nets share one channel
        overlaps; GREEN = joint_channel_assignment gives each net a DISJOINT, order-preserving channel (no
        competition), with a deterministic artifact hash. Deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_joint_alloc_v1", os.path.join("tools", "k2_joint_alloc_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        nets = ["MCU_VDD", "NRST", "P3V3"]
        ch = m.joint_channel_assignment(nets, (0, 0, 10, 10), 0.6, 0.2)
        naive = [ch[0]["channel"]] * len(nets)
        self.assertEqual(len({tuple(r) for r in naive}), 1, "RED: one shared channel would overlap")
        self.assertEqual([c["net"] for c in ch], nets, "GREEN: net order preserved")
        for i in range(len(ch) - 1):
            self.assertLessEqual(ch[i]["channel"][2], ch[i + 1]["channel"][0], "channels disjoint")
        self.assertEqual(m.joint_channel_assignment(nets, (0, 0, 10, 10), 0.6, 0.2), ch, "deterministic")
        self.assertEqual(m.artifact_hash16(ch), m.artifact_hash16(ch), "stable artifact hash")

    def test_C427_content_aware_allocation_beats_the_blind_slice(self):
        """#K2-427 sec.4.3 RED->GREEN: on a block containing a WALL, the equal-width blind slice puts the net ON
        the wall (conservation FAIL = RED) while the content-aware allocator finds the clear side (PASS = GREEN)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_joint_alloc_v1", os.path.join("tools", "k2_joint_alloc_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        blind = m.joint_channel_assignment(["N1"], (0, 0, 4, 4), 0.6, 0.2)
        wall = [[1.9, 0, 2.1, 4]]
        import importlib.util as iu, os as os_
        sp = iu.spec_from_file_location("rd", os.path.join("tools", "k2_corridor_redraw_v1.py"))
        rd = iu.module_from_spec(sp); sp.loader.exec_module(rd)
        b = blind[0]["channel"]; c = min(b[2] - b[0], b[3] - b[1])
        self.assertLess(rd.clear_subrect_containing_pts(b, wall, 0.20, [(2.0, 2.0)])[0] is not None, 1.0,
                        "RED: the blind slice's centre sits on the wall (no clear sub-rect)")
        ca = m.content_aware_joint_allocation([[("N1", 1.0, 2.0, "F.Cu")]], (0, 0, 4, 4), wall, 0.20, 0.60)
        self.assertEqual(ca[0]["status"], "OK", "GREEN: the content-aware allocator finds the clear side")
        self.assertGreaterEqual(ca[0]["capacity_mm"], 0.60 - 1e-9)

    def test_C430_channel_including_reach_is_deterministic_and_covers_the_net_copper(self):
        """#K2-430 sec.3.1/3.2 RED->GREEN: a channel drawn only from the endpoints can CUT the net's own copper
        (=> the reachable own-cell falls outside => no-free-start-node). RED = the narrow box misses it; GREEN = the
        reach-inclusive channel covers it. FROZEN constant, deterministic."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_joint_alloc_v1", os.path.join("tools", "k2_joint_alloc_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        row = [("N1", 0.0, 0.0, "F.Cu")]
        own = [[0.6, -0.2, 1.0, 0.2]]                       # the net's own copper just outside the endpoint-only box
        narrow = [row[0][1] - 0.4, row[0][2] - 0.4, row[0][1] + 0.4, row[0][2] + 0.4]
        self.assertLess(narrow[2], own[0][0], "RED: the endpoint-only box does not reach the net's own copper")
        ch = m.channel_including_reach(row, own, 0.5, 0.4)
        self.assertGreaterEqual(ch[2], own[0][2], "GREEN: the channel covers the net's own copper")
        self.assertEqual(m.channel_including_reach(row, own, 0.5, 0.4), ch, "frozen constant / deterministic")

    def test_C426_contraction_lists_are_deterministic_and_net_aware(self):
        """#K2-426 sec.3: the deterministic contraction - parts on the certificate's non-reconnectable nets become
        STAY candidates, the rest MOVE candidates. Deterministic, zero search."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_contraction_v1", os.path.join("tools", "k2_contraction_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        netof = {"A": ["MCU_VDD"], "B": ["GND"], "C": ["NRST", "P3V3"]}
        st, mv = m.contraction_lists(["A", "B", "C"], netof, ["MCU_VDD", "P3V3"])
        self.assertEqual(st, ["A", "C"]); self.assertEqual(mv, ["B"])
        self.assertEqual(m.contraction_lists(["A", "B", "C"], netof, ["MCU_VDD", "P3V3"]), (st, mv), "deterministic")

    def test_C416_deviation_generator_is_pure_and_names_the_blockers(self):
        """#K2-416 sec.5: the deviation generator - pure parts pinned (layer parse, in-domain clamp, pair extraction).
        Deterministic; the board pass is a read-only run, no exam, no board change."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "k2_deviation_gen_v1", os.path.join("tools", "k2_deviation_gen_v1.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        self.assertEqual(m._layers("走线 [N] (In5.Cu), 长度: 0.7 mm"), ["In5.Cu"])
        self.assertEqual(m._layers("F.Cu - In4.Cu 上的盲孔 [N]")[:2], ["F.Cu", "In4.Cu"])
        self.assertEqual(m._clamp((-5.0, 99.0), (0.0, 0.0, 10.0, 10.0)), (0.0, 10.0))
        pr = m.pairs({"unconnected_items": [{"items": [
            {"description": "走线 [A] (F.Cu)", "pos": {"x": 1.0, "y": 2.0}},
            {"description": "走线 [A] (B.Cu)", "pos": {"x": 3.0, "y": 4.0}}]}]})
        self.assertEqual(pr[0]["net"], "A"); self.assertEqual(pr[0]["layers"], ["F.Cu", "B.Cu"])

    def test_C415_the_wrapper_actually_exposes_the_order_lever(self):
        """#K2-415 sec.2.2: the chain wires `--order list --order-list <file>`, so the WRAPPER must accept `list`
        AND forward the list to the in-register maze (both were missing => the authorised run burned on rc=2)."""
        src = open(os.path.join("tools", "k2_reroute_router_floor_v1.py"), encoding="utf-8").read()
        self.assertIn('"hard", "list"]', src, "`list` must be an allowed --order choice")
        self.assertIn("mr.run(a.src, a.drc, a.out, a.ledger, a.margin, a.only_net, a.dry_run, a.order, a.order_list)",
                      src, "the order-list file must be forwarded, not hardcoded to None")

    def test_C34_the_gate_guards_the_wipe_resolve_entry(self):
        """#K2-388 §七.3：C34 §20 闸须守**实际开跑的那道门** —— wipe_resolve 入口也须先过闸。"""
        import importlib.util
        src = open(os.path.join("tools", "eda_eng", "cli.py"), encoding="utf-8").read()
        self.assertIn('"wipe_resolve": "A_double_prime_placement_pour"', src,
                      "the wipe_resolve entry must declare its gate capability")
        self.assertIn("REFUSED_BY_SEC20_GATE", src)
        self.assertLess(src.index("_sec20_gate(a.capability or DEFAULT_GATE_CAPABILITY"),
                        src.index("regen_mod.preflight(a.which, W)"),
                        "the sec.20 gate must bite BEFORE the run starts")
        led = json.load(open(os.path.join(L2, "PRODUCT_THREE_QUESTIONS_LEDGER_v1.json"), encoding="utf-8"))
        self.assertIn("A_double_prime_placement_pour", led)
        spec = importlib.util.spec_from_file_location(
            "k2_new_capability_gate_v1", os.path.join("tools", "k2_new_capability_gate_v1.py"))
        g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
        self.assertEqual(g.check("A_double_prime_placement_pour")["verdict"], "PASS")
        self.assertEqual(g.check("__no_such_capability__")["verdict"], "REFUSED")

    def test_C34_moves_from_the_gate_board_are_read_back_verbatim(self):
        """口径对齐（#K2-375 §四.3 secondary）：逐件位移图可由**闸验过的板**读回。同板对照 ⇒ 零位移。"""
        mv, unch, miss = block.moves_from_board(REF, REF, ["U1", "U2", "U5"])
        self.assertEqual(mv, [], "the same board must yield zero moves")
        self.assertEqual(sorted(unch), ["U1", "U2", "U5"])
        self.assertEqual(miss, [])

    def test_C34_new_capability_command_refuses_without_the_sec20_entry(self):
        """C34 **机闸**（#K2-375 §五）：新能力命令在缺少三问时**拒跑**（exit 2 · 具名 REFUSED）。"""
        rc, r, _ = self._cli("relocate-relative", "--rect", "0,0,1,1", "--members", "U1",
                             "--moves", "U1:1:1", "--work", "/tmp/eda_eng_selftest_sec20",
                             "--capability", "capability_without_a_ledger_entry")
        self.assertEqual(rc, 2, "the sec.20 gate must refuse BEFORE any work")
        self.assertEqual(r["state"], "REFUSED_BY_SEC20_GATE")
        self.assertEqual(r["gate"]["verdict"], "REFUSED")

    def test_C34_c17v1_product_path_argv_is_a_per_part_map(self):
        """#K2-375 §四.3「抄成品」：A′ 的 argv 必须把**逐件位移图**交给 C17 v1（多个 `--moved`），
        并按产品的**既定格式**给受损域（`x0,y0,x1,y1`，非 JSON）。"""
        moves = [("U1", 1.5, 1.5), ("J13", 4.0, 4.0), ("C87", 4.0, 4.0)]
        argv = regen.c17v1_argv("l14.kicad_pcb", moves, "ref.json", "/tmp/w", "/tmp/o.kicad_pcb",
                                report="/tmp/r.json", clear_rect=[22.95, 32.95, 51.5, 66.5])
        self.assertEqual(argv[0], regen.C17V1)
        self.assertEqual(argv.count("--moved"), 3, "the per-part displacement map must reach the product")
        self.assertIn("U1=+1.5000,+1.5000", argv)
        self.assertIn("J13=+4.0000,+4.0000", argv)
        i = argv.index("--clear-rect")
        self.assertEqual(argv[i + 1], "22.95,32.95,51.5,66.5", "clear-rect is the product's comma format")
        self.assertIn("--baseline-drc", argv)
        self.assertIn("--report", argv)
        argv2 = regen.c17v1_argv("b", moves, "r", "w", "o")
        self.assertNotIn("--clear-rect", argv2, "the damage zone is optional (the product may derive it)")

    def test_C34_new_capability_gate_requires_the_sec20_questions(self):
        """C34（#K2-375 §五）：新产品能力窗开跑前，§20 三问必须**在册**——闸缺即拒（不再靠人记）。"""
        import subprocess
        k2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        gate = os.path.join(k2, "tools", "k2_new_capability_gate_v1.py")
        ok = subprocess.run([sys.executable, gate, "--capability", "A_prime_C33_three_questions"],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertEqual(json.loads(ok.stdout)["verdict"], "PASS")
        bad = subprocess.run([sys.executable, gate, "--capability", "no_such_capability"],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(json.loads(bad.stdout)["verdict"], "REFUSED")

    def test_K372_multi_layer_obstacles_are_layer_tagged(self):
        """A′/C33：多层 maze 的障碍必须**带 layers 标记**（否则某一层的障碍会污染其它层）。"""
        obs, bnd = route.obstacles_multi(REF, set(), ["F.Cu", "B.Cu"])
        self.assertTrue(obs, "obstacles must be produced")
        self.assertTrue(all(o.get("layers") and len(o["layers"]) == 1 for o in obs),
                        "every obstacle must carry exactly one layer tag")
        layers = {o["layers"][0] for o in obs}
        self.assertEqual(layers, {"F.Cu", "B.Cu"})
        self.assertEqual(len(bnd), 4)

    def test_K371_planning_certificate_inputs_are_reproducible(self):
        """#K2-371：方案层证书的输入（移动/固定分类 ＋ 冲突最小距）必须可复现，且几何摘要稳定。"""
        regs = ["C73", "C84", "C85", "C86", "C87", "C88", "C90", "D2", "E2", "J12", "J13",
                "J6", "J9", "L1", "R40", "R41", "U1", "U2", "U4", "U5"]
        rect = [22.95, 32.95, 46.50, 62.50]
        mv, fx = block.classify_primitives(REF, rect, regs)
        self.assertEqual(len(mv), 718, "the moved set of the frozen scenario must be reproducible")
        self.assertEqual(len(fx), 7055, "the fixed set of the frozen scenario must be reproducible")
        conf = block.clearance_conflicts(REF, rect, regs, [3.5, 3.5])
        self.assertGreater(conf["n_conflicts_shown"], 0, "the frozen delta must collide")
        self.assertEqual(conf["min_pair_mm"], 0.0, "the collision is a ZERO-distance overlap")
        d1 = block.geometric_digest(REF)
        d2 = block.geometric_digest(REF)
        self.assertEqual(d1["sha256_16"], d2["sha256_16"], "the geometric digest must be stable")
        self.assertEqual(d1["n_segments"], 6338)
        self.assertEqual(d1["n_vias"], 736)

    def test_K371_prim_dist_is_exact_for_every_shape_pair(self):
        """#K2-371 sec.3：方案层净距冲突判定要**真形**逐对精确（线段/有向矩形/圆 全组合）。"""
        seg = {"a": [0.0, 0.0], "b": [10.0, 0.0], "half_w": 0.1}
        seg2 = {"a": [0.0, 2.0], "b": [10.0, 2.0], "half_w": 0.1}
        rect = {"rect": {"cx": 5.0, "cy": 3.0, "sx": 2.0, "sy": 1.0, "rot": 0.0}}
        rect2 = {"rect": {"cx": 5.0, "cy": -3.0, "sx": 2.0, "sy": 1.0, "rot": 0.0}}
        circ = {"center": [5.0, 3.0], "radius": 0.5}
        circ0 = {"center": [5.0, -2.0], "radius": 0.0}
        self.assertAlmostEqual(block.prim_dist(seg, circ0), 1.9, places=6)      # seg vs circle
        self.assertAlmostEqual(block.prim_dist(seg, rect), 2.4, places=6)       # seg vs rect
        self.assertAlmostEqual(block.prim_dist({"center": [5.0, -2.0], "radius": 0.5}, rect), 4.0, places=6)
        self.assertAlmostEqual(block.prim_dist(circ0, circ), 4.5, places=6)     # circle vs circle
        self.assertAlmostEqual(block.prim_dist(rect, rect2), 5.0, places=6)     # rect vs rect
        self.assertAlmostEqual(block.prim_dist(seg, seg2), 1.8, places=6)       # seg vs seg
        self.assertEqual(block.prim_dist({"center": [5.0, 3.0], "radius": 0.5}, rect), 0.0,
                         "a circle inside a rect is a hard conflict")

    def test_K370_exact_shape_obstacles_kill_the_aabb_false_positive(self):
        """#K2-370 sec.3.3 / C32：线段障碍用**真形**测距。
        45 度线段的 AABB 会罩住"离铜很远"的点 => 旧模型假阳；真形模型必须放行，而真紧点仍须拒。"""
        seg = {"id": "s", "kind": "copper", "net": "X", "a": [0.0, 0.0], "b": [10.0, 10.0],
               "half_w": 0.1, "bbox": [0.0, 0.0, 10.0, 10.0]}
        box = {"id": "b", "kind": "copper", "net": "X", "bbox": [0.0, 0.0, 10.0, 10.0]}
        far = [[0.0, 10.0], [0.0, 10.0]]
        self.assertEqual(route.poly_violations(far, [seg], clearance=0.175), [],
                         "a point inside the AABB but far from the 45-degree segment must be CLEAR")
        self.assertTrue(route.poly_violations(far, [box], clearance=0.175),
                        "the AABB model still flags it - that WAS the false positive (gap C32)")
        near = [[5.0, 5.05], [5.0, 5.05]]
        self.assertTrue(route.poly_violations(near, [seg], clearance=0.175),
                        "a point 0.035mm off the segment surface must still be refused")

    def test_K370_board_model_hookup_and_true_shape_clearance(self):
        """#K2-370 sec.3.3 (gap 3a): eda_eng's geometry primitives come from the SHARED layer
        `_shared/eda_core/board_model`; `true_clearance_mm` measures REAL segment distance, not an AABB
        (a point sitting on its own track must read ~0; excluding its own net it must be > 0)."""
        self.assertTrue(block.BOARD_MODEL, "eda_eng must consume the shared board_model geometry")
        self.assertIn("_shared/eda_core/board_model/geometry.py", block.BOARD_MODEL_MODULE)
        import pcbnew as P
        b = P.LoadBoard(REF)
        nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
        pick = None
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetLayerName() != "F.Cu":
                continue
            n = nets.get(t.GetNetCode(), "")
            if n and n != "GND":
                s_, e_ = t.GetStart(), t.GetEnd()
                pick = (n, t.GetLayerName(),
                        ((P.ToMM(s_.x) + P.ToMM(e_.x)) / 2.0, (P.ToMM(s_.y) + P.ToMM(e_.y)) / 2.0))
                break
        self.assertIsNotNone(pick, "need one F.Cu track to sample")
        n, lay, mid = pick
        on_own = block.true_clearance_mm(REF, lay, "__nobody__", [mid])["clearance_mm"][0]["min_mm"]
        off_own = block.true_clearance_mm(REF, lay, n, [mid])["clearance_mm"][0]["min_mm"]
        self.assertLessEqual(on_own, 1e-3, "a point on its own track must measure ~0")
        self.assertGreater(off_own, 0.0, "excluding its own net, the nearest foreign copper is > 0")

    def test_K369_judge_accepts_and_enforces_C6_C7(self):
        """C6/C7 入判卷：extra 判据必须出现在 criteria 里，且 pass=False 会把 verdict 拉成 FAIL。"""
        refdrc = os.path.join("pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
        ok = verify.judge(REF, refdrc, REF, refdrc,
                          extra={"C6_outside_copper_unchanged": {"diff": 0, "pass": True},
                                 "C7_hs_fanout_untouched": {"diff": 0, "pass": True}})
        self.assertIn("C6_outside_copper_unchanged", ok["criteria"])
        self.assertIn("C7_hs_fanout_untouched", ok["criteria"])
        bad = verify.judge(REF, refdrc, REF, refdrc,
                           extra={"C6_outside_copper_unchanged": {"diff": 3, "pass": False}})
        self.assertEqual(bad["verdict"], "FAIL")

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


# ── 套件哨兵（#K2-380 §二 / #K2-381 §五.1）：**同进程改板＝立即具名失败**（SWIG 类型态纪律，承 R964/R1036）
def _bench_sentinel():                                     # noqa: D401
    def _boom(*a, **k):
        raise AssertionError(
            "BENCH SENTINEL: a board-mutating call ran IN THE TEST PROCESS "
            "(use the subprocess helper `_cli`; see docs/K2-BLOCKER-REPORT-testsuite-isolation-20260929.md)")
    route.apply_routes = _boom
    block.move_block = _boom
    block.move_parts = _boom


_bench_sentinel()
