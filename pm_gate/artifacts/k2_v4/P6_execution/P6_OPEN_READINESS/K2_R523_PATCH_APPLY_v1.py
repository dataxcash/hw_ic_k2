#!/usr/bin/env python3
"""K2 · R523 —— 版本件生成器：由 **只读原件** R515 派生 R523 模型文件（读档只增不改 · 可复算）。
生成物 = K2_R523_LAYERHOP_PARITY_FORMC_v1.py，含三处**唯二**改动：
 (1) 并入 form C parity 约束（import K2_R523_PARITY_FORMC_v1）；
 (2) 修在册闸 gate_vias 的 numpy 广播崩溃（`np.stack([V[:,None,:],V[:,None,:]],1)` → `np.stack([V,V],1)`）；
 (3) 加「实际 bool 数 > 规模闸 ⇒ fail-closed，不求解」的显式闸 + V 族/H 族断面口径说明。
其余（R515 的 Gen2 / 逐层净距 / 节点容量 / 过孔机制 / 腿机制 / 提取与在册 exact_gate）**一字不改**。
"""
import os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "K2_R515_FREETERMINALS_v1.py")
DST = os.path.join(HERE, "K2_R523_LAYERHOP_PARITY_FORMC_v1.py")

HEADER = '''#!/usr/bin/env python3
"""K2 · R523 —— 丙（parity / 换位记账序变量）**形态 C · 可机核保真版** 的实现窗（承 HANDOFF-K2-522 §0 · #K2-189 §四）。

本件 = **只读原件** `K2_R515_FREETERMINALS_v1.py`（其"双层联合 MCF + 逐层精确净距 + F3 非空核假设字面量"
一字不改）+ 两处**具名**改动：

 ① **form C parity 约束**（`K2_R523_PARITY_FORMC_v1.py`）：每根线在四把**在册走廊刀**上的
    **In5 实际横穿**与实际横向序；同轴相邻断面间 **rank 序翻转 ⇒ 该区间内至少一根必须有过孔弧**。
    —— **断面口径更正**（相对 HANDOFF-K2-522 字面版）：不取「院列(行38..57) ↔ 墙洞行(行7..28)」
    （该对被机核反例证明**非蕴含**：两线零过孔、全程 In5、合法、却序翻转 —— 见
    `K2_R523_LITERAL_FORMC_COUNTEREXAMPLE_v1.json`），改取**走廊内相邻、且被同一简单条带连接的**断面：
      V 族：`col 60` ↔ `col 114`（rank = 行；区间 `x∈(x60,x114)`）；
      H 族：`row 36`（**向南穿门**）↔ `row 30`（焊盘场入口行，rank = 列；区间 `y∈(y30,y36)`）。
    蕴含证明与机核前提见 parity 模块 docstring（含「腿不可能穿过任何一把刀」的机核）。
 ② **在册闸 `gate_vias` 崩溃修复**（另起版本号，原件不动）：`np.stack([V[:,None,:],V[:,None,:]],1)`
    形状为 (n,2,1,2) ⇒ 与 `_seg_rect_dists` 期望的 (n,2,2) 不符 ⇒ 全尺寸下 numpy 广播 ValueError
    （R515/R517 均实测崩溃）。回归判据见 `K2_R523_GATE_VIAS_FIX_REGRESSION_v1.py`。

纪律：本件**不改** R515 编码/参数/冻结四源/判据；`Solve()` 仍**恰一次**；前置硬闸（规模闸 + `Validate()` +
R512 `gate_preexisting` + 声明集自检）不过 ⇒ 不求解。施工停线维持；P4 该项未归零前不导 Gerber、不进 P5。
"""
'''

FORM_C_BLOCK = '''
    # ================= R523: form C parity / swap-accounting（可机核保真断面口径） =================
    import K2_R523_PARITY_FORMC_v1 as FC
    lit_par = mo.NewBoolVar("par_formC")
    ASSUMP["parity_form_C"] = lit_par
    rep["form_c"] = FC.add_form_c(mo, x, lanes, NID, NX, NY, ASSUMP, lit_par)
    rep["form_c"]["sections_corrected_vs_handoff_literal"] = (
        "V: col 60 <-> col 114 (rank=row); H: row 36 (southbound gate) <-> row 30 (pad-entry row, rank=col). "
        "The handoff-literal pairing (yard rows vs wall-gap rows) is machine-refuted as NON-IMPLIED "
        "(K2_R523_LITERAL_FORMC_COUNTEREXAMPLE_v1.json) and is therefore NOT used (handoff sec.0: ning qian wu lan).")
    rep["form_c"]["factored_by"] = "R523 patch of the read-only R515 model; R515 itself unchanged"

'''

SCALE_BLOCK = '''
    if len(mo.Proto().variables) > SCALE_GATE:
        rep["decision"] = ("STOP-BEFORE-SOLVE: 实际 bool 数 %d > 规模闸 %d ⇒ fail-closed（Solve() 0 次 · 额度未耗）"
                           % (len(mo.Proto().variables), SCALE_GATE))
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(rep["decision"]); print("WROTE", out); return
'''


def main():
    s = open(SRC).read()
    orig = hashlib.sha256(s.encode()).hexdigest()
    # (0) 换头（保留原 docstring 作为普通字符串表达式 · 一字不改其正文）
    assert s.startswith("#!/usr/bin/env python3\n")
    s = HEADER + s[len("#!/usr/bin/env python3\n"):]
    # (1) 版本号/产物名
    assert s.count('"artifact": "k2_r514_layerhop_joint_mcf_v1"') == 1
    s = s.replace('"artifact": "k2_r514_layerhop_joint_mcf_v1"', '"artifact": "k2_r523_parity_formc_v1"')
    assert s.count('"K2_R514_LAYERHOP_JOINT_MCF_v1.json"') == 1
    s = s.replace('"K2_R514_LAYERHOP_JOINT_MCF_v1.json"', '"K2_R523_PARITY_FORMC_RESULT_v1.json"')
    assert s.count('"K2_R515_FREETERMINALS_ROUTES_v1.json"') == 1
    s = s.replace('"K2_R515_FREETERMINALS_ROUTES_v1.json"', '"K2_R523_PARITY_FORMC_ROUTES_v1.json"')
    # (2) gate_vias 广播修复
    bad = ("        if len(PB2):\n"
           "            mg = _seg_rect_dists(np.stack([V[:, None, :], V[:, None, :]], 1), PB2) - VR - PR2[None, :]\n"
           "            if mg.min() < -1e-6:\n"
           "                bad.append((\"via-obstacle-pad\", L, round(float(mg.min()), 4)))\n")
    good = ("        if len(PB2):\n"
            "            # R523 fix-1: (n,2,2) 退化段（原 (n,2,1,2) 全尺寸必崩 numpy 广播）\n"
            "            _db = _seg_rect_dists(np.stack([V, V], 1), PB2)\n"
            "            # R523 fix-2: 包含感知 —— 过孔落在焊盘盒内时距离应为 0（原实现只给\"到盒边\"的距离，容器内漏检）\n"
            "            _ins = ((V[:, None, 0] >= PB2[None, :, 0]) & (V[:, None, 0] <= PB2[None, :, 2]) &\n"
            "                    (V[:, None, 1] >= PB2[None, :, 1]) & (V[:, None, 1] <= PB2[None, :, 3]))\n"
            "            mg = np.where(_ins, 0.0, _db) - VR - PR2[None, :]\n"
            "            if mg.min() < -1e-6:\n"
            "                bad.append((\"via-obstacle-pad\", L, round(float(mg.min()), 4)))\n")
    assert s.count(bad) == 1, "pad block not found"
    s = s.replace(bad, good)
    # (3) 并入 form C（在所有基础约束之后、Validate 之前）
    assert s.count("\n    v = mo.Validate()\n") == 1
    s = s.replace("\n    v = mo.Validate()\n", FORM_C_BLOCK + "\n    v = mo.Validate()\n")
    # (4) 实际规模闸（不求解）
    anchor = "    for nm, lit in ASSUMP.items():\n        mo.AddAssumption(lit)\n"
    assert s.count(anchor) == 1
    s = s.replace(anchor, SCALE_BLOCK + "\n" + anchor)
    open(DST, "w").write(s)
    print("WROTE", DST)
    print("source sha256:", orig)
    print("dest   sha256:", hashlib.sha256(s.encode()).hexdigest())
    print("syntax:", end=" ")
    import ast; ast.parse(s); print("OK")


if __name__ == "__main__":
    main()
