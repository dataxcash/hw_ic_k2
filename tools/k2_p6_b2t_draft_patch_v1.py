#!/usr/bin/env python3
"""k2_p6_b2t_draft_patch_v1.py — B2-T（13 项既有隐藏失败）**甲案草稿补丁 + 影子验证**。

真源零改动：只读 k2/_shared、k2/hw、criteria/；全部编辑/产物落 /tmp/opencode。
产出：
  · B2T_DRAFT_PATCH_v1.json（机读：锚 / 5 棵树读数 / 逐项定性 / 缺陷 / 能力缺口）
  · docs/K2-P6-B2T-DRAFT-PATCH-AND-DISPOSITION-20260920.md（人读）
  · /tmp/opencode/b2t_draft_patch_v1.diff（可直接应用的草稿补丁 diff）

五棵树（全部 --board k2/k2_v4_8L.kicad_pcb + SHADOW-ONLY 测试板锚）：
  base     : 遗留 alloc 锚（现状）            —— 基线
  anchor   : 现行 pipeline alloc 锚（仅重锚）  —— 证明「锚」是 13 项的主因之一
  draft    : anchor + 甲案测试补丁            —— 期望值重基线
  draft_b1 : draft + B1 引擎最小守卫（/tmp 影子）—— 缺陷 B1 的影子修复
  negctl   : draft_b1 + 逐项 mutation         —— **牙齿证明**（改错期望必 FAIL）

严谨性（fail-closed）：
  ① cwd 必须 = 影子树根：容器根存在 `eda_core -> _shared/eda_core` 符号链接，
     `python3 -m pytest` 会把 cwd 置于 sys.path[0]，若 cwd=容器根则 import eda_core
     命中**真源**，影子补丁静默失效（本轮发现的影子 import 缺陷，C-19）。
  ② 每次 pytest 前在影子 tests/ 落 conftest.py，断言 `eda_core.__file__` 在影子树内（fail-closed）。
  ③ 禁 skipped 充绿：逐项读 PASSED/FAILED/SKIPPED 三态。
  ④ 确定性：两跑（不同树根）逐字节同。

用法（容器根）：python3 k2/tools/k2_p6_b2t_draft_patch_v1.py [--verify-determinism]
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_REL = "shared/eda_core/tests/test_hs_route_model.py"
HW_REL = "shared/eda_core/hs_route_model.py"
BOARD = os.path.join(REPO, "k2", "k2_v4_8L.kicad_pcb")
LEGACY_ALLOC = os.path.join(REPO, "k2/pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json")
E2E_REPORT = os.path.join(REPO, "k2/pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e/p3_real_board_e2e_report.json")
CUR_ALLOC = "/tmp/opencode/current_alloc_from_pipeline.json"
OUT_JSON = os.path.join(REPO, "k2", "pm_gate", "artifacts", "k2_v4", "P6_execution", "B2T_DRAFT_PATCH_v1.json")
OUT_DOC = os.path.join(REPO, "k2", "docs", "K2-P6-B2T-DRAFT-PATCH-AND-DISPOSITION-20260920.md")
OUT_DIFF = "/tmp/opencode/b2t_draft_patch_v1.diff"

# ── B2-T 13 项（基线 13 FAIL 清单；分类见文件末 DISPOSITION）───────────────
B2T_TESTS = ["test_probe_escape_capacity_dn0", "test_probe_reports_via_gap_fact",
             "test_capacity_regions_derived", "test_probe_region_capacity_structure",
             "test_capacity_map_persist", "test_corridor_clear_span",
             "test_chain_no_pn_zero_spacing", "test_flip_polarity_cross_rejected",
             "test_drawing_only_refuses_no_node",
             "test_escape_deterministic_byte_identical",
             "test_board_level_consistency",
             "test_link_topology_crossing_old_topology",
             "test_correct_polarity_solves_clean"]


SYNTH_COVERAGE_CLS = r'''

class TestB2TSyntheticCoverage:
    """B2-T 甲案配套（A3 重基线后『器件缩进』分支失去真板覆盖 ⇒ 合成现行 fixture 保覆盖）。

    合成件：spec.components（footprint 正则取器件半宽）+ corridor.x_range，零真板依赖。
    覆盖：① 左端缩进 ② 右端缩进 ③ 无尺寸器件不缩进 ④ 净空必含于 x_range ⑤ 确定性。
    """

    def _m(self, tmp_path, components):
        pcb = tmp_path / "syn.kicad_pcb"
        pcb.write_text(MINI_PCB, encoding="utf-8")
        sp = tmp_path / "spec.json"
        sp.write_text(json.dumps({"corridors": [{"id": "C_SYN",
                                                 "x_range": [100.0, 120.0]}],
                                  "components": components}), encoding="utf-8")
        ap = tmp_path / "alloc.json"
        ap.write_text(json.dumps({"alloc": {}}), encoding="utf-8")
        return HSRouteModel(str(pcb), str(sp), str(ap),
                            str(REPO / "_shared" / "eda_core" / "drc_rules.json"))

    def _span(self, m):
        c = next(c for c in m.spec["corridors"] if c["id"] == "C_SYN")
        return m._corridor_clear_span(c), c["x_range"]

    def test_corridor_clear_span_left_indent(self, tmp_path):
        """① 器件（半宽 5.0，pos x=100）覆盖走廊左端 x0 ⇒ x0 缩进到 105.2。"""
        m = self._m(tmp_path, {"redriver": {"R1": {"pos": [100.0, 50.0],
                                                   "footprint": "WQFN-64_10x5.5mm"}},
                               "connectors": {}})
        (x0, x1), xr = self._span(m)
        assert (x0, x1) == (105.2, 120.0)
        assert xr[0] <= x0 < x1 <= xr[1]

    def test_corridor_clear_span_right_indent(self, tmp_path):
        """② 器件（pos x=115）覆盖走廊右端 x1 ⇒ x1 缩进到 109.8。"""
        m = self._m(tmp_path, {"redriver": {"R1": {"pos": [115.0, 50.0],
                                                   "footprint": "WQFN-64_10x5.5mm"}},
                               "connectors": {}})
        (x0, x1), xr = self._span(m)
        assert (x0, x1) == (100.0, 109.8)
        assert xr[0] <= x0 < x1 <= xr[1]

    def test_corridor_clear_span_no_size_no_indent(self, tmp_path):
        """③ 无尺寸器件（连接器 footprint 无 _WxH）⇒ 不缩进；④ 含于 x_range；⑤ 确定性。"""
        m = self._m(tmp_path, {"redriver": {},
                               "connectors": {"J1": {"pos": [110.0, 50.0],
                                                     "footprint": "MCIO_4i_SFF-1016_RASide"}}})
        (x0, x1), xr = self._span(m)
        assert (x0, x1) == (100.0, 120.0)
        assert xr[0] <= x0 < x1 <= xr[1]
        assert self._span(m) == ((x0, x1), xr)   # ⑤ 确定性
'''


SYNTH_POLARITY_CLS = r'''

class TestB2TSyntheticPolarityCoverage:
    """B2-T 甲案配套：极性交叉必拒性质**去真板耦合**（合成 fixture；A7 真板版之外的合成保底）。

    合成件：P pad(100,55.2) / N pad(100,55.6)（异排 0.4 脚距）+ 走廊 C_SYN[110,131.5] 轨道 48.7。
    实测：flip=False ⇒ INFEASIBLE(kind=VIA) 证据 @ (100.243,55.211)；flip=True ⇒ @ (104.538,48.702)；
    两次调用逐字节同（确定性）。
    """

    def _m(self, tmp_path):
        pcb = tmp_path / "synb.kicad_pcb"
        pcb.write_text(
            "\n(kicad_pcb (version 20260306) (generator \"test\")\n"
            "\t(footprint \"U7\" (layer \"F.Cu\") (at 100 55.2 0)\n"
            "\t\t(pad \"1\" smd rect (at 0 0) (size 0.45 0.25) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_P\") (uuid \"u1\"))\n"
            "\t\t(pad \"2\" smd rect (at 0 0.4) (size 0.45 0.25) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_N\") (uuid \"u2\"))\n"
            "\t)\n\t(footprint \"J2\" (layer \"F.Cu\") (at 133.825 55.2 0)\n"
            "\t\t(pad \"1\" smd rect (at 1.175 -0.3) (size 1.3 0.35) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_P\") (uuid \"j1\"))\n"
            "\t\t(pad \"2\" smd rect (at -1.175 0.3) (size 1.3 0.35) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_N\") (uuid \"j2\"))\n"
            "\t)\n)\n", encoding="utf-8")
        sp = tmp_path / "spec.json"
        sp.write_text(json.dumps({
            "spec_version": "1.0",
            "components": {"redriver": {},
                           "connectors": {"J2": {"pos": [133.825, 55.2],
                                                 "footprint": "MCIO_4i_SFF-1016_RASide"}}},
            "corridors": [{"id": "C_SYN", "x_range": [110.0, 131.5], "y_range": [46.0, 52.0],
                           "bands": [{"band": "upper", "layer": "F.Cu",
                                      "tracks_y": [48.7], "pairs": 8}]}],
            "impedance": {"width_mm": 0.205}}), encoding="utf-8")
        ap = tmp_path / "alloc.json"
        ap.write_text(json.dumps({"alloc": {"PCIE_X1": {
            "band": "upper", "track_y": 48.7, "corridor": "C_SYN", "layer": "F.Cu",
            "status": "SOLVED", "seg_tracks": {"input": 48.7}}}}), encoding="utf-8")
        return HSRouteModel(str(pcb), str(sp), str(ap),
                            str(REPO / "_shared" / "eda_core" / "drc_rules.json"))

    def _call(self, m, flip):
        ep = pair_endpoints(m.board, "PCIE_X1_P", "PCIE_X1_N")
        pad_p, pad_n = ep["P"][0], ep["N"][0]
        band = build_hs_field(m.board, m.rules, layer="F.Cu", clear_hs_pads=True,
                              config=m.config, clear_hs_nets=("PCIE_X1_P", "PCIE_X1_N"))
        esc = build_hs_field(m.board, m.rules, layer="In2.Cu", clear_hs_pads=True,
                             config=m.config, clear_hs_nets=("PCIE_X1_P", "PCIE_X1_N"))
        return m._escape_pair(band, band, esc, pad_p, pad_n, 110.0, 48.7, 131.5, 1,
                              "PCIE_X1_P", "PCIE_X1_N", flip=flip)

    def test_polarity_cross_rejected_synthetic(self, tmp_path):
        """合成 fixture：flip=False ⇒ 相向交叉被拒（带几何证据）+ 确定性。"""
        m = self._m(tmp_path)
        r = self._call(m, False)
        assert r["status"] == "INFEASIBLE"
        assert r["kind"] == "VIA"
        assert "极性" in r["reason"] and "相向交叉" in r["reason"]
        ce = r["cross_evidence"]
        assert ce["min_edge"] <= -0.2 and ce["req"] == 0.175
        assert abs(ce["point"][0] - 100.243) < 0.01
        assert abs(ce["point"][1] - 55.211) < 0.01
        assert json.dumps(r, sort_keys=True) == json.dumps(self._call(m, False), sort_keys=True)

    def test_polarity_flip_true_also_rejected_synthetic(self, tmp_path):
        """合成 fixture：flip=True ⇒ 同样拒绝（证据点随 flip 变化）@ (104.538, 48.702)。"""
        m = self._m(tmp_path)
        r = self._call(m, True)
        assert r["status"] == "INFEASIBLE" and r["kind"] == "VIA"
        ce = r["cross_evidence"]
        assert ce["min_edge"] <= -0.2
        assert abs(ce["point"][0] - 104.538) < 0.01
        assert abs(ce["point"][1] - 48.702) < 0.01
'''


SYNTH_COMBINED_CLS = r'''

class TestB2TSyntheticCombinedCoverage:
    """B2-T 甲案配套：**跨廊道 0.4mm 偏移 × 层换位** 组合性质（合成 fixture，零真板依赖）。

    合成件：U7 侧 PCIE_X1_P(100,55.2)/N(100,55.6)（异排 0.4）+ J2 连接器；SPEC 双走廊
    `C_MAIN`(tracks 48.7) / `C_ALT`(tracks 49.1 = +0.4)；alloc `seg_tracks={input:48.7, out_J2:49.1}`
    且**分配廊道 = C_MAIN**（即 seg 轨道落在**另一条**廊道上）。
    实测（本用例固化）：跨廊道同 band 索引映射成立；错廊道解析 fail-closed 返回 None；
    层换位逃逸在 48.7/49.1 两轨道均 SOLVED/LSWAP 且两次调用逐字节同。
    """

    def _m(self, tmp_path):
        pcb = tmp_path / "syn_combined.kicad_pcb"
        pcb.write_text(
            "\n(kicad_pcb (version 20260306) (generator \"test\")\n"
            "\t(footprint \"U7\" (layer \"F.Cu\") (at 100 55.2 0)\n"
            "\t\t(pad \"1\" smd rect (at 0 0) (size 0.45 0.25) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_P\") (uuid \"u1\"))\n"
            "\t\t(pad \"2\" smd rect (at 0 0.4) (size 0.45 0.25) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_N\") (uuid \"u2\"))\n"
            "\t)\n\t(footprint \"J2\" (layer \"F.Cu\") (at 133.825 55.2 0)\n"
            "\t\t(pad \"1\" smd rect (at 1.175 -0.3) (size 1.3 0.35) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_P\") (uuid \"j1\"))\n"
            "\t\t(pad \"2\" smd rect (at -1.175 0.3) (size 1.3 0.35) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (net \"PCIE_X1_N\") (uuid \"j2\"))\n"
            "\t)\n)\n", encoding="utf-8")
        sp = tmp_path / "spec.json"
        sp.write_text(json.dumps({
            "spec_version": "1.0",
            "components": {"redriver": {},
                           "connectors": {"J2": {"pos": [133.825, 55.2],
                                                 "footprint": "MCIO_4i_SFF-1016_RASide"}}},
            "corridors": [
                {"id": "C_MAIN", "x_range": [98.83, 131.5], "y_range": [46.0, 52.0],
                 "bands": [{"band": "upper", "layer": "F.Cu", "tracks_y": [48.7], "pairs": 8}]},
                {"id": "C_ALT", "x_range": [98.83, 131.5], "y_range": [46.0, 52.0],
                 "bands": [{"band": "upper", "layer": "F.Cu", "tracks_y": [49.1], "pairs": 8}]}],
            "impedance": {"width_mm": 0.205}}), encoding="utf-8")
        ap = tmp_path / "alloc.json"
        ap.write_text(json.dumps({"alloc": {"PCIE_X1": {
            "band": "upper", "track_y": 48.7, "corridor": "C_MAIN", "layer": "F.Cu",
            "status": "SOLVED", "seg_tracks": {"input": 48.7, "out_J2": 49.1}}}}), encoding="utf-8")
        return HSRouteModel(str(pcb), str(sp), str(ap),
                            str(REPO / "_shared" / "eda_core" / "drc_rules.json"))

    def _lswap(self, m, track_y):
        ep = pair_endpoints(m.board, "PCIE_X1_P", "PCIE_X1_N")
        j2_p, j2_n = ep["P"][1], ep["N"][1]
        fcu = build_hs_field(m.board, m.rules, layer="F.Cu", clear_hs_pads=True,
                             config=m.config, clear_hs_nets=("PCIE_X1_P", "PCIE_X1_N"))
        in2 = build_hs_field(m.board, m.rules, layer="In2.Cu", clear_hs_pads=True,
                             config=m.config, clear_hs_nets=("PCIE_X1_P", "PCIE_X1_N"))

        def pn_ok(p_pts, p_layers, n_pts, n_layers):
            me, _pt = _path_pn_min_edge_pt(p_pts, p_layers, n_pts, n_layers, 0.205)
            return me is None or me >= 0.155

        return m._layer_swap_escape(fcu, fcu, in2, j2_p, j2_n, corr_x=131.5,
                                    track_y=track_y, bound_x=98.83, direction=-1,
                                    net_p="PCIE_X1_P", net_n="PCIE_X1_N", flip=False,
                                    esc_layer="In2.Cu", pn_ok=pn_ok)

    def test_cross_corridor_index_mapping(self, tmp_path):
        """跨廊道同 band 索引映射：seg 轨道 49.1 在 C_ALT 命中；对分配廊道 C_MAIN fail-closed None。"""
        m = self._m(tmp_path)
        assert m._track_y_for("PCIE_X1_P", "C_ALT", "out_J2") == (49.1, "F.Cu")
        assert m._track_y_for("PCIE_X1_P", "C_MAIN", "out_J2") is None
        assert m._track_y_for("PCIE_X1_P", "C_MAIN", "input") == (48.7, "F.Cu")

    def test_lswap_with_offsetsolved_and_deterministic(self, tmp_path):
        """层换位 × 0.4mm 偏移：48.7 与 49.1 两轨道均 SOLVED/LSWAP 且逐字节确定。"""
        m = self._m(tmp_path)
        for ty in (48.7, 49.1):
            r = self._lswap(m, ty)
            assert r is not None and r["status"] == "SOLVED", f"track_y={ty} 未 SOLVED"
            assert r["kind"] == "LSWAP"
            assert json.dumps(r, sort_keys=True) == json.dumps(self._lswap(m, ty), sort_keys=True)
'''

EXTRA_ITEMS = [
 dict(id="A13", cls="甲-配套新增合成覆盖（保 A3 缩进分支）",
      src="合成 spec：redriver footprint WQFN-64_10x5.5mm 半宽 5.0 + corridor[100,120] ⇒ 左/右缩进与不缩进三分支；实测 (105.2,120.0)/(100.0,109.8)/(100.0,120.0)",
      anchor="class TestLayerSwapEscape:",
      tests=["test_corridor_clear_span_left_indent",
             "test_corridor_clear_span_right_indent",
             "test_corridor_clear_span_no_size_no_indent"],
      mut=("assert (x0, x1) == (105.2, 120.0)", "assert (x0, x1) == (100.0, 120.0)")),
 dict(id="A14", cls="甲-配套新增合成覆盖（极性交叉必拒去真板耦合）",
      src="合成 fixture：P(100,55.2)/N(100,55.6) + 走廊 C_SYN[110,131.5] track_y 48.7 ⇒ flip=False 实测 INFEASIBLE(VIA) @ (100.243,55.211)、flip=True @ (104.538,48.702)，min_edge=-0.205，两次调用逐字节同",
      anchor="class TestLayerSwapEscape:",
      tests=["test_polarity_cross_rejected_synthetic",
             "test_polarity_flip_true_also_rejected_synthetic"],
      text=SYNTH_POLARITY_CLS,
      mut=("abs(ce[\"point\"][0] - 100.243) < 0.01", "abs(ce[\"point\"][0] - 999.0) < 0.01")),

 dict(id="A15", cls="甲-配套新增合成覆盖（跨廊道 0.4mm 偏移 × 层换位组合）",
      src="合成双走廊 C_MAIN(48.7)/C_ALT(49.1=+0.4)+alloc seg_tracks{input:48.7,out_J2:49.1}(分配廊道 C_MAIN) ⇒ "
          "_track_y_for(C_ALT,out_J2)=(49.1,F.Cu) 跨廊道索引映射、对 C_MAIN=None fail-closed；"
          "_layer_swap_escape 在 48.7/49.1 均 SOLVED/LSWAP 且逐字节确定",
      anchor="class TestLayerSwapEscape:",
      tests=["test_cross_corridor_index_mapping",
             "test_lswap_with_offsetsolved_and_deterministic"],
      text=SYNTH_COMBINED_CLS,
      mut=('assert m._track_y_for("PCIE_X1_P", "C_ALT", "out_J2") == (49.1, "F.Cu")', 'assert m._track_y_for("PCIE_X1_P", "C_ALT", "out_J2") == (48.7, "F.Cu")')),
]

ANCHOR_OLD = '''K2V4_ALLOC = (Path("/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4")
              / "L3" / "model_solves" / "channel_alloc_v2"
              / "channel_alloc.json")'''
ANCHOR_NEW = f'''K2V4_ALLOC = Path("{CUR_ALLOC}")  # B2T-DRAFT 重锚（现行 pipeline alloc）'''

B1_OLD_1 = '''        x_l = min(s["end_left"]["x"] for s in segs
                  if "end_left" in s)
        x_r = max(s["end_right"]["x"] for s in segs
                  if "end_right" in s)'''
B1_NEW_1 = '''        _ls = [s["end_left"]["x"] for s in segs if "end_left" in s]
        _rs = [s["end_right"]["x"] for s in segs if "end_right" in s]
        x_l = min(_ls) if _ls else None
        x_r = max(_rs) if _rs else None'''
B1_OLD_2 = '''            if xr and xr[0] <= x_r and xr[1] >= x_l:'''
B1_NEW_2 = '''            if (xr and x_l is not None and x_r is not None
                    and xr[0] <= x_r and xr[1] >= x_l):'''

# ── 甲案测试补丁（old/new 在**该 test 函数体内**唯一）─────────────────────
ITEMS = [
 dict(id="A1", test="test_capacity_regions_derived", cls="甲-期望重基线",
      src="m._capacity_regions() 实测 = 2 区域 connector",
      old='''        regions = m._capacity_regions()
        by_id = {r["id"]: r for r in regions}
        assert set(by_id) == {"U7_region", "U3_region", "J2_region",
                              "MCIO_region"}
        assert by_id["U7_region"]["type"] == "pin_region"
        assert by_id["U7_region"]["side"] == "left"
        assert by_id["U7_region"]["segname"] == "out_U7"
        assert len(by_id["U7_region"]["bases"]) == 8
        assert by_id["J2_region"]["type"] == "connector"
        assert by_id["J2_region"]["side"] == "right"''',
      new='''        # B2-T 甲：现行真源 2 区域（connector）；U7/U3 pin_region 属旧代际。
        # 来源：m._capacity_regions() 实测（alloc band 分组 + SPEC 组件类别）
        regions = m._capacity_regions()
        by_id = {r["id"]: r for r in regions}
        assert set(by_id) == {"J2_region", "MCIO_region"}
        for rid, cid in (("J2_region", "EAST_CHIP_TO_J2"),
                         ("MCIO_region", "WEST_MCIO_TO_CHIP")):
            assert by_id[rid]["type"] == "connector"
            assert by_id[rid]["side"] == "right"
            assert by_id[rid]["corridor_id"] == cid
            assert len(by_id[rid]["bases"]) == 8
        assert by_id["J2_region"]["bases"][0] == "UP0"
        assert by_id["MCIO_region"]["bases"][0] == "DN0"''',
      mut=('assert set(by_id) == {"J2_region", "MCIO_region"}',
           'assert set(by_id) == {"J2_region", "MCIO_region", "U7_region"}')),
 dict(id="A2", test="test_capacity_map_persist", cls="甲-期望重基线",
      src="m.capacity_map() 实测 = 2 区域 / 6 走廊（2 廊道 × 3 band）",
      old='''        cap = m.capacity_map()
        assert len(cap["regions"]) == 4
        assert len(cap["corridors"]) == 6''',
      new='''        cap = m.capacity_map()
        # 来源：m.capacity_map() 实测 = 2 区域 / 6 走廊（2 廊道 × 3 band）
        assert len(cap["regions"]) == 2
        assert set(cap["regions"]) == {"J2_region", "MCIO_region"}
        assert len(cap["corridors"]) == 6
        assert set(cap["corridors"]) == {
            "EAST_CHIP_TO_J2_dn", "EAST_CHIP_TO_J2_up",
            "EAST_CHIP_TO_J2_refclk", "WEST_MCIO_TO_CHIP_dn",
            "WEST_MCIO_TO_CHIP_up", "WEST_MCIO_TO_CHIP_refclk"}''',
      mut=('assert len(cap["regions"]) == 2', 'assert len(cap["regions"]) == 3')),
 dict(id="A3", test="test_corridor_clear_span", cls="甲-期望重基线",
      src="m._corridor_clear_span() 实测 = 各走廊 x_range 原值（无器件缩进）",
      old='''        corr = next(c for c in m.spec["corridors"]
                    if c["id"] == "J2_TO_U")
        x0, x1 = m._corridor_clear_span(corr)
        assert x0 > corr["x_range"][0]  # U7 器件右缘缩进
        assert x1 == corr["x_range"][1]
        corr2 = next(c for c in m.spec["corridors"]
                     if c["id"] == "U_TO_MCIO")
        y0, y1 = m._corridor_clear_span(corr2)
        assert y1 < corr2["x_range"][1]  # U3 器件左缘缩进
        assert y0 == corr2["x_range"][0]''',
      new='''        # B2-T 甲：现行几何无器件缩进（U7/U3 缩进属旧代际布局）。
        # 来源：m._corridor_clear_span() 实测 = 走廊 x_range 原值。
        # 保留不变量：净空区间必含于走廊 x_range（越界即 FAIL）。
        # 注：缩进分支在现行真板数据下不再被覆盖 ⇒ 另需合成 SPEC 单测保覆盖。
        for cid, x_range in (("EAST_CHIP_TO_J2", [105.25, 132.65]),
                             ("WEST_MCIO_TO_CHIP", [65.05, 82.35])):
            corr = next(c for c in m.spec["corridors"] if c["id"] == cid)
            assert corr["x_range"] == x_range
            x0, x1 = m._corridor_clear_span(corr)
            assert [x0, x1] == x_range
            assert x_range[0] <= x0 < x1 <= x_range[1]''',
      mut=('("EAST_CHIP_TO_J2", [105.25, 132.65])', '("EAST_CHIP_TO_J2", [105.26, 132.65])')),
 dict(id="A4", test="test_probe_escape_capacity_dn0", cls="甲-期望重基线",
      src='probe_escape_capacity(DN0,"input") 实测 status=BLOCKED / corridor=EAST_CHIP_TO_J2',
      old='''        res = m.probe_escape_capacity("PCIE_DN0_P", "PCIE_DN0_N", "input")
        assert res["status"] in ("SOLVED", "BLOCKED")
        assert res["corridor"] == "J2_TO_U"
        assert set(res["ends"]) == {"left", "right"}''',
      new='''        # 来源：probe_escape_capacity(DN0,"input") 实测
        # status=BLOCKED / corridor=EAST_CHIP_TO_J2 / ends={left,right}
        res = m.probe_escape_capacity("PCIE_DN0_P", "PCIE_DN0_N", "input")
        assert res["status"] == "BLOCKED"
        assert res["corridor"] == "EAST_CHIP_TO_J2"
        assert set(res["ends"]) == {"left", "right"}''',
      mut=('assert res["status"] == "BLOCKED"', 'assert res["status"] == "SOLVED"')),
 dict(id="A5", test="test_probe_reports_via_gap_fact", cls="甲-期望重基线",
      src="DN0 芯片侧实测 pn_pad_center_dist=0.6（0.4 脚距属旧代际引脚区）",
      old='''        left = res["ends"]["left"]
        assert left["pn_pad_center_dist"] == pytest.approx(0.4, abs=1e-3)
        assert left["candidates"][0]["pn_via_edge"] == pytest.approx(0.05, abs=1e-3)
        assert left["candidates"][0]["pn_via_gap_ok"] is False''',
      new='''        left = res["ends"]["left"]
        # 来源：DN0 芯片侧实测 pn_pad_center_dist=0.6
        assert left["pn_pad_center_dist"] == pytest.approx(0.6, abs=1e-3)
        c0 = left["candidates"][0]
        # 物理事实不变量（保牙齿）：via 边距 = P/N via 中心距 − 0.35（0.35 直径）
        assert c0["pn_via_edge"] == pytest.approx(
            c0["pn_via_center"] - 0.35, abs=1e-3)
        assert c0["pn_via_gap_ok"] is (c0["pn_via_edge"] >= 0.175 - 1e-9)''',
      mut=('pytest.approx(0.6, abs=1e-3)', 'pytest.approx(0.4, abs=1e-3)')),
 dict(id="A6", test="test_probe_region_capacity_structure", cls="甲-输入重锚(数据驱动)",
      src="m._capacity_regions() 的 J2_region（corridor=EAST_CHIP_TO_J2, side=right, out_J2, band=up）实测 CAPACITY_OK/8 对",
      old='''        region = {"id": "U7_region", "type": "pin_region",
                  "corridor_id": "J2_TO_U", "band": "upper",
                  "bases": [f"UP{i}" for i in range(8)],
                  "segname": "out_U7", "side": "left"}
        res = m.probe_region_capacity(region, demand=8)''',
      new='''        # B2-T 甲：区域由模型自推导（数据驱动），不硬编码旧代际 pin_region。
        # 来源：m._capacity_regions() 取 J2_region → 实测 CAPACITY_OK / 8 对。
        region = next(r for r in m._capacity_regions()
                      if r["id"] == "J2_region")
        assert region["corridor_id"] == "EAST_CHIP_TO_J2"
        res = m.probe_region_capacity(region, demand=8)''',
      mut=('if r["id"] == "J2_region")', 'if r["id"] == "MCIO_region")')),
 dict(id="A7", test="test_flip_polarity_cross_rejected", cls="甲-场景/事故点重锚",
      src="UP0+EAST_CHIP_TO_J2 flip=False 实测 INFEASIBLE(kind=VIA) min_edge=-0.205 @ (64.300,43.060)；原 WEST 场景实测已 SOLVED(LSWAP_V)",
      old='''        corr = next(c for c in m.spec["corridors"] if c["id"] == "U_TO_MCIO")
        track_y = m._track_y_for("PCIE_UP0_P", "U_TO_MCIO", "input")[0]''',
      new='''        # B2-T 甲：场景重锚（原 U_TO_MCIO 角色 ⇒ 现行 WEST_MCIO_TO_CHIP 下
        # 该对实测已 SOLVED(LSWAP_V)，不再交叉拒）；交叉拒证据改取自现行
        # EAST_CHIP_TO_J2 几何（同 _escape_pair，flip=False）。
        corr = next(c for c in m.spec["corridors"]
                    if c["id"] == "EAST_CHIP_TO_J2")
        track_y = m._track_y_for("PCIE_UP0_P", "EAST_CHIP_TO_J2", "input")[0]''',
      old2='''        assert abs(ce["point"][0] - 64.317) < 0.01
        assert abs(ce["point"][1] - 49.077) < 0.01''',
      new2='''        # 来源：实测交叉点 (64.300, 43.060)（原 64.317/49.077 属旧代际事故点）
        assert abs(ce["point"][0] - 64.300) < 0.01
        assert abs(ce["point"][1] - 43.060) < 0.01''',
      mut=('abs(ce["point"][1] - 43.060) < 0.01', 'abs(ce["point"][1] - 49.077) < 0.01')),
 dict(id="A8", test="test_drawing_only_refuses_no_node", cls="甲-输入重锚(角色解析)",
      src="WEST_MCIO_TO_CHIP + track_y 可解析 ⇒ kind=NO_DRAWING_NODE（断言不变）",
      old='''        corr = next(c for c in m.spec["corridors"] if c["id"] == "U_TO_MCIO")
        track_y = m._track_y_for("PCIE_UP0_P", "U_TO_MCIO", "input")[0]''',
      new='''        # B2-T 甲：走廊按现行 id 解析（原 U_TO_MCIO 角色 = WEST_MCIO_TO_CHIP）
        corr = next(c for c in m.spec["corridors"]
                    if c["id"] == "WEST_MCIO_TO_CHIP")
        track_y = m._track_y_for("PCIE_UP0_P", "WEST_MCIO_TO_CHIP", "input")[0]''',
      mut=('assert r["kind"] == "NO_DRAWING_NODE"', 'assert r["kind"] == "SELF_SEARCH"')),
 dict(id="A9", test="test_escape_deterministic_byte_identical", cls="甲-输入重锚(角色解析)",
      src="WEST_MCIO_TO_CHIP + track_y 可解析 ⇒ 同一逃逸两次输出逐字节同",
      old='''        corr = next(c for c in m.spec["corridors"] if c["id"] == "U_TO_MCIO")
        track_y = m._track_y_for("PCIE_UP0_P", "U_TO_MCIO", "input")[0]''',
      new='''        # B2-T 甲：走廊按现行 id 解析（原 U_TO_MCIO 角色 = WEST_MCIO_TO_CHIP）
        corr = next(c for c in m.spec["corridors"]
                    if c["id"] == "WEST_MCIO_TO_CHIP")
        track_y = m._track_y_for("PCIE_UP0_P", "WEST_MCIO_TO_CHIP", "input")[0]''',
      mut=('if c["id"] == "WEST_MCIO_TO_CHIP")', 'if c["id"] == "U_TO_MCIO")')),
 dict(id="A10", test="test_correct_polarity_solves_clean", cls="甲-输入重锚(无需改文本)",
      src="重锚现行 alloc 后 DN4 input 段实测 SOLVED 且 P/N 最小边缘距 ≥0.155",
      old=None, new=None, mut=None),
 dict(id="A11", test="test_link_topology_crossing_old_topology", cls="甲-期望重基线(+B1 守卫)",
      src="现行 alloc(+B1 守卫) 实测 CROSSING_FOUND / crossing=[UP4..UP7] / DN0-3·UP0-3·REFCLK0-1 ALIGNED",
      old='''        topo = m.link_topology_map()
        assert topo["verdict"] == "CROSSING_FOUND"
        assert sorted(topo["crossing_links"]) == \\
            ["DN0", "DN1", "DN2", "DN3", "UP4", "UP5", "UP6", "UP7"]
        for b in ["UP0", "UP1", "UP2", "UP3", "DN4", "DN5", "DN6", "DN7"]:
            assert topo["links"][b]["verdict"] == "ALIGNED", f"{b} 应同排 ALIGNED"''',
      new='''        # 来源：现行 alloc + B1 守卫实测 = CROSSING_FOUND，crossing=[UP4..UP7]
        # 4 对；DN0-3 / REFCLK0-1 / UP0-3 共 10 对 ALIGNED（原 8 对含 DN0-3
        # 属旧代际方向分工拓扑）。
        topo = m.link_topology_map()
        assert topo["verdict"] == "CROSSING_FOUND"
        assert sorted(topo["crossing_links"]) == \\
            ["UP4", "UP5", "UP6", "UP7"]
        for b in ["UP0", "UP1", "UP2", "UP3", "DN0", "DN1", "DN2", "DN3",
                  "REFCLK0", "REFCLK1"]:
            assert topo["links"][b]["verdict"] == "ALIGNED", f"{b} 应同排 ALIGNED"''',
      mut=None),
 dict(id="A12", test="test_board_level_consistency", cls="甲-输入筛选修正（测试仍 RED：能力缺口 C1）",
      src="现行 alloc 含 16 个 *_OUT* 条目 ⇒ 原 base 筛选得 34（应为 18）；筛选修正后断言暴露真实『未全解』",
      old='''        bases = sorted(k for k in alloc_recs if k.startswith("PCIE_"))''',
      new='''        bases = sorted(k for k in alloc_recs
                       if k.startswith("PCIE_") and "_OUT" not in k)  # B2-T 甲：排除 *_OUT* 段条目''',
      mut=None),
]

# ── 13 项定性（结论；状态由本工具实跑填）────────────────────────────────
DISPOSITION = {
 "test_capacity_regions_derived": ("甲", "期望重基线（2 区域 connector，数据驱动）"),
 "test_capacity_map_persist": ("甲", "期望重基线（2 区域 / 6 走廊）"),
 "test_corridor_clear_span": ("甲", "期望重基线（无器件缩进；保留含于 x_range 不变量）"),
 "test_probe_escape_capacity_dn0": ("甲", "期望重基线 + 走廊 id（status=BLOCKED）"),
 "test_probe_reports_via_gap_fact": ("甲", "期望重基线（0.6 中心距；保留 edge=中心距−0.35 不变量）"),
 "test_probe_region_capacity_structure": ("甲", "输入重锚：区域由 _capacity_regions() 自推导"),
 "test_flip_polarity_cross_rejected": ("甲", "场景/事故点重锚：EAST 几何 (64.300,43.060) 仍是 INFEASIBLE+证据"),
 "test_drawing_only_refuses_no_node": ("甲", "输入重锚（走廊角色解析）；断言不变"),
 "test_escape_deterministic_byte_identical": ("甲", "输入重锚（走廊角色解析）；断言不变"),
 "test_correct_polarity_solves_clean": ("甲", "输入重锚后 DN4 input 段 SOLVED（无需改文本）"),
 "test_link_topology_crossing_old_topology": ("甲+B1", "期望重基线（4 对 crossing）+ 需 B1 引擎守卫"),
 "test_board_level_consistency": ("丙", "能力缺口（现行 alloc 实测 1/18 SOLVED）⇒ 保持 RED，具名登记"),
 "test_chain_no_pn_zero_spacing": ("丙", "能力缺口（REFCLK0 实测 INFEASIBLE：左逃逸极性交叉 -0.205）⇒ 保持 RED"),
}


# ── §6 三处 ENG 定性（本会话实测闭合；Q1/Q2/Q3）─────────────────────────
ENG_QUALITATIVE = [
 {"id": "Q1", "item": "§6-① INFRA_ERROR vs INSUFFICIENT",
  "repro": "probe_region_capacity 同形状 region（1 对 UP0），仅 corridor_id/segname 不同",
  "measured": {
   "corridor_id='J2_TO_U'（遗留；SPEC 无此 id）": "status=INFRA_ERROR reason='无走廊 J2_TO_U'",
   "corridor_id='EAST_CHIP_TO_J2' + segname='out_U7'（旧段名）":
     "status=INSUFFICIENT；pair UP0=INFRA_ERROR reason=\"UP0 无段 out_U7（链段: ['input','out_J2']）\"",
   "corridor_id='EAST_CHIP_TO_J2' + segname='out_J2' + side='right'（现行）":
     "status=CAPACITY_OK；pair 字段齐（track_y/pair_center/pn_pad_center_dist/form/flip_usable）"},
  "verdict": "INFRA_ERROR = **输入契约错**（走廊 id 或段名与现行真源不符），与容量无关；INSUFFICIENT = "
             "**真实容量判定**。原用例把东走廊 id 与 U7 侧 bases/out_U7 混用 ⇒ 自相矛盾输入 ⇒ "
             "INFRA_ERROR 属正确的 fail-closed 行为（非引擎缺陷）。"},
 {"id": "Q2", "item": "§6-② solve_all_v4 0/18 与『18/18 无走廊命中』的关系",
  "evidence": {
   "遗留载体（测试锚）": "channel_alloc_v2/channel_alloc.json：corridor=J2_TO_U/U_TO_MCIO（SPEC 无此 id）、"
     "band=lower/upper（SPEC 为 dn/up）、track_y 属旧代际轨道 ⇒ _track_y_for(...)=None ⇒ "
     "NO_CORRIDOR / INFEASIBLE（0/18）",
   "现行 pipeline 载体": "P3 E2E 报告 stages.alloc.alloc（34 条；corridor=EAST_CHIP_TO_J2/WEST_MCIO_TO_CHIP，"
     "band=dn/up/refclk，track_y=58.3…）⇒ 链路可解；实测 1/18 SOLVED（PCIE_DN6），其余 INFEASIBLE 原因为"
     "『对级对称逃逸无净空 / via 换层 P/N 极性交叉 min 边缘距 −0.205』",
   "P3 自证": "p3_real_board_e2e_report.json gaps 已登记同源缺口（D4 形态卡：_escape_pair 形态缺口，本卡不做）",
   "走廊命中": "probe_escape_capacity(DN0) 实测 corridor=EAST_CHIP_TO_J2（**命中**）；NO_CORRIDOR 真因是 "
     "track 解析失败，不是走廊未命中"},
  "verdict": "0/18 **主因 = 输入锚过时**（遗留 alloc 载体与现行 SPEC 不同步：corridor id + band 名 + track 值"
             "三代错位），**非**『端点不在走廊』、**非**『SPEC 前提不成立』；**残余 = D4 形态能力缺口**（真缺口，"
             "现行载体 1/18）。⇒ 前会话『18/18 无走廊命中 ⇒ 遗留 API 前提不成立』读数须按此修正。"},
 {"id": "Q3", "item": "§6-③ 端点取法 pair_endpoints(...)['P'][0] 复核",
  "measured": {
   "PCIE_DN0": "P_x=[84.85,132.65]（左=芯片侧，右=J2 侧）；pair 全跨度命中 EAST_CHIP_TO_J2",
   "PCIE_UP0": "P_x=[64.3,85.15]（左=芯片侧）；pair 全跨度命中 WEST_MCIO_TO_CHIP",
   "PCIE_REFCLK0": "P_x=[58.9,132.65]（左=芯片侧）；pair 全跨度命中 EAST_CHIP_TO_J2"},
  "verdict": "取法**正确**（P[0] = 最左 = P 网芯片侧焊盘）；但走廊选择用的是 pair 中点/全跨度"
             "（_pair_center + _corridor_for_x），**不是**单个 pad ⇒『18/18 chip 侧 pad x ∉ 走廊』为真但"
             "不导致 NO_CORRIDOR（见 Q2）。caveat 关闭。"},
]

DEFECT_B1 = {
 "id": "B1",
 "title": "probe_link_topology 在现行 schema alloc 下崩溃（缺 fail-closed 守卫）",
 "site": f"{HW_REL} link_topology:  x_l = min(...) / x_r = max(...) 空序列",
 "repro": ("PYTHONPATH=<影子>/shared python3 -c 'from eda_core.hs_route_model import HSRouteModel as M;"
           "m=M(\"k2/k2_v4_8L.kicad_pcb\",\"<SPEC>\",\"/tmp/opencode/current_alloc_from_pipeline.json\",\"<rules>\");"
           "m.link_topology_map()'  ⇒ ValueError: min() arg is an empty sequence"),
 "impact": "link_topology_map / probe_link_topology 全灭（4 个拓扑用例连带失败；旧锚下不触发）",
 "min_fix": "空序列 → None（fail-closed），cap_wall 判定加 None 守卫；见 B1_NEW_1/B1_NEW_2 影子草案",
 "shadow_verified": "draft_b1 树：拓扑 4 用例由 4 FAIL → 全 PASS（crossing=[UP4..UP7]）",
 "authorization": "改 _shared ⇒ 属批2 授权（B2-2/B2-3 同批）",
}
CAPABILITY_GAPS = [
 {"id": "C1", "test": "test_board_level_consistency",
  "measured": "现行 pipeline alloc 锚：solve_all_v4 = 1/18 SOLVED（PCIE_DN6）",
  "legacy_evidence": "历史 hs_rebuild_v4 = 6/18、v10/v11/v8/v9 = 1/18、v12 = 2/18（均为旧板/旧代）",
  "verdict": "整板 18 链全解属**能力缺口**（P3 E2E 已登记 D4 形态卡：对级对称逃逸无净空 / via 换层极性交叉 -0.205）",
  "action": "禁重基线至绿；保持 RED + 具名登记（重开条件 = D4 形态补齐）"},
 {"id": "C2", "test": "test_chain_no_pn_zero_spacing",
  "measured": "REFCLK0 solve_chain_v4 = INFEASIBLE（左逃逸极性相向交叉 min 边缘距 -0.205 @ (58.900,45.560)）",
  "verdict": "同 C1（D4 形态卡）；其守护性质（SOLVED 段不得 0 间距）由 test_no_solved_segment_carries_crossing 覆盖",
  "action": "禁重基线至绿；保持 RED + 具名登记"},
]
HARNESS_DEFECT = {
 "id": "C-19",
 "title": "影子 pytest 的 import 可能命中真源（cwd 缺陷）",
 "site": "k2/tools/k2_p6_shadow_verify_v1.py run_pytest(cwd=REPO)",
 "mechanism": ("容器根存在 eda_core -> _shared/eda_core 符号链接；`python3 -m pytest` 将 cwd 置于 "
               "sys.path[0] ⇒ cwd=容器根时 import eda_core 命中真源，影子补丁（尤其 _shared 内）静默失效"),
 "impact": "对 _shared 的补丁在影子 pytest 中不生效（本工具 draft_b1 首跑即中招：守卫未生效）",
 "fix": "影子 pytest 一律 cwd=<影子树根> + tests/conftest.py 断言 eda_core.__file__ 在影子树内（本工具已实现）",
 "note": "既有 SHADOW_VERIFY_v1 结论不受影响（其补丁集只碰 pm_gate；pytest 腿内容与真源逐字节同）",
}


def sha16(path):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return h[:16]


def extract_current_alloc():
    d = json.load(open(E2E_REPORT, encoding="utf-8"))
    alloc = d["stages"]["alloc"]["alloc"]
    doc = {"meta": {"source": os.path.relpath(E2E_REPORT, REPO) + "#stages.alloc.alloc",
                    "input_fp": d["input_fp"], "board": d["board"]["path"],
                    "board_sha256": d["board"]["sha256"],
                    "note": "现行 pipeline（SolvePipeline.run_alloc）自产 alloc；非人工构造"},
           "alloc": alloc}
    with open(CUR_ALLOC, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True, indent=1)
    return doc


def _shadow_tool():
    p = os.path.join(REPO, "k2/tools/k2_p6_shadow_verify_v1.py")
    spec = importlib.util.spec_from_file_location("k2shadow", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fn_span(text, name):
    i = text.index(f"def {name}(")
    j = text.index("\n", i) + 1
    while j < len(text):
        nl = text.find("\n", j)
        line = text[j: nl if nl != -1 else len(text)]
        if line.strip() and (len(line) - len(line.lstrip())) <= 4 and re.match(r"\s*(def |@|class )", line):
            break
        j = (nl + 1) if nl != -1 else len(text)
    return i, min(j, len(text))


def patch_fn(text, name, old, new):
    i, j = fn_span(text, name)
    body = text[i:j]
    assert body.count(old) == 1, f"{name}: old 在该函数体内命中 {body.count(old)} 次"
    return text[:i] + body.replace(old, new, 1) + text[j:]


CONFTEST = '''"""fail-closed：断言被测 eda_core 来自影子树（防 cwd 导入真源）。"""
import pathlib, sys
import eda_core  # noqa
_root = pathlib.Path(__file__).resolve().parents[2]   # <shadow>/shared
_loaded = pathlib.Path(eda_core.__file__).resolve()
assert _root in _loaded.parents or _loaded.parent == _root, (
    f"eda_core 非影子副本: {_loaded} (期望在 {_root} 内)")
'''


def build(kind, tag=""):
    """kind ∈ {base,anchor,draft,draft_b1,negctl}（决定补丁行为）；
    tag 仅改树根名（用于确定性两跑），**不得**参与行为判定。"""
    assert kind in ("base", "anchor", "draft", "draft_b1", "negctl", "diffbase")
    root = f"/tmp/opencode/b2t_{kind}{('_' + tag) if tag else ''}"
    shutil.rmtree(root, ignore_errors=True)
    patches = _shadow_tool().build_shadow(root, BOARD, apply_batch2=True)
    tp = os.path.join(root, TEST_REL)
    text = open(tp, encoding="utf-8").read()
    if kind != "base" and kind != "diffbase":
        assert text.count(ANCHOR_OLD) == 1, "alloc 锚块未命中"
        text = text.replace(ANCHOR_OLD, ANCHOR_NEW, 1)
    if kind in ("draft", "draft_b1", "negctl"):
        for it in ITEMS:
            if it["old"]:
                text = patch_fn(text, it["test"], it["old"], it["new"])
            if it.get("old2"):
                text = patch_fn(text, it["test"], it["old2"], it["new2"])
        for it in EXTRA_ITEMS:
            assert text.count(it["anchor"]) == 1, f'{it["id"]} anchor 未唯一命中'
            ins = it.get("text") or SYNTH_COVERAGE_CLS
            if kind == "negctl":
                ins = ins.replace(it["mut"][0], it["mut"][1], 1)
            text = text.replace(it["anchor"], ins + "\n\n" + it["anchor"], 1)
    if kind == "negctl":
        for it in ITEMS:
            if it.get("mut"):
                text = patch_fn(text, it["test"], it["mut"][0], it["mut"][1])
    open(tp, "w", encoding="utf-8").write(text)
    open(os.path.join(root, "shared/eda_core/tests/conftest.py"), "w", encoding="utf-8").write(CONFTEST)
    if kind == "draft_b1":
        hp = os.path.join(root, HW_REL)
        hs = open(hp, encoding="utf-8").read()
        assert hs.count(B1_OLD_1) == 1 and hs.count(B1_OLD_2) == 1, "B1 守卫补丁未命中"
        open(hp, "w", encoding="utf-8").write(
            hs.replace(B1_OLD_1, B1_NEW_1, 1).replace(B1_OLD_2, B1_NEW_2, 1))
    return root, patches, text


def run_pytest(root):
    env = {k: v for k, v in os.environ.items() if k != "PM_GATE_PROJECT_ROOT"}
    env["PYTHONPATH"] = os.path.join(root, "shared")
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-v",
           os.path.join(root, TEST_REL)]
    pr = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env, timeout=3600)
    st = {m.group(2): m.group(3)
          for m in re.finditer(r"::(\w+)::(\w+) (PASSED|FAILED|SKIPPED|ERROR)", pr.stdout)}
    assert st, "pytest 状态解析为空（-q/-v 组合或输出格式变更）"
    counts = {"passed": sum(1 for v in st.values() if v == "PASSED"),
              "failed": sum(1 for v in st.values() if v == "FAILED"),
              "skipped": sum(1 for v in st.values() if v == "SKIPPED")}
    return {"counts": counts, "status": st, "rc": pr.returncode}


def collect(tag=""):
    """跑 5 棵树，返回机读结果。"""
    res = {"trees": {}, "shadow_import_guard": "conftest 断言 eda_core 在影子树内"}
    for kind in ("base", "anchor", "draft", "draft_b1", "negctl"):
        root, patches, _ = build(kind, tag)
        r = run_pytest(root)
        res["trees"][kind] = {**r, "root": root, "patch_count": len(patches)}
    t = res["trees"]
    teeth = {}
    for it in ITEMS:
        if not it.get("mut"):
            continue
        d = t["draft_b1"]["status"].get(it["test"])
        n = t["negctl"]["status"].get(it["test"])
        teeth[it["id"]] = {"draft_b1": d, "negctl": n, "teeth_ok": (d == "PASSED" and n == "FAILED")}
    for it in EXTRA_ITEMS:
        ds = [t["draft_b1"]["status"].get(x) for x in it["tests"]]
        ns = [t["negctl"]["status"].get(x) for x in it["tests"]]
        teeth[it["id"]] = {"draft_b1": f"{ds.count('PASSED')}/{len(ds)} PASSED",
                           "negctl": f"{ns.count('FAILED')}/{len(ns)} FAILED",
                           "teeth_ok": all(x == "PASSED" for x in ds) and any(x == "FAILED" for x in ns)}
    res["teeth"] = teeth
    res["teeth_all_ok"] = bool(teeth) and all(v["teeth_ok"] for v in teeth.values())
    return res



def write_diff():
    """从 diffbase（未重锚、未改测试）与 draft_b1 树生成统一 diff（容器根相对路径）。"""
    root = "/tmp/opencode/b2t_diffbase"
    tf_root = "/tmp/opencode/b2t_draft_b1"
    _tp = "k2/_shared/eda_core/tests/test_hs_route_model.py"
    _hp = "k2/_shared/eda_core/hs_route_model.py"
    def rd(r, rel):
        return open(os.path.join(r, rel), encoding="utf-8").read()
    diff = list(difflib.unified_diff(rd(root, TEST_REL).splitlines(True),
                                     rd(tf_root, TEST_REL).splitlines(True),
                                     "a/" + _tp, "b/" + _tp)) + \
           list(difflib.unified_diff(rd(root, HW_REL).splitlines(True),
                                     rd(tf_root, HW_REL).splitlines(True),
                                     "a/" + _hp, "b/" + _hp))
    with open(OUT_DIFF, "w", encoding="utf-8") as fh:
        fh.writelines(diff)
    return len(diff)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-determinism", action="store_true")
    ap.add_argument("--augment", action="store_true",
                    help="只把 §6 三处 ENG 定性并入既有 JSON/文档（不重跑树）")
    args = ap.parse_args()
    if args.augment:
        out = json.load(open(OUT_JSON, encoding="utf-8"))
        out["eng_qualitative"] = ENG_QUALITATIVE
        n_diff = write_diff() if os.path.isdir("/tmp/opencode/b2t_draft_b1") else 0
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        write_doc(out, sum(1 for _ in open(OUT_DIFF, encoding="utf-8")))
        print("augmented:", OUT_JSON, OUT_DOC)
        return 0
    doc = extract_current_alloc()
    run = collect()
    det = "NOT_RUN"
    if args.verify_determinism:
        run2 = collect(tag="d2")
        _slim = lambda r: {k: {"counts": v["counts"], "status": v["status"]}
                           for k, v in r["trees"].items()}
        det = "MATCH" if json.dumps(_slim(run), sort_keys=True) == \
            json.dumps(_slim(run2), sort_keys=True) else "MISMATCH"
    out = {
        "artifact": "k2_p6_b2t_draft_patch", "schema": 1, "readonly_repo": True,
        "purpose": "B2-T 13 项既有隐藏失败：甲案草稿补丁（期望重基线/输入重锚）+ 影子验证 + 牙齿(负控)证明",
        "anchors": {
            "board_8L": {"path": os.path.relpath(BOARD, REPO), "sha16": sha16(BOARD)},
            "spec_rev52": {"path": "k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json",
                           "sha16": sha16(os.path.join(REPO, "k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"))},
            "legacy_alloc": {"path": os.path.relpath(LEGACY_ALLOC, REPO), "sha16": sha16(LEGACY_ALLOC)},
            "current_alloc": {"path": CUR_ALLOC, "sha16": sha16(CUR_ALLOC),
                              "provenance": doc["meta"]["source"], "alloc_entries": len(doc["alloc"])},
            "test_file": {"path": "k2/_shared/eda_core/tests/test_hs_route_model.py",
                          "sha16": sha16(os.path.join(REPO, "k2/_shared/eda_core/tests/test_hs_route_model.py"))},
            "engine_file": {"path": "k2/_shared/eda_core/hs_route_model.py",
                            "sha16": sha16(os.path.join(REPO, "k2/_shared/eda_core/hs_route_model.py"))},
        },
        "tree_legend": {"base": "遗留 alloc 锚（现状）", "anchor": "仅重锚现行 pipeline alloc",
                        "draft": "anchor + 甲案测试补丁", "draft_b1": "draft + B1 引擎守卫（/tmp 影子）",
                        "negctl": "draft_b1 + 逐项 mutation（期望改错必 FAIL）"},
        "trees": run["trees"], "teeth": run["teeth"], "teeth_all_ok": run["teeth_all_ok"],
        "determinism_2run": det,
        "b2t_13": [{"test": t, "class": DISPOSITION[t][0], "disposition": DISPOSITION[t][1],
                    "base": run["trees"]["base"]["status"].get(t),
                    "anchor": run["trees"]["anchor"]["status"].get(t),
                    "draft_b1": run["trees"]["draft_b1"]["status"].get(t),
                    "negctl": run["trees"]["negctl"]["status"].get(t)} for t in B2T_TESTS],
        "items": [{"id": it["id"], "test": it["test"], "class": it["cls"], "expectation_source": it["src"],
                   "patch": bool(it["old"]), "mutation": bool(it.get("mut")),
                   "draft_b1": run["trees"]["draft_b1"]["status"].get(it["test"]),
                   "negctl": run["trees"]["negctl"]["status"].get(it["test"])} for it in ITEMS],
        "coverage_items": [{"id": it["id"], "class": it["cls"], "expectation_source": it["src"],
                            "tests": it["tests"],
                            "draft_b1": {x: run["trees"]["draft_b1"]["status"].get(x) for x in it["tests"]},
                            "negctl": {x: run["trees"]["negctl"]["status"].get(x) for x in it["tests"]},
                            "mutation": it["mut"][1]} for it in EXTRA_ITEMS],
        "defects": [DEFECT_B1], "capability_gaps": CAPABILITY_GAPS, "harness_defect": HARNESS_DEFECT,
        "eng_qualitative": ENG_QUALITATIVE,
        "caveats": [
            "A3 缩进分支在现行真板数据下不再被覆盖 ⇒ 已由 A13（合成现行 fixture，TestB2TSyntheticCoverage 3 例）补齐覆盖。",
            "A12 仅修输入筛选（34→18）；能力断言保持 RED（C1），不得改绿。",
            "C1/C2 属能力缺口（D4 形态卡），禁重基线至绿；重开条件 = D4 形态补齐。",
            "B1 守卫属 _shared 改动 ⇒ 需批2 授权；本工具仅在 /tmp 影子验证。",
            "现行 alloc 取自 P3 E2E 报告的 stages.alloc.alloc（pipeline 自产）；落库前需监理裁定承载形态。",
        ],
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    # diff（base → draft_b1 的测试文件 + 引擎守卫）
    build("diffbase")
    n_diff = write_diff()
    write_doc(out, n_diff)
    print(json.dumps({"trees": {k: v["counts"] for k, v in run["trees"].items()},
                      "teeth_all_ok": run["teeth_all_ok"], "determinism": det,
                      "b2t_13": {t: run["trees"]["draft_b1"]["status"].get(t) for t in B2T_TESTS},
                      "out": {"json": OUT_JSON, "doc": OUT_DOC, "diff": OUT_DIFF}},
                     ensure_ascii=False, indent=1))
    return 0


def write_doc(out, diff_lines):
    cov = {c["id"]: c for c in out.get("coverage_items", [])}
    rows = "\n".join(
        f"| `{b['test']}` | {b['class']} | {b['base']} | {b['anchor']} | {b['draft_b1']} | {b['negctl']} | {b['disposition']} |"
        for b in out["b2t_13"])
    it_rows = "\n".join(
        f"| {i['id']} | `{i['test']}` | {i['class']} | {'是' if i['patch'] else '—'} | "
        f"{'是' if i['mutation'] else '—'} | {i['draft_b1']} | {i['negctl']} | {i['expectation_source']} |"
        for i in out["items"])
    teeth_rows = "\n".join(
        f"| {k} | {v['draft_b1']} | {v['negctl']} | {'✅' if v['teeth_ok'] else '❌'} |"
        for k, v in sorted(out["teeth"].items()))
    tc = {k: v["counts"] for k, v in out["trees"].items()}
    doc = f"""# K2 · P6/B2-T 13 项既有隐藏失败 · **甲案草稿补丁 + 逐项定性**（ENG / ARCHER）

> 状态：**草稿（/tmp 影子，真源零改动）**；判定归监理 · 施工前需批2 授权（碰 `_shared` / 测试锚）。
> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_DRAFT_PATCH_v1.json` · diff：`{OUT_DIFF}`
> 生成：`python3 k2/tools/k2_p6_b2t_draft_patch_v1.py --verify-determinism`
> **补记（同一会话续作）**：测试锚**承载形态**验证见
> `k2/docs/K2-P6-B2T-ANCHOR-CARRIER-AND-FAILCLOSED-20260920.md` —— 结论：**运行期自建 alloc 不可行**
> （现行 8L 输入下 alloc 阶段 0 解），锚迁移须走「具名冻结载体（P3 Sept-9 alloc，血缘登记）」或
> 「合成现行 fixture」；B1 同族 fail-closed 普查 = 单点缺陷（33 API × 2 载体仅 B1 抛异常）。

## 0. 五棵树读数（同一测试文件、同一板锚；差异只在 alloc 锚 / 补丁 / 引擎守卫）

| 树 | 含义 | passed | failed | skipped |
|---|---|---|---|---|
| base | 遗留 alloc 锚（现状） | {tc['base']['passed']} | {tc['base']['failed']} | {tc['base']['skipped']} |
| anchor | 仅重锚现行 pipeline alloc | {tc['anchor']['passed']} | {tc['anchor']['failed']} | {tc['anchor']['skipped']} |
| draft | anchor + 甲案测试补丁 | {tc['draft']['passed']} | {tc['draft']['failed']} | {tc['draft']['skipped']} |
| **draft_b1** | draft + B1 引擎守卫（/tmp 影子） | **{tc['draft_b1']['passed']}** | **{tc['draft_b1']['failed']}** | {tc['draft_b1']['skipped']} |
| negctl | draft_b1 + 逐项 mutation | {tc['negctl']['passed']} | {tc['negctl']['failed']} | {tc['negctl']['skipped']} |

牙齿（负控）总判：**{'PASS' if out['teeth_all_ok'] else 'FAIL'}**（改错期望必 FAIL ⇒ 补丁不是"改绿"）
确定性（两跑逐字节同）：**{out['determinism_2run']}**

## 1. 13 项逐项定性（状态 = 各树实测）

| test | 定性 | base(遗留锚) | anchor(仅重锚) | draft_b1(甲案+B1) | negctl | 处置 |
|---|---|---|---|---|---|---|
{rows}

**读法**：`甲` = 期望重基线 / 输入重锚（可施工，须监理批）；`丙` = 能力缺口（禁改绿，具名登记）。
`draft_b1` 列 FAILED 的 `丙` 项 = **故意保持 RED** 的真实缺口。

## 2. 甲案补丁逐项（含期望值来源；全部实测）

| # | test | 定性 | 改测试 | 负控 | draft_b1 | negctl | 期望值来源（实测） |
|---|---|---|---|---|---|---|---|
{it_rows}

**配套新增覆盖（A13）**：A3 重基线后「器件缩进」分支在真板数据下不再被覆盖，故新增**合成现行 fixture** 用例
（`TestB2TSyntheticCoverage`，3 例：左端缩进 / 右端缩进 / 无尺寸不缩进 + 含于 x_range + 确定性）：
draft_b1 = {cov.get('A13', {}).get('draft_b1')} · negctl（改错左端期望）= {cov.get('A13', {}).get('negctl')}
（来源：合成 spec，redriver `WQFN-64_10x5.5mm` 半宽 5.0 + corridor `[100,120]`）
另有 **A14**（`TestB2TSyntheticPolarityCoverage` 2 例）：合成 fixture 复现「极性交叉必拒 + 几何证据 + 确定性」
（`INFEASIBLE`/`kind=VIA`/`min_edge=-0.205`，证据点 flip=False @ (100.243,55.211)、flip=True @ (104.538,48.702)）
⇒ 极性性质**去真板耦合**：draft_b1 = {cov.get('A14', {}).get('draft_b1')} · negctl = {cov.get('A14', {}).get('negctl')}
另有 **A15**（`TestB2TSyntheticCombinedCoverage` 2 例）：**跨廊道 0.4mm 偏移 × 层换位**组合（`_track_y_for(C_ALT,out_J2)=(49.1,F.Cu)`、
对 `C_MAIN` 返回 None 的 fail-closed 负例；`_layer_swap_escape` 在 48.7/49.1 均 `SOLVED`/`LSWAP` 且逐字节确定）：
draft_b1 = {cov.get('A15', {}).get('draft_b1')} · negctl = {cov.get('A15', {}).get('negctl')}

**牙齿逐项**（draft_b1=PASSED 且 negctl=FAILED 才算✅）：
| # | draft_b1 | negctl | 牙齿 |
|---|---|---|---|
{teeth_rows}

## 3. 引擎缺陷 B1（真缺陷 · 需授权修）

- **现象**：现行 schema alloc（34 条，含 `*_OUT*`）下 `probe_link_topology` 抛
  `ValueError: min() arg is an empty sequence`（`x_l = min(... for s in segs if "end_left" in s)`）。
- **影响**：`link_topology_map` 全灭 ⇒ 4 个拓扑用例连带失败（遗留锚下不触发 ⇒ 长期隐藏）。
- **最小修**（fail-closed，2 处）：空序列 → `None` + cap_wall 判定加 `None` 守卫。
- **影子验证**：`draft_b1` 树拓扑 4 用例 **4 FAIL → 全 PASS**（crossing=[UP4..UP7]）。
- **授权**：改 `_shared` ⇒ 属批2（与 B2-2/B2-3 同批）。

## 4. 能力缺口（禁重基线至绿）

| # | test | 实测 | 定性 |
|---|---|---|---|
| C1 | `test_board_level_consistency` | 现行 alloc 锚 `solve_all_v4` = **1/18 SOLVED**（PCIE_DN6） | 整板 18 链全解 = 能力缺口（P3 E2E 已登记 D4 形态卡：对级对称逃逸无净空 / via 换层极性交叉 −0.205）；保持 RED + 具名登记 |
| C2 | `test_chain_no_pn_zero_spacing` | `REFCLK0` = INFEASIBLE（−0.205 @ (58.900,45.560)） | 同 C1；其守护性质由 `test_no_solved_segment_carries_crossing`（PASS）覆盖 |

## 5. 工具/口径缺陷（本轮发现，供监理）

- **C-19 影子 import 缺陷**：`k2_p6_shadow_verify_v1.py` 的 `run_pytest(cwd=REPO)` 在容器根运行
  `python3 -m pytest` ⇒ cwd 进 `sys.path[0]` ⇒ `import eda_core` 命中容器根符号链接
  `eda_core -> _shared/eda_core`（**真源**），对 `_shared` 的影子补丁静默失效。
  本工具已修：cwd=影子树根 + `tests/conftest.py` 断言 `eda_core.__file__` 在影子树内（fail-closed）。
  既有 `SHADOW_VERIFY_v1` 结论**不受影响**（其补丁集只碰 `pm_gate`，pytest 腿内容与真源逐字节同）。
- **前会话读数修正**："18/18 端点不在走廊 ⇒ 遗留 API 前提不成立"**不准确**：
  ① `probe_escape_capacity` 实测**命中走廊** `EAST_CHIP_TO_J2`，`NO_CORRIDOR` 的真因是
  `_track_y_for` 在**遗留 alloc**（corridor `J2_TO_U`/band `lower`/track 值旧代）解析失败；
  ② 换现行 alloc 锚后，13 项中 **10 项转为可实现**（实测），说明主因是**输入锚过时**+
  命名/几何代际漂移，而非"几何前提不成立"；③ 剩余真实缺口 = B1（崩溃）+ C1/C2（能力）。

## 6. §6 三处 ENG 定性（实测闭合）

| # | 议题 | 结论（实测） |
|---|---|---|
| Q1 | `INFRA_ERROR` vs `INSUFFICIENT` | **INFRA_ERROR = 输入契约错**（走廊 id `J2_TO_U` 不存在于 SPEC → "无走廊 J2_TO_U"；或段名 `out_U7` 与现行链段 `['input','out_J2']` 不符）——与容量无关；**INSUFFICIENT = 真实容量判定**（现行 id+段名 ⇒ CAPACITY_OK；旧段名 ⇒ INSUFFICIENT 且 pair 级 INFRA_ERROR）。原用例自相矛盾输入 ⇒ INFRA_ERROR 属正确 fail-closed。 |
| Q2 | `solve_all_v4` 0/18 的成因 | **主因 = 输入锚过时**：遗留 `channel_alloc_v2` 的 corridor id（`J2_TO_U`/`U_TO_MCIO`）、band 名（`lower`/`upper`）、track 值三代与现行 SPEC 错位 ⇒ `_track_y_for`=None ⇒ NO_CORRIDOR/INFEASIBLE。换**现行 pipeline alloc** 后链路可解，实测 **1/18 SOLVED**（PCIE_DN6），其余为 D4 形态能力缺口（对级对称逃逸无净空 / via 换层极性交叉 −0.205，P3 E2E gaps 已登记）。**非**"端点不在走廊"、**非**"SPEC 前提不成立"。 |
| Q3 | 端点取法 `pair_endpoints(...)['P'][0]` | 取法**正确**（P[0]=最左=P 网芯片侧焊盘：DN0 84.85 / UP0 64.3 / REFCLK0 58.9）；但走廊选择用 **pair 中点/全跨度**（`_pair_center`+`_corridor_for_x`），非单 pad ⇒ "18/18 chip 侧 pad x ∉ 走廊"为真但不导致 NO_CORRIDOR（见 Q2）。caveat 关闭。 |

## 7. 授权项（单列，等监理/批2）

1. **测试锚**：`K2V4_ALLOC` 由遗留 `channel_alloc_v2` 改指现行 pipeline alloc（承载形态待裁：
   落库再生成 or 测试内自建 `SolvePipeline.run_alloc`）。
2. **`_shared` 改动**：B1 守卫（2 处，fail-closed）。
3. **测试期望重基线批**：A1–A12（11 项期望/输入重锚）。
4. **不申请**：C1/C2 改绿（能力缺口，禁缩口径）。

—— ENG（ARCHER）· 2026-09-20 · 真源零改动（`_shared` / `criteria/` / 冻结四源 / 交付锚未动）· diff {diff_lines} 行
"""
    os.makedirs(os.path.dirname(OUT_DOC), exist_ok=True)
    with open(OUT_DOC, "w", encoding="utf-8") as fh:
        fh.write(doc)


if __name__ == "__main__":
    raise SystemExit(main())
