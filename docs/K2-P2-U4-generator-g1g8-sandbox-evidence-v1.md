# §五 生成器改造 G1–G8 · 沙箱干跑证据 + E4 判据（**未安装**）v1

- **依据**：#K2-12 §五（**改生成器源码已放行**，6 硬约束 + 停机条款）、handoff §7.4（**S1 放行后**执行 G1–G8）。
- **性质**：**沙箱证据，未改仓**。改动施加在 `/tmp` 副本（`k2_gen_v5.gfix.draft.py`）；**仓内 `k2/tools/k2_gen_v5.py` 一字未动**（sha16 `7577a15a76a09a22`），SPEC/图/板/`criteria/` 未动，未派 WORKER。
- **结论（一句话）**：**G1–G8 在沙箱内全部落地并跑通**，§五 基线三处阻断（板框 → `anchor_fixes` → `capacitor_walls`）全部消除，**E4 三项判据全 PASS**，产物 KiCad 解析零 DRC 违规；**待 S1 放行后原样粘贴入仓**。

## 1. 方法（只读真源 + `/tmp` 副本 + 3 个沙箱钩子）

| # | 钩子 | 作用 |
|---|---|---|
| H1 | `K2_GEN_ROOT` | 副本在 `/tmp` ⇒ `ROOT`（`__file__` 推导）失效；显式指向 `k2/` |
| H2 | `K2_SPEC_PATH` | S1 未放行 ⇒ 用 `/tmp/opencode/k2p1/SPEC_dryrun_r21.json`（rev-21 草案）驱动 |
| H3 | template 路径 | `k2_jlc_template.kicad_pro` 改用 `ROOT/tools/` 解析（副本不在 `k2/tools/`） |

- **禁硬编码未被破坏**：H2 仅叠加在**已实现 G2 的出口处**；G2 本体仍 = `pm_gate.config.spec_name()` + `artifacts.path("L3", …)`，实测解析到 `…/L3/SPEC_k2_v4.spec-rev-20.json`。
- 输出：`K2_OUT_PCB=/tmp/opencode/gen_a/k2_v6.kicad_pcb`、`K2_OUT_JSON=…/k2_v6_layout.json`（**只写 `/tmp`**）。

## 2. G1–G8 落点（§五 要求 → 沙箱实现）

| # | §五 要求 | 沙箱实现 | 落点 |
|---|---|---|---|
| G1 | 板框 → 46mm `[33,79]` | `BOARD y=[33.0, 79.0]` | `:47` |
| G2 | SPEC 路径经 `pm_gate.config` 解析 | `_ARTIFACTS.path("L3", _PMCFG.spec_name())`（+ H2 钩子） | `:40` |
| G3 | `K2_REFS` → 真源导出（单颗 `U6`，42 件；**禁字面表**） | 新增 `_derive_k2_refs_from_true_source(PCB_REF_PATH)`：解析真源板 `Reference` 属性得 refdes 集 | `:54–65` |
| G4 | 移除 `OLD_REF_MAP` 双颗重映射 | `OLD_REF_MAP = {}`（行为等同移除：两处查表自然落空） | `:114`（`:238,:325` 随之失效） |
| G5 | 移除 `DS160PR810` 热焊盘 `pad 65` 特判 | 删该 3 行 | `:355` |
| G6 | 移除 `check_ac_caps`（6L 死代码） | 删函数体 + S3 注册 + main 内 AC 墙摘要打印 | `:584–598, :846` |
| G7 | `apply_spec_overrides` 移除 `capacitor_walls` 段、**保留** `anchor_fixes` 严格校验 | 切掉 `cw = spec["capacitor_walls"] …` 段，保留 `pin_headers` + `anchor_fixes` 严格校验 | `:633–673` |
| G8 | 移除 S7 `check_ac_pitch` | 删函数体 + S7 注册 | `:677–700` |

- 沙箱 diff 规模：**+25 / −93 行**（867 → 799 行）。
- 沙箱特有附带（不入仓）：`MISSING_REFS = []`（`K2_REFS` 现由真源板导出，无「补齐」概念）。

## 3. E4 判据结果（§五 ⑥）

| # | 判据 | 结果 |
|---|---|---|
| ① | `K2_OUT_PCB` **两次连跑 sha 相同** | ✅ `k2_v6.kicad_pcb f615ffe6b83b88a3`、`k2_v6_layout.json a48778b818211e96`、`k2_v6.kicad_pro aed49832c39d2ad1`（**三件产物全部逐字节同**） |
| ② | 产物 **refs == 42** | ✅ 42 footprint；**refdes 集合 == 真源板 refdes 集合**（逐件相同） |
| ③ | 边框 **46mm `[33,79]`** | ✅ Edge.Cuts 4 段：`x∈[23.0,143.0] y∈[33.0,79.0]` = 120×46mm |
| ④ | 生成器自检 | ✅ S1/S2/S4/S5/S6/S8 **6/6 PASS**（S3/S7 已按 G6/G8 移除） |
| ⑤ | 产物可被 KiCad 接受（附加） | ✅ `kicad-cli pcb drc --severity-error` = **0 违规**（170 未连接项属预期：该生成器只产「布局+网表」板，不含走线） |

- 产物规模：42 footprint / 262 pad / 101 网名（YAML nets 101）/ 27 NO_CONNECT。

## 4. 观察项 **O2**：E4②（42）与 yaml 真源（55）的口径差

- 真源 `k2_sch.yaml` K2 侧器件（`card ∈ {2, both}`）= **55 件**；真源**板** = **42 件**；差集 13 件 = `D2, L1, R35–R39, R40, R41, R42–R45`（即 E1「板 42 ⇒ P4 补 13」）。
- 本沙箱按 Z4 计划字面要求（「真源（单颗 `U6`，**42 件**）」）+ E4②（refs==42）取 **真源板 42 件**，故 ② PASS。
- **须监理确认口径**：阶段内判据就是「对齐真源板 42」，还是最终以真源 **55** 为目标（则 E4② 需改判 55，并需补件几何/定位）。**ENG 不自行改判据。**

## 5. 复现（只写 `/tmp`）

1. 由仓内原件生成 `/tmp` 副本并施加 §6 的 G1–G8 diff；
2. 运行（含 H1–H3 钩子）：

```bash
cd /home/fila/jqdDev_2025/ic_hw
K2_GEN_ROOT=$PWD/k2 PM_GATE_PROJECT_ROOT=$PWD/k2 K2_SPEC_PATH=/tmp/opencode/k2p1/SPEC_dryrun_r21.json K2_OUT_PCB=/tmp/opencode/gen_a/k2_v6.kicad_pcb K2_OUT_JSON=/tmp/opencode/gen_a/k2_v6_layout.json AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/k2_gen_v5.gfix.draft.py
AppDir/bin/kicad-cli pcb drc --severity-error -o /tmp/opencode/drc_v6.rpt /tmp/opencode/gen_a/k2_v6.kicad_pcb
```

- 副本 sha16：**`c7a2887a58b5c789`**（799 行）；仓内原件 sha16：`7577a15a76a09a22`（867 行，**未变**）。

## 6. 附：G1–G8 完整 unified diff（沙箱副本；待 S1 放行后粘贴入仓）

```diff
--- k2/tools/k2_gen_v5.py
+++ /tmp/.../k2_gen_v5.gfix.draft.py
@@ -35,34 +35,38 @@
 # ─────────────────────────────────────────────────────────────────────────
 # 冻结路径 (只读)
 # ─────────────────────────────────────────────────────────────────────────
-ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
+ROOT = os.environ.get("K2_GEN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 沙箱钩子
 YAML_PATH = os.path.join(ROOT, "boards/k2_sch.yaml")
-SPEC_PATH = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json")
+sys.path.insert(0, os.path.join(ROOT, "_shared"))
+from pm_gate import artifacts as _ARTIFACTS, config as _PMCFG   # noqa: E402
+SPEC_PATH = _ARTIFACTS.path("L3", _PMCFG.spec_name())   # G2: 禁硬编码 SPEC 名 (§五 ④)
+SPEC_PATH = os.environ.get("K2_SPEC_PATH", SPEC_PATH)   # 沙箱测试钩子（S1 放行前测 rev-21 草案）
 PCB_REF_PATH = os.path.join(ROOT, "k2_v4.kicad_pcb")
 # 输出路径可经 K2_OUT_PCB / K2_OUT_JSON 环境变量覆盖（默认 v5 路径，
 # 行为零变化）；M13 v8 板重建经覆盖产出 k2_v6，保留 v5 证据不覆盖。
 OUT_PCB = os.environ.get("K2_OUT_PCB", "/tmp/opencode/boards/k2_v5.kicad_pcb")
 OUT_JSON = os.environ.get("K2_OUT_JSON", "/tmp/opencode/k2_v5_layout.json")
 
-BOARD = {"x": [23.0, 143.0], "y": [33.0, 71.0]}
+BOARD = {"x": [23.0, 143.0], "y": [33.0, 79.0]}   # G1: 板框 46mm (§五 ②)
 
 # ─────────────────────────────────────────────────────────────────────────
 # K2 refdes 权威清单 (MUST DO #2: YAML sheets K2 子集 + ECN-004 补齐器件)
 # 与旧产物 k2_v4.kicad_pcb 的 80 个已验证器件 + 21 个补齐器件一一对应 (共 101)。
 # U7 为上行 ReDriver (YAML 语义), 产物旧命名 "U3"@(93.825,44.7)。
 # ─────────────────────────────────────────────────────────────────────────
-K2_REFS = sorted(
-    ["J2", "J3", "J4", "U1", "U2", "U3", "U4", "U5", "U7", "E2", "D1"]
-    + [f"C{i}" for i in range(17, 33)]           # C17-C32 下行 AC 耦合
-    + [f"C{i}" for i in range(49, 65)]           # C49-C64 上行 AC 耦合
-    + [f"C{i}" for i in range(65, 91)]           # C65-C90 去耦/滤波/bulk
-    + ["R1", "R3", "R4", "R5", "R6", "R7",
-       "R9", "R10", "R11", "R12",
-       "R17", "R18", "R19", "R20", "R21",
-       "R22", "R23", "R24", "R25", "R26", "R27", "R28", "R29",
-       "R31", "R32", "R33", "R34"]
-    + ["J6", "J9", "J11", "J12", "J13"]
-)
+# G3: K2 refdes 集由真源板导出（禁字面表；单颗 U6；§五 ③）
+def _derive_k2_refs_from_true_source(path: str):
+    import re as _re
+    txt = open(path, encoding="utf-8").read()
+    refs = set(_re.findall(r'\(fp_text reference "([A-Z]+\d+)"', txt))
+    if not refs:
+        refs = set(_re.findall(r'\(property "Reference" "([A-Z]+\d+)"', txt))
+    if not refs:
+        raise ValueError(f"[G3] 真源板 {path} 未解析到任何 refdes")
+    return refs
+
+
+K2_REFS = sorted(_derive_k2_refs_from_true_source(PCB_REF_PATH))   # G3: 真源导出（42 件）
 K2_REFS_SET = set(K2_REFS)
 
 # K1 DNP / 不生成 (MUST DO #2)
@@ -70,7 +74,7 @@
           "R35", "R36", "R37", "C91"}
 
 # ECN-004 补齐器件 (MUST DO #4/#5)
-MISSING_REFS = [f"C{i}" for i in range(74, 91)] + ["R31", "R32", "R33", "R34"]
+MISSING_REFS = []   # 沙箱：K2_REFS 现由真源板导出，无「补齐」概念
 
 # ─────────────────────────────────────────────────────────────────────────
 # 补齐器件新定位 (ECN-004 规则, 从冻结决策落表; 已在板内空隙验证 0 重叠)
@@ -111,7 +115,7 @@
 }
 
 # 产物旧 refdes → YAML 语义 refdes (ECN-004 修正)
-OLD_REF_MAP = {"U3": "U7", "U4": "U3", "U6": "U4"}
+OLD_REF_MAP = {}   # G4: 双颗命名重映射已移除（单颗下 U6 不得被改名；§五 ③）
 
 # ─────────────────────────────────────────────────────────────────────────
 # 小封装 pad 几何 (0402/0603/0805 — 产物 MLCC/RES 已验几何; 0805 按同比例)
@@ -351,9 +355,6 @@
                     "at": (px, py), "size": (w, h),
                     "drill": None, "layers": '"F.Cu" "F.Mask" "F.Paste"',
                 }
-        # DS160PR810 热焊盘 pad65 (symbol 无 EP 引脚): TI SNLS658 要求接地, 产物亦为 GND
-        if d["symbol"] == "REDR_DS160PR810" and "65" in d["pads"]:
-            d["pad_net"]["65"] = "GND"
     return dev
 
 
@@ -580,22 +581,6 @@
     return True
 
 
-def check_ac_caps(dev):
-    ac_refs = [f"C{i}" for i in range(17, 33)] + [f"C{i}" for i in range(49, 65)]
-    cnt = 0
-    for r in ac_refs:
-        d = dev[r]
-        if d["symbol"] != "C_220N" or d["value"] != "220nF":
-            raise ValueError(f"[S3 AC_CAP] {r} 不是 C_220N/220nF: "
-                             f"symbol={d['symbol']} value={d['value']}")
-        if "C_0402_1005Metric" not in d["footprint"]:
-            raise ValueError(f"[S3 AC_CAP] {r} 封装非 0402: {d['footprint']}")
-        cnt += 1
-    if cnt != 32:
-        raise ValueError(f"[S3 AC_CAP] AC 耦合电容数量 {cnt} != 32")
-    return True
-
-
 def check_missing_devices(dev):
     for r in MISSING_REFS:
         if r not in dev:
@@ -650,53 +635,8 @@
         pos = fix["pos"]
         dev[ref]["at"] = (float(pos[0]), float(pos[1]), dev[ref]["at"][2])
 
-    cw = spec["capacitor_walls"]
-    min_pitch = cw["min_center_pitch_mm"]
-    lo, hi = cw["lower_band_y"]
-    rows = {}
-    for ref in [f"C{i}" for i in range(17, 33)]:
-        rows.setdefault(round(dev[ref]["at"][1], 2), []).append(ref)
-    in_band = sorted(y for y in rows if lo <= y <= hi)
-    out_band = sorted(y for y in rows if not (lo <= y <= hi))
-    taken = []
-    for y in in_band + out_band:
-        refs = sorted(rows[y], key=lambda r: int(r[1:]))
-        ny = y if y in in_band else min(max(y, lo), hi)
-        while any(abs(ny - ty) < 0.75 for ty in taken):
-            ny = round(ny + 0.75, 2)
-        if not (lo - 1e-6 <= ny <= hi + 1e-6):
-            raise ValueError(f"[SPEC] AC 墙行 y={y} 无 lower_band_y 带内空闲位置")
-        taken.append(ny)
-        xs = sorted((dev[r]["at"][0], r) for r in refs)
-        start_x = xs[0][0]
-        for i, (_, ref) in enumerate(xs):
-            dev[ref]["at"] = (round(start_x + i * min_pitch, 3), ny, 0.0)
+    # G7: capacitor_walls 段已移除（AC 墙对象不存在；§五 ③）
     return dev
-
-
-def check_ac_pitch(dev, spec):
-    """S7: AC 电容同 y 行相邻中心距 >= min_center_pitch_mm; C17-C32 行 y 在冻结带内."""
-    cw = spec["capacitor_walls"]
-    min_pitch = cw["min_center_pitch_mm"]
-    lo, hi = cw["lower_band_y"]
-    rows = {}
-    for ref in [f"C{i}" for i in range(17, 33)] + [f"C{i}" for i in range(49, 65)]:
-        rows.setdefault(round(dev[ref]["at"][1], 2), []).append(ref)
-    for y, refs in rows.items():
-        refs = sorted(refs, key=lambda r: int(r[1:]))
-        xs = [dev[r]["at"][0] for r in refs]
-        for i in range(1, len(xs)):
-            pitch = xs[i] - xs[i - 1]
-            if pitch < min_pitch - 1e-6:
-                raise ValueError(
-                    f"[S7 AC_PITCH] {refs[i-1]}/{refs[i]} 行 y={y} "
-                    f"中心距 {pitch:.3f} < {min_pitch}")
-        if all(int(r[1:]) <= 32 for r in refs):
-            if not (lo - 1e-6 <= y <= hi + 1e-6):
-                raise ValueError(
-                    f"[S7 AC_PITCH] C17-C32 行 y={y} 超出冻结带 "
-                    f"lower_band_y {lo}..{hi}")
-    return True
 
 
 def check_pin_headers(dev, spec):
@@ -793,11 +733,9 @@
     results = []
     results.append(("S1 焊盘重叠", check_pad_overlap(dev)))
     results.append(("S2 refdes 对齐", check_refdes(dev)))
-    results.append(("S3 AC 电容规格", check_ac_caps(dev)))
     results.append(("S4 缺失器件", check_missing_devices(dev)))
     results.append(("S5 坐标范围", check_board_bounds(dev)))
     results.append(("S6 网表一致性", check_nets(dev, nets)))
-    results.append(("S7 AC 电容中心距", check_ac_pitch(dev, spec)))
     results.append(("S8 排针坐标冻结", check_pin_headers(dev, spec)))
 
     # ── 序列化 ──
@@ -813,8 +751,8 @@
 
     # ── 复制 JLC 规则模板 (Board Setup, DRC 按板厂工艺而非 KiCad 默认) ──
     import shutil
-    tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
-                        "k2_jlc_template.kicad_pro")
+    tmpl = os.path.join(ROOT, "tools",
+                        "k2_jlc_template.kicad_pro")   # 沙箱钩子
     dst = OUT_PCB.replace(".kicad_pcb", ".kicad_pro")
     shutil.copy(tmpl, dst)
 
@@ -842,13 +780,7 @@
     ph = spec["components"]["pin_headers"]["positions"]
     print("  排针坐标 (SPEC 冻结): " + ", ".join(
         f"{r}@({p[0]},{p[1]})" for r, p in sorted(ph.items())))
-    rows = {}
-    for ref in [f"C{i}" for i in range(17, 33)]:
-        rows.setdefault(round(dev[ref]["at"][1], 2), []).append(ref)
-    for y in sorted(rows):
-        xs = sorted(dev[r]["at"][0] for r in rows[y])
-        pitch = [f"{xs[i+1]-xs[i]:.2f}" for i in range(len(xs)-1)]
-        print(f"  AC 墙行 y={y:.2f}: x={xs} 间距={pitch}")
+    # G6b/G8b: AC 墙摘要打印已随对象移除
     print(f"  器件数: {len(dev)}  (产物沿用 {len(dev) - len(MISSING_REFS)}, "
           f"补齐 {len(MISSING_REFS)})")
     print(f"  pads 总数: {n_pads}")```
