# K2 · P4 · **`D-6` / `N-03` 处置 diff 草案**（生成器自检声称 vs 实际 · pro 图纸悬挂指针；含传播源证明）· v1 · 2026-09-18

> 缘起：handoff inc66 §6-3-(q)「`D-6`（改声称＋重编号 / 补实现）与 `N-03`（置空 `[]` / 指真实 sch / 是否连 k1；**模板必含、模板是传播源**）**两案/多案处置 diff 草案**（§5-10『择一即做』，接 inc61 §1/§2）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 提案件/diff**，仓库零载体改动（仅新增本证据件）。
> 锚：生成器 `k2/tools/k2_gen_v5.py` **`d8d15a31061f450f`** · l5 pro `k2/hw/k2_v4_8L.l5.kicad_pro` **`d5e0ca067a7b585e`** · 设计源 pro `k2/hw/k2_v4_8L.kicad_pro` **`f54404024191ea64`** · 模板 pro `k2/tools/k2_jlc_template.kicad_pro` **`206dd0f26e245658`** · 根 sch `k2/hw/sch/k2_sch.kicad_sch`（root uuid **`3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9`**）。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/d6/{gen.a1.py,gen.a2.py,a1.diff,a2.diff,dyn_orig.txt}` · `/tmp/opencode/inc63/n03/{blank,real}/…`、`{blank,real}.diff`。
> **归属**：`D-6`/`N-03` 的处置选择＝**监理（判据/门禁口径）**；ENG 只出候选、diff 与证据，**不择一**。**不得新增检查齿（owner ②）**。

## 0. 结论（五条）

1. **`D-6` 实测再证（静态＋动态）**：`:742` 注释写「**8 项** fail-fast 自检」、`:786` 打印 `自检结果 (8/8):`；实际 `results.append` 仅 **6** 项（`S1/S2/S4/S5/S6/S8`），`S3`/`S7` **全文件 0 命中**；动态运行输出 **表头 `(8/8)` ＋ 仅 6 行 ✅**。
2. **`D-6` 三案**：**(a1) 仅改两处声称文本**（最小、零编号扰动，保留原跳号 `S1/S2/S4/S5/S6/S8`）· **(a2) 改声称 ＋ 连续重编号**（`S4→S3` `S5→S4` `S6→S5` `S8→S6`，须同步 ≥3 份文档的引用）· **(b) 补实现 `S3`/`S7`**＝**新增检查齿 ⇒ owner ② 禁**。ENG 建议 **(a1)**（代价最小），裁决归监理。
3. **`N-03` 的结构发现（决定性）**：pro 的 `top_level_sheets.filename` 按**相对 `.kicad_pro` 所在目录**解析 ⇒ 现值为 `k2_eco22.kicad_sch`（模板/设计源）/`k2_v4_8L.l4.kicad_sch`（l5），二者**在各自目录下均不存在**（挂空）。实测**唯一同时从 `k2/hw/` 与 `k2/tools/` 都解析成功**的字面量＝**`../hw/sch/k2_sch.kicad_sch`**（因二者同为 `k2` 下第 1 层）⇒ 该字面量可**统一**用于三载体，且被生成器原样继承到产物后**仍然有效**。
4. **`N-03` 两案 diff 已成件（3 个 k2 载体）**：**① 置空 `[]`**（位置无关；产物亦然）· **② 指真实 sch**（`../hw/sch/k2_sch.kicad_sch` ＋ `uuid` = 根 sch 的 root uuid `3ed817d0-…`）。**权威 schema 依据**＝KiCad 自带 demo `AppDir/share/kicad/demos/pic_programmer/pic_programmer.kicad_pro`：entry 键为 `{filename,name,uuid}` 且 **`uuid` == 根 sch 的 root uuid**（实测相等）；`sheets` 在 demo 中同为 `null` ⇒ 无需填 `sheets`。
5. **传播源证明**：生成器 `:764-767` `tmpl = k2/tools/k2_jlc_template.kicad_pro` → `dst = OUT_PCB.replace(".kicad_pcb",".kicad_pro")` → `shutil.copy(tmpl,dst)`（随后注入 `net_settings`）⇒ 实测**产物 pro 的 `top_level_sheets` 逐字继承模板**（`/tmp` 生成件仍为 `k2_eco22.kicad_sch`）⇒ **不修模板则每次生成复发**。

## 1. `D-6`：生成器自检「声称 8 / 实际 6」

| 证据 | 结果 |
|---|---|
| 静态 | `:742` `# ── 8 项 fail-fast 自检 …` · `:786` `print("k2_gen_v5 自检结果 (8/8):")`；`results.append` = 6 项（`S1 S2 S4 S5 S6 S8`）；`S3`/`S7` 0 命中 |
| 动态 | `K2_OUT_PCB=/tmp/… python3 k2/tools/k2_gen_v5.py` ⇒ 表头 `k2_gen_v5 自检结果 (8/8):` ＋ **6 行** `✅ S1/S2/S4/S5/S6/S8`（`dyn_orig.txt` `d7b199a3d913483b`）|
| 受影响的陈旧陈述（需同步） | `k2/pm_gate/artifacts/k2_v4/L2/AUDIT_yaml_vs_pcb_v1.0.md:155`「8 项 fail-fast 自检（S1-S8）全 PASS…」；`k2/docs/K2-P2-U4-generator-g1g8-sandbox-evidence-v1.md:232-239`（6 行 append 摘录）；`k2/docs/K2-ENG-AUDIT-2026-09-15.md:185-187`（`S1`/`S5`/`S8` 行）|

**案 (a1) —— 仅改两处声称文本（最小；编号不动）**（diff `ae53a82036b09625`）：
```diff
--- k2/tools/k2_gen_v5.py	2026-09-16 20:48:22.313639784 +0800
+++ /tmp/opencode/inc63/d6/gen.a1.py	2026-09-18 11:31:47.051687758 +0800
@@ -739,7 +739,7 @@
     apply_spec_overrides(dev, spec)
     assign_nets(dev, nets)
 
-    # ── 8 项 fail-fast 自检 (全 PASS 才写盘) ──
+    # ── 6 项 fail-fast 自检 (全 PASS 才写盘) ──
     results = []
     results.append(("S1 焊盘重叠", check_pad_overlap(dev)))
     results.append(("S2 refdes 对齐", check_refdes(dev)))
@@ -783,7 +783,7 @@
     used_nets = sorted({net for d in dev.values() for net in d["pad_net"].values()}
                        - {"NO_CONNECT"})
     print("=" * 56)
-    print("k2_gen_v5 自检结果 (8/8):")
+    print("k2_gen_v5 自检结果 (6/6):")
     for name, _ in results:
         print(f"  ✅ {name}: PASS")
     print("=" * 56)
```

**案 (a2) —— 继承 (a1) ＋ 连续重编号 `S1..S6`**（编号相关 hunk；diff `08d232a78bbe293e`；须同步上表 3 份文档的引用，否则 `S4/S5/S6/S8` 语义漂移）：
```diff
     results.append(("S1 焊盘重叠", check_pad_overlap(dev)))
     results.append(("S2 refdes 对齐", check_refdes(dev)))
-    results.append(("S4 缺失器件", check_missing_devices(dev)))
-    results.append(("S5 坐标范围", check_board_bounds(dev)))
-    results.append(("S6 网表一致性", check_nets(dev, nets)))
-    results.append(("S8 排针坐标冻结", check_pin_headers(dev, spec)))
+    results.append(("S3 缺失器件", check_missing_devices(dev)))
+    results.append(("S4 坐标范围", check_board_bounds(dev)))
+    results.append(("S5 网表一致性", check_nets(dev, nets)))
+    results.append(("S6 排针坐标冻结", check_pin_headers(dev, spec)))
```
提案件：`gen.a1.py` **`98121c76858518b8`** · `gen.a2.py` **`335678a6330c677c`**（`compile()` 语法自检通过）。

**案 (b) 禁因**：补实现 `S3`/`S7` ⇒ 新增两条检查齿 ⇒ **违反 owner ②**（且 `S3`/`S7` 的判据语义、阈值、在岗口径均未定义）。

## 2. `N-03`：解析基准与权威 schema

**2.1 `filename` 解析实测（相对于 `.kicad_pro` 所在目录）**

| 载体（pro 所在目录） | `sch/k2_sch.kicad_sch` | **`../hw/sch/k2_sch.kicad_sch`** | `hw/sch/k2_sch.kicad_sch` |
|---|---|---|---|
| `k2/hw/`（l5 · 设计源） | EXISTS | **EXISTS** | MISSING |
| `k2/tools/`（模板） | MISSING | **EXISTS** | MISSING |

⇒ **`../hw/sch/k2_sch.kicad_sch` 是唯一三载体通用、且被生成器继承后仍有效的字面量**。

**2.2 权威 schema（KiCad 自带 demo 实测）**
```json
{"filename": "pic_programmer.kicad_sch", "name": "pic_programmer",
 "uuid": "2e45d1d2-c73f-46e5-98d6-3a9dc360bff5"}
```
该 `uuid` == 该 demo 根 sch 的 root uuid（实测相等）。本板根 sch root uuid = **`3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9`** ⇒ 直接采用；`sheets` 保持 `null`（demo 同形）。

**2.3 传播源证明（生成器 → 产物 pro）**
```
:764  tmpl = <k2>/tools/k2_jlc_template.kicad_pro
:766  dst  = OUT_PCB.replace(".kicad_pcb", ".kicad_pro")
:767  shutil.copy(tmpl, dst)          # 之后仅注入 net_settings
```
实测：`K2_OUT_PCB=/tmp/opencode/inc63/gen/g.kicad_pcb` 生成后，`gen/g.kicad_pro` 的 `top_level_sheets` ＝ **`k2_eco22.kicad_sch`**（＝模板现值）⇒ **模板是根治点**。

## 3. `N-03` 两案 diff（3 个 k2 载体；可直接 `git apply`）

**案 ① 置空（位置无关）** —— 提案件 sha：`l5 a5dff9def24d158a` · `设计源 7b2103e33bf9623d` · `模板 c2c9905cabd81b1f`；diff `9b32fa5f55cb0a26`
```diff
--- k2/hw/k2_v4_8L.l5.kicad_pro	2026-09-17 22:45:01.574659462 +0800
+++ /tmp/opencode/inc63/n03/blank/hw/k2_v4_8L.l5.kicad_pro	2026-09-18 11:31:31.620837603 +0800
@@ -807,13 +807,7 @@
     "bus_aliases": {},
     "legacy_lib_dir": "",
     "legacy_lib_list": [],
-    "top_level_sheets": [
-      {
-        "filename": "k2_v4_8L.l4.kicad_sch",
-        "name": "k2_v4_8L.l4",
-        "uuid": "00000000-0000-0000-0000-000000000000"
-      }
-    ]
+    "top_level_sheets": []
   },
   "sheets": [],
   "text_variables": {},
--- k2/hw/k2_v4_8L.kicad_pro	2026-09-11 20:20:31.730664400 +0800
+++ /tmp/opencode/inc63/n03/blank/hw/k2_v4_8L.kicad_pro	2026-09-18 11:31:31.621837593 +0800
@@ -808,13 +808,7 @@
     "bus_aliases": {},
     "legacy_lib_dir": "",
     "legacy_lib_list": [],
-    "top_level_sheets": [
-      {
-        "filename": "k2_eco22.kicad_sch",
-        "name": "k2_eco22",
-        "uuid": "00000000-0000-0000-0000-000000000000"
-      }
-    ]
+    "top_level_sheets": []
   },
   "sheets": [],
   "text_variables": {},
```

**案 ② 指真实 sch（`../hw/sch/k2_sch.kicad_sch` ＋ root uuid）** —— 提案件 sha：`l5 8bd17d9bdac3d691` · `设计源 8f1966458c0cae60` · `模板 0af67f154fd0e029`；diff `fd6c2906fd1cb41b`
```diff
--- k2/hw/k2_v4_8L.l5.kicad_pro	2026-09-17 22:45:01.574659462 +0800
+++ /tmp/opencode/inc63/n03/real/hw/k2_v4_8L.l5.kicad_pro	2026-09-18 11:31:31.621837593 +0800
@@ -809,9 +809,9 @@
     "legacy_lib_list": [],
     "top_level_sheets": [
       {
-        "filename": "k2_v4_8L.l4.kicad_sch",
-        "name": "k2_v4_8L.l4",
-        "uuid": "00000000-0000-0000-0000-000000000000"
+        "filename": "../hw/sch/k2_sch.kicad_sch",
+        "name": "k2_sch",
+        "uuid": "3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9"
       }
     ]
   },
--- k2/hw/k2_v4_8L.kicad_pro	2026-09-11 20:20:31.730664400 +0800
+++ /tmp/opencode/inc63/n03/real/hw/k2_v4_8L.kicad_pro	2026-09-18 11:31:31.621837593 +0800
@@ -810,9 +810,9 @@
     "legacy_lib_list": [],
     "top_level_sheets": [
       {
-        "filename": "k2_eco22.kicad_sch",
-        "name": "k2_eco22",
-        "uuid": "00000000-0000-0000-0000-000000000000"
+        "filename": "../hw/sch/k2_sch.kicad_sch",
+        "name": "k2_sch",
+        "uuid": "3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9"
       }
     ]
   },
--- k2/tools/k2_jlc_template.kicad_pro	2026-08-29 11:13:15.630101041 +0800
+++ /tmp/opencode/inc63/n03/real/tools/k2_jlc_template.kicad_pro	2026-09-18 11:31:31.622837583 +0800
@@ -314,9 +314,9 @@
     "legacy_lib_list": [],
     "top_level_sheets": [
       {
-        "filename": "k2_eco22.kicad_sch",
-        "name": "k2_eco22",
-        "uuid": "00000000-0000-0000-0000-000000000000"
+        "filename": "../hw/sch/k2_sch.kicad_sch",
+        "name": "k2_sch",
+        "uuid": "3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9"
       }
     ]
   },
```
**机检（两案 × 三载体）**：JSON 解析成功 · `schematic.top_level_sheets` 值符合预期 · 案② 解析到的文件**存在**且 `uuid` == 根 sch root uuid（脚本见 §5）。

**注**：l5 的现值是**另一变体**（指向 `k2_v4_8L.l4.kicad_sch`），故两案都改 l5 的同一处；设计源与模板互为同值（`k2_eco22`）。

## 4. `k1` 同族（**跨项目旁证**，不在本次投递范围）

| 事实 | 值 |
|---|---|
| `k1/k1_v1.kicad_pro` · `k1/tools/k1_jlc_template.kicad_pro` | `top_level_sheets` = `k2_eco22.kicad_sch`（同样挂空）；两者模板 sha 与 k2 模板**完全相同**（`206dd0f26e245658`） |
| `k1/sch/k1_sch.kicad_sch` root uuid | `3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9`（**与 k2 根 sch 同 uuid** ⇒ k1 图根为 k2 克隆件）|
| 单一字面量是否可行 | **不可行**：k1 的 pro 在 `k1/`（第 0 层）、模板在 `k1/tools/`（第 1 层）⇒ 不存在同时解析成功的相对字面量；k1 若采案② 须**生成器侧动态写路径**或**分文件不同字面量**（后者产物继承会失配） |
| k1 是否有 pro-copy 生成器 | `k1/tools/` 内**未见** pro 复制逻辑（`grep` 无 `shutil.copy(tmpl…)`）⇒ k1 模板可能为残留副本 |

⇒ **k1 与 k2 不同批**；若监理判需同修，须 **k1 侧属主/监理同意**（跨项目，红线：不得擅改他项目载体）。

## 5. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# D-6 动态（期望 表头 (8/8) + 6 行 ✅）
K2_OUT_PCB=/tmp/opencode/inc63/d6/run/o.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc63/d6/run/o.json \
  python3 k2/tools/k2_gen_v5.py 2>&1 | grep -E "自检结果|✅"
# D-6 diff（现值与两案）
diff -u k2/tools/k2_gen_v5.py /tmp/opencode/inc63/d6/gen.a1.py
diff -u k2/tools/k2_gen_v5.py /tmp/opencode/inc63/d6/gen.a2.py
# N-03 机检（两案 × 三载体：JSON/值/解析存在性/uuid）
python3 /tmp/opencode/inc63/n03_check.py
# 传播源（期望产物 pro 的 top_level_sheets == 模板值）
python3 -c "import json;print(json.load(open('/tmp/opencode/inc63/gen/g.kicad_pro'))['schematic']['top_level_sheets'])"
```

## 6. 边界

本件**只读 + `/tmp` 提案件/diff**：未改生成器/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/SPEC/真源/图纸/`criteria/**`/`_shared/**`/闭环表/k1；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 生成器 `d8d15a31061f450f` · l5 pro `d5e0ca067a7b585e` · 模板 `206dd0f26e245658`
