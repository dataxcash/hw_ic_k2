#!/usr/bin/env python3
"""CO-164/CO-167/CO-169/CO-174/CO-180/CO-181/CO-182/CO-183/CO-187/CO-188/CO-189/CO-190/CO-191/CO-192/CO-193/CO-194/CO-195/CO-196/CO-197/CO-198/CO-199/CO-200/CO-201/CO-202/CO-203 — **规范复现序机判执行器**（R-CO164-1 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1）：以 rc 为准判定收敛，禁「sha 稳定即收敛」。

缘起（实测事故，CO-163）：`co146_boundary_append.py` 因 §37 文本里的 f-string 花括号语法错误**每次崩溃（rc=1）**，
但收敛判定只看 boundary/记录 sha ⇒ sha 恒不变 ⇒ 报「CONVERGED」，边界 §37 实际从未写入、pin 表陈旧（co77/co135/co136 判 FAIL）。
即「以 sha 稳定替代 rc 检查」会产生**假收敛**（本会话由一个独立 rc 复核才发现）。

本器（**不在**规范序内运行，避免自递归；其报告落在 `.archer_tmp/`，**不被 boundary 引用** ⇒ 不构成下游快照/不动点）：
  ① 依 R-CO163-3 顺序逐步执行（子进程），rc 策略：`EXPECTED_NONZERO = {co146_jlc_dfm_gate}`（verdict=FAIL 属预期），
     其余任一步非零 ⇒ **立即停机**并报出门名/rc/stderr 尾（fail-fast，禁"继续跑完再说"）；
  ② 每轮迭代后比对受控 sha（boundary + 关键记录 + 台账/登记簿）；**仅当** rc 全合规**且** sha 逐轮稳定 ⇒ 判 CONVERGED；
  ③ `--check` 只做静态体检：步骤文件存在 + 可编译 + rc 策略声明完备（零执行、零落盘），可作轻量 sanity；
  ④ CO-174（R-CO174-1）：`did_work` 归因**仅限本步声明的主产物集**（非全局受控集）⇒ 并发/他人写**其它**受控件
     不再被误判为「本步做了事」（关闭 CO-172 F-7 的假通过方向）；报告另记 `declared_changed` / `stray_changed` 证据。
     全局受控集仍保留用于收敛 sha（R-CO165）；**残余如实登记**：共享主产物（台账/登记簿）上的并发写仍可误判。
  ⑤ CO-188（R-CO188-1）：**越界写**（步骤写其 `STEP_ARTIFACTS` **未声明**的受控件）⇒ 运行时停机类 `stray_write`
     + 静态齿 **t22**（合成正负控 + `STRAY_WRITE_ALLOWED` 例外表完备）。理由：确定性越界写不破 sha 收敛、亦不被
     步本地 `did_work` 归因抓到 ⇒ 可与「sha 稳定」共存而**假通过**。
  ⑥ CO-189（R-CO189-1）：**受控集外写入**（承载根内、非受控件、非豁免）⇒ 运行时停机类 `uncontrolled_write`
     （stat 轻量 shadow 快照）+ 静态齿 **t23**（shadow 根 ⊇ 受控集；`WRITE_SHADOW_EXEMPT` 完备性 + 正负控）。
  ⑦ CO-190（R-CO190-1）：**步骤超时**（`STEP_TIMEOUT_S`）⇒ 杀子进程 + 停机类 `step_timeout` + 每步 `duration_s`
     记录 + 静态齿 **t24**（超时值带 + 正负控）。缺超时 = 挂起步使 runner 永久阻塞而非 fail-closed。
  ⑧ CO-191（R-CO191-1）：**判定基据完备性** —— ① 步骤**全部**声明 verdict 一律判决（禁只判首个 ⇒ 隐藏非 PASS 可逃逸）；
     ② 每步须有可机判基据（`teeth`/`verdict`/登记簿自洽/**显式下游** `JUDGMENT_DOWNSTREAM`）⇒ 禁「静默步」；静态齿 **t25**。
  ⑨ CO-192（R-CO192-1，**非执行者对抗复评 CO-187..CO-191 的处置**）：① 静态扫描**形态完备性**续加固——牙齿棘轮补 `|=`/嵌套下标/推导/`__setitem__`/Attribute/下标赋别名；md 写补 `Path.open(w)`/`shutil.move`/`os.replace|rename`；boundary 读补 `.open().read()`/`io.open`；② **放行档一律判全 verdict**（`all_verdicts_gate`：`ok` **与** `expected_nonzero` 均判 ⇒ 白名单步副 verdict 不得逃逸）。t18/t20/t21/t25 合成控同步扩展。
  ⑩ CO-193（R-CO193-1/2，**声明↔实现绑定的可执行性**）：① `JUDGMENT_DOWNSTREAM` 下游声明须**可执行** —— 每条给被judged工件 basename，ref 须在序内**晚于**声明步（存在性）且 ref 步工具**确实读取**该工件，否则 fail-closed；② `EXPECTED_NONZERO` 证据须**本步绑定** —— `record` 须 ∈ `STEP_ARTIFACTS[step]`、`teeth_path` 须在记录内**可解析**。静态齿 **t26**。
  ⑩ CO-193（R-CO193-1/2，**声明↔实现绑定的可执行性**）：① `JUDGMENT_DOWNSTREAM` 下游声明须**可执行** —— 每条给被judged工件 basename，ref 须在序内**晚于**声明步（存在性）且 ref 步工具**确实读取**该工件，否则 fail-closed；② `EXPECTED_NONZERO` 证据须**本步绑定** —— `record` 须 ∈ `STEP_ARTIFACTS[step]`、`teeth_path` 须在记录内**可解析**。静态齿 **t26**。
  ⑪ CO-194（R-CO194-1/2，**基据↔判官 + 声明↔工具能力**）：① 每个**基据类别**须显式声明其**判官**（`BASIS_JUDGE_DECLARED`）并机判 —— 判官须在序内、须读被judged件、且**自身有**机判基据（否则 fail-closed；`register_consistency` 系 latent 类别，当前不可达但须绑定）；② `EXPECTED_NONZERO` 声明的 verdict 字面须出现在该步**工具源**（声明不得指向工具不可能产出的 verdict）。静态齿 **t27**。
  ⑫ CO-195（R-CO195-1，**固定点唯一性 oracle 绑定**）：规范序的**不动点唯一性（路径无关）**（CO-151 失效模式：按序连跑两遍得
     **另一稳定不动点**）由 `tools/p3_v57_co195_fixpoint_uniqueness_oracle.py` **直接判**（扰动启动 ⇒ 收敛须复原规范态）。
     **CO-196（J-1）修正**：静态齿 **t28** 只判「oracle 工具**存在 + 可编译**」——**不得读其证据件**（`--check` 以被验证证据为输入会构成
     **验证循环**：证据 FAIL ⇒ t28 拒 ⇒ 规范序静态前置失败 ⇒ oracle 无法跑 ⇒ 永久锁死；实测已复现）。证据件的 PASS 由 oracle 自身承载。
     **CO-196（J-4）修正**：t28 的合成控须**逐返回路径**对应（缺件 → `oracle_tool_ok`；语法错 → 内存 `src_compiles`）——
     以「不存在的路径」充作语法错控是**恒真**（仅重复缺件分支），故新增纯内存判据 `src_compiles()`。
⑬ CO-197（K-1/K-2，**复评 CO-192..CO-195 产物之形态完备性**）：① `teeth_hygiene_scan` 补关键字解包形态
     `dict(**{...})` / `.update(**{...})`；② `md_write_scan` 补 `io.open(<md>, "w")` 与 `Path(...)/路径别名.replace|rename(<md>)`
     目的；t18/t20 合成控同步扩展（含 `"a.md".replace(".md","")` 字符串操作**不得误报**之对偶负控）。
⑭ CO-198（R-CO198-1，**代理 ↔ 语义闸绑定机判化**）：凡**代理判据**代替语义判据之处，须显式声明**残余**（不得宣称完备）
     + 承载该语义性质的**外部判官**（工具 + **源内声明**的齿名）+ 代理自身 fail-closed 齿所在记录（须在 pin 表）；静态齿 **t29**。
⑮ CO-199（R-CO199-1，**白名单 rc 类语义**）：`EXPECTED_NONZERO` 须显式声明**预期 rc 值**（= 该判决的规格化出口），
     运行期 **只**豁免该 rc；其余非零一律 `expected_step_rc_mismatch` 停机（禁以「rc≠0」笼统放行）。静态齿 **t30**。
⑯ CO-201（R-CO201-1/2，**出口语义与豁免边界**）：① 白名单**预期非零出口**须**无任何错误输出**（stderr 空），
     旧 Traceback 子串代理不足；② 写影子**豁免前缀**的**段边界**分支须入合成控。静态齿 **t31** + t23 扩展。
⑰ CO-202（R-CO202-1/2/3/4，**非执行者复评 CO-196..CO-201 之处置**）：t28 谓词级逐返回路径控（存在但不可编译 / 类型错）；
     `allowlist_decision(decl=)` 可注入声明面 + t30 控 `expected_step_rc_undeclared`；proxy「源内声明」改 **AST 字面量集**
     （注释/散文不得满足）；静态齿 **t32**（受控集产物类别 ⊆ oracle 扰动量类别）。
⑱ CO-203（R-CO203-1，**自声明修订号绑定**）：凡工具**自声明 `revision`** 者，其记录 dict 字面量之修订号（**AST 抽取**；
     注释/散文不得满足 —— 承 R-CO202-4）须等于 `TOOL_REVISION_DECLARED` 之声明 —— 防「内容已升级、自声明滞留」
     （CO-202 之残余：oracle 内容已 CO-202 而 `revision` 仍 CO-200）。静态齿 **t33**。
⑲ CO-215（R-CO215-1，**代理帮助函数之源面收窄 + 覆盖面机判**）：`artifact_readers()`（判「某步**确实读取**该工件」之**语法代理**）
     原按**原文子串** `basename in src` 判 ⇒ **注释/散文即可满足**（与 R-CO202-4「注释不得满足源内声明」同源缺陷，CO-215 实测复现）⇒
     收窄为 **AST 字面量集**（`_source_strings`）匹配 + glob 字面量；并把该帮助函数之**残余显式登记**
     （`PROXY_RESIDUAL_EXPLICIT`：动态构造漏判 / 非读取语境误判，**不宣称完备**）以 `PROXY_HELPERS_PINNED` **覆盖面齿**机判
     （每枚帮助函数须恰登记于 `PROXY_SEMANTIC_BINDING`（有语义判官）或 `PROXY_RESIDUAL_EXPLICIT`（显式残余）之一）。
⑳ CO-216（R-CO216-1，**源面判据之 AST 收窄（续）**）：把 R-CO215-1 之纪律推广到 runner 内**其余两枚源面帮助函数** ——
     `declared_verdict_in_tool()`（原 `v in src` ⇒ **注释含 verdict 字面即满足**，令 t27 之「声明↔工具能力」臂近乎空真）
     改判 **AST 字符串字面量集**；`boundary_read_scan()`（原 `re` 扫**原文** + `read_text` 等**原文子串**判读取者 ⇒ 注释可伪造引用/读取）
     改判 **AST 形态**（引用 = 字面量或 `_latest_boundary` 标识符；读取 = `Attribute.attr ∈ READ_ATTRS` 或 `io.open` 调用）。
     两枚一并纳入 `PROXY_HELPERS_PINNED` + `PROXY_RESIDUAL_EXPLICIT`（消费齿 = t27 / t21）。
㉑ CO-218（R-CO218-1，**冻结源不变性 + 规则源唯一性入机判**）：冻结四源跨会话仅由**人手复核**（各件「写件时复核」之
     「4/4 MATCH」）+ CO-91.2 之**一次性**断言 ⇒ 源漂移（SPEC / 清单 / 冻结板 / 规则）**不使规范序失败**
     （序只消费当下内容，仍可收敛）⇒ 判定基据**失锚**。现以 `FROZEN_SOURCES`（pin 表）+ `FROZEN_SRC_COPIES`
     （K2 ↔ 容器 `drc_rules.json` 同字节）+ 纯判据 `frozen_sources_decision()` 入**静态齿 t34**（fail-closed），
     并把解析结果写入报告 `frozen_sources` 证据块。
CLI:
  python3 tools/p3_v57_co164_order_runner.py [--check] [--max-iter 5]
"""
from __future__ import annotations
import argparse, ast, fnmatch, hashlib, json, re, subprocess, sys, time, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REPORT = K2 / ".archer_tmp/co164_order_report.json"
# R-CO163-3 规范复现序（与 boundary §37 同步；末步 boundary_append 为 pin 再对齐）
ORDER = ["co146_impedance_table", "co146_pm_eval", "co146_ledger_add", "co153_k9_domain_coverage",
         "co148_u6_datasheet_inputs", "co148_thermal_ruling", "co149_thermal_mitigation_derive", "co147_l2_ruling",
         "co146_jlc_dfm_gate", "co146_jlc_fab_package", "co152_findings_disposition", "co155_co154_findings_disposition",
         "co156_co154_open_disposition", "co157_gate_hardening_3", "co158_l5_packet_selfcontained",
         "co159_rev19_co156_co157_co158_review", "co160_co159_findings_disposition", "co161_gap_hardening_4",
         "co162_verdict_binding", "co163_binding_to_order_notes", "co166_rev19_co159_co165_review",
         "co167_co166_findings_disposition", "co168_register_consistency", "co169_step_output_oracle", "co170_stackup_binding", "co171_order_notes_record_figures",
         "co172_rev19_co166_co171_review", "co173_co172_findings_disposition", "co174_step_artifact_attribution", "co175_package_parity_binding", "co176_gate_selfcheck_evidence", "co177_capability_value_binding", "co178_drc_item_limit_derivation", "co179_sensitivity_teeth_hardening", "co180_teeth_judgment_integrity",
         "co124_input_selfcheck_gate", "co150_k9_domain_gate",
         "co146_boundary_append", "co77_closure_declaration_sweep", "co120_provenance_pin_gate", "co146_boundary_append", "co135_review_hygiene",
         "co136_gate_hygiene", "co78_layer_role_drift_gate", "co81_project_rules_gate", "co84_dru_domain_gate",
         "co95_in4_reachability", "co98_reachability_status_report", "co106_reference_plane_gate", "co146_boundary_append"]
# CO-182（R-CO182-1）：**扫描 boundary citation 的步**须**紧跟 boundary 刷新步**（原滞后根因：
# 刷新步在其前、co77/co120 在其后改写被引记录 ⇒ co135 见 pin 瞬时陈旧 ⇒ 首轮停机）。
BOUNDARY_SCAN_GUARDED = ("co77_closure_declaration_sweep", "co135_review_hygiene")
BOUNDARY_REFRESH_STEP = "co146_boundary_append"
# CO-193（R-CO193-1）：boundary 工件 basename（`JUDGMENT_DOWNSTREAM.artifact` 与 `BOUNDARY` 共用，防两处漂移）。
BOUNDARY_BASENAME = "m13_v57_w3_joint_assignment_boundary_v1_82.md"
# CO-202（L-1/R-CO202-1）：oracle 工具路径（恒常引用）+ 「存在但不可编译」探针件（boundary md 非 Python）。
ORACLE_TOOL = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
_NONCOMPILE_PROBE = STEP2 / BOUNDARY_BASENAME

# CO-187（F-3）：**读取 boundary 但非 citation 扫描步**的显式声明（禁「隐式读取者」漏网）。
# t21 机判：工具源内读取 boundary 的步集 == BOUNDARY_SCAN_GUARDED ∪ BOUNDARY_READ_DECLARED（互斥）。
BOUNDARY_READ_DECLARED = {
    "co146_boundary_append": "boundary 刷新步自身（pin 再对齐 + §节登记）；非扫描步。",
    "co166_rev19_co159_co165_review": "仅作**字节捕获**比对（复跑被评步前后 boundary 是否被写；disk_unchanged）；非 citation/时序扫描。",
    "co172_rev19_co166_co171_review": "只读引用 boundary 作 as-found 取证；不含 citation↔实件 sha 时序扫描。",
}

PASS_VERDICTS = ("PASS", "PASS_WITH_FINDINGS")
# CO-190（R-CO190-1）：**步骤超时 fail-closed** —— 规范序缺超时 ⇒ 任一挂起/无限迭代步使 runner **永久阻塞**
# 而非停机（违「冲突即停机」精神；「暴力迭代」是明令禁止形态，其症状面正是长跑/挂起）。超时值须 ≫ 最慢合法步
# （实测最慢 = DFM 闸 ~数秒）；`timed_out` ⇒ 停机类 `step_timeout`（对白名单步亦生效）。
STEP_TIMEOUT_S = 300
# CO-185（R-CO185-2）：**非 PASS 但 rc==0** 的类别须**显式声明**（禁静默）——
# 该步自评通过（rc=0），但其记录承载**已登记的缺陷结论**（故非 PASS）；须给 `why` + `register` 依据。
DECLARED_NONPASS_OK = {
    "co146_pm_eval": {"verdict": "FAIL", "register": "co148", "key_path": "thermal.verdict",
                      "why": "U6 热超限属**已登记结论**（co148 / L2 裁定：须系统/机械散热）；"
                             "该步 rc 另受 PDN 压降 + 牙齿把关，热结论不属「步失败」"},
}

# CO-191（R-CO191-1）：**判定基据显式化** —— 每步须有可机判基据（`teeth` / 声明产物 `verdict` / 登记簿自洽 / **显式下游**）；
# 禁「无 teeth、无 verdict、无登记簿、无下游声明」的静默步（CO-79「空真」在**执行器层面**的收口）。
JUDGMENT_DOWNSTREAM = {
    "co146_boundary_append": {"ref": ["co77_closure_declaration_sweep", "co135_review_hygiene"],
                              "artifact": BOUNDARY_BASENAME,   # CO-193（R-CO193-1）：被judged工件（须被 ref 工具读取）
                              "why": "本步只做 pin 再对齐 + §节登记；boundary 引用一致性由 co77/co135 的 citation 扫描判"},
}

# CO-194（R-CO194-1）：**基据↔判官**显式绑定 —— 每个基据类别（见 `judgment_basis`）须声明其判定机制；
# `judge=None` = 由运行时自检/声明逐条判（teeth / verdict / downstream）；外部判官须在序内、须读被judged件、且自身有机判基据。
# 缘起：`register_consistency` 分支此前**无判官绑定**（当前不可达：27 个写登记簿步皆先命中 `verdict`；一旦可达即「空真」基据）。
BASIS_JUDGE_DECLARED = {
    "teeth": {"judge": None, "why": "运行时 `step_declared_teeth`（声明产物 teeth 须全 True）"},
    "verdict": {"judge": None, "why": "运行时 `all_verdicts_decision`（**全部**声明 verdict 一律判决）"},
    "register_consistency": {"judge": "co124_input_selfcheck_gate", "artifact": "input_defect_register_v1.json",
                             "why": "登记簿自洽由 `co124.register_consistency()` 机判（其 T21/T21b 牙齿）"},
    "downstream": {"judge": None, "why": "由 `JUDGMENT_DOWNSTREAM` 逐条声明（t26 判方向 + 可执行）"},
}

# CO-203（R-CO203-1）：**自声明修订号**类工具 —— 其记录字面 `revision` 须等于此处之声明。
# （内容升级而自声明滞留即漂移；此为 CO-202 处置所遗漏之面。）
TOOL_REVISION_DECLARED = {
    "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py":
        {"artifact": "m13_v57_co195_fixpoint_uniqueness", "revision": "CO-202"},
}

# 允许非零的步骤（**须带 verdict 证据**：rc≠0 不等于预期 FAIL —— CO-165）
EXPECTED_NONZERO = {
    "co146_jlc_dfm_gate": {"verdict": "FAIL", "record": str(STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
                           # CO-176（G-1）：rc≠0 只豁免 **verdict**，不豁免该步**自检牙齿**（须全 True）
                           "teeth_path": ["teeth"],
                           # CO-199（F-1）：须声明**预期 rc 值**（= 该判决的规格化出口）；只认「非零」会把别的原因
                           # （内部错误 / 参数错 / sys.exit(2)）当预期 FAIL 放行 —— 语义：rc=1 是「闸判 FAIL」之出口。
                           "rc": 1,
                           "why": "verdict=FAIL（DFM 两项阻塞）属预期；rc=1 即 R-CO158-3/R-CO159-4 生效"},
}

# CO-186（R-CO186-1）：规范序各步**写出的 md 卡片产物**（R-CO165「受控 sha 覆盖全部产物」）。
# 由实测（mtime 变化）钉定；全部须在 `watch_paths()` 内（收敛 sha + did_work 归因），并**步本地声明**。
ORDER_MD_PRODUCTS = {
    "co146_impedance_table": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_impedance_table.md",
    "co146_pm_eval": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_pm_eval.md",
    "co147_l2_ruling": "pm_gate/artifacts/k2_v4/L2/L2_RULING_via_channel_and_interpair_domain_v1.md",
    "co148_thermal_ruling": "pm_gate/artifacts/k2_v4/L2/L2_RULING_u6_thermal_v1.md",
    "co149_thermal_mitigation_derive": "pm_gate/artifacts/k2_v4/L2/L2_RULING_u6_thermal_mitigation_v1.md",
    "co146_jlc_dfm_gate": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_jlc_dfm_gate.md",
    "co146_jlc_fab_package": "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md",
    "co124_input_selfcheck_gate": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO124_input_selfcheck_gate.md",
    "co150_k9_domain_gate": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO150_k9_domain_gate.md",
    "co146_boundary_append": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md",
    "co135_review_hygiene": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO135_review_hygiene.md",
    "co136_gate_hygiene": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO136_gate_hygiene.md",
    "co159_rev19_co156_co157_co158_review": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO159_rev19_co156_co157_co158_review.md",
    "co166_rev19_co159_co165_review": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO166_rev19_co159_co165_review.md",
    "co172_rev19_co166_co171_review": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO172_rev19_co166_co171_review.md",
}

# CO-187（F-2）：md 产物**显式豁免**（非「遗漏」）—— 每项须给理由 + 绑定的**补偿牙齿**（须存在于该步 pin 齿集）。
# 现行唯一豁免 = fab 包内阻抗表副本（`04_impedance/impedance_table.md`，由 co146_jlc_fab_package `shutil.copy` 产出）
# ⇒ 其**字节逐一致**由 fab 牙齿 t15_impedance_copy_parity 对冲（对照受控源 `m13_v57_co146_impedance_table.md`）。
ORDER_MD_PRODUCT_EXEMPT = {
    "impedance_table.md": {
        "why": "fab 包内副本（04_impedance/impedance_table.md）非独立产物，属受控源 m13_v57_co146_impedance_table.md 的副本",
        "covered_by": "t15_impedance_copy_parity",
    },
}

# ── CO-174（R-CO174-1）：**每步主产物集**（步本地归因；集合由实测探针逐步跑 ORDER 钉定，非猜测） ──
_A = "pm_gate/artifacts/k2_v4/"
_S2 = _A + "L3/mcio_feas_step2/"
_A2 = _A + "L2/"
_A5 = _A + "L5/jlc_package/"
_REG = _A2 + "input_defect_register_v1.json"
_LED = _A2 + "derived_value_ledger_v1.json"
_SVG = _A5 + "03_stackup/JLC08161H_stackup.svg"
_MD = {k: K2 / v for k, v in ORDER_MD_PRODUCTS.items()}

STEP_ARTIFACTS = {
    "co146_impedance_table": [_S2 + "m13_v57_co146_impedance_table.json", _MD["co146_impedance_table"]],
    "co146_pm_eval": [_S2 + "m13_v57_co146_pm_eval.json", _MD["co146_pm_eval"]],
    "co146_ledger_add": [_LED],
    "co153_k9_domain_coverage": [_LED, _REG],
    "co148_u6_datasheet_inputs": [_S2 + "m13_v57_co148_u6_ds320pr1601_inputs.json"],
    "co148_thermal_ruling": [_LED, _REG, _S2 + "m13_v57_co148_thermal_ruling.json", _MD["co148_thermal_ruling"]],
    "co149_thermal_mitigation_derive": [_LED, _REG, _S2 + "m13_v57_co149_u6_thermal_mitigation.json", _MD["co149_thermal_mitigation_derive"]],
    "co147_l2_ruling": [_REG, _S2 + "m13_v57_co147_l2_ruling.json", _MD["co147_l2_ruling"]],
    "co146_jlc_dfm_gate": [_S2 + "m13_v57_co146_jlc8_capability.json", _S2 + "m13_v57_co146_jlc_dfm_gate.json", _MD["co146_jlc_dfm_gate"]],
    "co146_jlc_fab_package": [_S2 + "m13_v57_co146_jlc_fab_package.json",
                              _A5 + "MANIFEST.json", _A5 + "ORDER_NOTES.md", _SVG],
    "co152_findings_disposition": [_REG],
    "co155_co154_findings_disposition": [_REG],
    "co156_co154_open_disposition": [_REG],
    "co157_gate_hardening_3": [_REG],
    "co158_l5_packet_selfcontained": [_REG],
    "co159_rev19_co156_co157_co158_review": [_S2 + "m13_v57_co159_rev19_co156_co157_co158_review.json", _MD["co159_rev19_co156_co157_co158_review"]],
    "co160_co159_findings_disposition": [_REG],
    "co161_gap_hardening_4": [_REG],
    "co162_verdict_binding": [_REG],
    "co163_binding_to_order_notes": [_REG],
    "co166_rev19_co159_co165_review": [_S2 + "m13_v57_co166_rev19_co159_co165_review.json", _MD["co166_rev19_co159_co165_review"]],
    "co167_co166_findings_disposition": [_REG],
    "co168_register_consistency": [_REG],
    "co169_step_output_oracle": [_REG],
    "co170_stackup_binding": [_REG],
    "co171_order_notes_record_figures": [_REG],
    "co172_rev19_co166_co171_review": [_S2 + "m13_v57_co172_rev19_co166_co171_review.json", _MD["co172_rev19_co166_co171_review"]],
    "co173_co172_findings_disposition": [_REG],
    "co174_step_artifact_attribution": [_REG],
    "co175_package_parity_binding": [_REG],
    "co176_gate_selfcheck_evidence": [_REG],
    "co177_capability_value_binding": [_REG],
    "co178_drc_item_limit_derivation": [_REG],
    "co179_sensitivity_teeth_hardening": [_REG],
    "co180_teeth_judgment_integrity": [_REG],
    "co124_input_selfcheck_gate": [_S2 + "m13_v57_co124_input_selfcheck_gate.json", _MD["co124_input_selfcheck_gate"]],
    "co150_k9_domain_gate": [_REG, _S2 + "m13_v57_co150_k9_domain_gate.json", _MD["co150_k9_domain_gate"]],
    "co146_boundary_append": [_S2 + "m13_v57_w3_joint_assignment_boundary_v1_82.md"],
    "co77_closure_declaration_sweep": [_S2 + "m13_v57_co77_closure_declaration_sweep.json"],
    "co120_provenance_pin_gate": [_S2 + "m13_v57_co120_provenance_pin_gate.json"],
    "co135_review_hygiene": [_S2 + "m13_v57_co135_review_hygiene.json", _MD["co135_review_hygiene"]],
    "co136_gate_hygiene": [_S2 + "m13_v57_co136_gate_hygiene.json", _MD["co136_gate_hygiene"]],
    "co78_layer_role_drift_gate": [_S2 + "m13_v57_co78_layer_role_drift_gate.json"],
    "co81_project_rules_gate": [_S2 + "m13_v57_co81_project_rules_gate.json"],
    "co84_dru_domain_gate": [_S2 + "m13_v57_co84_dru_domain_gate.json"],
    "co95_in4_reachability": [_S2 + "m13_v57_co95_in4_reachability.json"],
    "co98_reachability_status_report": [_S2 + "m13_v57_co98_reachability_status_report.json"],
    "co106_reference_plane_gate": [_S2 + "m13_v57_co106_reference_plane_gate.json"],
}
# CO-174 残余（如实登记）：主产物**被多步共享**时，他人对该件的写仍会被误判为「本步做了事」。
# 彻底关闭须每步写独立标记件（未做）；本表即该残余的**显式枚举**，t13c 机判防其被静默遗忘。
SHARED_ARTIFACT_RESIDUAL = {
    _LED: "共享主产物（co146_ledger_add / co153 / co148_thermal / co149）：他人写台账仍可误判",
    _REG: "共享主产物（co152..co174 处置类 17 步）：他人写登记簿仍可误判",
}

# CO-181（F-3）：**声明产物齿集 pin**（键 = 工件 basename；值 = 齿名有序集）——
# 判据不得自指：记录自定齿集 ⇒ 静默删齿/改名即可规避。任一漂移 ⇒ 该步 fail-closed（t16 机判）。
EXPECTED_TEETH = {
    "MANIFEST.json": ['t01_idempotent', 't02_8_copper_gerbers', 't03_drill_present', 't04_all_hashed', 't05_declared_rulings_packaged', 't06_order_notes_refs_resolve_in_package', 't07_packaged_rulings_match_sources', 't07b_parity_detector_sensitivity', 't08_declared_dirs_present', 't09_order_notes_binding_params', 't09b_binding_param_detector_sensitivity', 't10_declared_binding_source_pinned', 't10b_binding_source_pin_discriminates', 't11_stackup_svg_declared_binding', 't11b_stackup_svg_binding_sensitivity', 't11c_stackup_svg_copper_geometry_binding', 't11d_stackup_svg_copper_geometry_sensitivity', 't12_order_notes_record_figures', 't12b_record_figure_binding_sensitivity', 't12c_impedance_spread_binding_sensitivity', 't12d_via_census_binding_sensitivity', 't12e_mask_facts_binding_sensitivity', 't12f_thermal_figures_binding_sensitivity', 't12g_jlc_capability_binding_sensitivity', 't12h_drc_rules_edge_binding_sensitivity', 't15_impedance_copy_parity', 't15b_impedance_copy_parity_sensitivity', 't16_layer_sequence_derivation', 't16b_layer_sequence_sensitivity'],
    "m13_v57_co106_reference_plane_gate.json": ['baseline_pin_binding', 'carrier_exemption_declared_only', 'classifier_detector', 'continuity_detector', 'fail_open_closed', 'frame_inset_detector', 'teeth_are_bool_only', 'teeth_ok', 'verdict_positive_control'],
    "m13_v57_co120_provenance_pin_gate.json": ['negative_control_freetext_board_basis_rejected', 'negative_control_l5_degenerate_board_caught', 'negative_control_l5_md_board_caught', 'negative_control_l5_stale_board_caught', 'negative_control_live_state_snapshot_caught', 'negative_control_register_snapshot_caught', 'negative_control_top_level_register_snapshot_caught', 'negative_control_undeclared_snapshot_caught', 'negative_control_undeclared_stale_caught', 'negative_control_unregistered_board_sha_rejected', 'positive_control_board_sha_basis_accepted', 'positive_control_declared_live_snapshot_passes', 'positive_control_declared_register_snapshot_passes', 'positive_control_declared_snapshot_passes', 'positive_control_l5_records_pin_current_board', 'positive_control_matching_pin_passes', 'positive_control_note_key_not_snapshot', 'positive_control_upstream_input_pin_not_snapshot', 'teeth_ok'],
    "m13_v57_co124_input_selfcheck_gate.json": ['T10_thermal_option_domain_teeth', 'T10b_thermal_domain_no_false_positive', 'T11_drop_domain_teeth', 'T11b_drop_domain_no_false_positive', 'T12_declared_unpinned_teeth', 'T12b_declared_no_false_positive', 'T13_conservative_unproved_teeth', 'T13b_conservative_no_false_positive', 'T14_unknown_kind_teeth', 'T14b_empty_domain_cap_teeth', 'T14c_kind_coverage_no_false_positive', 'T15_declared_binding_teeth', 'T15b_declared_binding_no_false_positive', 'T15c_declared_empty_computed_teeth', 'T16_faithful_provenance_teeth', 'T16b_faithful_provenance_no_false_positive', 'T16c_authoritative_dv_missing_teeth', 'T17_process_floor_evidence_teeth', 'T17b_process_floor_no_false_positive', 'T18_k9_finder_id_coverage', 'T18b_k9_finder_id_no_undeclared', 'T18c_k9_finder_battery_nonempty', 'T18d_k9_finder_ids_source_complete', 'T18e_k9_finder_id_extractor_sensitivity', 'T19_dv_inventory_teeth', 'T19b_dv_inventory_no_false_positive', 'T1_netclass_drift', 'T20_identity_unhandled_form_teeth', 'T20b_identity_unhandled_no_false_positive', 'T21_register_status_vocabulary', 'T21b_register_counts_rederived', 'T21c_register_consistency_no_false_positive', 'T2_unregistered_finding_detected', 'T3_threshold_unregistered', 'T4_doc_anchor_missing', 'T5_derived_without_principle', 'T6_unreachable_derived', 'T7_requirement_carries_value', 'T8_identity_drift', 'T9_exemption_unpinned'],
    "m13_v57_co136_gate_hygiene.json": ['H4_negative_control_write_only_caught', 'H4_positive_control_upsert_ok'],
    "m13_v57_co146_impedance_table.json": ['t01_reproduce_spec_first_order', 't02_overwide_must_fail_tol'],
    "m13_v57_co146_jlc_dfm_gate.json": ['t01_track_width_limit_teeth', 't02_blind_via_item_fails', 't03_board_rule_edge_bound', 't04_capability_citation_bound', 't05_capability_citation_sensitivity', 't06_capability_value_bound', 't07_capability_value_bind_sensitivity', 't07b_anchor_localization_sensitivity', 't08_drc_item_limits_derived'],
    "m13_v57_co146_jlc_fab_package.json": ['t01_idempotent', 't02_8_copper_gerbers', 't03_drill_present', 't04_all_hashed', 't05_declared_rulings_packaged', 't06_order_notes_refs_resolve_in_package', 't07_packaged_rulings_match_sources', 't07b_parity_detector_sensitivity', 't08_declared_dirs_present', 't09_order_notes_binding_params', 't09b_binding_param_detector_sensitivity', 't10_declared_binding_source_pinned', 't10b_binding_source_pin_discriminates', 't11_stackup_svg_declared_binding', 't11b_stackup_svg_binding_sensitivity', 't11c_stackup_svg_copper_geometry_binding', 't11d_stackup_svg_copper_geometry_sensitivity', 't12_order_notes_record_figures', 't12b_record_figure_binding_sensitivity', 't12c_impedance_spread_binding_sensitivity', 't12d_via_census_binding_sensitivity', 't12e_mask_facts_binding_sensitivity', 't12f_thermal_figures_binding_sensitivity', 't12g_jlc_capability_binding_sensitivity', 't12h_drc_rules_edge_binding_sensitivity', 't15_impedance_copy_parity', 't15b_impedance_copy_parity_sensitivity', 't16_layer_sequence_derivation', 't16b_layer_sequence_sensitivity'],
    "m13_v57_co146_pm_eval.json": ['t01_current_doubling_linear', 't02_copper_thickness_monotone', 't03_plane_geometry_from_board', 't04_datasheet_input_flips_verdict', 't05_psi_route_agrees_fail'],
    "m13_v57_co147_l2_ruling.json": ['t01_mask_measured_below_jlc'],
    "m13_v57_co148_thermal_ruling.json": ['t01_worst_tj_over_limit', 't02_gnd_via_deficit'],
    "m13_v57_co148_u6_ds320pr1601_inputs.json": ['t01_seven_values', 't02_all_pact_rows'],
    "m13_v57_co149_u6_thermal_mitigation.json": ['t01_two_routes_agree', 't02_asbuilt_unreachable_all', 't03_declared_option_covers_all', 't04_rjb_more_demanding', 't05_sensitivity_disclosed'],
    "m13_v57_co150_k9_domain_gate.json": ['t01_k9_teeth_all_true', 't02_register_item_closed', 't03_ledger_domain_kinds_expected', 't04_dv_inventory_matches_producer', 't05_inventory_drift_detectable'],
    "m13_v57_co77_closure_declaration_sweep.json": ['l5_packet_citation_resolvable', 'table_row_citation_detected'],
    "m13_v57_co78_layer_role_drift_gate.json": ['control_historical_detected'],
    "m13_v57_co81_project_rules_gate.json": ['hist_netclass_detected', 'hist_rules_detected', 'min_track_width_negative_control', 'positive_control_clean', 'spec_drift_detected'],
    "m13_v57_co84_dru_domain_gate.json": ['clearance_off_detected', 'extra_area_detected', 'no_refclk_exclusion_detected', 'rect_drift_detected'],
    "m13_v57_co95_in4_reachability.json": ['band_point_flagged', 'east_point_passes'],
    "m13_v57_co98_reachability_status_report.json": ['integrity_detects_miscount', 'pip_rejects_bbox_approx'],
}


def watch_paths() -> list:
    """CO-165（t08）：受控 sha 覆盖**全部**规范序会写入的产物（边界 + 全部 co*.json 记录 + 台账/登记簿 + 打样包件）。

    CO-174：补入 `03_stackup` 叠层图 —— fab 包**直接生成**的制造输入件（此前仅被 boundary 表计 sha，
    **未**纳入收敛受控集 ⇒ fab 步静默停写该图时收敛不可见）。文本副本（04/05/06_*，均为已受控源的拷贝）
    不纳入，其一致性由 fab 牙齿 t07/t07b 把关。
    """
    out = [STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md",
           L2 / "input_defect_register_v1.json", L2 / "derived_value_ledger_v1.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/MANIFEST.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/03_stackup/JLC08161H_stackup.svg"]
    out += sorted(STEP2.glob("m13_v57_co*.json"))
    # CO-186：规范序写出的 md 卡片产物亦须入受控集（R-CO165「覆盖全部产物」）
    out += [K2 / v for v in ORDER_MD_PRODUCTS.values() if (K2 / v) not in out]
    return out


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _declared_pass_forbidden() -> bool:
    """CO-167（F-6）负控：把白名单项期望 verdict 临时改为 PASS ⇒ 必须返回 expected_verdict_pass_forbidden。"""
    key = "co146_jlc_dfm_gate"
    orig = EXPECTED_NONZERO[key]
    try:
        EXPECTED_NONZERO[key] = {**orig, "verdict": "PASS"}
        return allowlist_decision(key, 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
    finally:
        EXPECTED_NONZERO[key] = orig


def _record_snap(rec_path) -> dict:
    """CO-167（F-2）：捕获记录的产生态（存在性 + mtime_ns + 内容 sha16）。"""
    try:
        st = Path(rec_path).stat()
        return {"exists": True, "mtime_ns": st.st_mtime_ns, "sha": s16(rec_path)}
    except OSError:
        return {"exists": False, "mtime_ns": None, "sha": None}


def record_refreshed(before: dict, after: dict) -> bool:
    """CO-167（F-2）：记录须由**本次执行**产出 —— 以**变更检测**替代绝对时间比较：
    步前不存在，或 mtime_ns / 内容 sha16 任一变化即视为刷新。与时钟回拨/网络盘/异机写入无关，
    ⇒ 崩溃（未重写记录）恒判 `expected_step_record_not_produced`，不可被未来 mtime 伪「新鲜」。"""
    if not after.get("exists"):
        return False
    if not before.get("exists"):
        return True
    return after.get("mtime_ns") != before.get("mtime_ns") or after.get("sha") != before.get("sha")


def _artifact_stamp(p) -> dict | None:
    """CO-172（F-7）：受控产物的**多信号**指纹（mtime_ns + ctime_ns + size + 内容 sha16）。

    缘起（CO-169 单用 mtime_ns 的灵敏度缺口）：① 粗粒度/网络 FS 上同一时刻内重写可能**不前进**；
    ② 某步把 mtime 回写/规范化为定值（utime）而内容已变 ⇒ mtime 不变 ⇒ 被误判「未做事」而假停机；
    ③ mtime 易受系统时钟回拨/异机写入影响。加入 ctime/size/内容指纹后上述三类仍可判「做了事」。
    残余（如实登记）：**字节完全相同**的重写在粗粒度 FS 上仍与 no-op 不可分 —— 该残余只会导致
    **假停机（fail-closed）**，不会造成假通过；且收敛另由「循环至 sha 稳定」判定（R-CO164-1）。
    """
    try:
        st = p.stat()
    except OSError:
        return None
    try:
        sha = s16(p)
    except OSError:
        sha = None
    return {"mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns, "size": st.st_size, "sha16": sha}


def _snap_watched(paths=None) -> dict:
    """CO-169/CO-172/CO-174：产物集 (路径 -> 多信号指纹) 快照。

    `paths=None` ⇒ 全局受控集（收敛 sha 用，R-CO165）；传入步本地主产物集 ⇒ 步本地归因（R-CO174-1）。
    """
    ps = watch_paths() if paths is None else paths
    return {str(p): _artifact_stamp(p) for p in ps}


def step_paths(step: str) -> list:
    """CO-174（R-CO174-1）：该步**主产物集**（步本地归因用；由实测探针钉定，非猜测）。"""
    return [K2 / rel for rel in STEP_ARTIFACTS.get(step, [])]


def step_did_work(before: dict, after: dict) -> bool:
    """CO-169/CO-172：该步须**写出**至少一个受控产物（新增 / 删除 / 任一指纹信号变化）。

    `rc == 0` 本身不证明「做了事」：一个静默返回的步（早退/漏写）会因产物 sha 不变而被
    「sha 稳定 ⇒ 收敛」**背书**（与 CO-164 的教训同族，但故障类是「不崩也不写」）。
    """
    keys = set(before) | set(after)
    return any(after.get(k) != before.get(k) for k in keys)


def zero_rc_class(did_work: bool) -> str:
    """CO-169：非白名单步在 rc==0 时的分类（须真正写出受控产物）。"""
    return "ok" if did_work else "step_wrote_nothing"


def record_json_path(rec_path, keys) -> object:
    """CO-176（G-1）：从记录文件按 keys 逐层取值（缺文件/缺键/不可解析 ⇒ None）。"""
    try:
        node = json.loads(Path(rec_path).read_text(encoding="utf-8"))
    except Exception:
        return None
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return None
    return node


def teeth_all_true(node) -> bool | None:
    """CO-176（G-1）：记录内自检牙齿须**全 True**（值为 bool，或为含 `ok` 的 dict）。

    空/形状不明 ⇒ None（**fail-closed**：不可判即不通过）。
    """
    if not isinstance(node, dict) or not node:
        return None
    vals = []
    for v in node.values():
        if isinstance(v, bool):
            vals.append(v)
        elif isinstance(v, dict) and isinstance(v.get("ok"), bool):
            vals.append(v["ok"])
        else:
            return None
    return all(vals)


def _teeth_pin_negative_controls() -> bool:
    """CO-181（F-3）负控（**内存桩件、零落盘**）：pin 命中⇒True；齿集漂移 / 不可解析 / teeth_ok 冒充 ⇒ False。"""
    global step_paths
    _name = sorted(EXPECTED_TEETH)[0]
    _keys = EXPECTED_TEETH[_name]

    class _P:
        suffix = ".json"
        def __init__(self, text):
            self._t, self.name = text, _name
        def exists(self) -> bool:
            return True
        def read_text(self, encoding: str | None = None) -> str:
            if self._t is None:
                raise ValueError("injected unparsable payload")
            return self._t

    orig = step_paths
    try:
        step_paths = lambda step: [_P(json.dumps({"teeth": {k: True for k in _keys}}))]
        ok_hit = step_declared_teeth("__nc__") is True
        step_paths = lambda step: [_P(json.dumps({"teeth": {k: True for k in _keys[:-1]}}))]
        drift = step_declared_teeth("__nc__") is False
        step_paths = lambda step: [_P(None)]
        unparsable = step_declared_teeth("__nc__") is False
        step_paths = lambda step: [_P(json.dumps({"teeth_ok": True, "verdict": "PASS"}))]
        fake = step_declared_teeth("__nc__") is False
    finally:
        step_paths = orig
    return ok_hit and drift and unparsable and fake


def step_declared_teeth(step: str) -> bool | None:
    """CO-180/CO-181：该步**声明产物**中凡含 `teeth` 键者，须机判**全 True**（R-CO180-1）。

    CO-181 加固（F-2/F-3/F-4）：
      ① 声明 json **缺失 / 不可解析 / 非 dict** ⇒ **False**（`不可判一律 fail-closed`，禁静默跳过）；
      ② 齿集须**命中 `EXPECTED_TEETH` pin**（防**静默删齿 / 改名**——判据不得自指）；
      ③ 以 `teeth_ok` 冒充齿（无 `teeth` 布尔齿 dict）⇒ False（R-CO180-2 形状）。
    返回 True = 有声明齿且全 True；None = 无任何声明产物含 teeth（不适用）。
    """
    seen = False
    for p in step_paths(step):
        if getattr(p, "suffix", "") != ".json":
            continue
        if not p.exists():
            return False
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(d, dict):
            return False
        if "teeth" not in d:
            if "teeth_ok" in d:
                return False
            continue
        seen = True
        if EXPECTED_TEETH.get(p.name) != sorted(d["teeth"]):
            return False
        if teeth_all_true(d["teeth"]) is not True:
            return False
    return True if seen else None


def record_verdict(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")).get("verdict")
    except Exception:
        return None


def allowlist_decision(step: str, rc: int, stderr: str, verdict, record_fresh: bool = True,
                       teeth_ok: bool | None = None, timed_out: bool = False, decl=None) -> str:
    """CO-165 核心判据（纯函数）：
    非白名单步：rc==0 ⇒ ok，否则 unexpected_nonzero；
    白名单步：须 rc≠0 **且** 无 Traceback **且** 记录由**本次执行**产出（mtime 新鲜）
              **且** 记录 verdict == 声明 verdict
              **且** （CO-176 G-1）该步**自检牙齿全 True** ⇒ expected_nonzero；
    其余 ⇒ expected_step_* 失败（**不得把崩溃 / 未产出记录（陈旧 verdict 从盘上读取）/ 错误判决 / 自检失败当预期 FAIL**）。"""
    if timed_out:                       # CO-190（R-CO190-1）：超时优先 ⇒ fail-closed（禁以「仍在跑」冒充可判）
        return "step_timeout"
    # CO-202（L-2 / R-CO202-2）：白名单**声明面可注入**（`decl=`）⇒ 运行期**每个** return 分支（含
    # `expected_step_rc_undeclared`）均可由合成控逐分支行使；否则「当前不可达」之分支永远不可证伪。
    # 运行期调用（`decl=None`）语义不变。
    exp = EXPECTED_NONZERO.get(step) if decl is None else decl
    if exp is None:
        if rc != 0:
            return "unexpected_nonzero"
        # CO-180：非白名单步亦须**声明产物内牙齿全 True**（此前只记不判）
        if teeth_ok is False:
            return "step_teeth_failed"
        return "ok"
    if rc == 0:
        return "expected_step_returned_zero"
    # CO-199（F-1）：**rc 类语义** —— 白名单只豁免**声明的那一个** rc 值；其余非零（内部错误 / 参数错 / 其他出口）
    # 一律停机（否则「别的原因失败」会被当预期 FAIL 放行，rc 语义被架空）。
    _erc = exp.get("rc")
    if not (isinstance(_erc, int) and not isinstance(_erc, bool) and _erc != 0):
        return "expected_step_rc_undeclared"
    if rc != _erc:
        return "expected_step_rc_mismatch"
    if "Traceback (most recent call last)" in (stderr or ""):
        return "expected_step_crashed"
    # CO-201（G-1）：**预期非零出口 = 设计出口，不得伴生任何错误输出** —— 旧判据仅认 CPython 的
    # `Traceback (most recent call last)` 子串，`sys.exit("msg")` / 解释器外错误 / 库级 SystemExit 等
    # **非表头形态**的错误出口可逃逸（只要该步已把记录先落盘且 rc 恰为声明值）。此处收紧为 stderr 必须为空。
    if (stderr or "").strip():
        return "expected_step_error_output"
    if not record_fresh:
        return "expected_step_record_not_produced"
    # CO-167（F-6）：白名单不得把「成功」当预期 —— 声明的 expected verdict 为 PASS，或记录 verdict 为 PASS，
    # 均与 rc≠0 自相矛盾 ⇒ 一律停机（不得作为「预期 FAIL」放行）。
    if str(exp.get("verdict", "")).upper() == "PASS" or str(verdict or "").upper() == "PASS":
        return "expected_verdict_pass_forbidden"
    if verdict != exp.get("verdict"):
        return "expected_step_verdict_mismatch"
    # CO-176（G-1）：白名单豁免的是 **verdict**，不是该步**自检**；牙齿未全 True（含不可判）⇒ 停机
    if exp.get("teeth_path") and teeth_ok is not True:
        return "expected_step_teeth_failed"
    return "expected_nonzero"


def stable(prev: str, cur: str) -> bool:
    return bool(prev) and prev == cur


BOUNDARY = STEP2 / BOUNDARY_BASENAME


def boundary_order_steps() -> list:
    """CO-164（t06）：从 boundary 最后一条 R-COxxx-3「规范复现序」行抽取步骤名（防文档序与执行器 ORDER 漂移）。"""
    if not BOUNDARY.exists():
        return []
    _lines = BOUNDARY.read_text(encoding="utf-8").splitlines()
    _idx = [i for i, l in enumerate(_lines) if "规范复现序 =" in l]
    if not _idx:
        return []
    # CO-167（F-1）：若在最后一条可解析序行**之后**仍有其它 `规范复现序` 提及（措辞/格式变更的新式写法），
    # 说明最新序陈述不可解析 ⇒ fail-closed 返回 []（**禁止回落到更旧的序行** ⇒ 防 t06 假通过）。
    if any("规范复现序" in l for l in _lines[_idx[-1] + 1:]):
        return []
    lines = [_lines[_idx[-1]]]
    seg = lines[-1].split("规范复现序 =", 1)[1]
    out = []
    for tok in seg.replace("`", "").replace("**", "").split("→"):
        m = re.match(r"^([a-z0-9_]+)", tok.strip())   # 切掉尾注（如「，循环至 sha 稳定。」）
        t = m.group(1) if m else ""
        if re.match(r"^co\d", t):
            out.append(t)   # 不去重：`co146_boundary_append` 在序内合法出现两次
    return out



# CO-187（F-1）：**动态输入**节点集 —— 常量齿 = 值式子树**不含**任一动态输入（纯字面量/纯算符）。
_DYNAMIC_NODES = frozenset((
    "Name", "Attribute", "Subscript", "Call", "GeneratorExp", "ListComp", "DictComp", "SetComp",
    "NamedExpr", "Await", "Yield", "YieldFrom", "JoinedStr", "Lambda", "Starred",
))


def _tooth_dict_pairs(d) -> list:
    """从 Dict 字面量取 (key, value) 齿对（key 须为字面量）。"""
    out = []
    if isinstance(d, ast.Dict):
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value is not None:
                out.append((k.value, v))
    return out


def _tooth_call_pairs(c) -> list:
    """从 `dict(...)` 构造取 (key, value) 齿对（位置 Dict / 关键字实参）。"""
    out = []
    for a in c.args:
        out += _tooth_dict_pairs(a)
    for kw in c.keywords:
        if kw.arg is not None:
            out.append((kw.arg, kw.value))
        else:
            # CO-197（K-1）：关键字**解包** `dict(**{"t01": True})` —— kw.arg is None，旧式直接跳过 ⇒ 漏计。
            out += _tooth_dict_pairs(kw.value)
    return out


def teeth_hygiene_scan(src: str) -> dict:
    """CO-183/CO-187/CO-192：牙齿卫生静态扫描（AST、**只读**）——
    ① **常量齿**：值式子树**不含动态输入**（纯字面量/纯算符，含 `1 == 1`）⇒ 恒真/恒假齿候选；
    ② **提前结算**：`all/any(牙齿容器…)` 聚合之后**仍**向同一容器加齿。
    CO-187（F-1）加固**容器形态覆盖**：别名容器（`{"teeth": <Name>}`）、`AnnAssign`、`dict(...)`、
    `.update({...})`、`.setdefault(k, v)` 的下标/增量赋值一律纳扫（旧式仅认裸 `teeth` + 下标）。
    CO-192（F-1）续加固：`|=`（AugAssign）、**嵌套下标**（`rec["teeth"][k]`）、**dict 推导**、`__setitem__`、
    **Attribute 目标**（`self.teeth[k]`）、**下标赋别名**（`rec["teeth"] = <Name>`）一律纳扫。
    CO-197（K-1）续加固：关键字**解包**形态 `dict(**{...})` / `.update(**{...})`（`kw.arg is None`）一律纳扫。
    返回 {"n_teeth": int, "constant_teeth": [...], "premature_agg": [...]}。
    """
    tree = ast.parse(src)
    tooth_vars = set()          # {'teeth': <Name>} / rec["teeth"] = <Name> ⇒ 该 Name 亦为牙齿容器
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "teeth" and isinstance(v, ast.Name):
                    tooth_vars.add(v.id)
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if (isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                        and t.slice.value == "teeth" and isinstance(n.value, ast.Name)):
                    tooth_vars.add(n.value.id)

    def _is_container(node) -> bool:
        """CO-192（F-1）：牙齿容器判据改为**节点形态无关**（Name / `self.teeth` Attribute）。"""
        if isinstance(node, ast.Name):
            return node.id == "teeth" or node.id in tooth_vars
        if isinstance(node, ast.Attribute):
            return node.attr == "teeth"
        return False

    def _is_teeth_subscript(node) -> bool:
        return (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
                and node.slice.value == "teeth")

    def _key(node):
        return node.value if isinstance(node, ast.Constant) else None

    pairs, stores = [], []

    def _add(key, value, lineno):
        pairs.append((key, value)); stores.append(lineno)

    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and _is_container(t.value):
                    _add(_key(t.slice), n.value, n.lineno)
                elif isinstance(t, ast.Subscript) and _is_teeth_subscript(t.value):
                    _add(_key(t.slice), n.value, n.lineno)          # 嵌套下标 rec["teeth"][k]
                elif isinstance(t, ast.Name) and _is_container(t):
                    if isinstance(n.value, ast.Dict):
                        pairs += _tooth_dict_pairs(n.value)
                    elif isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) \
                            and n.value.func.id == "dict":
                        pairs += _tooth_call_pairs(n.value)
                    elif isinstance(n.value, ast.DictComp):
                        _add(None, n.value.value, n.lineno)         # 推导齿矩阵
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and _is_container(n.target):
            if isinstance(n.value, ast.Dict):
                pairs += _tooth_dict_pairs(n.value)
            elif isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) \
                    and n.value.func.id == "dict":
                pairs += _tooth_call_pairs(n.value)
        elif isinstance(n, ast.AugAssign):
            # `teeth |= {...}` / `rec["teeth"] |= {...}` —— 增量加齿（CO-192 F-1）
            if isinstance(n.value, ast.Dict) and (
                    (isinstance(n.target, ast.Name) and _is_container(n.target))
                    or (isinstance(n.target, ast.Subscript)
                        and (_is_container(n.target.value) or _is_teeth_subscript(n.target.value)))):
                pairs += _tooth_dict_pairs(n.value); stores.append(n.lineno)
        elif isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Attribute) and _is_container(fn.value):
                if fn.attr == "update":
                    for a in n.args:
                        if isinstance(a, ast.Dict):
                            pairs += _tooth_dict_pairs(a)
                    for kw in n.keywords:
                        if kw.arg is not None:
                            _add(kw.arg, kw.value, n.lineno)
                        else:
                            # CO-197（K-1）：`update(**{"t01": True})` 关键字解包（旧式漏计）
                            pairs += _tooth_dict_pairs(kw.value)
                    stores.append(n.lineno)
                elif fn.attr in ("setdefault", "__setitem__") and len(n.args) >= 2:
                    _add(_key(n.args[0]), n.args[1], n.lineno)
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "teeth" and isinstance(v, ast.Dict):
                    pairs += _tooth_dict_pairs(v)
    # 同一值式去重（Dict 字面量可能被多条分支命中；None 值式 = 无键聚合）
    _seen, uniq = set(), []
    for k, v in pairs:
        if v is None or id(v) in _seen:
            continue
        _seen.add(id(v)); uniq.append((k, v))
    pairs = uniq
    constant_teeth = [{"key": k, "expr": ast.unparse(v)[:60]} for k, v in pairs
                      if not ({type(x).__name__ for x in ast.walk(v)} & _DYNAMIC_NODES)]
    tooth_ids = {id(v) for _, v in pairs}
    premature_agg = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("all", "any")
                and any(isinstance(x, ast.Name) and (x.id == "teeth" or x.id in tooth_vars) for x in ast.walk(n))
                and id(n) not in tooth_ids):
            later = [ln for ln in stores if ln > n.lineno]
            if later:
                premature_agg.append({"line": n.lineno, "later_tooth_line": min(later)})
    return {"n_teeth": len(pairs), "constant_teeth": constant_teeth, "premature_agg": premature_agg}



def step_verdict(step: str):
    """CO-185：该步**声明产物**中首个携带 `verdict` 的记录值（优先步自身记录）。"""
    cands = []
    for rel in STEP_ARTIFACTS.get(step, []):
        p = K2 / rel
        if getattr(p, "suffix", "") != ".json" or not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "verdict" in d:
            own = 0 if p.name.startswith(f"m13_v57_{step}") else 1
            cands.append((own, d["verdict"]))
    if not cands:
        return None
    return min(cands, key=lambda t: t[0])[1]      # 仅按「是否步自身记录」取优，避免 verdict 间比较


def declared_verdicts(step: str) -> list:
    """CO-191：该步**全部声明产物**中携带 `verdict` 键者（(basename, verdict) 有序）。"""
    out = []
    for rel in STEP_ARTIFACTS.get(step, []):
        if not str(rel).endswith(".json"):
            continue
        p = K2 / rel
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "verdict" in d:
            out.append((p.name, d["verdict"]))
    return out


def all_verdicts_decision(step: str, verdicts=None) -> str:
    """CO-191 纯判据：**所有**声明 verdict 一律判决（非首个）——任一未声明非 PASS ⇒ `undeclared_nonpass`。"""
    vs = declared_verdicts(step) if verdicts is None else verdicts
    for _, v in vs:
        if nonpass_decision(step, v) == "undeclared_nonpass":
            return "undeclared_nonpass"
    return "ok"


def src_compiles(src: str, name: str = "<synthetic>") -> bool:
    """CO-196（**J-4**）：源文本**可编译**判据（**纯内存**，不触盘、无副作用）。

    供 t28 的**语法错分支**负控使用：以「不存在的路径」充当语法错控是**恒真**的反模式
    （缺件走的是 `FileNotFoundError`，与语法错是**不同返回路径**）。"""
    try:
        compile(src, name, "exec")
        return True
    except Exception:
        return False


def oracle_tool_ok(path) -> bool:
    """CO-195/CO-196（R-CO195-1 / R-CO196-1）：oracle **工具**可判定 —— 存在 + 可编译。

    **只判工具本体，不读其证据件**：`--check` 若以被验证证据（oracle 记录 verdict）为输入，则证据 FAIL ⇒ t28 拒 ⇒
    规范序静态前置失败 ⇒ oracle 无法运行 ⇒ 永久锁死（实测：上一案 FAIL 后 oracle 连跑 1.7s 即 `settle failed`）。
    证据件的 PASS 由 oracle 自身 + 复核清单承载。"""
    try:
        p = Path(path)
        return src_compiles(p.read_text(encoding="utf-8"), str(p))
    except Exception:
        return False


# CO-198（R-CO198-1）：**代理 ↔ 语义闸绑定**。凡**代理判据**（如键名启发式、廉价前置）代替语义判据之处，
# 须显式声明 ① 残余（**不得宣称完备**）② 承载该语义性质的外部判官（工具 + **源内声明**的齿名）③ 代理自身的
# fail-closed 齿所在记录（须在 pin 表内），并由静态齿 **t29** 机判。**不读判官证据件**（R-CO196-1：禁验证循环）。
PROXY_SEMANTIC_BINDING = {
    "co120_provenance_pin_gate": {
        "proxy": "_is_downstream_snapshot（键名启发式：`*_sha16_after` / `*_(current|live|latest|now)_sha16` / "
                 "register|ledger 容器面）",
        "residual": "**键名启发式**：更名（如 `*_state_sha16` / `*_snapshot_sha16`）或换容器名即可逃逸；判据**不判语义**"
                    "（「记录是否随文档化复现序漂移」）。**不作完备性声明**。",
        "semantic_judge": "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py",
        "semantic_teeth": ["t00_settle_converged", "t02_A_converged_and_restored", "t03_B_converged_and_restored",
                           "t04_C_converged_and_restored", "t07_no_residual_perturbation"],
        "artifact": "m13_v57_co120_provenance_pin_gate.json",
        "why": "co120 P5 为**廉价前置代理**（键名面）；其要保证的语义性质 =『复现序不动点唯一（路径无关）』，由 co195 "
               "oracle 以「扰动启动 ⇒ 收敛须复原规范态」**直接判**（R-CO195-1）；本表把该「代理↔语义闸」关系机判化。",
    },
}

# CO-215（R-CO215-1）：**代理帮助函数**（启发式/廉价前置之实现函数）之**覆盖面齿** —— 每枚须**恰**登记于
# `PROXY_SEMANTIC_BINDING`（有外部语义判官 + 其源内齿 + 代理齿在 pin 表）**或** `PROXY_RESIDUAL_EXPLICIT`
# （判官支路当前不可达时：**残余显式** + 依据 + **consumer 齿**）；二者**互斥**且完备覆盖本表。
# 值 = 消费该代理的 fail-closed 静态齿名（须为本工具源内字面量 ⇒ 机判）。
PROXY_HELPERS_PINNED = {
    "artifact_readers": "t26_judgment_binding_executable",
    # CO-216：其余两枚源面帮助函数（CO-187/CO-194 引入）一并纳入覆盖登记
    "boundary_read_scan": "t21_boundary_reader_declared",
    "declared_verdict_in_tool": "t27_basis_judge_and_verdict_binding",
}
PROXY_RESIDUAL_EXPLICIT = {
    "artifact_readers": {
        "residual": "源面**字面量上界**：① 动态构造路径（f-string / 变量 / 外部来源）⇒ **漏判**"
                    "（方向 = fail-closed：声明被判「不可执行」）；② 字面量出现于**非读取语境**"
                    "（`os.path.join` 片段 / 日志与异常文案）⇒ 仍**误判为读者**（方向 = fail-open）。**不宣称完备**。",
        "basis": "语义性质 =『该步**运行时确实读取**该工件』；直判须**运行时读观测**（本器无该机制）"
                 "⇒ 按 R-CO215-1 登记为**显式残余**，**不虚造**语义判官（R-CO198-1 之判官支路在此不可达）。",
        "deferral_trigger": "引入步骤子进程**运行时读观测**（access tracing）时，须改挂 `PROXY_SEMANTIC_BINDING` 之语义判官支路。",
    },
    # CO-216：两枚源面帮助函数（判据已收窄为 AST 形态；残余如实登记，不宣称完备）
    "boundary_read_scan": {
        "residual": "**源面形态上界**：① 以**无可匹配字面量**之完全动态方式引用 boundary 者 ⇒ **漏判**"
                    "（方向 = fail-closed：读者未被识别，t21 之等式可静默漏过）；② 引用字面量出现于**非读取语境**"
                    "（日志/映射表）而该文件恰有任意读取调用 ⇒ **误判为读者**（方向 = fail-open）。**不宣称完备**。",
        "basis": "语义性质 =『该步在**运行时确实读取** boundary 文件』；直判须**运行时读观测**（本器无）"
                 "⇒ 按 R-CO216-1 承 R-CO215-1 登记为**显式残余**，**不虚造**语义判官。",
        "deferral_trigger": "引入步骤子进程**运行时读观测**（access tracing）时，须改挂 `PROXY_SEMANTIC_BINDING` 之语义判官支路。",
    },
    "declared_verdict_in_tool": {
        "residual": "**字面量上界**：字面量出现 ≠ 该工具**能产出**该 verdict（工具可以动态拼接 verdict、或含字面量却永不产出）"
                    "⇒ 本判据只否证「源内毫无该字面量」，**不宣称**能力等价。",
        "basis": "语义性质 =『该步工具**实际可产出**其声明之 verdict』；直判须**运行时出口观测** ⇒ 按 R-CO216-1 承 R-CO215-1 登记为**显式残余**。",
        "deferral_trigger": "引入步骤出口观测（子进程 verdict/rc 采样矩阵）时，须改挂 `PROXY_SEMANTIC_BINDING` 之语义判官支路。",
    },
}


# CO-218（R-CO218-1）：**冻结源**（判定基据之锚点）—— 路径（K2 相对）→ sha16 pin。
# 缘起：跨会话仅由人手复核 + CO-91.2 一次性断言 ⇒ 漂移不使序失败（序消费当下内容仍可收敛）⇒ 基据失锚。
FROZEN_SOURCES = {
    "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
    "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
    "_shared/eda_core/drc_rules.json": "0a459839e15960b8",
}
# CO-91.2 之「规则源唯一性」：下列副本须与首个路径**同字节**（原为一次性断言 ⇒ 现入机判）。
FROZEN_SRC_COPIES = {
    "_shared/eda_core/drc_rules.json": "../_shared/eda_core/drc_rules.json",
}


def frozen_sources_decision(pins, sha16_of, copies=None, bytes_of=None) -> str:
    """CO-218（R-CO218-1）纯判据：**冻结源不变性 + 规则源唯一性**（`sha16_of`/`bytes_of` 可注入 ⇒ 合成控零落盘）。

    返回 `ok` / `frozen_source_missing`（不可读）/ `frozen_source_drift`（sha16 ≠ pin）/
    `rule_source_not_unique`（声明为同一源之副本**不同字节**）。
    """
    for rel, pin in dict(pins).items():
        try:
            got = sha16_of(rel)
        except OSError:
            return "frozen_source_missing"
        if got != pin:
            return "frozen_source_drift"
    for a, b in dict(copies or {}).items():
        try:
            if bytes_of(a) != bytes_of(b):
                return "rule_source_not_unique"
        except OSError:
            return "frozen_source_missing"
    return "ok"


def proxy_coverage_decision(helpers, declared, residual) -> str:
    """CO-215（R-CO215-1）纯判据：代理帮助函数之登记**互斥完备性**（`helpers`/`declared`/`residual` 可注入 ⇒ 合成控）。

    返回 `ok` / `no_fail_closed_tooth`（该帮助函数未 pin 消费齿）/ `helper_registration_not_exclusive`
    （两表皆无 **或** 两表皆有 = 互斥违例）/ `residual_incomplete`（残余条目缺 residual/basis/deferral_trigger）。
    """
    for h, tooth in dict(helpers).items():
        if not str(tooth or "").strip():
            return "no_fail_closed_tooth"
        in_d, in_r = h in declared, h in residual
        if in_d == in_r:
            return "helper_registration_not_exclusive"
        if in_r:
            d = residual[h]
            if not isinstance(d, dict) or not all(str(d.get(k) or "").strip()
                                                  for k in ("residual", "basis", "deferral_trigger")):
                return "residual_incomplete"
    return "ok"


def proxy_binding_decision(gate: str, decl, *, tool_ok=None, src_has=None, proxy_teeth=None) -> str:
    """CO-198（R-CO198-1）纯判据：代理判据 ↔ 语义闸绑定的**可执行性**（`tool_ok`/`src_has`/`proxy_teeth` 可注入 ⇒ 合成控）。

    返回 `ok` / `declaration_incomplete`（缺 proxy/residual/semantic_judge/semantic_teeth/artifact/why）/
    `no_semantic_judge`（判官工具不存在或不可编译）/ `semantic_tooth_undeclared`（齿名未在该判官**源内**声明）/
    `proxy_teeth_unpinned`（代理自身 fail-closed 齿未入 pin 表）。**只读判官源**，不读其证据件。
    """
    if not isinstance(decl, dict):
        return "declaration_incomplete"
    if any(not decl.get(k) for k in ("proxy", "residual", "semantic_judge", "artifact", "why")) \
            or not isinstance(decl.get("semantic_teeth"), list) or not decl["semantic_teeth"]:
        return "declaration_incomplete"
    judge = K2 / decl["semantic_judge"]
    if not (oracle_tool_ok(judge) if tool_ok is None else bool(tool_ok(judge))):
        return "no_semantic_judge"
    src = judge.read_text(encoding="utf-8") if judge.exists() else ""
    # CO-202（L-3 / R-CO202-4）：默认「源内**声明**其齿名」须以 **AST 字面量集**判 —— 原文子串 `name in src`
    # 会被**注释/散文**满足（实测：注释提及齿名即通过）⇒ 非语义判据。
    has = (lambda name: name in set(_source_strings(src))) if src_has is None else src_has
    if not all(has(x) for x in decl["semantic_teeth"]):
        return "semantic_tooth_undeclared"
    teeth = EXPECTED_TEETH.get(Path(decl["artifact"]).name, []) if proxy_teeth is None else list(proxy_teeth)
    if not any(str(x).startswith("negative_control") for x in teeth):
        return "proxy_teeth_unpinned"
    return "ok"


def all_verdicts_gate(cls: str, step: str, verdicts=None) -> tuple:
    """CO-192（F-4）：**放行档**（`ok` / `expected_nonzero`）一律施加「全声明 verdict」判决。

    CO-191 只在 `cls == "ok"` 时调 `all_verdicts_decision` ⇒ 白名单步（rc≠0 预期 FAIL）的**副**声明产物
    verdict 不被运行期判决，与 R-CO191-1「**全部**声明 verdict 一律判决」不符。返回 (cls, decision)。
    """
    if cls in ("ok", "expected_nonzero") and all_verdicts_decision(step, verdicts) == "undeclared_nonpass":
        return "undeclared_nonpass_verdict", "undeclared_nonpass"
    return cls, "ok"


def judgment_basis(step: str) -> str:
    """CO-191：该步的机判基据类别（teeth / verdict / register_consistency / downstream / none）。"""
    if step_declared_teeth(step) is not None:
        return "teeth"
    if declared_verdicts(step):
        return "verdict"
    if _REG in STEP_ARTIFACTS.get(step, []):
        return "register_consistency"
    if step in JUDGMENT_DOWNSTREAM:
        return "downstream"
    return "none"


def _source_strings(src: str) -> list:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def basis_judge_decision(category: str, decl, order=None, readers=None, judge_basis=None) -> str:
    """CO-194（R-CO194-1）纯判据：基据类别的判官**可执行性**（`order`/`readers`/`judge_basis` 可注入 ⇒ 合成控）。

    `judge=None` ⇒ 该类别由运行时自检/声明判（须给 `why`）；外部判官须：在序内 → 读被judged件（若声明 `artifact`）→
    自身有机判基据。返回 `ok` / `declaration_incomplete` / `judge_not_in_order` /
    `judge_does_not_read_artifact` / `judge_has_no_basis`。
    """
    _order = list(ORDER) if order is None else list(order)
    if not isinstance(decl, dict) or not str(decl.get("why") or "").strip():
        return "declaration_incomplete"
    judge = decl.get("judge")
    if judge is None:
        return "ok"
    if judge not in _order:
        return "judge_not_in_order"
    art = decl.get("artifact")
    if art and judge not in set(artifact_readers(art) if readers is None else readers):
        return "judge_does_not_read_artifact"
    jb = judgment_basis(judge) if judge_basis is None else judge_basis
    if not jb or jb == "none":
        return "judge_has_no_basis"
    return "ok"


def declared_verdict_in_tool(step: str, decl, src: str | None = None) -> bool:
    """CO-194（R-CO194-2）／CO-216（R-CO216-1）：`EXPECTED_NONZERO` 声明的 verdict 字面须出现在该步**工具源**（声明↔工具能力绑定）。

    判据（CO-216 收窄） = 该 verdict 出现在源的 **AST 字符串字面量集**内 —— 原判据为**原文子串** `v in src`，
    实测「注释含该词」即满足（如 `# FAIL here`）⇒ 该臂近乎空真（与 R-CO202-4 同源缺陷）。`src` 可注入 ⇒ 合成控（零落盘）。

    **残余（显式登记于 `PROXY_RESIDUAL_EXPLICIT`）**：字面量出现 ≠ 该工具**能产出**该 verdict（无运行时出口观测）。
    """
    v = str((decl or {}).get("verdict") or "").strip()
    if not v:
        return False
    if src is None:
        p = tool_path(step)
        if p is None:
            return False
        src = p.read_text(encoding="utf-8")
    return v in set(_source_strings(src))


def revision_literal_from_src(src: str, artifact: str):
    """CO-203（R-CO203-1）纯判据：AST 抽取**记录 dict 字面量**内之 `revision`（注释/散文不得满足 —— R-CO202-4）。
    返回 `(artifact 字面量存在, revision 字面量)`；不可解析 ⇒ `(False, None)`（fail-closed）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return (False, None)
    found, rev = False, None
    for n in ast.walk(tree):
        if not isinstance(n, ast.Dict):
            continue
        kv = {(k.value if isinstance(k, ast.Constant) else None):
              (v.value if isinstance(v, ast.Constant) else None) for k, v in zip(n.keys, n.values)}
        if kv.get("artifact") == artifact:
            found = True
            if isinstance(kv.get("revision"), str):
                rev = kv["revision"]
    return (found, rev)


def tool_revision_bound(rel: str, decl) -> str:
    """CO-203（R-CO203-1）：工具**自声明修订号**须等于 runner 之声明。
    返回 `ok` / `tool_missing` / `artifact_literal_absent` / `revision_absent` / `revision_mismatch`（不可判一律 fail-closed）。"""
    p = K2 / rel
    if not p.exists():
        return "tool_missing"
    _d = decl or {}
    found, rev = revision_literal_from_src(p.read_text(encoding="utf-8"), str(_d.get("artifact") or ""))
    if not found:
        return "artifact_literal_absent"
    if not rev:
        return "revision_absent"
    return "ok" if rev == _d.get("revision") else "revision_mismatch"


def artifact_readers(basename: str, sources=None) -> list:
    """CO-193（R-CO193-1）／CO-215（R-CO215-1）：源内**引用**该工件 basename 的规范序步（**语法代理**，非运行时读确认）。

    判据（CO-215 收窄） = 源内 **AST 字符串字面量集**含该 basename，**或**含可 `fnmatch` 命中的 glob 字面量
    （如 co77 经 `m13_v57_w3_joint_assignment_boundary_v1_*.md` 定位最新版 ⇒ 须计入）。**注释/散文一律不计**
    —— 原判据按**原文子串** `basename in src`，实测「注释提及 basename」即可满足（与 R-CO202-4 同源缺陷）。
    writer 亦会命中 ⇒ 作**上界**用。`sources`（step→源码）可注入 ⇒ 合成控（零落盘）。

    **残余（显式登记于 `PROXY_RESIDUAL_EXPLICIT`；不作完备性声明）**：① 以**动态构造**路径读取者**漏判**
    （方向 = fail-closed：声明被判「不可执行」）；② 字面量出现于**非读取语境**（`os.path.join` 片段 / 错误文案）
    仍可**误判为读者**（方向 = fail-open）。语义性质（运行时确实读取）须**运行时读观测**直判 —— 列为有据延后。
    """
    out = []
    for st in (sorted(sources) if sources is not None else sorted(set(ORDER))):
        if sources is None:
            p = tool_path(st)
            if p is None:
                continue
            src = p.read_text(encoding="utf-8")
        else:
            src = sources.get(st)
            if src is None:
                continue
        lits = _source_strings(src)
        if basename in lits:
            out.append(st)
            continue
        for lit in lits:
            if ("*" in lit or "?" in lit) and "/" not in lit and fnmatch.fnmatch(basename, lit):
                out.append(st)
                break
    return out


def downstream_refs_after(order: list, step: str, refs) -> bool:
    """CO-193（R-CO193-1）：**方向**判据 —— 存在 step 的某一出现位置，使其后**全部** refs 在序内。

    步可在序内多次出现（如 `co146_boundary_append`）：只要**有一次**其后覆盖全部 refs 即可（存在性）。
    """
    pos = [i for i, x in enumerate(order) if x == step]
    return any(all(r in order[i + 1:] for r in refs) for i in pos)


def judgment_downstream_binding(step: str, decl, order=None, readers=None) -> str:
    """CO-193（R-CO193-1）纯判据：下游声明**可执行性**（`order`/`readers` 可注入 ⇒ 合成控）。

    返回 `ok` / `declaration_incomplete`（缺 ref/artifact/why 或 artifact 非 basename）/
    `refs_not_downstream`（无任一出现位置在其后覆盖全部 refs）/
    `refs_not_reading_artifact`（某 ref 步工具未引用该工件 ⇒ 声明不可执行 = 静默步漂移）。
    """
    _order = list(ORDER) if order is None else list(order)
    refs = decl.get("ref") if isinstance(decl, dict) else None
    art = decl.get("artifact") if isinstance(decl, dict) else None
    if not (isinstance(refs, list) and bool(refs) and isinstance(art, str) and art.strip()
            and "/" not in art and str(decl.get("why") or "").strip()):
        return "declaration_incomplete"
    if not downstream_refs_after(_order, step, refs):
        return "refs_not_downstream"
    rd = set(artifact_readers(art) if readers is None else readers)
    if not set(refs) <= rd:
        return "refs_not_reading_artifact"
    return "ok"


def expected_nonzero_binding(step: str, decl) -> str:
    """CO-193（R-CO193-2）纯判据：白名单声明↔**本步**声明产物绑定。

    返回 `ok` / `record_not_step_artifact`（`record` 非该步 `STEP_ARTIFACTS` 之一 ⇒ 步本地归因/新鲜度测错件）/
    `teeth_path_unresolved`（`teeth_path` 缺失或在其记录内**取不到值** ⇒ 自检牙齿判据静默降级）。
    """
    arts = {Path(r).name for r in STEP_ARTIFACTS.get(step, [])}
    rec = (decl or {}).get("record")
    if rec is None or Path(rec).name not in arts:
        return "record_not_step_artifact"
    tp = (decl or {}).get("teeth_path")
    if not tp or record_json_path(rec, tp) is None:
        return "teeth_path_unresolved"
    _rc = (decl or {}).get("rc")                      # CO-199（F-1）：预期 rc 类须显式声明且非零
    if not (isinstance(_rc, int) and not isinstance(_rc, bool) and _rc != 0):
        return "rc_not_declared"
    return "ok"


def nonpass_decision(step: str, verdict) -> str:
    """CO-185（R-CO185-2）纯判据：非 PASS verdict 的**显式性**判定。

    `pass_band` = 无 verdict / PASS / PASS_WITH_FINDINGS；`declared_whitelist` = 白名单步且 verdict 与声明相符；
    `declared_nonpass` = 已在 `DECLARED_NONPASS_OK` 显式声明；`undeclared_nonpass` = **未声明的非 PASS ⇒ 停机**。
    """
    if verdict is None or verdict in PASS_VERDICTS:
        return "pass_band"
    exp = EXPECTED_NONZERO.get(step)
    if exp and verdict == exp.get("verdict"):
        return "declared_whitelist"
    dec = DECLARED_NONPASS_OK.get(step)
    if dec and verdict == dec.get("verdict"):
        return "declared_nonpass"
    return "undeclared_nonpass"


# CO-188（R-CO188-1）：**越界写 fail-closed** —— 步骤写其**未声明**的受控件 = 越界（写他步专属件）或**漏声明**
# （声明不完整）。二者都使该件变更**无人归因**；且收敛只比较 sha ⇒ **确定性**越界写（每轮同内容）可静默通过
# （`did_work` 由本步声明件决定，仍 True）⇒ 故须独立判决。合法写集 = `STEP_ARTIFACTS[step]`；
# 下表为**显式**例外（当前为空；新增须给理由 `why` + `paths`，且不得与该步声明件重叠）。
STRAY_WRITE_ALLOWED = {}


def stray_decision(step: str, stray, allowed: dict | None = None) -> str:
    """CO-188 纯判据：`stray`（相对 K2 的受控件路径）中凡不在该步声明/显式例外内者 ⇒ `stray_write`。"""
    table = STRAY_WRITE_ALLOWED if allowed is None else allowed
    allow = set((table.get(step) or {}).get("paths", []))
    return "stray_write" if (set(stray) - allow) else "ok"


# CO-189（R-CO189-1）：**受控集外写入可见性** —— 步骤在受控产物**承载根**内写**非受控件**（既非 `watch_paths()`、
# 又非显式豁免）时：不入收敛 sha、不产生 `stray` 证据（stray 只比较受控集）⇒ **完全不可见**
# （CO-186 只覆盖 md 卡片、CO-188 只覆盖受控集**内**越界）。shadow 用 **stat 轻量指纹**（mtime/ctime/size、不哈希）
# ⇒ 承载根 ~1.8k 件可逐步快照。
WRITE_SHADOW_ROOT = K2 / "pm_gate/artifacts/k2_v4"
# 显式豁免（**实测钉定** @ CO-189：全序实测仅 `co146_jlc_fab_package` 在受控集外写 32 件、全在打样包内）：
# 这些件由**受控 `MANIFEST.json` 逐文件 sha256 覆盖**（其 `manifest` 键 34 件）⇒ 任何变更经 MANIFEST sha 可见。
WRITE_SHADOW_EXEMPT = (
    {"prefix": "pm_gate/artifacts/k2_v4/L5/jlc_package/01_gerber_rs274x", "covered_by": "MANIFEST.json",
     "why": "Gerber 输出（fab 步生成；逐文件 sha 由受控 MANIFEST.json 覆盖）"},
    {"prefix": "pm_gate/artifacts/k2_v4/L5/jlc_package/02_drill_excellon", "covered_by": "MANIFEST.json",
     "why": "Excellon 钻孔 + 图（同上）"},
    {"prefix": "pm_gate/artifacts/k2_v4/L5/jlc_package/04_impedance", "covered_by": "MANIFEST.json",
     "why": "阻抗表副本（MANIFEST 覆盖 + fab 齿 t15 与受控源逐字节 parity）"},
    {"prefix": "pm_gate/artifacts/k2_v4/L5/jlc_package/05_layer_sequence.txt", "covered_by": "MANIFEST.json",
     "why": "叠层次序派生件（MANIFEST 覆盖 + fab 齿 t16 由冻结 SPEC 重算 parity）"},
    {"prefix": "pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings", "covered_by": "MANIFEST.json",
     "why": "裁定副本（MANIFEST 覆盖 + fab 齿 t07 与受控源逐字节 parity）"},
)


def shadow_paths() -> list:
    """CO-189：承载根内全部文件（相对 K2 posix），供 stat 轻量快照。"""
    return sorted(p.relative_to(K2).as_posix() for p in WRITE_SHADOW_ROOT.rglob("*") if p.is_file())


def write_shadow_snapshot() -> dict:
    """CO-189：`{rel_posix: (mtime_ns, ctime_ns, size)}`（**stat 轻量**，不哈希）。"""
    out = {}
    for p in WRITE_SHADOW_ROOT.rglob("*"):
        if not p.is_file():
            continue
        st = p.stat()
        out[p.relative_to(K2).as_posix()] = (st.st_mtime_ns, st.st_ctime_ns, st.st_size)
    return out


def shadow_exempt(rel: str, table=None) -> bool:
    """CO-189：`rel` 是否落入显式豁免前缀（`rel == prefix` 或其子路径）。"""
    for e in (WRITE_SHADOW_EXEMPT if table is None else table):
        pre = str(e.get("prefix") or "").rstrip("/")
        if pre and (rel == pre or rel.startswith(pre + "/")):
            return True
    return False


def uncontrolled_decision(changes, exempt=None) -> str:
    """CO-189 纯判据：承载根内、受控集外的变更若不在豁免内 ⇒ `uncontrolled_write`。"""
    return "uncontrolled_write" if any(not shadow_exempt(c, exempt) for c in changes) else "ok"



def md_write_scan(src: str) -> list:
    """CO-186/CO-187/CO-192：静态提取该工具 **`.md` 写/拷目标**（模块级 Name 常量一并解析）。

    覆盖面（CO-187 F-2 加固）：`write_text`/`write_bytes`、写模式 `open(...)`、`shutil.copy*` 的**目的**参数。
    CO-192（F-2）续加固：`Path.open(w)`、`shutil.move`、`os.replace`/`os.rename` 的**目的**参数。
    CO-197（K-2）续加固：`io.open(<md>, "w")`、`Path(...)`/路径别名 `.replace|rename(<md>)` 的**目的**参数。
    仅看**写**上下文 ⇒ 只读引用（BASIC_SKILL_VS_REDLINE / boundary 读取 / 只读 open）不误报。
    """
    tree = ast.parse(src)
    namemap = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            for c in ast.walk(n.value):
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value.endswith(".md"):
                    namemap[n.targets[0].id] = Path(c.value).name

    # CO-197（K-2）：`Path(...)`/`pathlib.Path(...)` 构造及其**模块级别名** ⇒ `X.replace/rename(<md>)` 纳扫
    _pathvars = set()
    for n in ast.walk(tree):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and isinstance(n.value, ast.Call)
                and ((isinstance(n.value.func, ast.Name) and n.value.func.id == "Path")
                     or (isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "Path"))):
            _pathvars.add(n.targets[0].id)

    def _is_path_ctor(node) -> bool:
        """`Path(...)` / `pathlib.Path(...)` 调用，或绑定该构造的模块级名（CO-197 K-2）。

        只认**路径构造**接收者 ⇒ `"a.md".replace(".md","")` 之类字符串操作**不**误报。"""
        if isinstance(node, ast.Name):
            return node.id in _pathvars
        return (isinstance(node, ast.Call)
                and ((isinstance(node.func, ast.Name) and node.func.id == "Path")
                     or (isinstance(node.func, ast.Attribute) and node.func.attr == "Path")))

    def _target_name(node):
        if isinstance(node, ast.Name) and node.id in namemap:
            return namemap[node.id]
        for c in ast.walk(node):
            if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value.endswith(".md"):
                return Path(c.value).name
        return None

    def _is_write_mode(nodes) -> bool:
        return any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                   and any(ch in a.value for ch in "wax+") for a in nodes)

    found = set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        if isinstance(fn, ast.Attribute) and fn.attr in ("write_text", "write_bytes"):
            nm = _target_name(fn.value)
            if nm:
                found.add(nm)
        elif isinstance(fn, ast.Name) and fn.id == "open" and n.args:
            if _is_write_mode(n.args[1:]):
                nm = _target_name(n.args[0])
                if nm:
                    found.add(nm)
        elif (isinstance(fn, ast.Attribute) and fn.attr == "open" and isinstance(fn.value, ast.Name)
                and fn.value.id == "io" and n.args):
            if _is_write_mode(n.args[1:]):                    # CO-197（K-2）：io.open(<md>, "w")
                nm = _target_name(n.args[0])
                if nm:
                    found.add(nm)
        elif isinstance(fn, ast.Attribute) and fn.attr == "open" and _is_write_mode(n.args):
            nm = _target_name(fn.value)                      # CO-192（F-2）：Path.open(w)
            if nm:
                found.add(nm)
        elif isinstance(fn, ast.Attribute) and fn.attr in ("copy", "copy2", "copyfile", "move") and len(n.args) >= 2:
            nm = _target_name(n.args[1])
            if nm:
                found.add(nm)
        elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "os" \
                and fn.attr in ("replace", "rename") and len(n.args) >= 2:
            nm = _target_name(n.args[1])                     # CO-192（F-2）：os.replace/rename 目的
            if nm:
                found.add(nm)
        elif isinstance(fn, ast.Attribute) and fn.attr in ("replace", "rename") \
                and _is_path_ctor(fn.value) and n.args:
            nm = _target_name(n.args[0])                     # CO-197（K-2）：Path(...).replace|rename(目的)
            if nm:
                found.add(nm)
    return sorted(found)


# CO-187（F-3）：工具源是否**读取** boundary（引用 boundary 名/族 + 有读取调用）。
_BOUNDARY_REF_RE = re.compile(r"w3_joint_assignment_boundary|_latest_boundary")
# CO-216（R-CO216-1）：读取指标以 **AST 形态**判（属性名/调用），**不得**以原文子串判（注释可伪造）。
READ_ATTRS = ("read_text", "read_bytes", "read", "readline", "readlines")


def _boundary_ref_ast(tree) -> bool:
    """引用面（CO-216）：AST **字面量**（族正则命中）**或** `_latest_boundary` **标识符** —— 注释/散文不能伪造。"""
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and _BOUNDARY_REF_RE.search(n.value):
            return True
        if isinstance(n, ast.Name) and n.id == "_latest_boundary":
            return True
        if isinstance(n, ast.Attribute) and n.attr == "_latest_boundary":
            return True
    return False


def _read_shape_ast(tree) -> bool:
    """读取面（CO-216）：`Attribute.attr ∈ READ_ATTRS` 或 `io.open(...)` 调用（CO-192 之开口/read 形态同覆盖）。"""
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in READ_ATTRS:
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "open" \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "io":
            return True
    return False


def boundary_read_scan(src: str) -> bool:
    """CO-187（F-3）/ CO-192（F-3）／CO-216（R-CO216-1）：工具源是否**读取** boundary。

    判据（CO-216 收窄为 AST 形态） = **引用**（字面量命中族正则，或 `_latest_boundary` 标识符）
    **且 读取**（`Attribute.attr ∈ READ_ATTRS`，或 `io.open` 调用）。仅引用 boundary 名（写/常量）**不**计读取者。
    原判据为 `re` 扫**原文** + `read_text` 等**原文子串** ⇒ **注释即可伪造引用与读取**（CO-216 实测复现）。

    **残余（显式登记于 `PROXY_RESIDUAL_EXPLICIT`）**：① 以**无可匹配字面量**之完全动态方式引用者**漏判**
    （方向 = fail-closed：读者未被识别 ⇒ t21 之等式可静默漏过）；② 字面量出现于**非读取语境**而该文件恰有
    任意读取调用者**误判为读者**（方向 = fail-open）。**不宣称完备**。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    return _boundary_ref_ast(tree) and _read_shape_ast(tree)


def boundary_readers() -> list:
    out = []
    for s in sorted(set(ORDER)):
        p = tool_path(s)
        if p is not None and boundary_read_scan(p.read_text(encoding="utf-8")):
            out.append(s)
    return out


def tool_path(step: str) -> Path | None:
    direct = K2 / "tools" / f"p3_v57_{step}.py"
    if direct.exists():
        return direct
    cands = sorted((K2 / "tools").glob(f"p3_v57_{step}*.py"))
    return cands[0] if len(cands) == 1 else None


def snapshot() -> str:
    h = hashlib.sha256()
    for p in watch_paths():
        h.update(p.read_bytes() if p.exists() else b"<missing>")
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="静态体检（不执行、不落盘）")
    ap.add_argument("--max-iter", type=int, default=5)
    a = ap.parse_args(argv)
    checks = {}
    # 静态体检：步骤文件存在 + 可编译 + rc 策略声明齐备
    missing, uncompilable = [], []
    for step in sorted(set(ORDER)):
        p = tool_path(step)
        if p is None:
            missing.append(step); continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except SyntaxError as e:
            uncompilable.append(f"{step}: {e}")
    checks["t01_steps_exist"] = not missing
    checks["t02_steps_compile"] = not uncompilable
    checks["t03_expected_nonzero_policy_declared"] = set(EXPECTED_NONZERO) <= set(ORDER)
    checks["t04_unexpected_nonzero_detected"] = (
        allowlist_decision("co78_layer_role_drift_gate", 1, "", None) == "unexpected_nonzero"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS") == "ok")
    # CO-165（t07）：白名单步的**伪通过**必须被拒（崩溃 / 意外归零 / verdict 不符 / 缺证据）
    checks["t07_allowlist_evidence_enforced"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "Traceback (most recent call last):\n", "FAIL", True) == "expected_step_crashed"
        and allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True) == "expected_step_returned_zero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "INDETERMINATE", True) == "expected_step_verdict_mismatch"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", False) == "expected_step_record_not_produced"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
        and all(("verdict" in v and "record" in v) for v in EXPECTED_NONZERO.values())
        and all(str(v.get("verdict", "")).upper() != "PASS" for v in EXPECTED_NONZERO.values())
        # 注入「声明 PASS」的临时白名单项 ⇒ 必须被禁（F-6 声明面）
        and _declared_pass_forbidden())
    # CO-165（t08）：受控 sha 覆盖全部记录类产物（非窄清单）
    _w = [p.as_posix() for p in watch_paths()]
    checks["t08_watch_covers_records"] = (len(_w) >= 20
                                          and any(p.endswith("m13_v57_co106_reference_plane_gate.json") for p in _w)
                                          and any(p.endswith("jlc_package/MANIFEST.json") for p in _w)
                                          # CO-174：fab 直接生成的制造输入件（叠层图）亦须在受控集内
                                          and any(p.endswith("03_stackup/JLC08161H_stackup.svg") for p in _w))
    # CO-167（F-3）：白名单记录必须 ⊆ 受控集（防未来白名单项指向 glob 外件 ⇒ 收敛盲区）
    checks["t09_allowlist_records_watched"] = (
        bool(EXPECTED_NONZERO)
        and {Path(v["record"]).resolve() for v in EXPECTED_NONZERO.values()}
            <= {p.resolve() for p in watch_paths()})
    # CO-167（F-2）：刷新判据为**变更检测**（拒未重写的陈旧记录，含未来 mtime）
    checks["t10_record_refresh_change_detection"] = (
        record_refreshed({"exists": False, "mtime_ns": None, "sha": None}, {"exists": True, "mtime_ns": 5, "sha": "a"})
        and record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": True, "mtime_ns": 2, "sha": "a"})
        and not record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": True, "mtime_ns": 1, "sha": "a"})
        and not record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": False, "mtime_ns": None, "sha": None}))
    # CO-169（G-1）：非白名单步 rc==0 亦须**真正写出**受控产物（禁「静默 no-op 步」被收敛背书）
    checks["t11_step_output_oracle"] = (
        step_did_work({"a": 1}, {"a": 2})                  # mtime 前进 ⇒ 做了事
        and (not step_did_work({"a": 1}, {"a": 1}))        # 零变动 ⇒ 未做事
        and step_did_work({"a": 1}, {"a": 1, "b": 7})      # 新增受控产物
        and step_did_work({"a": 1}, {"a": None})           # 产物被删/失联
        and zero_rc_class(True) == "ok" and zero_rc_class(False) == "step_wrote_nothing")
    # CO-172（F-7）：快照须为**多信号**（mtime 不变而内容/ctime/size 变 ⇒ 仍须判「做了事」）
    _s0 = {"mtime_ns": 1, "ctime_ns": 1, "size": 5, "sha16": "a"}
    checks["t12_watched_snapshot_multisignal"] = (
        step_did_work({"p": _s0}, {"p": {**_s0, "sha16": "b"}})                    # 内容变、mtime 未动
        and step_did_work({"p": _s0}, {"p": {**_s0, "ctime_ns": 9}})              # ctime 前进
        and step_did_work({"p": _s0}, {"p": {**_s0, "size": 6}})                  # size 变
        and not step_did_work({"p": _s0}, {"p": dict(_s0)}))                      # 全同 ⇒ 未做事
    # CO-174（G-1）：每步须声明**主产物集**（步本地归因；禁全局集合代为背书）
    _watch = {p.resolve() for p in watch_paths()}
    checks["t13_step_artifacts_declared"] = (
        set(ORDER) <= set(STEP_ARTIFACTS)
        and all(STEP_ARTIFACTS[s] for s in set(ORDER))
        and all((K2 / rel).resolve() in _watch for s in STEP_ARTIFACTS for rel in STEP_ARTIFACTS[s]))
    # CO-174（G-1）负控：快照**只含**本步声明集 —— 非声明受控件的变动**不得**归因于本步
    _demo = next(s for s in ORDER if len(step_paths(s)) == 1)
    _dp = step_paths(_demo)
    _dps = {str(q) for q in _dp}
    _other = {str(q) for q in watch_paths() if str(q) not in _dps}
    _s0 = {"mtime_ns": 1, "ctime_ns": 1, "size": 5, "sha16": "a"}
    checks["t13b_step_local_attribution"] = (
        bool(_dp) and bool(_other)
        and set(_snap_watched(_dp)) == _dps                                  # 快照仅声明集 ⇒ 无 strays
        and not (set(_snap_watched(_dp)) & _other)
        and step_did_work({_dp[0].as_posix(): _s0}, {_dp[0].as_posix(): {**_s0, "sha16": "b"}})
        and not step_did_work({_dp[0].as_posix(): _s0}, {_dp[0].as_posix(): dict(_s0)}))
    # CO-174（G-1）残余如实登记：共享主产物须**显式枚举**（防静默遗忘；新增共享件即 fail）
    _shared = [rel for s in STEP_ARTIFACTS for rel in STEP_ARTIFACTS[s]]
    _multi = sorted({rel for rel in _shared if _shared.count(rel) > 1})
    checks["t13c_shared_artifact_residual_enumerated"] = (_multi == sorted(SHARED_ARTIFACT_RESIDUAL))
    # CO-176（G-1）：白名单步**自检牙齿**须机判全 True —— 正控/负控/形状不明 fail-closed
    checks["t14_allowlist_teeth_enforced"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True,
                           teeth_all_true({"t01": {"ok": True}})) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True,
                               teeth_all_true({"t01": {"ok": False}})) == "expected_step_teeth_failed"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, None) == "expected_step_teeth_failed"
        and all("teeth_path" in v for v in EXPECTED_NONZERO.values())
        and teeth_all_true({"t": True, "u": {"ok": True}}) is True
        and teeth_all_true({"t": True, "u": {"ok": False}}) is False
        and teeth_all_true({}) is None and teeth_all_true({"t": 1}) is None and teeth_all_true("x") is None)
    # CO-180：步骤**声明产物牙齿**须纳入判决（含非白名单步）—— 正控/负控/不适用（None）
    checks["t15_step_declared_teeth_enforced"] = (
        allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, False) == "step_teeth_failed"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, True) == "ok"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, None) == "ok"
        and allowlist_decision("co77_closure_declaration_sweep", 1, "", None, True, False) == "unexpected_nonzero"
        # 现状普查：声明产物含 teeth 的步骤须**全为 True**（co78 散文 teeth 之类即在此被抓）
        and step_declared_teeth("co146_jlc_fab_package") is True
        and step_declared_teeth("co146_boundary_append") is None
        and step_declared_teeth("co146_ledger_add") is None
        and sum(1 for s in set(ORDER) if step_declared_teeth(s) is True) >= 13
        and sum(1 for s in set(ORDER) if step_declared_teeth(s) is False) == 0)
    # CO-181（F-3）：齿集 pin 覆盖一致 + fail-closed（不可判/删齿/改名/teeth_ok 冒充一律不通过）
    _decl_teeth = set()
    for _s in set(ORDER):
        for _r in STEP_ARTIFACTS.get(_s, []):
            if not str(_r).endswith(".json"):
                continue
            try:
                _d = json.loads((K2 / _r).read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(_d, dict) and "teeth" in _d:
                _decl_teeth.add(Path(_r).name)
    checks["t16_teeth_set_pinned"] = (
        set(EXPECTED_TEETH) == _decl_teeth
        and all(step_declared_teeth(s) is not False for s in set(ORDER))
        and step_declared_teeth("__UNKNOWN__") is None
        and _teeth_pin_negative_controls())
    # CO-182（R-CO182-1）：boundary citation 扫描步须**紧跟**boundary 刷新步（消除一轮 pin 滞后）
    _gi = [i for i, s in enumerate(ORDER) if s in BOUNDARY_SCAN_GUARDED]
    checks["t17_boundary_scan_follows_refresh"] = (
        len(_gi) == len(BOUNDARY_SCAN_GUARDED)
        and all(i > 0 and ORDER[i - 1] == BOUNDARY_REFRESH_STEP for i in _gi))
    # CO-183（R-CO183-1）/ CO-187（F-1）：牙齿卫生**棘轮**（常量齿 / 提前结算）—— 合成正负控 + 现行零违规 + 齿数下限
    _p_good = 'def f(d):\n    teeth={}\n    teeth["t01"]=d["a"]>0\n    teeth["t02"]=all(isinstance(v,bool) for v in teeth.values())\n    return all(teeth.values())\n'
    _p_const = 'def f(d):\n    teeth={"t01":True,"t02":d["a"]>0}\n    return all(teeth.values())\n'
    _p_prem = 'def f(d):\n    teeth={"t01":d["a"]>0}\n    ok=all(teeth.values())\n    teeth["t02"]=d["b"]>0\n    return ok\n'
    _p_foreign = 'def f(c):\n    teeth=c.get("teeth",{})\n    ok=all(teeth.get(k) is True for k in ("a",))\n    rec={"teeth":{"t01":ok}}\n    return rec\n'
    # CO-187（F-1）：容器形态一律须纳扫（别名下标 / update / AnnAssign / dict(...) / 字面恒真式）
    _p_alias = 'def f(d):\n    tooth={"a":d["x"]>0}\n    rec={"teeth":tooth}\n    tooth["t01"]=True\n    return rec\n'
    _p_upd = 'def f():\n    teeth={}\n    teeth.update({"t01":True})\n    return teeth\n'
    _p_ann = 'def f():\n    teeth: dict={"t01":True}\n    return teeth\n'
    _p_dictc = 'def f():\n    teeth=dict(t01=True)\n    return teeth\n'
    _p_setd = 'def f():\n    teeth={}\n    teeth.setdefault("t01",True)\n    return teeth\n'
    _p_lit = 'def f(d):\n    teeth={"t01":(1==1),"t02":d["a"]>0}\n    return teeth\n'
    # CO-192（F-1）：续加固形态一律须纳扫（`|=` / 嵌套下标 / dict 推导 / __setitem__ / Attribute / 下标赋别名）
    _p_192 = [
        'def f():\n    teeth={}\n    teeth |= {"t01": True}\n    return teeth\n',
        'def f():\n    rec={"teeth":{}}\n    rec["teeth"]["t01"]=True\n    return rec\n',
        'def f(ks):\n    teeth={k: True for k in ks}\n    return teeth\n',
        'def f():\n    teeth={}\n    teeth.__setitem__("t01", True)\n    return teeth\n',
        'def f(self):\n    self.teeth["t01"]=True\n    return self.teeth\n',
        'TEETH={"t01":True}\ndef f():\n    rec={}\n    rec["teeth"]=TEETH\n    return rec\n',
        # CO-197（K-1）：关键字**解包**形态（kw.arg is None）亦须纳扫 —— dict(**{...}) / update(**{...})
        'def f():\n    teeth=dict(**{"t01": True})\n    return teeth\n',
        'def f():\n    teeth={}\n    teeth.update(**{"t01": True})\n    return teeth\n',
    ]
    _ev192 = [teeth_hygiene_scan(x) for x in _p_192]
    _g = teeth_hygiene_scan(_p_good); _c = teeth_hygiene_scan(_p_const)
    _m = teeth_hygiene_scan(_p_prem); _f = teeth_hygiene_scan(_p_foreign)
    _ev = [teeth_hygiene_scan(x) for x in (_p_alias, _p_upd, _p_ann, _p_dictc, _p_setd)]
    _scan_ok = (not _g["constant_teeth"] and not _g["premature_agg"]
                and len(_c["constant_teeth"]) == 1 and not _c["premature_agg"]
                and len(_m["premature_agg"]) == 1 and not _f["constant_teeth"] and not _f["premature_agg"]
                and all([x["key"] for x in r["constant_teeth"]] == ["t01"] for r in _ev)
                and [x["key"] for x in teeth_hygiene_scan(_p_lit)["constant_teeth"]] == ["t01"]
                and all(r["n_teeth"] >= 1 and r["constant_teeth"] for r in _ev192))
    _own = {}
    for _s in set(ORDER):
        for _r in STEP_ARTIFACTS.get(_s, []):
            if Path(_r).name in EXPECTED_TEETH:
                _tp = tool_path(_s)
                if _tp is not None:
                    _own[Path(_r).name] = _tp
    _scan_by_tool = {q.name: teeth_hygiene_scan(q.read_text(encoding="utf-8")) for q in set(_own.values())}
    _floor_by_tool = {}
    for _art, _tp in _own.items():
        _floor_by_tool[_tp.name] = max(_floor_by_tool.get(_tp.name, 0), len(EXPECTED_TEETH[_art]))
    checks["t18_teeth_hygiene_ratchet"] = (
        _scan_ok and set(_own) == set(EXPECTED_TEETH)
        and all(_scan_by_tool[k]["n_teeth"] >= v for k, v in _floor_by_tool.items())   # CO-187（F-1）：漏计即停机
        and sum(v["n_teeth"] for v in _scan_by_tool.values()) >= 100
        and all(not v["constant_teeth"] and not v["premature_agg"] for v in _scan_by_tool.values()))
    # CO-185（R-CO185-2）：非 PASS verdict 类别须显式声明（白名单 ∪ DECLARED_NONPASS_OK）且互斥、有依据
    checks["t19_nonpass_verdict_declared"] = (
        not (set(EXPECTED_NONZERO) & set(DECLARED_NONPASS_OK))
        and all(str(v.get("verdict", "")).strip() and str(v.get("why", "")).strip()
                and str(v.get("register", "")).strip() for v in DECLARED_NONPASS_OK.values())
        and all(v["verdict"] not in PASS_VERDICTS for v in DECLARED_NONPASS_OK.values())
        # 合成正/负控：未声明的非 PASS 必被截；已声明的白名单/非 PASS 放行；PASS 档放行
        and nonpass_decision("__undeclared__", "FAIL") == "undeclared_nonpass"
        and nonpass_decision("co146_pm_eval", "FAIL") == "declared_nonpass"
        and nonpass_decision("co146_jlc_dfm_gate", "FAIL") == "declared_whitelist"
        and nonpass_decision("__x__", "PASS") == "pass_band"
        and nonpass_decision("__x__", None) == "pass_band"
        # 现状：全序各步的记录 verdict 均属通过档或已声明
        and all(nonpass_decision(s, step_verdict(s)) != "undeclared_nonpass" for s in set(ORDER))
        # CO-191：**全部**声明 verdict 亦须零未声明（非首个）
        and all(all_verdicts_decision(s) != "undeclared_nonpass" for s in set(ORDER)))
    # CO-186（R-CO186-1）/ CO-187（F-2）：规范序 md 产物须**全部受控**（pin ∪ 显式豁免）**且步本地声明**
    _md_scan = {_s: md_write_scan(_tp.read_text(encoding="utf-8"))
                for _s in set(ORDER) if (_tp := tool_path(_s)) is not None}
    _md_found = {b for v in _md_scan.values() for b in v}
    _md_pin = {Path(v).name for v in ORDER_MD_PRODUCTS.values()}
    _md_exempt = set(ORDER_MD_PRODUCT_EXEMPT)
    checks["t20_order_md_products_controlled"] = (
        set(ORDER_MD_PRODUCTS) == {_s for _s, v in _md_scan.items() if set(v) - _md_exempt}
        and _md_found - _md_exempt == _md_pin
        and _md_found & _md_exempt == _md_exempt
        and _md_pin.isdisjoint(_md_exempt)
        and all(str(e.get("why") or "").strip() for e in ORDER_MD_PRODUCT_EXEMPT.values())
        and all(e["covered_by"] in EXPECTED_TEETH["m13_v57_co146_jlc_fab_package.json"]
                for e in ORDER_MD_PRODUCT_EXEMPT.values())          # 豁免须绑定**实存**补偿牙齿
        and _md_pin <= {q.name for q in watch_paths()}
        and all((K2 / v).exists() for v in ORDER_MD_PRODUCTS.values())
        and all(Path(v).name in {q.name for q in step_paths(_s)} for _s, v in ORDER_MD_PRODUCTS.items())
        # 合成正/负控：写/拷上下文必被抽出；只读引用不得误报
        and md_write_scan('CARD = S2 / "probe.md"\nCARD.write_text("x")') == ["probe.md"]
        and md_write_scan('(STEP2 / "inline.md").write_text("x")') == ["inline.md"]
        and md_write_scan('open("probe.md","w").write("x")') == ["probe.md"]
        and md_write_scan('shutil.copy(S2 / "a.md", OUT / "imp/table.md")') == ["table.md"]
        and md_write_scan('x = (STEP2 / "read_only.md").read_text()\n') == []
        and md_write_scan('open("ro.md").read()\n') == []
        # CO-192（F-2）：Path.open(w) / shutil.move / os.replace|rename 目的亦须纳扫
        and md_write_scan('CARD = S2 / "x.md"\nf = CARD.open("w")') == ["x.md"]
        and md_write_scan('shutil.move(S2 / "a.md", OUT / "b.md")') == ["b.md"]
        and md_write_scan('os.replace(S2 / "a.md", OUT / "b.md")') == ["b.md"]
        and md_write_scan('CARD = S2 / "x.md"\nf = CARD.open("r")') == []
        # CO-197（K-2）：io.open(w) / Path(...).replace|rename 目的亦须纳扫；只读 / 非 .md 目的不得误报
        and md_write_scan('import io\nf = io.open("probe.md","w")') == ["probe.md"]
        and md_write_scan('Path("a.md").replace("dst.md")') == ["dst.md"]
        and md_write_scan('P = Path("a.md")\nP.rename("dst.md")') == ["dst.md"]
        and md_write_scan('import io\nf = io.open("ro.md")') == []
        and md_write_scan('Path("a.md").replace("b.txt")') == []
        and md_write_scan('s = "a.md".replace(".md", "")') == [])
    # CO-187（F-3）：读取 boundary 的步须**显式归类**（扫描步 ⇒ 紧跟刷新；非扫描步 ⇒ 声明理由）—— t21
    checks["t21_boundary_reader_declared"] = (
        set(boundary_readers()) == (set(BOUNDARY_SCAN_GUARDED) | set(BOUNDARY_READ_DECLARED))
        and set(BOUNDARY_SCAN_GUARDED).isdisjoint(BOUNDARY_READ_DECLARED)
        and set(BOUNDARY_READ_DECLARED) <= set(ORDER)
        and all(str(v).strip() for v in BOUNDARY_READ_DECLARED.values())
        # 合成正/负控：读 boundary ⇒ True；只读他件 / 仅写 boundary / 无 read ⇒ False
        and boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"\nt = DOC.read_text()')
        and boundary_read_scan('B = _latest_boundary()\nx = B.read_bytes()')
        and not boundary_read_scan('x = (STEP2 / "other.md").read_text()')
        and not boundary_read_scan('DOC.write_text("x")')
        and not boundary_read_scan('BOUNDARY_STEP = "co146_boundary_append"\n')
        # CO-192（F-3）：Path.open().read() / io.open(...).read() 形态亦须计入读取者
        and boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"\nt = DOC.open().read()')
        and boundary_read_scan('B = _latest_boundary()\nt = io.open(B).read()')
        # CO-216（R-CO216-1）：**注释/散文不得伪造**引用与读取（AST 形态判据）
        and not boundary_read_scan('# w3_joint_assignment_boundary  （仅注释）\n# read_text\n')
        and boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"  # read_text\nt = DOC.read_bytes()')
        and not boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"\n')
        # 残余如实登记（方向）：无匹配字面量之动态引用 ⇒ 漏判（fail-closed）；不作完备性声明
        and not boundary_read_scan('DOC = base / suffix\nt = DOC.read_text()\n'))
    # CO-188（R-CO188-1）：越界写（stray）须 fail-closed；显式例外表须完备（键/理由/受控/不与声明重叠）
    _watch_abs = {p.as_posix() for p in watch_paths()}
    _stray_tbl_ok = all(
        k in set(ORDER) and isinstance(v, dict) and str(v.get("why") or "").strip()
        and isinstance(v.get("paths"), list)
        and set(v["paths"]) <= _watch_abs
        and not (set(v["paths"]) & set(STEP_ARTIFACTS.get(k, [])))
        for k, v in STRAY_WRITE_ALLOWED.items())
    checks["t22_stray_write_fail_closed"] = (
        _stray_tbl_ok
        and stray_decision("__s__", []) == "ok"
        and stray_decision("__s__", ["a/b.json"]) == "stray_write"
        and stray_decision("__s__", ["a/b.json"], {"__s__": {"paths": ["a/b.json"], "why": "w"}}) == "ok"
        and stray_decision("__s__", ["a/b.json", "c.json"],
                           {"__s__": {"paths": ["a/b.json"], "why": "w"}}) == "stray_write")
    # CO-189（R-CO189-1）：受控集外写入可见性 —— shadow 根须 ⊇ 受控集；豁免表完备；纯判据正负控
    _shadow_root_ok = all(str(p).startswith(str(WRITE_SHADOW_ROOT) + "/") for p in watch_paths())
    _cov_ok = ({q.name for q in watch_paths()} | {t for v in EXPECTED_TEETH.values() for t in v})
    _exp_ok = all(
        isinstance(e, dict) and str(e.get("prefix") or "").strip() and str(e.get("why") or "").strip()
        and str(e.get("covered_by") or "").strip() and e["covered_by"] in _cov_ok
        and (K2 / e["prefix"]).exists()
        for e in WRITE_SHADOW_EXEMPT)
    checks["t23_write_shadow_visible"] = (
        _shadow_root_ok and _exp_ok
        and uncontrolled_decision([]) == "ok"
        and uncontrolled_decision(["pm_gate/artifacts/k2_v4/L9_none/x.json"]) == "uncontrolled_write"
        and uncontrolled_decision(["pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings/a.md"]) == "ok"
        and uncontrolled_decision(["pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings/a.md",
                                   "pm_gate/artifacts/k2_v4/elsewhere.json"]) == "uncontrolled_write"
        and shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/01_gerber_rs274x/x.gbr")
        and shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/05_layer_sequence.txt")
        and not shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/07_new/x.txt")
        # CO-201（G-2）：豁免前缀的**段边界**分支须有负控（防回归为裸 `startswith(pre)` ⇒ 兄弟路径被误豁免）
        and shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings/sub/a.md")
        and not shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulingsX/a.md")
        and not shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/05_layer_sequence.txtX"))
    # CO-190（R-CO190-1）：步骤超时须 fail-closed（正控 timed_out ⇒ step_timeout；负控 ⇒ 不误报；超时值须在带内）
    checks["t24_step_timeout_fail_closed"] = (
        isinstance(STEP_TIMEOUT_S, int) and 60 <= STEP_TIMEOUT_S <= 3600
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS", True, None, True) == "step_timeout"
        and allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True, True, True) == "step_timeout"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS") == "ok"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True, False) == "expected_nonzero")
    # CO-191（R-CO191-1）：判定基据完备性 —— 每步须有可机判基据（禁静默步；下游声明须有理由且指向在序步）
    _basis = {s: judgment_basis(s) for s in set(ORDER)}
    _dn_ok = all(str(v.get("why") or "").strip() and isinstance(v.get("ref"), list) and bool(v["ref"])
                 and set(v["ref"]) <= set(ORDER) for v in JUDGMENT_DOWNSTREAM.values())
    checks["t25_judgment_basis_declared"] = (
        all(b != "none" for b in _basis.values())
        and set(JUDGMENT_DOWNSTREAM) <= set(ORDER) and _dn_ok
        # 合成正/负控：多产物 verdict 全判（隐藏的非 PASS 必被截；全通过档不误报）
        and all_verdicts_decision("__nc__", [("a", "PASS"), ("b", "FAIL")]) == "undeclared_nonpass"
        and all_verdicts_decision("__nc__", [("a", "PASS"), ("b", "PASS_WITH_FINDINGS")]) == "ok"
        and all_verdicts_decision("co146_pm_eval", [("x", "FAIL")]) == "ok")   # 已声明非 PASS 放行
    # CO-192（F-4）：**放行档**（ok / expected_nonzero）一律判全 verdict（白名单步副 verdict 不得逃逸）
    checks["t25_judgment_basis_declared"] = checks["t25_judgment_basis_declared"] and (
        # 白名单步：副 verdict 须为**不同于**其声明 FAIL 的非 PASS 值（同值属 declared_whitelist，不可分）
        all_verdicts_gate("expected_nonzero", "co146_jlc_dfm_gate", [("a", "PASS"), ("b", "ERROR")])
        == ("undeclared_nonpass_verdict", "undeclared_nonpass")
        and all_verdicts_gate("expected_nonzero", "co146_jlc_dfm_gate", [("a", "PASS")])
        == ("expected_nonzero", "ok")
        and all_verdicts_gate("ok", "__x__", [("a", "FAIL")])
        == ("undeclared_nonpass_verdict", "undeclared_nonpass")
        and all_verdicts_gate("ok", "co146_pm_eval", [("x", "FAIL")]) == ("ok", "ok")
        and all_verdicts_gate("step_timeout", "co146_jlc_dfm_gate", [("a", "ERROR")])
        == ("step_timeout", "ok"))
    # CO-193（R-CO193-1/2）：下游声明**可执行** + 白名单证据**本步绑定** —— 静态齿 t26
    _dn_bind = {k: judgment_downstream_binding(k, v) for k, v in JUDGMENT_DOWNSTREAM.items()}
    _exp_bind = {k: expected_nonzero_binding(k, v) for k, v in EXPECTED_NONZERO.items()}
    checks["t26_judgment_binding_executable"] = (
        all(v == "ok" for v in _dn_bind.values()) and all(v == "ok" for v in _exp_bind.values())
        # 合成正控：方向对 + ref 读工件 ⇒ ok
        and judgment_downstream_binding("S", {"ref": ["A"], "artifact": "x.md", "why": "w"},
                                        order=["S", "A"], readers=["A"]) == "ok"
        # 合成负控：方向错（ref 在上游）
        and judgment_downstream_binding("S", {"ref": ["A"], "artifact": "x.md", "why": "w"},
                                        order=["A", "S"], readers=["A"]) == "refs_not_downstream"
        # 合成负控：不可执行（ref 工具不引用工件）
        and judgment_downstream_binding("S", {"ref": ["A"], "artifact": "x.md", "why": "w"},
                                        order=["S", "A"], readers=["B"]) == "refs_not_reading_artifact"
        # 合成负控：声明不完整（缺 artifact）
        and judgment_downstream_binding("S", {"ref": ["A"], "why": "w"},
                                        order=["S", "A"], readers=["A"]) == "declaration_incomplete"
        # 多次出现存在性：S 在第 0/2 位，ref 仅在末次之后 ⇒ ok
        and judgment_downstream_binding("S", {"ref": ["A"], "artifact": "x.md", "why": "w"},
                                        order=["S", "B", "S", "A"], readers=["A"]) == "ok"
        # 白名单证据绑定：正控 + 负控（record 非本步声明 / teeth_path 不可解析）
        and expected_nonzero_binding("co146_jlc_dfm_gate", EXPECTED_NONZERO["co146_jlc_dfm_gate"]) == "ok"
        and expected_nonzero_binding("co146_jlc_dfm_gate",
                                     {"record": str(STEP2 / "m13_v57_co146_impedance_table.json"),
                                      "teeth_path": ["teeth"]}) == "record_not_step_artifact"
        and expected_nonzero_binding("co146_jlc_dfm_gate",
                                     {**EXPECTED_NONZERO["co146_jlc_dfm_gate"],
                                      "teeth_path": ["nope"]}) == "teeth_path_unresolved"
        # CO-215（R-CO215-1）：**注释/散文不得满足**「该步读取该工件」（AST 字面量集；原文子串判据实测被注释满足）
        and artifact_readers("x.md", sources={"S": "# x.md  （仅注释，非读取）\n"}) == []
        and artifact_readers("x.md", sources={"S": "p = ROOT / 'x.md'\n"}) == ["S"]
        and artifact_readers("x_v1.md", sources={"S": "g = 'x_*.md'\n"}) == ["S"]
        # 残余如实登记（方向）：动态构造 ⇒ 漏判（fail-closed）；不作完备性声明
        and artifact_readers("x.md", sources={"S": "p = f'{pre}/x.md'\n"}) == [])
    # CO-194（R-CO194-1/2）：基据↔判官绑定 + 白名单声明↔工具源绑定 —— 静态齿 t27
    _bj = {c: basis_judge_decision(c, d) for c, d in BASIS_JUDGE_DECLARED.items()}
    checks["t27_basis_judge_and_verdict_binding"] = (
        set(BASIS_JUDGE_DECLARED) == {"teeth", "verdict", "register_consistency", "downstream"}
        and all(v == "ok" for v in _bj.values())
        and all(declared_verdict_in_tool(s, v) for s, v in EXPECTED_NONZERO.items())
        # CO-216（R-CO216-1）：**注释含 verdict 字面不得满足**（AST 字面量集；原原文子串判据此处近乎空真）
        and declared_verdict_in_tool('S', {'verdict': 'FAIL'}, src='# FAIL  （仅注释）\n') is False
        and declared_verdict_in_tool('S', {'verdict': 'FAIL'}, src='v = "FAIL"\n') is True
        and declared_verdict_in_tool('S', {'verdict': 'FAIL'}, src='') is False
        # 合成正控：外部判官在序 + 读件 + 自身有基据 ⇒ ok；judge=None 类别给 why ⇒ ok
        and basis_judge_decision("x", {"judge": "J", "artifact": "a.json", "why": "w"},
                                 order=["J"], readers=["J"], judge_basis="teeth") == "ok"
        and basis_judge_decision("x", {"judge": None, "why": "w"}) == "ok"
        # 合成负控：判官不在序 / 不读件 / 自身无基据 / 声明不完整
        and basis_judge_decision("x", {"judge": "J", "artifact": "a.json", "why": "w"},
                                 order=["K"], readers=["J"], judge_basis="teeth") == "judge_not_in_order"
        and basis_judge_decision("x", {"judge": "J", "artifact": "a.json", "why": "w"},
                                 order=["J"], readers=["K"], judge_basis="teeth") == "judge_does_not_read_artifact"
        and basis_judge_decision("x", {"judge": "J", "artifact": "a.json", "why": "w"},
                                 order=["J"], readers=["J"], judge_basis="none") == "judge_has_no_basis"
        and basis_judge_decision("x", {"judge": "J"}) == "declaration_incomplete"
        # 声明↔工具绑定负控：工具不可能产出的 verdict 不得通过
        and not declared_verdict_in_tool("co146_jlc_dfm_gate", {"verdict": "TOTALLY_BROKEN"}))
    # CO-195/CO-196（R-CO195-1 / R-CO196-1）：固定点唯一性 oracle 工具**存在 + 可编译** —— **不读其证据件**（禁验证循环）
    _oracle = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
    checks["t28_fixpoint_uniqueness_oracle"] = (
        oracle_tool_ok(_oracle)
        # CO-196（J-4）：合成控须**逐返回路径可证伪**，且**与证据件内容无关**。
        #   缺件分支（FileNotFoundError）→ `not oracle_tool_ok(<不存在>)`；
        #   语法错分支（SyntaxError）→ `not src_compiles(<内存非法源>)` —— 用**内存**合成源，
        #   不得以「不存在的路径」冒充语法错控（旧版恒真：该文件在任何规范态下都不存在）。
        and not oracle_tool_ok(K2 / "tools/__no_such_oracle__.py")
        and not src_compiles("def (:", "<synthetic_syntax_error>")
        and src_compiles("x = 1", "<synthetic_ok>")
        # CO-202（L-1 / R-CO202-1）：谓词**自身**之逐返回路径控 —— 「存在但不可编译」与「类型错」各一
        # （旧控只把「语法错」挂在共享子程序 `src_compiles` 上 ⇒ 谓词之编译失败**传播**不可证伪）。
        and _NONCOMPILE_PROBE.exists()
        and not src_compiles(_NONCOMPILE_PROBE.read_text(encoding="utf-8"), _NONCOMPILE_PROBE.name)
        and oracle_tool_ok(_NONCOMPILE_PROBE) is False
        and oracle_tool_ok(None) is False)
    # CO-198（R-CO198-1）：代理 ↔ 语义闸绑定须机判（残余显式 + 外部语义判官存在且**源内声明**其齿 + 代理齿在 pin 表）
    _pj = "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
    _pbase = {"proxy": "p", "residual": "r（非完备）", "semantic_judge": _pj,
              "semantic_teeth": ["t00_settle_converged"], "artifact": "m13_v57_co120_provenance_pin_gate.json", "why": "w"}
    checks["t29_proxy_semantic_binding"] = (
        set(PROXY_SEMANTIC_BINDING) <= set(ORDER)
        and all(proxy_binding_decision(g, d) == "ok" for g, d in PROXY_SEMANTIC_BINDING.items())
        # 合成正/负控（可证伪；只涉**结构性事实**，R-CO196-1）
        and proxy_binding_decision("__nc__", dict(_pbase)) == "ok"
        and proxy_binding_decision("__nc__", {"residual": "r"}) == "declaration_incomplete"
        and proxy_binding_decision("__nc__", {**_pbase, "residual": ""}) == "declaration_incomplete"
        and proxy_binding_decision("__nc__", {**_pbase, "semantic_teeth": []}) == "declaration_incomplete"
        and proxy_binding_decision("__nc__", _pbase, tool_ok=lambda _p: False) == "no_semantic_judge"
        and proxy_binding_decision("__nc__", {**_pbase, "semantic_teeth": ["__no_such_tooth__"]}) == "semantic_tooth_undeclared"
        and proxy_binding_decision("__nc__", _pbase, proxy_teeth=[]) == "proxy_teeth_unpinned"
        # CO-202（L-3 / R-CO202-4）：**注释/散文不得满足**「源内声明」（AST 字面量集之判别力）
        and "t00_settle_converged" not in set(_source_strings("# t00_settle_converged  （仅注释，非声明）"))
        and "t00_settle_converged" in set(_source_strings("t = {'t00_settle_converged': False}"))
        # CO-215（R-CO215-1）：代理帮助函数**覆盖面** —— 每枚须恰登记于一表；残余条目字段须完备
        and proxy_coverage_decision(PROXY_HELPERS_PINNED, PROXY_SEMANTIC_BINDING, PROXY_RESIDUAL_EXPLICIT) == "ok"
        and set(PROXY_HELPERS_PINNED.values()) <= set(
            _source_strings(Path(__file__).read_text(encoding="utf-8")))
        and proxy_coverage_decision({"h": "t26"}, {"h": 1}, {}) == "ok"
        and proxy_coverage_decision({"h": "t26"}, {}, {"h": {"residual": "r", "basis": "b", "deferral_trigger": "t"}}) == "ok"
        and proxy_coverage_decision({"h": "t26"}, {}, {}) == "helper_registration_not_exclusive"
        and proxy_coverage_decision({"h": "t26"}, {"h": 1}, {"h": {}}) == "helper_registration_not_exclusive"
        and proxy_coverage_decision({"h": "t26"}, {}, {"h": {"residual": "r", "basis": "b"}}) == "residual_incomplete"
        and proxy_coverage_decision({"h": ""}, {}, {}) == "no_fail_closed_tooth")
    # CO-199（F-1）：白名单须声明**预期 rc 类**（rc≠0 不等于预期 FAIL —— 别的原因失败须停机）
    _d199 = dict(EXPECTED_NONZERO["co146_jlc_dfm_gate"])
    checks["t30_expected_nonzero_rc_class"] = (
        all(isinstance(d.get("rc"), int) and not isinstance(d.get("rc"), bool) and d["rc"] != 0
            for d in EXPECTED_NONZERO.values())
        and all(expected_nonzero_binding(s, d) == "ok" for s, d in EXPECTED_NONZERO.items())
        # 声明面负控：rc 缺失 / rc=0（「成功」不得充当预期）⇒ rc_not_declared
        and expected_nonzero_binding("co146_jlc_dfm_gate", {**_d199, "rc": 0}) == "rc_not_declared"
        and expected_nonzero_binding("co146_jlc_dfm_gate", {k: v for k, v in _d199.items() if k != "rc"}) == "rc_not_declared"
        # 运行期正/负控：声明 rc 匹配 ⇒ 放行；其余非零 ⇒ 停机；rc=0 ⇒ 停机
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 2, "", "FAIL", True, True) == "expected_step_rc_mismatch"
        and allowlist_decision("co146_jlc_dfm_gate", 127, "", "FAIL", True, True) == "expected_step_rc_mismatch"
        and allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True, True) == "expected_step_returned_zero"
        # CO-202（L-2 / R-CO202-2）：**运行期**分支 `expected_step_rc_undeclared` 须由可注入声明面行使
        and allowlist_decision("__nc_rc__", 1, "", "FAIL", True, True, False,
                               {k: v for k, v in _d199.items() if k != "rc"}) == "expected_step_rc_undeclared"
        and allowlist_decision("__nc_rc__", 1, "", "FAIL", True, True, False,
                               {**_d199, "rc": 0}) == "expected_step_rc_undeclared")
    # CO-201（G-1）：白名单**预期非零出口**须**无错误输出**（设计出口 vs 错误路径的机判面）
    checks["t31_expected_nonzero_error_free"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "Error: boom\n", "FAIL", True, True)
            == "expected_step_error_output"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "Traceback (most recent call last):\n", "FAIL", True, True)
            == "expected_step_crashed"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "   \n", "FAIL", True, True) == "expected_nonzero")
    # CO-202（L-4 / R-CO202-3）：受控集产物**类别数** == oracle 扰动量类别数（逐类别 ≥1 案）
    # （R-CO200-1「覆盖面 = 类别数」之机判面：新增/既有类别未被 oracle 扰动量覆盖 ⇒ 停机）
    try:
        _orc = types.ModuleType("oracle_probe")
        _orc.__file__ = str(ORACLE_TOOL)
        exec(compile(ORACLE_TOOL.read_text(encoding="utf-8"), str(ORACLE_TOOL), "exec"), _orc.__dict__)
        _case_cat = {Path(t).suffix for _c in _orc.CASES for t in _c["targets"]}
        checks["t32_oracle_category_coverage"] = bool(_case_cat) and {p.suffix for p in watch_paths()} <= _case_cat
    except Exception:
        checks["t32_oracle_category_coverage"] = False   # fail-closed（不可判即不通过）
    # CO-203（R-CO203-1）：工具**自声明修订号**须与 runner 之声明一致（内容升级而自声明滞留 ⇒ 停机）
    _orc_rel = "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
    _oc = "m13_v57_co195_fixpoint_uniqueness"
    checks["t33_tool_revision_bound"] = (
        set(TOOL_REVISION_DECLARED) == {_orc_rel}
        and all(tool_revision_bound(k, d) == "ok" for k, d in TOOL_REVISION_DECLARED.items())
        # 正控：AST 字面量抽取（dict 内 revision）
        and revision_literal_from_src('D = {"artifact": "%s", "revision": "CO-202"}' % _oc, _oc) == (True, "CO-202")
        # 负控：自声明不符 / artifact 字面量缺失 / 工具缺失
        and tool_revision_bound(_orc_rel, {"artifact": _oc, "revision": "CO-999"}) == "revision_mismatch"
        and tool_revision_bound(_orc_rel, {"artifact": "__absent__", "revision": "CO-202"}) == "artifact_literal_absent"
        and tool_revision_bound("tools/__no_such_tool__.py", {"artifact": _oc, "revision": "CO-202"}) == "tool_missing"
        # 判别力控（承 R-CO202-4）：注释/散文提及修订号与 artifact 名**不得**满足（AST 无 dict 字面 ⇒ 不可抽）
        and revision_literal_from_src('"""revision: CO-202（仅散文，非声明）"""\n# artifact: %s' % _oc, _oc) == (False, None))
    # CO-218（R-CO218-1）：**冻结源不变性 + 规则源唯一性**须机判（原仅人手复核 + CO-91.2 一次性断言）
    _fs_sha = lambda rel: hashlib.sha256((K2 / rel).read_bytes()).hexdigest()[:16]        # noqa: E731
    _fs_bytes = lambda rel: (K2 / rel).read_bytes()                                      # noqa: E731

    def _fs_raise(_rel):
        raise OSError("synthetic-missing")

    checks["t34_frozen_sources_pinned"] = (
        frozen_sources_decision(FROZEN_SOURCES, _fs_sha, FROZEN_SRC_COPIES, _fs_bytes) == "ok"
        # 正控：pin 命中 ⇒ ok；副本同字节 ⇒ ok
        and frozen_sources_decision({"a": "x"}, lambda _r: "x") == "ok"
        and frozen_sources_decision({}, lambda _r: "x", {"a": "b"}, lambda _r: b"same") == "ok"
        # 负控：sha 漂移 / 缺件 / 副本不同字节
        and frozen_sources_decision({"a": "x"}, lambda _r: "y") == "frozen_source_drift"
        and frozen_sources_decision({"a": "x"}, _fs_raise) == "frozen_source_missing"
        and frozen_sources_decision({}, lambda _r: "x", {"a": "b"},
                                    lambda r: b"1" if r == "a" else b"2") == "rule_source_not_unique")
    checks["t05_stability_oracle"] = (stable("x", "x") and not stable("x", "y") and not stable("", ""))
    # CO-164（t06）：执行器 ORDER 必须与 boundary 规范复现序**有序一致**（文档↔执行器防漂移）
    _bdy = boundary_order_steps()
    checks["t06_order_matches_boundary"] = bool(_bdy) and _bdy == ORDER
    static_ok = all(checks.values())
    if a.check:
        print(json.dumps({"mode": "check", "checks": checks, "missing": missing,
                          "uncompilable": uncompilable, "ok": static_ok}, ensure_ascii=False, indent=1))
        return 0 if static_ok else 1
    if not static_ok:
        print(json.dumps({"mode": "run", "aborted": "static_precheck_failed", "checks": checks,
                          "missing": missing, "uncompilable": uncompilable}, ensure_ascii=False, indent=1))
        return 1
    # ── 执行：每轮逐步跑，rc 不合规立即停机 ─────────────────────────────────
    iterations, abort = [], None
    prev = ""
    converged = False
    _watched_rel = {p.relative_to(K2).as_posix() for p in watch_paths()}
    for it in range(1, a.max_iter + 1):
        rcs, unexpected = {}, None
        _sh_prev = write_shadow_snapshot()   # CO-189：承载根 stat 快照（跨步复用：上步 after = 本步 before）
        for step in ORDER:
            p = tool_path(step)
            _exp = EXPECTED_NONZERO.get(step) or {}
            _before = _record_snap(_exp["record"]) if _exp.get("record") else None
            # CO-174（G-1）：did_work 归因**仅限本步主产物集**（禁全局集合代为背书）
            _decl_set = {str(q) for q in step_paths(step)}
            _ball = _snap_watched()                                            # 全局：仅用于 stray 证据
            _w_before = {k: _ball.get(k) for k in _decl_set}
            _t0 = time.monotonic()
            try:                            # CO-190（R-CO190-1）：步骤须在 STEP_TIMEOUT_S 内结束；超时 ⇒ 杀子进程 + 停机
                r = subprocess.run([str(PY), str(p)], cwd=K2, capture_output=True, text=True,
                                   timeout=STEP_TIMEOUT_S)
                _to, _rc, _err = False, r.returncode, r.stderr
            except subprocess.TimeoutExpired:
                _to, _rc, _err = True, None, f"STEP_TIMEOUT after {STEP_TIMEOUT_S}s"
            _dur = round(time.monotonic() - _t0, 3)
            _aall = _snap_watched()
            _sh_cur = write_shadow_snapshot()                          # CO-189
            _sh_changes = sorted(rel for rel in set(_sh_prev) | set(_sh_cur)
                                 if _sh_prev.get(rel) != _sh_cur.get(rel) and rel not in _watched_rel)
            _w_after = {k: _aall.get(k) for k in _decl_set}
            _did = step_did_work(_w_before, _w_after)                          # 步本地归因（CO-174）
            # CO-167（F-2）：变更检测（非绝对 mtime）
            _fresh = record_refreshed(_before, _record_snap(_exp["record"])) if _exp.get("record") else True
            # CO-176（G-1）：白名单步**自检牙齿**须机判全 True；CO-180：**全部步骤**的**声明产物牙齿**亦然
            _tcand = []
            if _exp.get("teeth_path"):
                _tcand.append(teeth_all_true(record_json_path(_exp["record"], _exp["teeth_path"])))
            _tcand.append(step_declared_teeth(step))
            _tcand = [c for c in _tcand if c is not None]
            _teeth_ok = all(_tcand) if _tcand else None
            cls = allowlist_decision(step, _rc, _err, record_verdict(_exp.get("record")),
                                     _fresh, _teeth_ok, _to)
            _stray = sorted(Path(k).relative_to(K2).as_posix()
                            for k in set(_ball) | set(_aall)
                            if k not in _decl_set and _ball.get(k) != _aall.get(k))
            # CO-185（R-CO185-2）+ CO-191（R-CO191-1）+ CO-192（F-4）：**全部**声明 verdict 一律判决
            # （放行档 `ok` **与** `expected_nonzero` 均判；禁只判首个、禁白名单步副 verdict 逃逸）
            cls, _ = all_verdicts_gate(cls, step)
            # CO-188（R-CO188-1）：越界写（未声明受控件）⇒ 停机（确定性越界写不破收敛、亦不被步本地归因抓到）
            if cls in ("ok", "expected_nonzero") and _stray and stray_decision(step, _stray) != "ok":
                cls = "stray_write"
            # CO-189（R-CO189-1）：承载根内、受控集外的写（非豁免）⇒ 停机（不入 sha、不产生 stray ⇒ 完全不可见）
            if cls in ("ok", "expected_nonzero") and uncontrolled_decision(_sh_changes) != "ok":
                cls = "uncontrolled_write"
            if cls == "ok" and not _did:
                cls = zero_rc_class(False)     # CO-169（G-1）：rc==0 但未写出任何受控产物 ⇒ 立即停机
            rcs[step] = {"rc": _rc, "class": cls, "did_work": _did,
                         "duration_s": _dur, "timed_out": _to,
                         "declared_changed": sorted(Path(k).relative_to(K2).as_posix()
                                                    for k in _decl_set if _w_before.get(k) != _w_after.get(k)),
                         "stray_changed": _stray,
                         "uncontrolled_writes": [c for c in _sh_changes if not shadow_exempt(c)]}
            _sh_prev = _sh_cur
            if cls not in ("ok", "expected_nonzero"):
                unexpected = {"step": step, "rc": _rc, "class": cls, "timed_out": _to,
                              "stderr_tail": (_err or "")[-600:]}
                break
        cur = snapshot()
        iterations.append({"iter": it, "rcs": rcs, "sha": cur, "unexpected": unexpected})
        if unexpected:
            abort = unexpected
            break
        if stable(prev, cur):
            converged = True
            break
        prev = cur
    report = {"artifact": "m13_v57_co164_order_runner_report", "schema": 1, "revision": "CO-203.1",
              "nature": "规范复现序机判执行器（rc 策略 + 真收敛判定）；报告落 .archer_tmp/ 且**不被 boundary 引用**（避免不动点）",
              "order": ORDER, "expected_nonzero": EXPECTED_NONZERO,
              "checks": checks, "iterations": iterations, "abort": abort, "converged": converged,
              # CO-218：冻结源证据块（判定基据之锚点解析结果；报告不参与 pin 表）
              "frozen_sources": {
                  "pins": FROZEN_SOURCES,
                  "resolved": {rel: (hashlib.sha256((K2 / rel).read_bytes()).hexdigest()[:16]
                                     if (K2 / rel).exists() else None) for rel in FROZEN_SOURCES},
                  "copy_uniqueness": {a: {"peer": b,
                                          "identical": ((K2 / a).read_bytes() == (K2 / b).read_bytes()
                                                        if (K2 / a).exists() and (K2 / b).exists() else None)}
                                      for a, b in FROZEN_SRC_COPIES.items()}},
              "watched": [str(p.relative_to(K2)) for p in watch_paths()],
              "redline": "只读工具源；执行序内写记录/边界（即规范序本身）；本报告不参与 pin 表。"}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "run", "converged": converged, "abort": abort,
                      "iterations": len(iterations), "checks": checks,
                      "report": str(REPORT.relative_to(K2))}, ensure_ascii=False, indent=1))
    return 0 if (converged and not abort) else 1


if __name__ == "__main__":
    sys.exit(main())
