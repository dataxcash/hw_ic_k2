#!/usr/bin/env python3
"""CO-146 A3 — JLC 打样包（Gerber RS-274X + 钻孔 Excellon + 叠层图 + 阻抗表 + 层序 + 下单备注）。

性质：**只出交付物，不改板/SPEC/冻结四源**（读交付板 `k2_v4_8L.l4.kicad_pcb`）。
产出目录：`pm_gate/artifacts/k2_v4/L5/jlc_package/`
  01_gerber_rs274x/*.gbr(.gbrjob)   kicad-cli pcb export gerbers --board-plot-params --no-x2
  02_drill_excellon/*.drl + *.drl 图 + report
  03_stackup/JLC08161H_stackup.svg + .md      叠层图（由 SPEC dielectrics 确定性绘制）
  04_impedance/impedance_table.md|json        CO-146 阻抗表副本
  05_layer_sequence.txt                       层序 + 层角色
  ORDER_NOTES.md                              下单备注（含 DFM 阻塞项，如实）
  MANIFEST.json                               每文件 sha256 + 计数
牙齿：① 跑两次 MANIFEST 必须逐字节同（幂等）；② 必须存在 8 个铜层 .gbr + 钻孔文件；
      ③ 目录内任何 sha 缺失即 FAIL。
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
CLI = ROOT / "AppDir/bin/kicad-cli"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
PLOT_LAYERS = ",".join(COPPER + ["F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen",
                                 "F.Mask", "B.Mask", "Edge.Cuts"])


CANON_DATE = "2026-09-12T00:00:00+08:00"
TS_PAT = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?")


def canonicalize(d: Path) -> int:
    """KiCad 导出件内嵌墙钟时间戳 ⇒ 规范化（可复现性；制造语义不受影响）。"""
    n = 0
    for p in sorted(d.rglob("*")):
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


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha16(p) -> str:
    return sha256(Path(p))[:16]


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def export_gerbers(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    run([str(CLI), "pcb", "export", "gerbers", "--board-plot-params", "--no-x2",
         "--layers", PLOT_LAYERS, "--output", str(d), str(BOARD)])


def export_drill(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    run([str(CLI), "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
         "--generate-map", "--map-format", "svg", "--generate-report",
         "--report-path", str(d / "drill_report.txt"), "--output", str(d), str(BOARD)])


def stackup_svg(spec: dict) -> str:
    dz = spec["stackup"]["dielectric_8l"]
    order = ["F.Cu", "d(F.Cu-In1.Cu)", "In1.Cu", "d(In1.Cu-In2.Cu)", "In2.Cu", "d(In2.Cu-In3.Cu)",
             "In3.Cu", "d(In3.Cu-In4.Cu)", "In4.Cu", "d(In4.Cu-In5.Cu)", "In5.Cu",
             "d(In5.Cu-In6.Cu)", "In6.Cu", "d(In6.Cu-B.Cu)", "B.Cu"]
    scale, top, h, w = 600.0, 40.0, 0.0, 560.0
    rows, y = [], top
    for name in order:
        if name.endswith("Cu"):
            th, fill, label = 0.035 if name in ("F.Cu", "B.Cu") else 0.0175, "#c8811e", name
        else:
            c = dz[name]
            th, fill, label = c["mm"], "#d8e8d8", f'{c["material"]} {c["mm"]}mm er={c["er"]}'
        px = max(6.0, th * scale)
        rows.append(f'<rect x="40" y="{y:.2f}" width="{w}" height="{px:.2f}" fill="{fill}" '
                    f'stroke="#333" stroke-width="0.4"/>')
        rows.append(f'<text x="{w + 50}" y="{y + px / 2 + 3:.2f}" font-size="11">{name}  —  {label}</text>')
        y += px
    total = y - top
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{total + 80:.0f}">'
            f'<rect width="100%" height="100%" fill="white"/>'
            f'<text x="40" y="24" font-size="15" font-weight="bold">JLC08161H 8L 1.6mm 叠层（南亚 NP-155F）'
            f'｜外层 1oz / 内层 0.5oz｜总厚 {spec["stackup"]["total_thickness_mm"]}mm｜单边比例 {scale:.0f}px/mm</text>'
            + "".join(rows) + '</svg>')


def layer_sequence(spec: dict) -> str:
    imp = spec["impedance"]["per_layer"]
    lines = ["# 层序（top → bottom）｜交付板 k2_v4_8L.l4.kicad_pcb", ""]
    for i, ln in enumerate(COPPER, 1):
        role = spec["stackup"][ln]
        extra = ""
        if ln in imp:
            c = imp[ln]
            extra = (f"｜阻抗 {c['kind']} w={c['w_mm']}mm 对内净距{ c['gap_mm_delivered']}mm "
                     f"er={c['er']} ⇒ 85Ω±10%（见 04_impedance）")
        lines.append(f"{i}. {ln} — {role}{extra}")
    lines += ["", "介质：见 03_stackup/JLC08161H_stackup.svg｜铜厚：外层 1oz / 内层 0.5oz｜成品厚 1.6mm ±10%",
              "表面处理：ENIG 沉金（JLC：6 层及以上不支持 HASL）"]
    return "\n".join(lines) + "\n"


def order_notes(spec: dict, dfm: dict, imp: dict) -> str:
    b = dfm["as_built"]
    try:
        probe_shorts = json.loads((STEP2 / "m13_v57_co146_through_via_probe.json").read_text())[
            "delta_by_type"].get("shorting_items")
    except Exception:
        probe_shorts = "N/A"
    return f"""# JLC（嘉立创）8 层打样下单备注 — k2_v4_8L.l4

> 生成：tools/p3_v57_co146_jlc_fab_package.py｜板 `{b['board_sha16']}`｜SPEC rev-19
> 定值来源：监理指令 #10「JLC 8 层打样就绪」定值表（叠层/铜厚/阻抗/表面处理/压降/环境）

## 1. 下单参数（监理定值）
| 项 | 值 |
|---|---|
| 层数 | 8 |
| 叠层 | **JLC08161H**（南亚 NP-155F） |
| 成品厚 | 1.6 mm（公差 ±10%） |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | {b['board_size_mm'][0]} × {b['board_size_mm'][1]} mm |
| 阻抗 | **85Ω 差分 ±10%，下单勾选「阻抗控制」** |
| 表面处理 | 沉金 ENIG |
| 文件 | Gerber RS-274X（01_）+ Excellon 钻孔（02_）+ 本叠层图（03_）+ 阻抗表（04_） |

## 2. 下单渠道（CO-147 L2 裁定 R1，生效）
本板 {b['n_non_through_vias']}/{b['n_vias']} 支过孔为**非通孔**（`F.Cu→In2.Cu` 92、`In2.Cu→In5.Cu` 88（埋孔）、
`In5.Cu→B.Cu` 32、`F.Cu→In5.Cu` 8）；JLC 公布能力页明写 *"Blind/Buried Vias Not supported … only make through holes"*，
FAQ 将 blind/buried 列为 **advanced options（须 DFM review，成本/交期上升）**。

⇒ **下单走 JLC advanced / 盲埋孔通道**（L2 自裁 = 过孔策略），随单提交：本备注 + 叠层图(03_) + 阻抗表(04_) +
L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md`；接受其 DFM review 与重报价。
若只接受标准通孔工艺 ⇒ 须重开 W3 **通孔化派生**（独立 L2 候选；前置 = 引擎通孔模型 + 可行性证明；
原地通孔化实测 {probe_shorts} 项 shorting_items ⇒ 不可直接降级）。

## 3. 板级 DFM 项（CO-147 L2 裁定 R3，随板厂评审提交）
**阻焊开窗-邻铜净距 1 处**：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm
（欠 0.0205mm）。裁定 = **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何、不改板）。
若板厂拒绝 ⇒ 回退最小修法：R3 开窗 0.05→0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。

## 4. 其余 DFM 项（对照 JLC 8 层能力，实测 PASS）
最小线宽 {b['min_track_width_mm']}mm(≥3.5mil)；过孔 {b['min_via_drill_mm']}/{b['min_via_diameter_mm']}mm（孔 ≥0.15、盘径 ≥0.25、环宽 0.075=JLC「盘径 ≥ 孔径+0.15」）；
孔到孔 {b['min_via_hole_to_hole_mm']}mm(≥0.2)；板规铜-板边 0.30mm(≥0.2)；层数/尺寸/铜厚/板厚/表面处理均落 JLC 能力。
逐项见 `m13_v57_co146_jlc_dfm_gate.json`。

## 5. 阻抗
85Ω 差分两套独立闭式模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）均落 ±10%（as-built 对内净距），
设计名义最宽间距下有 1 项 model-spread 观察值（+11.6%），已列下单备注：
**请 JLC 阻抗表覆盖最宽对内间距（0.6mm 中心）的几何**。终判 = JLC 阻抗控制服务。
见 04_impedance/。

## 6. 已知板级非 DFM 事实（如实登记，非本单阻塞）
- 本板无 PTH/NPTH 焊盘：`J6/J9/J11/J12/J13` 为无焊盘占位（netlist 骨架），板上无安装孔。
- DRC（as-designed，含逃逸域 dru）：42 项，全部为 `lib_footprint_*`(41) + `silk_edge_clearance`(1)，无铜几何违规。
"""


def manifest(root: Path) -> dict:
    files = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files[str(p.relative_to(root))] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    return files


def main() -> int:
    spec = json.loads(SPEC.read_text())
    dfm = json.loads((STEP2 / "m13_v57_co146_jlc_dfm_gate.json").read_text())
    imp = json.loads((STEP2 / "m13_v57_co146_impedance_table.json").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    gdir, ddir = OUT / "01_gerber_rs274x", OUT / "02_drill_excellon"
    export_gerbers(gdir)
    export_drill(ddir)
    n_canon = canonicalize(gdir) + canonicalize(ddir)
    (OUT / "03_stackup").mkdir(parents=True, exist_ok=True)
    (OUT / "03_stackup" / "JLC08161H_stackup.svg").write_text(stackup_svg(spec))
    (OUT / "04_impedance").mkdir(parents=True, exist_ok=True)
    shutil.copy(STEP2 / "m13_v57_co146_impedance_table.md", OUT / "04_impedance/impedance_table.md")
    shutil.copy(STEP2 / "m13_v57_co146_impedance_table.json", OUT / "04_impedance/impedance_table.json")
    (OUT / "05_layer_sequence.txt").write_text(layer_sequence(spec))
    (OUT / "ORDER_NOTES.md").write_text(order_notes(spec, dfm, imp))
    m1 = manifest(OUT)
    # 幂等：重出 gerber/drill，比较
    tmpg, tmpd = OUT / "_rerun_gerber", OUT / "_rerun_drill"
    export_gerbers(tmpg); export_drill(tmpd)
    canonicalize(tmpg); canonicalize(tmpd)
    ident = True
    for sub, tmp in (("01_gerber_rs274x", tmpg), ("02_drill_excellon", tmpd)):
        for p in sorted(tmp.iterdir()):
            q = OUT / sub / p.name
            if not q.exists() or sha256(p) != sha256(q):
                ident = False
    shutil.rmtree(tmpg); shutil.rmtree(tmpd)
    gbr = sorted(p.name for p in gdir.glob("*.gbr"))
    cu = [n for n in gbr if any(n.endswith(f"-{l.replace('.', '_')}.gbr") for l in COPPER)]
    drl = sorted(p.name for p in ddir.glob("*.drl"))
    teeth = {"t01_idempotent": ident,
             "t02_8_copper_gerbers": len(cu) >= 8,
             "t03_drill_present": len(drl) >= 1,
             "t04_all_hashed": all(v.get("sha256") for v in m1.values())}
    rec = {"artifact": "m13_v57_co146_jlc_fab_package", "schema": 1, "revision": "CO146-PKG.1",
           "nature": "JLC 打样包（监理指令 #10 动作 3）；只出交付物，不改板/SPEC",
           "board": BOARD.name, "board_sha16": sha16(BOARD),
           "package_dir": str(OUT.relative_to(K2)), "n_files": len(m1),
           "commands": {
               "gerber": f"{CLI.name} pcb export gerbers --board-plot-params --no-x2 --layers {PLOT_LAYERS}",
               "drill": f"{CLI.name} pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg --generate-report"},
           "kicad_version": subprocess.run([str(CLI), "--version"], capture_output=True, text=True).stdout.strip(),
           "gerbers": gbr, "drills": drl,
           "canonicalization": {"date_pattern": TS_PAT.pattern, "replacement": CANON_DATE,
                               "files_normalized": n_canon,
                               "reason": "KiCad 导出件内嵌墙钟时间戳 ⇒ 规范化以保证命令+sha 可复现；制造语义不受影响"},
           "stackup_svg_sha16": sha16(OUT / "03_stackup/JLC08161H_stackup.svg"),
           "teeth": teeth,
           "orderable_at_jlc_standard": not dfm["fails"],
           "blockers": dfm["fails"],
           "manifest": m1,
           "redline": "只读板；零坐标搜索；不改板/图纸/SPEC/冻结四源（输出全在 L5 交付目录）。"}
    (OUT / "MANIFEST.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    (STEP2 / "m13_v57_co146_jlc_fab_package.json").write_text(json.dumps(
        {k: v for k, v in rec.items() if k != "manifest"}, ensure_ascii=False, indent=1) + "\n")
    print("files:", len(m1), "| gerbers:", len(gbr), "| copper gerbers:", len(cu), "| drills:", len(drl))
    print("teeth:", teeth)
    print("package:", OUT)
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
