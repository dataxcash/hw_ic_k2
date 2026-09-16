# P1 · manifest 覆盖补齐与「不补之理由」（监理 #K2-09 §二 应答）

- **性质**：只读自查 + ENG 起草（**判据域 `criteria/` 属 `ic_hw_gate`，ENG 只读 ⇒ 本件只交草稿，不自行安装**）
- **登记册**：`.omo/supervision/ledger/K2-DEFECT-REGISTER-v1.md` **§C 出厂判据（冻结维度 J-1..J-10）**
- **现行 manifest** `criteria/manifest.k2.yaml`（sha256 `7ce08757…fb081a623a`，`not_countersigned: true`）

## 0. 结论

- 监理口径（覆盖 7 / 缺 3）**成立**；本轮**补齐 1 项**（J-7a），其余按 §2 给出**逐项覆盖时点与判据名** —— **不补 ≠ 静默**。
- 补入件以**草案**交付（安装需 gate 主体）：`/tmp/opencode/k2p1/adjudicate.draft.py` + `/tmp/opencode/k2p1/manifest.k2.additions.draft.yaml`。

## 1. 十维度覆盖矩阵（ENG 自查）

| 登记册 §C | 现行 manifest 判据 | 状态 |
|---|---|---|
| J-1 DRC error = 0 | — | **缺**：依赖「判定器内 DRC 运行」能力（见 §2-1） |
| J-2 连通 = 0（补铜后） | `net_declared_realized`（声明网 ≥2 焊盘） | **部分**：真「连通」需 DRC unconnected 面（见 §2-1） |
| J-3 铺铜全填充 | `zone_filled` | 已有 |
| J-4 丝印全开且 0 违规 | —（经 **deny-by-default** 的 `ignore` 面间接命中 `silk_over_copper`/`silk_overlap`） | **部分**：全开面已抓，0 违规需 DRC（§2-1） |
| J-5 走线仅 45° | `non45_segments` | 已有 |
| J-6 板↔原理图一致 | `refdes_sets_equal` + `pin_map_complete` | 已有 |
| J-7 封装 = 库 | **本轮补 J-7a**（`fp_lib_table_present`）；J-7b 见 §2-2 | **补 a / b 待 DRC 能力** |
| J-8 器件位置合理性 | `drill_count`（**固定孔**子项） | **部分**：其余子项见 §2-3 |
| J-9 门禁接入 | `pipeline_present` | 已有 |
| J-10 完工定义可复现 | — | 见 §2-4（P2-E4 / P4 + 附录） |

> **附**：现行清单另含 `device_has_pads`（5 颗 0 焊盘连接器）——来源为**审计缺陷**（非 §C 维度），作附加机判保留，**非 ENG 自造阈值**；`verdict_schema` 属 §6.2 C4 机制项，亦非 §C 维度。

## 2. 未补维度的覆盖时点与判据（逐项，禁静默）

**2-1 共同根因（J-1 / J-2 数值面 / J-4 数值面 / J-7b）**：判定器现**无 DRC 运行能力**（仅解析 `.kicad_pro` 的 `rule_severities`，见 FINDING-4）。
⇒ 覆盖时点 = **P1 补丁（判定器加 `kicad-cli pcb drc` 运行）** 或 **P4 闸**；判据名（拟定）`drc_error_zero` / `unconnected_zero` / `silk_clean` / `lib_footprint_clean`，值取 DRC 报告逐类计数 = 0。

**2-2 J-7b `lib_footprint_mismatch + lib_footprint_issues == 0`**：同上依赖 DRC 能力（现值 29 + 12 = 41）⇒ 覆盖时点 = 该能力落地后 / P4 闸。

**2-3 J-8 拆分（6 子项）**

| 子项 | 覆盖 | 时点 |
|---|---|---|
| 固定孔 | `drill_count`（NPTH ≥ 1）**已有** | P1 |
| 出框 | 判据名 `device_within_outline`：器件焊盘 ⊆ Edge.Cuts 包围盒 | **P3**（需先有冻结板框图：P3「板框 = 120×46, y[33,79]」） |
| 重叠 / 密度分布 / 关键间距 | 属 courtyard/keepout 的 DRC 语义 | **P3（回避区图/走廊占用图） + DRC 能力落地**。**不采用朴素 bbox 重叠检查**（相邻连接器会误报 ⇒ 错判据比缺判据更坏） |
| 回避区 | P3「回避区图」判据 | **P3** |

**2-4 J-10 完工定义可复现**：拆两半 ——
- 「命令 + 阈值 + 原始输出」：**P1 形式面已覆盖**（计划「附：本计划内所有"现状"数字的原始输出出处」+ 本件 §3 复跑命令）；
- 「生成器输入齐 + 两次输出 sha 相同」：**P2 的 E4**（生成器可复跑）与 **P4 闸**（全链重基线）⇒ 时点 = **P2 / P4**。

## 3. 本轮补入项（J-7a）—— 转写 + 测证

- **转写自**：登记册 §C J-7「封装 = 库（mismatch/issues = 0，**且 `fp-lib-table` 存在**）」的**后半句**
- **应然表达式**：`fp-lib-table exists in project dir`（自 board 所在目录向上最多 5 层）；**无阈值**
- **草案**：`/tmp/opencode/k2p1/adjudicate.draft.py`（新增 `measure_fp_lib_table()` + `fp_lib_table_present` 判定）；manifest 追加：
  ```yaml
  fp_lib_table_present:   {enabled: true, expect: "fp-lib-table exists in project dir (J-7a)"}
  ```
- **测证（本会话实跑，可复跑）**

| 控制 | 做法 | 结果 |
|---|---|---|
| 负控 | k2 真实（无 `fp-lib-table`） | `[FAIL] fp_lib_table_present: 存在 = False`，rc=1；**其余 9 类不受影响** |
| 正控 1 | board 同目录放 `fp-lib-table` | `[OK] 存在 = True` |
| 正控 2 | board 上 2 层放 `fp-lib-table` | `[OK] 存在 = True` |

## 4. 交监理（决定项）

1. **J-7a 是否采纳**；§2 的**覆盖时点/判据名**是否认可；
2. 若采纳：以 gate 主体安装草案（`adjudicate.draft.py` → `criteria/adjudicate.py`，manifest 追加一行），随后**重出冻结值**（两份 sha256）并令 `criteria/CHANGELOG` 记一条；
3. 签认 `criteria/manifest.k2.yaml`（`not_countersigned` → `false`）。

## 5. 判定器内 DRC 运行能力（FINDING-4）—— 草案 + 保真度验证（本轮新增）

- **草案**：`/tmp/opencode/k2p1/drc_measure.draft.py`
- **契约**：在**副本**上按 manifest 豁免集（`rule_severity_exemptions`）覆盖 severity 后跑
  `kicad-cli pcb drc --format json --severity-all`，输出**逐类计数**与 **error/warning 分计**
  ⇒ 实现 C1 的「副本上覆盖后跑」形态（改 `.kicad_pro` 不再影响判定）。

**保真度验证（本会话实跑，可复跑）**

| 策略 | 实测 | 对照 |
|---|---|---|
| honor 模板 9 条 `ignore`（as-designed 口径） | **42**（全 warning）：`lib_footprint_mismatch` 29 / `lib_footprint_issues` 12 / `silk_edge_clearance` 1 | **与审计 as-designed = 42 完全一致** ✅ |
| deny-by-default（`exemptions=[]`，即现行 manifest） | **313**（error 271 / warning 42）：`via_dangling` 199 / `missing_courtyard` 41 / `lib_footprint_mismatch` 29 / `silk_over_copper` 22 / `lib_footprint_issues` 12 / `silk_overlap` 9 / `silk_edge_clearance` 1 | 见下「数字差异」 |

**数字差异（如实登记，待监理对账）**
计划 §3.4 载「副本上把 9 条 `ignore` 改回 → DRC 42 → **131**」；本节以**同一 9 条**改回 `error` ＋ `--severity-all` 实测 = **313**，
**未复现 131**。可能成因：当时所用取消集／目标 severity／CLI 旗标／板修订不同。⇒ 请监理以本节命令复算并裁定基据值；
**本件不擅改计划既有数字**。

**可解锁维度（策略需监理/owner 定，属判据应然值）**

| 维度 | 拟定判据名 | 应然表达式 |
|---|---|---|
| J-1 | `drc_error_zero` | `errors == 0`（登记册原文：error=0；warning 逐项有处置结论 ⇒ warning 入处置台账） |
| J-2 数值面 | `unconnected_zero` | DRC `unconnected_items` == 0 |
| J-4 数值面 | `silk_clean` | `silk_*` 类 == 0 |
| J-7b | `lib_footprint_clean` | `lib_footprint_mismatch + lib_footprint_issues == 0` |

- **待裁定**：① error／warning 分界；② 豁免集（现行 `[]` = 全禁 `ignore`，会把 313 条全判不合格，是否符合预期）。
- **安装**：需 gate 主体将 `measure_drc()` 并入 `criteria/adjudicate.py`（判据域 ENG 只读，故只交草案）。

## 6. FINDING-5 门（监理指派，实现归 ENG）+ `countersigned_scope` 草案 + 同族新发现（本轮新增）

> 依监理 `K2-RULING-k2-09-closeout-v1.md` §四：判定器须在 `uncovered` 非空时**不得输出整体 PASS**；**实现归 ENG（起草）**、**验收归监理**、时点 = **P2 开工前**、与 J-7a 安装**同批**。

### 6.1 合并草案（J-7a + FINDING-5，一次落地）

`/tmp/opencode/k2p1/adjudicate.draft.batch1.py`（359 行；同名 `adjudicate.draft.py` 内容相同）＝ `criteria/adjudicate.py` ＋
`measure_fp_lib_table()`/`fp_lib_table_present`（J-7a）＋ **覆盖范围完整性门**：
- `countersigned_scope` **缺失** ⇒ `uncovered = ["<未声明：覆盖范围不可判 ⇒ fail-closed>"]`（**fail-closed**）；
- `uncovered` 非空 ⇒ `passed = (not fails) and (not uncovered)`，输出 `INCOMPLETE`，`rc=1`；`verdict` 增 `scope_incomplete` / `uncovered` 两字段。

### 6.2 `countersigned_scope` 草案结构（内容待监理定；本件为转写）

```yaml
countersigned_scope:
  covered: ["J-3","J-5","J-6","J-7a","J-9","J-2(显式网实现面)","J-8(固定孔子项)","C4","device_has_pads(审计来源)"]
  uncovered:
    - {dim: "J-1 DRC error=0",            criterion: "drc_error_zero",      at: "P1 补丁(DRC) / P4 闸"}
    - {dim: "J-2 连通=0 数值面",           criterion: "unconnected_zero",    at: "同 J-1"}
    - {dim: "J-4 丝印 0 违规数值面",        criterion: "silk_clean",          at: "同 J-1"}
    - {dim: "J-7b 封装=库 数值面",          criterion: "lib_footprint_clean", at: "同 J-1"}
    - {dim: "J-8 出框",                    criterion: "device_within_outline", at: "P3"}
    - {dim: "J-8 重叠/密度/关键间距/回避区",  criterion: "(P3 施工图 + DRC)",    at: "P3"}
    - {dim: "J-10 可复现面",               criterion: "(P2-E4 / P4 闸)",      at: "P2/P4"}
```

### 6.3 验收控制实测（本会话实跑；请在 gate 安装后由**监理**复算验收）

| # | manifest 场景 | 期望 | 实测 |
|---|---|---|---|
| C1 | **无 `countersigned_scope`**（现装 manifest 形态） | 不得 PASS | `INCOMPLETE`，rc=1，`scope_incomplete=True`，`uncovered=1` ✅ |
| C2 | `uncovered` = 7 项（真实缺口） | 不得 PASS | `INCOMPLETE`，rc=1，`uncovered=7` ✅ |
| C3 | `uncovered = []` ＋ 板有 10 项 FAIL | 仍 FAIL（门不得掩盖 FAIL） | `FAIL`，rc=1，`scope_incomplete=False`，`n_fail=10` ✅ |
| **C4** | **全 `checks` 关闭（0 FAIL）＋ `uncovered` = 1** | **不得 PASS**（**决定性正控**） | `INCOMPLETE`，rc=1，`passed=False`，`n_fail=0` ✅ |
| C5 | 同上但 `uncovered = []` | （对照）允许 PASS | `PASS`，rc=0，`passed=True` ✅ |

> C4/C5 成对：**同一 0-FAIL 场景**，`uncovered` 非空 ⇒ 不 PASS、空 ⇒ PASS ⇒ 门**确为**翻转向量，非橡皮图章。

### 6.4 同族新发现 —— **FINDING-6（ENG 提出；判据域变更须监理裁定）**

| 项 | 内容 |
|---|---|
| **现象** | C5（`uncovered=[]` ＋ 全 `checks` 关闭 ＋ 9 条 ignore 获豁免）在**冻结板**上输出 **`PASS` / rc=0** |
| **根因** | `adjudicate()` 以 `C.get(name,{}).get('enabled')` 逐项取用 ⇒ **manifest 可整体关闭判据**；`checks` 键集与应然集**无 deny-by-default 比对** |
| **性质** | 与 **C-12（判据自废）** 及 FINDING-5 **同型**：不合格板可"PASS"，且路径是**改判据**而非改板 |
| **建议（待裁）** | manifest `checks` 键集须 **== 应然集**（缺项/关闭 ⇒ FAIL）；`enabled:false` 须逐条登记理由（同 `rule_severity_exemptions` 的留痕口径） |
| **归属/时点** | 实现归 ENG（起草）、验收归监理；建议与 FINDING-5 **同批**安装 |


> **命名消歧（对账用）**：本批共两份草案 ——
> ① **J-7a 专件** `/tmp/opencode/k2p1/adjudicate.draft.j7a.py`（sha16 `141e637d…`，即监理 `K2-RULING-k2-09-closeout-v1.md` 所引之件，已重建核对一致）；
> ② **合并批 1** `/tmp/opencode/k2p1/adjudicate.draft.batch1.py`（J-7a ＋ FINDING-5 门，供与 `countersigned_scope` + `CHANGELOG` 一次原子安装）。

## 7. 原子批清单（监理 #K2-10 §二；ENG 起草 → 监理验收 → **gate 主体安装**）

| # | 件 | 草案路径（ENG 写域 = /tmp/opencode） | sha256 | 对应 §二项 |
|---|---|---|---|---|
| D1 | 判定器（J-7a **＋** FINDING-5 门） | `/tmp/opencode/k2p1/adjudicate.draft.batch1.py` | `74512e71f94dcf20519fe6fe0cd598b4fad49d3d9e9eba38db2bd24085584115` | §二-1 + §二-2 |
| D1' | （参考）J-7a 专件 = 监理所引之件 | `/tmp/opencode/k2p1/adjudicate.draft.j7a.py` | `141e637d43ed5ae704439ebb7519f87ece338e4a1fd6728c3322301ea7261170` | §二-1 |
| D2 | manifest 增补（`fp_lib_table_present` + `countersigned_scope`） | `/tmp/opencode/k2p1/manifest.k2.additions.draft.yaml` | `e2fa703ed7bb3103cf9b94f05eb0512f75d5ed783cde4089133f335dd1ab27d3` | §二-3 |
| D3 | `criteria/CHANGELOG` 初始条目（含 rev=2 待安装行） | `/tmp/opencode/k2p1/CHANGELOG.draft` | `1ae871f6c86d5aafc1a7787358ac03391d80fc8b860427b9f436836978b58306` | §二-4 |

**FINDING-5 正控（本次复跑，rc≠0）**
```
$ python3 adjudicate.draft.batch1.py --manifest m_passbut_open.yaml <ARGS>
  [OK]   rule_severity_manifest: 未登记豁免的 ignore 0/62: []      ← 0 FAIL 场景
  => INCOMPLETE（覆盖范围不完整：1 项未覆盖 ⇒ 按 FINDING-5 不得判 PASS）
rc=1 | passed=False | scope_incomplete=True
```
对照（同 0-FAIL 场景、`uncovered=[]`）：`=> PASS | rc=0` ⇒ 门为**翻转向量**。

**安装（gate 主体，监理执行；ENG 不写 `criteria/`）**：D1 → `criteria/adjudicate.py`；D2 → `criteria/manifest.k2.yaml`；D3 → `criteria/CHANGELOG`；随后 `chown ic_hw_gate` + `chmod 0555/0444`，**重出两份 sha（rev=2）**并落锚 `adjudication-ledger.jsonl`，再行**带范围签认**。

**未决（不阻塞本批）**：**FINDING-6**（manifest 可整体关闭 `checks` ⇒ 0 FAIL ⇒ PASS，见 §6.4）—— 建议 `checks` 键集 == 应然集、缺项/关闭即 FAIL；待监理裁定是否并入。
