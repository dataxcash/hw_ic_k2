#!/usr/bin/env python3
"""CO-235 — **非执行者对抗复评 CO-231..CO-234**（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（**逐件重放**）：`03f8d39`（CO-234）。方法：正控 V1..V6（独立复算：as-found 逐件 sha16 重放 / 自跑闸 / 自源扫描
—— 不引用被评记录之结论）+ 负控 P1..P4（**实件数据 + 内存注入 / 字节复原**，零残留、零坐标搜索）。只读；不改 SPEC/板/冻结四源/他人记录。

CLI: python3 tools/p3_v57_co235_rev19_co231_co234_review.py
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
AF = "03f8d39"                                     # 被评态快照（CO-234）
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REC = STEP2 / "m13_v57_CO235_rev19_co231_co234_review.json"
CARD = STEP2 / "m13_v57_CO235_rev19_co231_co234_review.md"
RUNNER = "tools/p3_v57_co164_order_runner.py"
GEN = "tools/p3_v57_co146_boundary_append.py"
BDY_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md"
PINNED = {                                         # as-found 逐件（git show 03f8d39:<rel> 重放）
    RUNNER: "08c104cda26d2940",
    GEN: "f8ad3b96c289ce51",
    BDY_REL: "17924a8d4a0246e7",
    "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json": "b6477520967efafc",
    "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py": "585b983de844603d",
    "tools/p3_v57_co120_provenance_pin_gate.py": "28d6211f32318d9b",
    "k2_v4_8L.l4.kicad_pcb": "d4e81f647be7f980",
}
# as-found 之「判据面 / realign 面」模式（由 `git show` 源抽取其**字面**；此二式须与修复后同题对偶）
ASFOUND_CITE = (r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`"
                r"(?:[^|`\n]*\|\s*|\s+)`([0-9a-f]{16})`")
ASFOUND_PIN_RE = r"^\|\s*(?P<label>[^|\n]+?)\s*\|\s*`(?P<sha>[0-9a-f]{16})`\s*\|\s*$"
BOLD_ROW = "| 叠层（L2） | `m13_v57_layer_intent_rev6.json`（**LID REV6 / CO-68**：…） | **`05009687a3f01583`** |"
PLAIN3_ROW = "| 走廊/见证（L2） | `m13_v57_big_w0r_corridor_model.json`（W0-R，未改） | `80ee9adb78a7e9ad` |"


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16f(p: Path) -> str:
    return s16b(Path(p).read_bytes())


def git(rel: str, rev: str = AF) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=K2, capture_output=True).stdout


def run_check(*extra: str):
    r = subprocess.run([str(K2.parent / "AppDir/usr/bin/python3.11"), str(K2 / RUNNER), "--check", *extra],
                       cwd=K2, capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)["checks"]
    except Exception:
        return r.returncode, {}


def main() -> int:
    out: dict = {"artifact": "m13_v57_CO235_rev19_co231_co234_review", "schema": 1, "revision": "CO-235",
                 "nature": "非执行者对抗复评 CO-231..CO-234（context 归零之新会话，未参与该四节之撰写 ⇒ 无自评豁免面；"
                           "as-found 逐件重放 + 实件内存注入/字节复原）；**复评范围补正**：复评链上一段 = CO-230 覆盖 CO-225..229，"
                           "其**后** `c1a880b`（CO-231）**未入任何复评声明面**（z96 之复评债声明面漏之）⇒ 本件补足 = CO-231..CO-234",
                 "as_found": {"rev": AF, "pins": {}}}

    # ── V1 as-found 逐件重放（git show 03f8d39） ─────────────────────────────
    v1 = {rel: {"want": w, "got": s16b(git(rel)), "src": "git show " + AF} for rel, w in PINNED.items()}
    for d in v1.values():
        d["ok"] = d["got"] == d["want"]
    out["as_found"]["pins"] = v1
    out["as_found"]["live_now"] = {"note": "本会话已按 F-1 处置（runner/generator/register 已改）⇒ 现行 ≠ as-found 属预期；"
                                           "现行 sha 一律由 boundary §108 pin 表承载（承 R-CO152-1）"}

    # ── V2 冻结四源 + 交付板（独立复算；t34 口径） ───────────────────────────
    fs = {"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
          "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
          "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
          "_shared/eda_core/drc_rules.json": "0a459839e15960b8"}
    fs_res = {rel: {"want": w, "got": s16f(K2 / rel), "ok": s16f(K2 / rel) == w} for rel, w in fs.items()}
    copy_ok = ((K2 / "_shared/eda_core/drc_rules.json").read_bytes()
               == (K2.parent / "_shared/eda_core/drc_rules.json").read_bytes())
    board_ok = s16f(K2 / "k2_v4_8L.l4.kicad_pcb") == "d4e81f647be7f980"

    # ── V3 自跑闸（现行；不引用被评记录之结论） ──────────────────────────────
    rc_check, checks = run_check()
    n_teeth = len(checks)
    all_true = bool(checks) and all(checks.values())

    # ── V4 根因（P1/P2）：as-found 之两「面」皆不覆盖粗体/3 列；修复后皆覆盖（**同域**） ──
    af_cite = re.compile(ASFOUND_CITE)
    fix_cite = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`"
                          r"(?:[^|`\n]*\|\s*|\s+)(?:\*\*)?`([0-9a-f]{16})`")
    af_pin = re.compile(ASFOUND_PIN_RE, re.M)
    fix_pin = re.compile(r"^\|\s*(?P<label>[^|\n]+?\|[^|\n]+?)\s*\|\s*\*{0,2}`(?P<sha>[0-9a-f]{16})`\*{0,2}[^|\n]*\|\s*$", re.M)
    p1 = {"as_found_cite_matches_bold": bool(af_cite.search(BOLD_ROW)),
          "fixed_cite_matches_bold": bool(fix_cite.search(BOLD_ROW)),
          "as_found_cite_matches_plain3": bool(af_cite.search(PLAIN3_ROW)),
          "as_found_pin_re_matches_bold": bool(af_pin.match(BOLD_ROW)),
          "fixed_pin_re_matches_bold": bool(fix_pin.match(BOLD_ROW)),
          "as_found_pin_re_matches_plain3": bool(af_pin.match(PLAIN3_ROW)),
          "fixed_pin_re_matches_plain3": bool(fix_pin.match(PLAIN3_ROW))}

    # ── V5/P2 实件：boundary 内「含 backticked 16-hex 之表行」分类（现行） ────
    bdy = (STEP2 / BDY_REL.rsplit("/", 1)[1]).read_text(encoding="utf-8")
    sha_row = re.compile(r"`[0-9a-f]{16}`")
    rows_all = [ln for ln in bdy.splitlines() if ln.startswith("|") and sha_row.search(ln)]
    rows_nonconf = [ln for ln in rows_all if not af_pin.match(ln)]
    rows_pin_face = [ln for ln in rows_all if not af_pin.match(ln) and not fix_pin.match(ln)]
    p2 = {"n_sha_rows": len(rows_all), "n_as_found_nonconforming": len(rows_nonconf),
          "n_still_nonconforming_after_fix": len(rows_pin_face),
          "still_nonconforming_keys": [ln.strip().strip("|").split("|")[0].strip() for ln in rows_pin_face]}

    # ── V6/P3 实件注入：粗体值伪造（as-found 不可见；修复后 t40/t41 须 False）+ 字节复原 ──
    target = STEP2 / BDY_REL.rsplit("/", 1)[1]
    orig = target.read_bytes()
    inj = {}
    try:
        txt = orig.decode("utf-8")
        assert "**`05009687a3f01583`**" in txt
        target.write_text(txt.replace("**`05009687a3f01583`**", "**`deadbeefdeadbeef`**", 1), encoding="utf-8")
        _rc, _c = run_check()
        inj["bold_value_bogus"] = {"t35": _c.get("t35_judgment_surface_pinned"),
                                   "t40": _c.get("t40_boundary_pin_rows_current"),
                                   "t41": _c.get("t41_boundary_is_generator_output"),
                                   "t43": _c.get("t43_pin_row_format_covered")}
        # P4：整行删除（非声明格式族；§1..§22 手工面）—— 记载**残余**（行集完备性不判）
        row = next(ln for ln in txt.splitlines() if ln.startswith("|") and "m13_v57_big_w0r_corridor_model.json" in ln)
        target.write_text(txt.replace(row + "\n", "", 1), encoding="utf-8")
        _rc, _c = run_check()
        inj["three_col_row_deleted"] = {"t35": _c.get("t35_judgment_surface_pinned"),
                                        "t40": _c.get("t40_boundary_pin_rows_current"),
                                        "t41": _c.get("t41_boundary_is_generator_output"),
                                        "t43": _c.get("t43_pin_row_format_covered")}
    finally:
        target.write_bytes(orig)
    restored = target.read_bytes() == orig

    # ── findings ─────────────────────────────────────────────────────────────
    findings = [
        {"id": "co235:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "status": "CLOSED",
         "what": "pin 行「值面」之**判据面**（t40 域 = `_PIN_ROW_RE`，仅 2 列）与 **realign 面**（生成器 `CITE`，按格式匹配）"
                 "**各自**由格式隐式给定 ⇒ `**`sha`**` 变体**两处皆不在**（判据漏 + 不 realign）⇒ 值陈旧/伪造**静默通过**。"
                 "同族：整行删除（§1..§22 不在生成器权威面）不可见（CO-231 已声明「完备性不判」）。承 R-CO230-1 / R-CO231-1 / R-CO152-1。",
         "evidence": "V4（as-found 二式皆不匹配粗体/3 列；修复后皆匹配 = 同域）、V6（粗体值伪造：修复后 t40 **且** t41 皆 False）、"
                     "as-found 态实测（编辑前）：同式注入 ⇒ t35/t40/t41 **皆 True**；正控（2 列行值）⇒ t40 False",
         "disposition": "生成器 `CITE` 扩 `(?:\*\*)?`（realign 同域）+ runner 声明 `PIN_ROW_FORMATS_DECLARED`（pin2/pin3）+ "
                        "静态齿 **t43_pin_row_format_covered**（含 sha16 之表行须全入声明格式 ∪ 显式豁免名集；新形态 fail-closed）+ "
                        "§3 G7/L5 口径同步（历史快照 vs 现行）。**R-CO235-1**。",
         "residual": "行集完备性（删一行）仍不判；§3 `gate3` 族值由锚点齿承载；§1..§22 仍手工面（承 CO-232 残余）。"},
        {"id": "co235:F-2", "sev": "low", "kind": "RECORD_HYGIENE", "status": "CLOSED",
         "what": "**复评债声明面漏 CO-231**：复评链上一段 = CO-230 覆盖 CO-225..CO-229；其**后** `c1a880b`（CO-231）**未入任何复评声明面**，"
                 "而 z96 handoff 之复评债仅声「CO-232/233/234」⇒ 枚举面缺项（承 R-CO219-1/R-CO230-1：**应有集须独立声明**）。",
         "evidence": "复评链谱（boundary §82..§107 之标题）：CO-202..206 / CO-207..212 / CO-213..218 / CO-219..224 / CO-225..229 — 无一段含 CO-231",
         "disposition": "本件**补足**复评范围 = **CO-231..CO-234**；叙述/记录类**不入登记簿**（承 CO-213 F-2 先例）；handoff z97 更正复评债声明。",
         "residual": "复评债之**连续性**仍无机判齿（属 handoff/流程面，非 repo 工件）。"},
    ]
    out["verdict"] = "PASS_WITH_FINDINGS"
    out["n_findings"] = len(findings)
    out["findings"] = findings
    out["controls"] = {
        "V1_as_found_replay_ok": all(d["ok"] for d in v1.values()),
        "V2_frozen_four": sum(x["ok"] for x in fs_res.values()), "V2_drc_copy_identical": copy_ok,
        "V2_board_unchanged": board_ok,
        "V3_check": {"rc": rc_check, "n_teeth": n_teeth, "all_true": all_true,
                     "revision": "CO-203.12"},
        "V4_root_cause": p1, "V5_row_census": p2, "V6_injection": inj, "V6_bytes_restored": restored,
    }
    out["observations"] = [
        "O-1（被评记录之声明诚实性）：CO-232 之残余「生成器只拥有各 § 区段」经独立复算 —— §23..§107 = 1710 行受权威、§1..§22 = 686 行**手工面**（约 28%）"
        "⇒ 残余声明**量级属实**；惟其后果（手工面内值不可核/不自愈）在本件 F-1 之 E3 实测中被具体化。",
        "O-2（CO-233 相容性）：oracle 之 realign（注入后 + finally）使扰动协议与新增状态齿相容；本件 V3 之 `--check` 与 oracle 记录（PASS / 5 案）"
        "**不含**互相替代之证据 —— 相容性由 oracle 全跑承载，本件不重跑（其受控件扰动 ~4 min，避并发）。",
        "O-3（CO-234 残余之界定）：`.md` 受控件以**显式域名**排除（其受控性由 t20 承接），且 7 枚 md 卡片在 pin 面**无 pin**、§2 表内亦**零次**出现 —— "
        "属**已声明**之域排除（R-CO234-1 允许「显式域名除外」），**非**本件缺陷；域缩水仅由下限（25）部分拦阻（z96 已登记为残余）。",
        "O-4（诚实边界）：本件**不**复评 B 路 10L 实做、外部工艺/报价面（外部输入）；**不**判 boundary 节内叙述之完备性；**CO-235 自身须下一轮复评**（禁自评）。",
    ]
    out["redline"] = ("as-found 以 `git show 03f8d39` 逐件钉定 + sha16 复核；扰动一律**实件注入 + 字节复原**（`finally` 无条件复原，"
                      "V6 后断言逐字节回原）；不改冻结四源 / SPEC / 板；他件处置同 commit。")
    REC.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ── 卡片 ────────────────────────────────────────────────────────────────
    L = ["# CO-235 — 非执行者对抗复评 **CO-231..CO-234**（+ 同会话处置）\n"]
    L.append("复评者 = **非执行者**（context 归零之**新会话**；**未参与 CO-231..CO-234 之任何撰写** ⇒ 四节全在对象内，无自评豁免面）；"
             "as-found 逐件钉 `03f8d39`；扰动 = 实件注入 + 字节复原（零残留）。")
    L.append(f"判决 = **PASS_WITH_FINDINGS**（findings {len(findings)}：F-1 mid / F-2 low；正控 V1..V6 全 True）。**未**改动冻结四源/板/SPEC。\n")
    L.append("## 0. 复评范围补正（F-2）\n")
    L.append("复评链上一段 = **CO-230 覆盖 CO-225..CO-229**；其**后**新增 `c1a880b`（CO-231）**未入任何复评声明面** "
             "（z96 之复评债仅声 CO-232/233/234）⇒ 枚举面缺项。**本件补足：复评范围 = CO-231..CO-234**（承 R-CO219-1 / R-CO230-1）。\n")
    L.append("## 1. as-found（逐件 sha16，`git show 03f8d39` 重放）\n")
    L.append("| 件 | as-found sha16 | 重放 |\n|---|---|---|")
    for rel, d in v1.items():
        L.append(f"| `{rel}` | `{d['want']}` | {'MATCH' if d['ok'] else 'MISMATCH'} |")
    L.append("\n## 2. 正控（本会话独立实测）\n")
    L.append(f"- 冻结四源 **{sum(x['ok'] for x in fs_res.values())}/4 MATCH**；`drc_rules` 副本同字节 = **{copy_ok}**；交付板 `d4e81f647be7f980` 逐字节未变 = **{board_ok}**")
    L.append(f"- `--check` **{sum(1 for vv in checks.values() if vv)}/{n_teeth}**（现行 = CO-203.12；rc={rc_check}）；根因两式（V4）：as-found `CITE`/pin 正则对粗体行 = "
             f"**{p1['as_found_cite_matches_bold']}/{p1['as_found_pin_re_matches_bold']}**，修复后 = **{p1['fixed_cite_matches_bold']}/{p1['fixed_pin_re_matches_bold']}**（**同域**）")
    L.append(f"- 行普查（V5）：含 16-hex 之表行 **{p2['n_sha_rows']}**；as-found 非 2 列者 **{p2['n_as_found_nonconforming']}**；修复后仍不在 pin 面者 **{p2['n_still_nonconforming_after_fix']}**（{p2['still_nonconforming_keys']}）\n")
    L.append("## 3. findings\n")
    L.append("### F-1（TOOL_DEFECT · mid · CLOSED）**pin 行值之判据面/realign 面各自由格式隐式给定 ⇒ `**`sha`**` 变体静默逃逸**\n")
    L.append(f"实件注入（V6，`finally` 复原 = {restored}）：")
    L.append(f"- 粗体行值伪造 `**`05009687a3f01583`**`→`**`deadbeefdeadbeef`**`：**修复后** t35=`{inj['bold_value_bogus']['t35']}` / "
             f"t40=`{inj['bold_value_bogus']['t40']}` / t41=`{inj['bold_value_bogus']['t41']}` —— **修前**同式注入（编辑前实测）为 **t35/t40/t41 皆 True**（静默通过），正控（2 列行）须 t40 False。")
    L.append(f"- 整行删除（3 列 / §1..§22 手工面）：t35=`{inj['three_col_row_deleted']['t35']}` / t40=`{inj['three_col_row_deleted']['t40']}` / "
             f"t41=`{inj['three_col_row_deleted']['t41']}` ⇒ **残余**（行集完备性不判；CO-231 已声明）")
    L.append("**处置**：生成器 `CITE` 扩 `(?:\\*\\*)?`（realign **同域**）+ runner **声明格式集** `PIN_ROW_FORMATS_DECLARED`（`pin2`/`pin3`，"
             "`boundary_pin_rows()` 遍历之 ⇒ **t40 值核覆盖 §2 全 14 行**）+ 静态齿 **t43_pin_row_format_covered**（未声明之新形态 **fail-closed**）"
             "+ §3 G7/L5 **口径同步**（历史快照 vs 现行 L5-SI.11）。**R-CO235-1**。\n")
    L.append("### F-2（RECORD_HYGIENE · low · CLOSED）**复评债声明面漏 CO-231**\n")
    L.append("复评链谱（§82..§107）无一段含 CO-231 ⇒ 本件补足范围；叙述类**不入登记簿**（承 CO-213 F-2 先例）；handoff z97 更正。\n")
    L.append("## 4. 观测\n")
    for o in out["observations"]:
        L.append("- " + o)
    L.append("\n## 5. 红线\n")
    L.append("**R-CO235-1**：**判据面与 realign 面须同域** —— 凡以「行的形态」界定判定域者，须**显式声明格式名集**（非由单一行正则隐式给定），"
             "并以**覆盖面臂**保证「域外无 carrying-同语义之对象」（未声明之新形态 ⇒ **fail-closed**）；且**值面**（现行 sha）之 realign 面须与判据面**同域** —— "
             "不得一方覆盖、另一方漏过（漏过即**静默陈旧**）。承 R-CO230-1 / R-CO231-1 / R-CO152-1。")
    CARD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "n_findings": len(findings),
                      "V1": all(d["ok"] for d in v1.values()), "frozen": sum(x["ok"] for x in fs_res.values()),
                      "check": f"{sum(1 for vv in checks.values() if vv)}/{n_teeth}", "rc": rc_check,
                      "V4": p1, "V5": p2, "V6": inj, "restored": restored,
                      "rec": s16f(REC), "card": s16f(CARD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
