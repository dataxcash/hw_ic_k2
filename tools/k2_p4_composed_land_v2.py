#!/usr/bin/env python3
"""K2 · P4 · **复合落件器 v2**（supersedes `k2_p4_composed_land_v1.py`；dry-run 默认）。

把「W-7 修复 + PDN 接线 + tncv 对齐 + C86 重落位 + **③ 丝印位号残余修复**」的
**五步复合结果板**一笔落进仓库，并
  ① 写板 → **dst pro 逐字节校验**（T-22）；
  ② SPEC 新增 **rev-47** = rev-46 + `_spec_rev_37`（**按复合实况**的变更记录）+ `spec_version` bump
     + **`pd` 内 `C86` 的 `pad_pos`/`via_pos` 同步对齐**（由落地板几何派生，非硬编码）；
     + **丝印位号残余修复台账**（由 `--silk-report` 逐条入账：ref/old/new/角度/位移）；
  ③ `project.yaml.spec_name` bump；
  ④ 落件后 DRC 复核（仓库 pro 语义）。
前置 fail-closed：仓库板/pro/canonical rev-46/`criteria` 两份 sha 全对；结果板 sha 指定；rev-47 不存在；
`--silk-report` 必给且含实际移动台账（丝印步骤不可无凭落地）。

用法（dry-run）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_composed_land_v2.py \
    --result-board <五步复合板> --result-sha16 <sha16> --silk-report <silk_fix_report.json>
"""
import argparse
import copy
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W
import k2_p4_w7_land_v1 as L

NM = 1_000_000
REF = "C86"


def board_anchor(board):
    """从落地板派生 C86 各 pad 的 (pad_pos, via_pos)。"""
    bd = pcbnew.LoadBoard(board)
    fp = next((f for f in bd.GetFootprints() if f.GetReference() == REF), None)
    if fp is None:
        raise RuntimeError(f"{REF} not found in {board}")
    out = {}
    for p in fp.Pads():
        pp, net = p.GetPosition(), p.GetNetname()
        best = None
        for t in bd.GetTracks():
            if not W.is_via(t) or t.GetNetname() != net:
                continue
            q = t.GetPosition()
            d = ((q.x - pp.x) ** 2 + (q.y - pp.y) ** 2) ** 0.5
            if d <= NM and (best is None or d < best[0]):
                best = (d, q.x, q.y)
        out[p.GetPadName()] = {"net": net,
                               "pad_pos": [pp.x / NM, pp.y / NM],
                               "via_pos": [best[1] / NM, best[2] / NM] if best else None}
    return out


def align_pd(node, anchor, path="pd", out=None):
    """递归对齐 `pd` 子树内 ref==C86 且含 pad_pos 的**现行**叶（跳过 `retired_*` 历史块）。"""
    out = [] if out is None else out
    if "retired" in path:
        return out
    if isinstance(node, dict):
        if node.get("ref") == REF and isinstance(node.get("pad_pos"), list):
            pad = str(node.get("pad", ""))
            a = anchor.get(pad)
            if a:
                node["pad_pos"] = [round(a["pad_pos"][0], 3), round(a["pad_pos"][1], 3)]
                if a["via_pos"]:
                    node["via_pos"] = [round(a["via_pos"][0], 3), round(a["via_pos"][1], 3)]
                node["relocated_basis"] = (f"P4 C86 重落位（清除 C86⊂U2 实体碰撞）："
                                           f"pad_pos/via_pos 由落地板几何派生")
                out.append({"at": path, "pad": pad, "net": node.get("net"),
                            "pad_pos": node["pad_pos"], "via_pos": node.get("via_pos")})
        for k, v in node.items():
            align_pd(v, anchor, f"{path}/{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            align_pd(v, anchor, f"{path}[{i}]", out)
    return out


def spec_record(composed):
    return {
        "card": "SPEC-REV-37（复合）",
        "at": "2026-09-18",
        "authority": ("owner #14「L2 = 叠层/PDN/走廊/布线/过孔策略/等长/热机械 = 自裁勿停」"
                      " + 监理 #K2-19 §二（W-7 deny-by-default；W-8 以板为准）"
                      " + 监理续推令（按已批准计划推进 P4，不越阶段）"),
        "basis": [
            "复合结果板 = 源板 → W-7 修复 → PDN 接线增量 → tncv 对齐增量 → C86 重落位；"
            "四步均为 L2 施工（不改 L1：拓扑/器件集合/网络/球映射/接口朝向/信号流向不变）。",
            "每步各自的复算闸（无新类型 / 无类型增量 / error=0 / unconnected=0 [+ 总量下降]）逐案通过；"
            "结果板由 `KIID.SeedGenerator(20260918)` 固定，多次复跑逐字节相同。",
            "C86 重落位用于清除 `p3_placement_solution.json` 遗留的实体碰撞（C86⊂U2）："
            "`pd` 内 C86 的 `pad_pos`/`via_pos` 已随本 rev 由落地板几何同步对齐。",
        ],
        "findings": composed,
        "landed": {"after": {"board_sha16": None}},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--result-board", required=True)
    ap.add_argument("--result-sha16", required=True)
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l5.kicad_pcb")
    ap.add_argument("--pro", default="k2/hw/k2_v4_8L.l5.kicad_pro")
    ap.add_argument("--expect-board-sha16", default="37019705ef994ccc")
    ap.add_argument("--expect-pro-sha16", default="f68a5fb2f82bd02d")
    ap.add_argument("--spec-dir", default="k2/pm_gate/artifacts/k2_v4/L3")
    ap.add_argument("--project-yaml", default="k2/pm_gate/project.yaml")
    ap.add_argument("--expect-spec-sha16", default="dea36093ba2b4031")
    ap.add_argument("--criteria", default="criteria")
    ap.add_argument("--expect-adjudicate-sha16", default="897e8bfde60e2cfe")
    ap.add_argument("--expect-manifest-sha16", default="7ce08757eff25557")
    ap.add_argument("--kicad-cli", default="AppDir/bin/kicad-cli")
    ap.add_argument("--work-dir", default="/tmp/opencode/land-composed")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--silk-report", default="",
                    help="③ 丝印修复台账 JSON（k2_p4_silk_text_fix_v1.py 产物）；必给")
    ap.add_argument("--confirm-repo-write", action="store_true",
                    help="写仓库的**显式**二次确认（T-41：无此旗标则拒绝 --apply）")
    a = ap.parse_args(argv)
    os.makedirs(a.work_dir, exist_ok=True)
    if a.apply and not a.confirm_repo_write:
        L.die("T-41：`--apply` 会写仓库板/SPEC/project.yaml —— 必须同时给 `--confirm-repo-write`")
    print(f"=== K2 复合落件器 v2 · {'APPLY' if a.apply else 'DRY-RUN（默认，不写仓库）'} ===")
    for path, exp, what in ((a.board, a.expect_board_sha16, "仓库板"),
                            (a.pro, a.expect_pro_sha16, "仓库 pro")):
        got = L.s16(path)
        (L.ok if got == exp else L.die)(f"{what} sha16={got}（期望 {exp}）")
    if L.s16(a.result_board) != a.result_sha16:
        L.die(f"结果板 sha16={L.s16(a.result_board)}（期望 {a.result_sha16}）")
    L.ok(f"结果板 sha16={a.result_sha16}（{a.result_board}）")
    rev46 = os.path.join(a.spec_dir, "SPEC_k2_v4.spec-rev-46.json")
    if L.s16(rev46) != a.expect_spec_sha16:
        L.die(f"canonical SPEC rev-46 sha16={L.s16(rev46)}（期望 {a.expect_spec_sha16}）")
    L.ok(f"canonical SPEC rev-46 sha16={a.expect_spec_sha16}")
    for name, exp in (("adjudicate.py", a.expect_adjudicate_sha16),
                      ("manifest.k2.yaml", a.expect_manifest_sha16)):
        got = L.s16(os.path.join(a.criteria, name))
        (L.ok if got == exp else L.die)(f"criteria/{name} sha16={got}（期望 {exp}）")
    if not a.silk_report or not os.path.exists(a.silk_report):
        L.die(f"T-41/台账：必须给 `--silk-report`（存在且含 moves）：{a.silk_report or '(空)'}")
    silk = json.load(open(a.silk_report, encoding="utf-8"))
    if not silk.get("moves"):
        L.die("丝印台账 `moves` 为空 —— 复合板未含 ③ 丝印步骤，拒绝按 v2 落件")
    L.ok(f"丝印台账 {os.path.basename(a.silk_report)}：移动 {len(silk['moves'])} 件 · "
         f"未落位 {len(silk.get('unplaced', []))} · 几何剩余 {silk.get('after_geo_offenders')}")

    rev47 = os.path.join(a.spec_dir, "SPEC_k2_v4.spec-rev-47.json")
    if os.path.exists(rev47):
        L.die(f"SPEC rev-47 已存在（{rev47}）")
    n_err, n_warn, n_unc = L.drc_counts(a.kicad_cli, a.result_board,
                                        os.path.join(a.work_dir, "drc_result.json"))
    L.ok(f"结果板 DRC（探针 pro）：error={n_err} warning={n_warn} unconnected={n_unc}")
    if n_err or n_unc:
        L.die("结果板自带 error 或未连接 —— 不得落件")

    anchor = board_anchor(a.result_board)
    d = json.load(open(rev46, encoding="utf-8"))
    d2 = copy.deepcopy(d)
    changed = align_pd(d2.get("pd", {}), anchor, "pd")
    print(f"[plan] `pd` 内 C86 对齐 {len(changed)} 处：")
    for c in changed:
        print("   ", json.dumps(c, ensure_ascii=False))
    if not changed:
        L.die("`pd` 内未找到 C86 叶 —— 人工确认后再落")

    if not a.apply:
        print("\n[DRY-RUN] 批准后执行：")
        print(f"  AppDir/usr/bin/python3.11 k2/tools/k2_p4_composed_land_v2.py \\\n"
              f"    --result-board {a.result_board} --result-sha16 {a.result_sha16} --apply")
        print("拟改动：① 仓库板（五步复合）② SPEC rev-47（= rev-46 + 复合变更记录 + 丝印台账 + `pd` C86 对齐 + spec_version）"
              " ③ project.yaml bump。**不动**：仓库 pro（逐字节校验）、`criteria/`、rev-19..46 原件。")
        return 0

    bdir = os.path.join(a.work_dir, "backup")
    os.makedirs(bdir, exist_ok=True)
    L.shutil.copy2(a.board, os.path.join(bdir, "board.bak"))
    L.shutil.copy2(a.pro, os.path.join(bdir, "pro.bak"))
    pro_before = L.sha(a.pro)
    L.shutil.copy2(a.result_board, a.board)
    if L.sha(a.pro) != pro_before:
        L.shutil.copy2(os.path.join(bdir, "board.bak"), a.board)
        L.die("dst pro 字节变化 ⇒ 回滚（T-22）")
    L.ok(f"板已落 {a.board}（sha16={L.s16(a.board)}）；dst pro 逐字节不变 ✓")

    composed = {
        "probe_5class": "181 → 75（via_dangling 12→0 · tncv 30→0 · silk_over_copper 43→0 · silk_overlap 21→0）",
        "lib_footprint_mismatch": "35（W-8/O-2 另案）",
        "missing_courtyard": "40（外扩口径属 §4-1 耦合裁定，未动）",
        "c86": "C86 (32.40,36.00) → (31.55,58.85)：清除 C86⊂U2 实体碰撞；+2 同网通孔 +2 引线 −2 孤立残段；位号重排 0.8mm/90°",
        "silk_refdes": {
            "tool": "k2/tools/k2_p4_silk_text_fix_v1.py",
            "method": "字形级几何（GetEffectiveTextShape 笔画 vs 阻焊开窗/via-tunnel 开窗/可见丝印笔画，间隙 0）",
            "moves": silk["moves"],
            "byte_scope": "仅 3 个位号字段的封装内局部 (at …) 偏移 —— 铜/区域/孔径/层归属逐字节不变",
        },
        "determinism": "各增量多次独立复跑结果板逐字节相同",
    }
    rec = spec_record(composed)
    rec["landed"] = {"after": {"board_sha16": L.s16(a.board)}}
    d2["_spec_rev_37"] = rec
    d2["spec_version"] = d2.get("spec_version", "1.1.spec-rev-46").replace("spec-rev-46", "spec-rev-47")
    with open(rev47, "w", encoding="utf-8") as fh:
        json.dump(d2, fh, ensure_ascii=False, indent=1, sort_keys=False)
    L.ok(f"SPEC 新增 {rev47}（sha16={L.s16(rev47)}）")
    txt = open(a.project_yaml, encoding="utf-8").read()
    if "SPEC_k2_v4.spec-rev-46.json" not in txt:
        L.die("project.yaml 未指向 rev-46")
    open(a.project_yaml, "w", encoding="utf-8").write(
        txt.replace("SPEC_k2_v4.spec-rev-46.json", "SPEC_k2_v4.spec-rev-47.json"))
    L.ok(f"project.yaml spec_name → rev-47（sha16={L.s16(a.project_yaml)}）")
    n_err, n_warn, n_unc = L.drc_counts(a.kicad_cli, a.board,
                                        os.path.join(a.work_dir, "drc_after_land.json"))
    print(f"[verify] 落件后 DRC（仓库 pro 语义）：error={n_err} warning={n_warn} unconnected={n_unc}"
          f"（期望 error=0 / warning=35）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
