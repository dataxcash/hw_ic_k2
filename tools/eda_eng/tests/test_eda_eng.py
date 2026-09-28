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

    def test_C36_the_judging_table_of_the_eco_is_read_row_by_row(self):
        """C36（#K2-377 §五 F3）：执行入口的判卷必须覆盖 ECO-K2-0004 §6 **全部九行**（含 C8）。"""
        eco = open(os.path.join("docs", "ECO", "ECO-K2-0004-reroute-engine-exam-A-prime.md"), encoding="utf-8").read()
        rows = [r for r in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9") if ("| **%s**" % r) in eco or ("| %s " % r) in eco]
        self.assertEqual(len(rows), 9, "the ECO must carry nine rows; found %s" % rows)
        src = open(os.path.join("tools", "eda_eng", "regen.py"), encoding="utf-8").read()
        for k in ("C6_outside_copper_unchanged", "C7_hs_fanout_untouched",
                  "C8_members_inside_frame", "C9_geometric_digest"):
            self.assertIn(k, src, "the product-path judging must emit %s" % k)

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
