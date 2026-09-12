#!/usr/bin/env python3
"""CO-146 — boundary 收口件登记（§23）+ 现行态 pin 再对齐（co77 口径）。

幂等：§23 已存在则整段替换；pin 重对齐按「文件→当前 sha16」表逐条替换**非历史**引用。
"""
from __future__ import annotations
import hashlib, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = L3 / "mcio_feas_step2"
DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"
MARK = "## 23. CO-146"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    txt = DOC.read_text()
    # ── 1. 现行态 pin 再对齐（只改「文件 <-> 旧 sha」这种当前态引用） ─────────
    realign_files = None   # None = 全量（现行态引用一律对齐当前实件 sha16；历史引用跳过）
    CITE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`"
                      r"(?:[^|`\n]*\|\s*|\s+)`([0-9a-f]{16})`")
    HIST_AFTER = re.compile(r"^[\s）)】,，、/]*[（(]?\s*(已取代|历史|应为|实为)")

    def _fix(m: re.Match) -> str:
        name, sha = m.group(1), m.group(2)
        if realign_files is not None and Path(name).name not in realign_files:
            return m.group(0)
        nxt = txt[m.end():m.end() + 16]
        if HIST_AFTER.match(nxt) or "→" in txt[m.end():m.end() + 8] or "->" in txt[m.end():m.end() + 8]:
            return m.group(0)
        cands = [Path(name), STEP2 / Path(name).name, L3 / Path(name).name, L2 / Path(name).name,
                 K2 / "tools" / Path(name).name, K2 / Path(name).name,
                 K2 / "_shared" / "eda_core" / Path(name).name,
                 K2.parent / "_shared" / "eda_core" / Path(name).name]
        hit = next((c for c in cands if c.exists()), None)
        if hit is None:
            return m.group(0)
        cur = s16(hit)
        return m.group(0).replace(sha, cur) if cur != sha else m.group(0)

    txt = CITE.sub(_fix, txt)
    # ── 2. §23 替换/追加 ────────────────────────────────────────────────────
    rows = [("冻结 SPEC `SPEC_k2_v4.spec-rev-19.json`(未变)", L3 / "SPEC_k2_v4.spec-rev-19.json"),
            ("交付板 `k2_v4_8L.l4.kicad_pcb`(未变)", K2 / "k2_v4_8L.l4.kicad_pcb"),
            ("阻抗表 `m13_v57_co146_impedance_table.json`", STEP2 / "m13_v57_co146_impedance_table.json"),
            ("PM 评估 `m13_v57_co146_pm_eval.json`", STEP2 / "m13_v57_co146_pm_eval.json"),
            ("DFM 闸 `m13_v57_co146_jlc_dfm_gate.json`", STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
            ("JLC 能力表 `m13_v57_co146_jlc8_capability.json`", STEP2 / "m13_v57_co146_jlc8_capability.json"),
            ("通孔化反证 `m13_v57_co146_through_via_probe.json`", STEP2 / "m13_v57_co146_through_via_probe.json"),
            ("打样包记录 `m13_v57_co146_jlc_fab_package.json`", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
            ("定性更正 `m13_v57_co146_jlc_rebind.json`", STEP2 / "m13_v57_co146_jlc_rebind.json"),
            ("L2 定值绑定 `jlc_prototype_parameters_v1.json`", L2 / "jlc_prototype_parameters_v1.json"),
            ("登记簿 `input_defect_register_v1.json`(+2 OPEN)", L2 / "input_defect_register_v1.json"),
            ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
            ("工具 `p3_v57_co146_jlc_dfm_gate.py`", K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
            ("工具 `p3_v57_co146_impedance_table.py`", K2 / "tools/p3_v57_co146_impedance_table.py"),
            ("工具 `p3_v57_co146_pm_eval.py`", K2 / "tools/p3_v57_co146_pm_eval.py"),
            ("工具 `p3_v57_co146_jlc_fab_package.py`", K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
            ("工具 `p3_v57_co146_through_via_probe.py`", K2 / "tools/p3_v57_co146_through_via_probe.py"),
            ("工具 `p3_v57_co146_closeout.py`", K2 / "tools/p3_v57_co146_closeout.py")]
    sec = [MARK + "（L2 · 监理指令 #10「JLC 8 层打样就绪」）：阻抗表 / PM 评估 / 打样包 / DFM 闸 / 定性更正", "",
           "> 依据：`instruction-10-jlc-prototype-ready.md`（监理定值：JLC08161H 1.6mm / 外层 1oz 内层 0.5oz / "
           "85Ω±10% 勾阻抗控制 / ENIG / 压降 3% / 40°C 自然对流）。冻结四源 **逐字节未动**（SPEC `5f72182a2616392c`、"
           "板 `d4e81f647be7f980`）。", "",
           "**动作 1 阻抗表**：JLC08161H 交付几何双模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）交叉核对 ⇒ "
           "as-built 对内净距下 85Ω±10% **PASS**；设计名义最宽间距（0.6mm 中心）下有 1 项 model-spread 越界 "
           "⇒ 列入下单备注（请 JLC 阻抗表覆盖该几何）。终判 = JLC 阻抗控制服务。", "",
           "**动作 2 PM 评估**：一阶确定性（平面 Rs·L/W + 过孔并联 + 热 ΔT=P/(h·2A)）。四轨压降 "
           "0.007%–0.69%（预算 3%）全 PASS；热 ΔT_board 29.0°C ⇒ T_board 69.0°C、热点 Tj(U6) 106.5°C < 125°C。"
           "**电流/功耗/θJA/对流系数为显式声明值（非实测）**，器件手册到位后替换重跑。", "",
           "**动作 3 打样包**：`L5/jlc_package/`（Gerber RS-274X ×13 含 8 铜层 + Excellon 钻孔 ×5 + 叠层图 SVG + "
           "阻抗表 + 层序 + 下单备注 + MANIFEST）；命令+sha 可复现（时间戳规范化；重跑逐字节同）。", "",
           "**动作 4 DFM 闸（对照 JLC 公布能力）**：**FAIL** —— ① **盲/埋孔**：交付板 **220/493** 支非通孔"
           "（含 `In2.Cu→In5.Cu` **埋孔 88**），而 JLC 标准服务 *Blind/Buried Vias Not supported*；原地改通孔实测 "
           "**111 项 shorting_items** ⇒ 现行 W3 派生**结构依赖盲/埋孔**；② **阻焊桥 1 处**（JLC 0.09mm 下限，"
           "`PCIE_UP3_N`×`R3.pad2(PWR_BTN_ISO)`）。其余项（线宽 0.16≥0.09、孔 0.2/盘 0.35、环宽 0.075、孔距 0.25、"
           "板边 0.30、尺寸/层数/铜厚/板厚/表面处理）全 PASS。", "",
           "**动作 5 定性更正**：**撤回「外部输入阻塞」**（阻抗终判改绑 JLC 阻抗控制服务；PM 改绑监理定值 + 本件评估）；"
           "SPEC `impedance.coupon_required=true` **字段不动**（改绑的是解释与签署路径）；登记簿 **+2 OPEN**"
           "（盲/埋孔 = 结构/工艺类别 ⇒ 需 owner 一句话；阻焊桥 = 可修）。", "",
           "**残留（如实）**：① owner：盲/埋孔出路 (a) 走 JLC advanced 盲埋孔通道 / (b) 重开 W3 通孔化派生；"
           "② owner：J2 接口 3W 适用域（既有 L1）；③ 复评债 CO-142..145 + **CO-146 全部产物**（另一会话，禁自评）。", "",
           "| 工件 | sha16 |", "|---|---|"]
    for label, p in rows:
        if p.exists():
            sec.append(f"| {label} | `{s16(p)}` |")
    sec.append("")
    body = "\n".join(sec)
    if MARK in txt:
        txt = re.sub(re.escape(MARK) + r"[\s\S]*?(?=\n## |\Z)", body, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body
    txt = txt.replace("W3 Boundary **v1.97**", "W3 Boundary **v1.98**")
    DOC.write_text(txt)
    print("boundary sha16:", s16(DOC), "| lines:", len(txt.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
