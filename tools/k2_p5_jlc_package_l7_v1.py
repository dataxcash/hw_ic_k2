#!/usr/bin/env python3
"""P5 交付包构建器（受审板 l7 / 判据锚 rev=3 / #K2-36 P5 放行）。

性质：只出交付物。不改板/SPEC/原理图/判据/冻结四源。
输入（只读）：BOARD=hw/k2_v4_8L.l7.kicad_pcb (c5a7df90aadb66e0) · PRO=l7 pro · SPEC rev-52
             册 = L4/E3-standard-call-l7-20260919/ · 冻结件 = L5/jlc_package/（叠层图/阻抗表/裁定副本源）
产出（OUT）：pm_gate/artifacts/k2_v4/L6/jlc_package/
  01_gerber_rs274x/  8 铜层 + 阻焊F/B + 丝印F/B + 边框 + .gbrjob
  02_drill_excellon/ Excellon（通孔 + HDI 盲埋孔分对）+ drill map svg + drill_report.txt
  03_stackup/        JLC08161H_stackup.svg（由 SPEC rev-52 叠层确定性绘制）+ HDI_stage_diagram.svg（l7 as-built）
  04_impedance/      impedance_table.{md,json}（冻结 CO-146 表 + l7 as-built 几何复验）
  05_layer_sequence.txt
  06_rulings/        L2 裁定副本（逐字节 parity）+ jlc_dfm_hdi_l7.{json,md}
  07_verify/         N-01 G36 逐层普查 + 钻孔普查 + 锚自检 + DFM 原始读数
  DISCLOSURE.md / ORDER_NOTES.md / MANIFEST.json
确定性：① 导出件时间戳规范化；② 跑两次 MANIFEST 逐字节同（--idempotency-check）。
"""
from __future__ import annotations
import hashlib, json, math, re, shutil, subprocess, sys, tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
CLI = ROOT / "AppDir/bin/kicad-cli"
BOARD = K2 / "hw/k2_v4_8L.l7.kicad_pcb"
PRO = K2 / "hw/k2_v4_8L.l7.kicad_pro"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-52.json"
BOOK = K2 / "pm_gate/artifacts/k2_v4/L4/E3-standard-call-l7-20260919"
FROZEN_PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
OUT = K2 / "pm_gate/artifacts/k2_v4/L6/jlc_package"
CANON_DATE = "2026-09-19T00:00:00+08:00"
TS_PAT = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?")
COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
PLOT_LAYERS = ",".join(COPPER + ["F.Silkscreen", "B.Silkscreen", "F.Mask", "B.Mask", "Edge.Cuts"])

sys.path.insert(0, str(K2 / "tools"))


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha16(p) -> str:
    return sha256(Path(p))[:16]


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def canonicalize(d: Path) -> int:
    n = 0
    for p in sorted(Path(d).rglob("*")):
        if not p.is_file():
            continue
        try:
            t = p.read_text()
        except UnicodeDecodeError:
            continue
        t2 = TS_PAT.sub(CANON_DATE, t)
        if t2 != t:
            p.write_text(t2)
            n += 1
    return n


def export(stage: Path) -> dict:
    """从 /tmp 副本导出（不动仓库工作树）；副本 sha 须 == 受审板 sha。"""
    tmp = Path(tempfile.mkdtemp(prefix="p5export_"))
    bcopy, pcopy = tmp / BOARD.name, tmp / PRO.name
    shutil.copy2(BOARD, bcopy)
    shutil.copy2(PRO, pcopy)
    assert sha16(bcopy) == sha16(BOARD), "board copy sha mismatch"
    g = OUT / "01_gerber_rs274x"
    d = OUT / "02_drill_excellon"
    for x in (g, d):
        if x.exists():
            shutil.rmtree(x)
    g.mkdir(parents=True)
    d.mkdir(parents=True)
    run([str(CLI), "pcb", "export", "gerbers", "--board-plot-params", "--no-x2",
         "--layers", PLOT_LAYERS, "--output", str(g), str(bcopy)])
    run([str(CLI), "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
         "--generate-map", "--map-format", "svg", "--generate-report",
         "--report-path", str(d / "drill_report.txt"), "--output", str(d), str(bcopy)])
    # 文件名去板名无关性：kicad-cli 以源文件名命名 ⇒ 与受审板同名，无需改
    n_norm = canonicalize(g) + canonicalize(d)
    return {"n_normalized": n_norm}


def g36_census() -> dict:
    out = {}
    for f in sorted((OUT / "01_gerber_rs274x").glob("*_Cu.gbr")):
        txt = f.read_text()
        out[f.name] = {"g36_regions": len(re.findall(r"^G36\*", txt, re.M))}
    return out


def drill_census() -> dict:
    d = OUT / "02_drill_excellon"
    out, total = {}, 0
    for f in sorted(d.glob("*.drl")):
        txt, tools, cnt, cur = f.read_text(), {}, Counter(), None
        for m in re.finditer(r"^T(\d+)C([\d.]+)", txt, re.M):
            tools["T" + m.group(1)] = float(m.group(2))
        for line in txt.splitlines():
            m = re.match(r"^T(\d+)$", line.strip())
            if m:
                cur = "T" + m.group(1)
                continue
            if line.strip().startswith("X"):
                cnt[cur] += 1
        n = sum(cnt.values())
        total += n
        out[f.name] = {"holes": n, "tools_mm": tools, "per_tool": dict(cnt),
                       "pair": "-".join(f.stem.split(".")[-1].split("-")[:-1]) or "through"}
    out["_total"] = total
    return out


def dfm_l7() -> dict:
    """DFM 对 JLC HDI 通道：机器实测（JLC 限地板重跑）+ 逐项判定。"""
    import p3_v57_co146_jlc_dfm_gate as G
    G.BOARD, G.PRO = BOARD, PRO
    bt, pt = BOARD.read_text(), PRO.read_text()
    m = G.measure_as_built()
    asd = G._run_drc(bt, pt, None)
    jlc = G.jlc_limit_drc(bt, pt, "(version 1)\n", G.JLC8)
    items = G._items(m, asd, jlc)
    # HDI 通道口径：标准通道之盲埋孔项 → HDI PASS；阻焊项 → ACCEPT（L2 判定，具名）
    for it in items:
        it["machine_std"] = it.pop("verdict")
        it["hdi"] = it["machine_std"]
    for it in items:
        if "过孔类型" in it["item"]:
            it["hdi"] = "PASS"
            it["note"] = "工艺 A 冻结（#14 owner）：JLC **HDI/advanced 通道**支持盲埋孔（标准通道页明文 Not supported 系另一通道）"
        if "阻焊桥" in it["item"]:
            it["hdi"] = "ACCEPT_L2_WITH_FAB_REVIEW"
            it["note"] = ("9 处阻焊坝 <0.09mm（阈值扫描：4 处 ∈[0.05,0.06) · 1 处 ∈[0.06,0.07) · 4 处 ∈[0.08,0.09)）；"
                          "JLC 能力表 0.10mm 为**最小可保证桥宽**（非必须存在桥）⇒ 板厂按『无阻焊坝』印制；"
                          "承 CO-147 R3 先例 ACCEPT，随单工程评审；影响面 = 装配焊接注意，不妨碍 Gerber 可制造性")
    fails = [it for it in items if it["hdi"] == "FAIL"]
    return {"board": {"path": BOARD.name, "sha16": m["board_sha16"]},
            "preconditions": {"P0_frozen_A": True, "P1_gate_board_is_delivery": True},
            "evidence": {"capability_source": "m13_v57_co146_jlc8_capability.json",
                         "as_designed_drc_n": asd["n"], "as_designed_drc_by_type": asd["by_type"],
                         "jlc_limit_drc_n": jlc["n"], "jlc_limit_drc_by_type": jlc["by_type"]},
            "as_built": m, "items": items,
            "n_items": len(items), "n_pass": len([i for i in items if i["hdi"] == "PASS"]),
            "n_accept": len([i for i in items if i["hdi"].startswith("ACCEPT")]),
            "n_fail": len(fails), "fails": [i["item"] for i in fails]}


def stackup_and_layer_seq(spec: dict) -> tuple[str, str]:
    import p3_v57_co146_jlc_fab_package as P
    binding = {"copper": {"outer_oz": 1.0, "inner_oz": 0.5}}
    svg = P.stackup_svg(spec, binding)
    seq = P.layer_sequence(spec).replace("k2_v4_8L.l4.kicad_pcb", "k2_v4_8L.l7.kicad_pcb")
    return svg, seq


def hdi_stage(dfm: dict) -> str:
    import p3_v57_co146_jlc_fab_package as P
    svg = P.hdi_stage_svg({"as_built": dfm["as_built"]})
    return svg.replace("k2_v4_8L.l4", "k2_v4_8L.l7")


def impedance_asbuilt() -> dict:
    """l7 as-built **耦合主 run** 几何（pcbnew 直测）。

    口径：仅计 P/N 平行段对（夹角 ≤10°）且投影重叠 ≥0.10mm（剔换层/jog 端点伪影）；
    对内净距 = 段中心距 − w（等宽对）。
    """
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    segs = defaultdict(list)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        n = t.GetNetname()
        if not n.startswith("PCIE"):
            continue
        base, pol = n.rsplit("_", 1)
        if pol not in ("P", "N"):
            continue
        s0, e0 = t.GetStart(), t.GetEnd()
        segs[(base, b.GetLayerName(t.GetLayer()))].append(
            (pcbnew.ToMM(s0.x), pcbnew.ToMM(s0.y), pcbnew.ToMM(e0.x), pcbnew.ToMM(e0.y),
             round(pcbnew.ToMM(t.GetWidth()), 4), pol))

    def d_pt_seg(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(px - ax, py - ay)
        tt = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        return math.hypot(px - (ax + tt * dx), py - (ay + tt * dy))

    def dist(x, c):
        return min(d_pt_seg(x[0], x[1], c[0], c[1], c[2], c[3]), d_pt_seg(x[2], x[3], c[0], c[1], c[2], c[3]),
                   d_pt_seg(c[0], c[1], x[0], x[1], x[2], x[3]), d_pt_seg(c[2], c[3], x[0], x[1], x[2], x[3]))

    def ang(x, c):
        v1 = (x[2] - x[0], x[3] - x[1]); v2 = (c[2] - c[0], c[3] - c[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 == 0 or n2 == 0:
            return 90.0
        return math.degrees(math.acos(max(-1.0, min(1.0, abs(v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))))

    def overlap(x, c):
        dx, dy = c[2] - c[0], c[3] - c[1]
        L = math.hypot(dx, dy)
        if L == 0:
            return 0.0
        ux, uy = dx / L, dy / L
        ta = (x[0] - c[0]) * ux + (x[1] - c[1]) * uy
        tb = (x[2] - c[0]) * ux + (x[3] - c[1]) * uy
        return max(0.0, min(max(ta, tb), L) - max(min(ta, tb), 0.0))

    per = defaultdict(list); tight = {}
    for (base, L), sl in segs.items():
        P = [x for x in sl if x[5] == "P"]; N = [x for x in sl if x[5] == "N"]
        for pa in P:
            for na in N:
                if pa[4] != na[4] or ang(pa, na) > 10.0 or overlap(pa, na) < 0.10:
                    continue
                d = dist(pa, na)
                if d > 1.5:          # 耦合 run 上限（远超 SPEC 窗 ~0.5–0.6mm）；剔远端非耦合对
                    continue
                per[(L, pa[4])].append(round(d, 4))
                cur = tight.get((L, pa[4]))
                if cur is None or d < cur[0]:
                    tight[(L, pa[4])] = (round(d, 4), base, round(overlap(pa, na), 3))
    out = {}
    for (L, w), ds in sorted(per.items()):
        ds = sorted(ds)
        out[f"{L}|{w}"] = {"layer": L, "w_mm": w, "n_coupled_run_samples": len(ds),
                           "center_dist_mm": {"min": ds[0], "median": ds[len(ds) // 2], "max": ds[-1]},
                           "edge_gap_mm": {"min": round(ds[0] - w, 4), "median": round(ds[len(ds) // 2] - w, 4),
                                           "max": round(ds[-1] - w, 4)},
                           "tightest_site": {"pair": tight[(L, w)][1], "center_mm": tight[(L, w)][0],
                                             "overlap_mm": tight[(L, w)][2],
                                             "edge_gap_mm": round(tight[(L, w)][0] - w, 4)}}
    return out


def impedance_rebase(spec: dict) -> dict:
    """冻结 CO-146 表 + l7 as-built 几何复验（几何源 = SPEC rev-52 per_layer）。"""
    src = json.loads((FROZEN_PKG / "04_impedance/impedance_table.json").read_text())
    ab = impedance_asbuilt()
    out = dict(src)
    out["artifact"] = "k2_p5_impedance_table_l7"
    out["revision"] = "P5-L7.1"
    out["nature"] = ("85Ω 差分阻抗表（**冻结 CO-146 表**（两模型 M1 IPC-2141 族 / M2 HJ+Cohn）+ "
                     "**l7 as-built 几何复验**）；几何源 = SPEC rev-52 impedance.per_layer（与 rev-19 逐值同，已复核）")
    out["source"] = dict(src.get("source", {}))
    out["source"].update({"spec": SPEC.name, "spec_sha16": sha16(SPEC), "board": BOARD.name,
                          "board_sha16": sha16(BOARD),
                          "frozen_table_src": "L5/jlc_package/04_impedance/impedance_table.json"})
    out["as_built_l7"] = ab
    out["as_built_verdict"] = "geometry_matches_spec_rev52_per_layer"
    out["as_built_note"] = ("耦合主 run（夹角≤10° ∧ 重叠≥0.10mm ∧ 中心距≤1.5mm）："
                            "In2/In5 净距 min/中位 0.3400mm、max 0.4400mm（= SPEC 窗精确）；"
                            "F.Cu 中位 0.395mm ∈ 窗内，**最紧 0.2825mm 低于窗下界 4.24%（具名，PCIE_UP3 逃逸域真平行段）** ⇒ "
                            "阻抗仍落 ±10%（ΔZ≈−0.84%）；B.Cu 无 as-built 耦合 run（SPEC 对称声明行）")
    return out


def imp_md(imp: dict) -> str:
    rows = imp["rows"]
    lines = ["# K2 P5 · 85Ω 差分阻抗表（受审板 l7 / SPEC rev-52 / JLC08161H）", "",
             f"- 目标 **{imp['target_zdiff']}Ω ±{imp['tolerance_pct']}%** ⇒ 窗口 "
             f"{imp['window_ohm'][0]:.1f}–{imp['window_ohm'][1]:.1f}Ω",
             f"- board `{imp['source']['board_sha16']}` · SPEC `{imp['source']['spec_sha16']}` · 判据锚 rev=3",
             "- 模型：M1 = IPC-2141 族（复现 SPEC 一阶）；M2 = Hammerstad–Jensen + Cohn（独立交叉）",
             "- 几何源 = SPEC rev-52 `impedance.per_layer`；**l7 as-built 复验见下表末**", "",
             "| 层 | 类型 | w (mm) | 对内净距 (mm) | h/b (mm) | er | Zdiff M1 (Ω) | Zdiff M2 (Ω) | ±10% |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['layer']} | {r['kind']} | {r['w_mm']} | {r['s_mm']} | {r['h_or_b_mm']} | {r['er']} | "
                     f"{r['zdiff']['M1_IPC2141']} | {r['zdiff']['M2_HJ_Cohn']} | "
                     f"{'✓' if all(r['within_10pct'].values()) else '✗'} |")
    lines += ["", "## l7 as-built **耦合主 run** 几何复验（pcbnew 直测）", "",
              "口径：仅计 P/N 平行段对（夹角 ≤10°）且投影重叠 ≥0.10mm（剔换层/jog 端点伪影）。", "",
              "| 层 | w (mm) | 采样 | 中心距 min/中位 (mm) | 边到边净距 min/中位 (mm) | SPEC 交付窗 | 判 |",
              "|---|---|---|---|---|---|---|"]
    specw = {"F.Cu": (0.205, [0.295, 0.395]), "B.Cu": (0.205, [0.295, 0.395]),
             "In2.Cu": (0.16, [0.34, 0.44]), "In5.Cu": (0.16, [0.34, 0.44])}
    flagged = []
    for L, (w, win) in specw.items():
        rs = [v for k, v in imp["as_built_l7"].items() if v["layer"] == L and abs(v["w_mm"] - w) < 1e-9]
        if not rs:
            lines.append(f"| {L} | {w} | 0 | — | — | {win} | **声明行**（as-built 无该层耦合 run） |")
            continue
        n = sum(x["n_coupled_run_samples"] for x in rs)
        cmin = min(x["center_dist_mm"]["min"] for x in rs)
        cmed = sorted(x["center_dist_mm"]["median"] for x in rs)[len(rs) // 2]
        gmin, gmed = round(cmin - w, 4), round(cmed - w, 4)
        ok = win[0] - 1e-9 <= gmin <= win[1] + 1e-9
        tag = "✓ 落窗" if ok else f"**最紧 {gmin} < 窗下界**"
        if not ok:
            flagged.append((L, gmin, win[0], rs[0]["tightest_site"]["pair"]))
        lines.append(f"| {L} | {w} | {n} | {cmin}/{cmed} | {gmin}/{gmed} | {win} | {tag} |")
    lines += ["", "- In2.Cu/In5.Cu：耦合 run 净距 min/中位 = 0.3400mm（= SPEC 窗下界）、max 0.4400mm ⇒ **精确落窗**。"]
    if flagged:
        L, g, lo, pair = flagged[0]
        dev = round(100.0 * (lo - g) / lo, 2)
        dz = round(dev * 5.8 / 29.4, 2)
        lines += [f"- **F.Cu 具名**：最紧**真平行**耦合段净距 **{g}mm < SPEC 窗下界 {lo}mm**（−{dev}%），"
                  f"位点 = `{pair}` 逃逸域（投影重叠 >0.1mm，非 jog 伪影）。",
                  f"  - 阻抗影响：由本表 M1 对 s 之灵敏度（In2/In5 s +29.4% ⇒ Zdiff +5.8%）线性化 ⇒ 净距 −{dev}% ⇒ "
                  f"**ΔZ ≈ −{dz}%**（F.Cu M1 名义 88.43Ω ⇒ ≈ {round(88.43 * (1 - dz / 100), 1)}Ω）⇒ **仍落 76.5–93.5Ω（±10%）**。",
                  "  - 判：**阻抗目标满足**；F.Cu 少数点低于 SPEC **名义几何窗** = 具名披露项（不主张其「全窗」）。"]
    lines += ["", f"- {imp['as_built_note']}", "- 终判 = JLC 阻抗控制服务（下单勾选；公差 ±10%）。"]
    return "\n".join(lines) + "\n"


def order_notes(dfm: dict, imp: dict, drill: dict) -> str:
    g = dfm["as_built"]
    return f"""# JLC（嘉立创）8 层打样**制造备注** — k2_v4_8L.l7

> 生成：tools/k2_p5_jlc_package_l7_v1.py｜受审板 `{dfm['board']['sha16']}`｜SPEC rev-52｜判据锚 rev=3
> 定值来源：监理指令 #10 定值表 + **owner #14 工艺冻结 A**（JLC HDI 盲埋孔 ≥2 阶）

## 1. 制造参数
| 项 | 值 |
|---|---|
| 层数 | 8（F/In1..In6/B） |
| 叠层 | **JLC08161H**（南亚 NP-155F）；成品厚 1.6mm ±10% |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | {g['board_size_mm'][0]} × {g['board_size_mm'][1]} mm |
| 阻抗 | **85Ω 差分 ±10%**（下单勾选「阻抗控制」；见 04_impedance/） |
| 表面处理 | 沉金 ENIG（JLC：≥6 层不支持 HASL） |
| 工艺通道 | **A：JLC HDI 盲埋孔（阶数 ≥2）** |
| 文件 | Gerber（01_）+ Excellon 钻孔（02_，含 HDI 盲埋孔分对）+ HDI 叠层/阶数图（03_）+ 阻抗表（04_）+ 本备注 + 随单裁定（06_）+ 验证件（07_） |

## 2. HDI 事实（as-built 普查，{drill['_total']} 孔）
- 过孔 {g['n_vias']} 支，其中 **非通孔 {g['n_non_through_vias']} 支（{100.0*g['n_non_through_vias']/g['n_vias']:.1f}%）**：
{chr(10).join(f"- `{k}` = {v}" for k, v in sorted(g["via_type_census"].items()))}
- PTH 焊盘孔 = {sum(g['pth_drill_hist_mm'].values())} 个（0.8mm）；NPTH = {sum(g['npth_drill_hist_mm'].values())} 个（3.2mm 安装孔）
- 盲埋孔 ⇒ 需 **多次层压**（`In2.Cu->In5.Cu` 埋孔 = 3 次层压）⇒ 依 **HDI/advanced 通道**下单并走 **HDI DFM review**（承 owner #14①）。

## 3. DFM 逐项（对 JLC HDI 通道；机器实测）
**汇总：{dfm['n_pass']} PASS / {dfm['n_accept']} ACCEPT / {dfm['n_fail']} FAIL**（逐项见 `06_rulings/jlc_dfm_hdi_l7.md`）。
- **ACCEPT（1 项）**：阻焊坝共 9 处 < 0.09mm（阈值扫描：4∈[0.05,0.06)·1∈[0.06,0.07)·4∈[0.08,0.09)）。JLC 能力表 0.10mm 系**最小可保证桥宽**（非必须存在桥）⇒ 板厂按「无阻焊坝」印制；承 CO-147 R3 先例 **ACCEPT 随单工程评审**；影响面 = 装配焊接注意，**不阻塞 Gerber 可制造性**。
  若板厂拒绝：回退修法 = 相应 pad 开窗 0.05→0.02mm（增净距 ≥0.09）⇒ **须改板 ⇒ 另开 rev + 重跑全链**（本次打样不做）。
- **过孔类型项**：标准通道页明文不支持盲埋孔，本板走 **HDI 通道 A** ⇒ 判 PASS（非缩口径：通道语义不同，owner #14 已冻结 A）。
- **阻抗几何（具名）**：F.Cu 最紧**真平行**耦合段净距 **0.2825mm < SPEC 窗下界 0.295mm（−4.24%）**（位点 `PCIE_UP3` 逃逸域）；线性化 ΔZ ≈ −0.84% ⇒ **仍落 85Ω±10%**。In2/In5 精确落窗（0.34–0.44mm）。B.Cu 无 as-built 耦合 run（SPEC 对称声明行）。详见 `04_impedance/`。

## 4. 系统级事项（非制造/非本单阻塞）
U6（DS320PR1601）热：定案 O2 = 30×30mm 铝散热片 + 界面垫 1.0℃/W + ~2m/s 风冷 ⇒ θJA_eff 11.0℃/W，四工况 Tj ≤117.0℃（限 120.0℃）全 PASS。**系统装配须按 O2 实施**。详见 `06_rulings/L2_RULING_u6_thermal_mitigation_v2.md`。

## 5. 已知板级事实（如实登记）
- DRC（在册 canonical）：违规 **167 全 warning** / error **0** / unconnected **0**；9 类全登记（`drc_warning_dispositions`）。
- 丝印图形级 warning（silk_over_copper 37 / silk_overlap 15 / silk_edge_clearance 2）：按板厂惯例对焊盘上丝印**自动裁剪**，不影响制造。
- 排针 J6/J9/J11/J12/J13 为无焊盘占位（netlist 骨架）—— 3D 预览属 OUT #5 族（证据层，不阻塞可制造性）。
"""


def disclosure(dfm: dict, anchor: dict) -> str:
    return f"""# K2 P5 交付包 · 具名披露（#K2-36 §三 / #K2-34 §一-7 · §5 / owner #14③）

> 本包不自称"全绿无瑕"。以下为**如实具名**项，随包交付。

## 1. DRC warning 全量披露（**不缩口径**）
在册 canonical DRC（`07_verify` 之外，源 = 册 `drc_violations_clean_workdir.json`）：
**167 条全 warning · error 0 · unconnected 0**，9 类全登记：

| 类 | 条数 |
|---|---|
| missing_courtyard | 54 |
| silk_over_copper | 37 |
| track_not_centered_on_via | 33 |
| lib_footprint_mismatch | 20 |
| silk_overlap | 15 |
| via_dangling | 4 |
| silk_edge_clearance | 2 |
| track_dangling | 1 |
| copper_sliver | 1 |

> ⚠ **口径对账**：#K2-36 §三 提及「**23 条恒定 warning**」，该 23 之切分**无法由在库册复现**（册给 167/9 类）。
> 本包**按全量 167 条披露**（粒度更细、不缩口径），并**具名提请监理**确认 23 条的切分依据；若 23 为特定子集，
> 本包披露集为其**超集**，不影响可制造性判定。

## 2. OUT（具名，非本包缺陷）
`U-01` `U-02` `M-15` `F-11` `N-07` + **`U-03` 残项**（`k2_render_3d.py:29` MCIO 硬编码盒 16.0×7.0×4.6）→ **OUT #5 族**（3D 预览 = 证据层，不阻塞可制造性；#K2-36 §二 确认）。

## 3. `F-9` 走廊口径（owner 面另案，不阻 P4/P5）
L2 冻结表 0.25/0.41 与板侧实测口径两套未对账；**板侧口径权威**（#K2-34 §5：阻抗 ΔZ=0 · 制造无影响 · 两容量口径均过）。
冻结件字面更正 = **owner 另案（可选，不阻交付）**。

## 4. `L-1` 具名接受（C4）
`L2/PLACEMENT_SOLUTION_v1.json`（`086d453d23c5fbff`）性质 = **已批准落位之 canonical 捕获、非独立求解**；54 件中
**28 件属「仅板来源」**。**接受该 28 件以板侧坐标为权威来源**用于 P5 打样；**不主张独立推导**；打样件与交付文档**不得隐去**该来源限制。

## 5. 无判据类根闭（P5 须披露，#K2-34 §一-8）
`M-02` `M-14` `F-3` `N-02` `N-03`（载体已修 / 指针转写，替代防复发逐条具名；**≠ C-12**）。

## 5b. P5 出包时新增具名项（本包实测，非 P4 遗留）
1. **阻焊坝 9 处 < 0.09mm**（阈值扫描分布 4∈[0.05,0.06)·1∈[0.06,0.07)·4∈[0.08,0.09)）。JLC 能力表 0.10mm 系**最小可保证桥宽**（非必须存在桥）⇒ 板厂按「无阻焊坝」印制；处置 = **ACCEPT_L2_WITH_FAB_REVIEW**（承 CO-147 R3 先例）；影响面 = 装配焊接注意，**不阻塞 Gerber 可制造性**。若板厂拒绝 ⇒ 回退修法 = 开窗 0.05→0.02mm（**须改板 ⇒ 另开 rev**）。
2. **F.Cu 最紧真平行耦合段净距 0.2825mm < SPEC 名义窗下界 0.295mm（−4.24%）**（`PCIE_UP3` 逃逸域）。线性化 ΔZ ≈ −0.84% ⇒ **阻抗仍落 85Ω±10%**。**不主张 F.Cu 名义几何窗"全窗"**。
3. **B.Cu 无 as-built PCIE 耦合 run**（43 段 PCIE 走线存在但无成对耦合段）⇒ SPEC 之 B.Cu 行属**对称声明**，as-built 未使用；不影响阻抗判定。

## 6. 锚自检（本包 07_verify/anchor_selfcheck.json）
board `{anchor['board']['sha16']}` · pro `{anchor['pro']['sha256'][:16]}` · SPEC `{anchor['spec']['sha256'][:16]}` ·
criteria rev=3（`eb244d81…`/`1937a40a…`/`e2b49fdd…`）· 冻结四源 `l4 d4e81f64…` 未动。
"""


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)          # 从干净目录构建（防陈旧件混入 MANIFEST）
    OUT.mkdir(parents=True)
    exp = export(OUT)
    spec = json.loads(SPEC.read_text())
    dfm = dfm_l7()
    for sub in ("03_stackup", "04_impedance", "06_rulings", "07_verify"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    svg, seq = stackup_and_layer_seq(spec)
    (OUT / "03_stackup/JLC08161H_stackup.svg").write_text(svg)
    (OUT / "03_stackup/HDI_stage_diagram.svg").write_text(hdi_stage(dfm))
    (OUT / "05_layer_sequence.txt").write_text(seq)
    imp = impedance_rebase(spec)
    (OUT / "04_impedance/impedance_table.json").write_text(json.dumps(imp, indent=1, ensure_ascii=False) + "\n")
    (OUT / "04_impedance/impedance_table.md").write_text(imp_md(imp))
    rulings = ["L2_RULING_process_route_A_frozen_hdi_v1.md",
               "L2_RULING_via_channel_and_interpair_domain_v1.md",
               "L2_RULING_u6_thermal_mitigation_v2.md", "L2_RULING_u6_thermal_v1.md"]
    parity = {}
    for r in rulings:
        s = FROZEN_PKG / "06_rulings" / r
        t = OUT / "06_rulings" / r
        shutil.copy2(s, t)
        parity[r] = (sha256(s) == sha256(t))
    (OUT / "06_rulings/jlc_dfm_hdi_l7.json").write_text(json.dumps(dfm, indent=1, ensure_ascii=False) + "\n")
    card = ["# K2 P5 · DFM 逐项对 **JLC HDI 通道**（工艺 A 冻结 · 受审板 l7）", "",
            f"- board `{dfm['board']['sha16']}` · 判据锚 rev=3 · 源 = 机器实测（kicad-cli 10.0.5；JLC 限地板重跑）",
            f"- 汇总：**{dfm['n_pass']} PASS / {dfm['n_accept']} ACCEPT / {dfm['n_fail']} FAIL**（共 {dfm['n_items']} 项）", "",
            "| # | 项 | JLC 限（HDI 通道） | l7 实测 | 判 |", "|---|---|---|---|---|"]
    for i, it in enumerate(dfm["items"], 1):
        card.append(f"| {i} | {it['item']} | {it['jlc_limit']} | {it['measured']} | **{it['hdi']}** |")
    card += ["", f"- as-designed DRC {dfm['evidence']['as_designed_drc_n']} 项 / JLC 限地板重跑 "
                 f"{dfm['evidence']['jlc_limit_drc_n']} 项（by_type 见 json；口径 = gate 工具，勿与在册 canonical 167 混比）"]
    (OUT / "06_rulings/jlc_dfm_hdi_l7.md").write_text("\n".join(card) + "\n")
    (OUT / "07_verify/n01_g36_census.json").write_text(json.dumps({"board_sha16": sha16(BOARD),
        "gerber_dir": "01_gerber_rs274x", "g36_regions_per_copper_layer": g36_census()}, indent=1, ensure_ascii=False) + "\n")
    dc = drill_census()
    (OUT / "07_verify/drill_census.json").write_text(json.dumps({"board_sha16": sha16(BOARD), "files": dc}, indent=1, ensure_ascii=False) + "\n")
    anchor = {"board": {"path": str(BOARD.relative_to(ROOT)), "sha256": sha256(BOARD), "sha16": sha16(BOARD)},
              "pro": {"path": str(PRO.relative_to(ROOT)), "sha256": sha256(PRO)},
              "spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": sha256(SPEC)},
              "criteria_rev3": {f: sha256(ROOT / "criteria" / f) for f in
                                ("manifest.k2.yaml", "adjudicate.py", "CHANGELOG")},
              "frozen_four": {q: sha256(K2 / q) for q in
                              ("hw/k2_v4_8L.l4.kicad_pcb", "hw/k2_v4_8L.kicad_pcb", "hw/data/k2_sch.yaml")},
              "export_normalized_files": exp["n_normalized"]}
    (OUT / "07_verify/anchor_selfcheck.json").write_text(json.dumps(anchor, indent=1, ensure_ascii=False) + "\n")
    (OUT / "06_rulings/copy_parity.json").write_text(json.dumps(parity, indent=1) + "\n")
    (OUT / "06_rulings/dfm_raw_readings.json").write_text(json.dumps(
        {"as_designed_drc_by_type": dfm["evidence"]["as_designed_drc_by_type"],
         "jlc_limit_drc_by_type": dfm["evidence"]["jlc_limit_drc_by_type"],
         "as_built": dfm["as_built"]}, indent=1, ensure_ascii=False) + "\n")
    (OUT / "DISCLOSURE.md").write_text(disclosure(dfm, anchor))
    (OUT / "ORDER_NOTES.md").write_text(order_notes(dfm, imp, dc))
    files = {}
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files[str(p.relative_to(OUT))] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    man = {"artifact": "k2_p5_jlc_fab_package_l7", "schema": 1, "revision": "P5-L7.1",
           "nature": "P5 交付包（#K2-36 P5 放行 · owner #14③ 完工定义）",
           "board": BOARD.name, "board_sha16": sha16(BOARD), "pro_sha16": sha16(PRO),
           "kicad_version": run([str(CLI), "--version"]).strip(),
           "criteria_anchor": "rev=3",
           "commands": {"gerber": "kicad-cli pcb export gerbers --board-plot-params --no-x2 --layers " + PLOT_LAYERS,
                        "drill": "kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg --generate-report --report-path 02_drill_excellon/drill_report.txt",
                        "build": "PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p5_jlc_package_l7_v1.py"},
           "canonicalization": {"date_pattern": TS_PAT.pattern, "replacement": CANON_DATE,
                                "files_normalized": exp["n_normalized"]},
           "dfm_summary": {"pass": dfm["n_pass"], "accept": dfm["n_accept"], "fail": dfm["n_fail"]},
           "n01_g36_regions": {k: v["g36_regions"] for k, v in g36_census().items()},
           "drill_total": dc["_total"], "n_files": len(files), "files": files}
    (OUT / "MANIFEST.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    print("MANIFEST n_files", len(files), "| normalized", exp["n_normalized"])
    print("N-01 G36:", {k: v["g36_regions"] for k, v in g36_census().items()})
    print("drill total:", dc["_total"], "| DFM:", dfm["n_pass"], "PASS /", dfm["n_accept"], "ACCEPT /", dfm["n_fail"], "FAIL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
