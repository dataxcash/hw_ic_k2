# K2 · P4 · **#K2-34 §三 执行报告**：§1 `M-14` fail-closed · §2 `(i-a′)`+⑦→`l7`+SPEC rev-52 · §5 P3 图集重发 · §6 确定性 · **§3 停等 gate 属主（criteria rev=3）** · v1 · 2026-09-19

> 授权：监理 **#K2-34**（§一逐项裁定 + §三执行序；owner 项 = 0）。
> ENG（ARCHER）· 2026-09-19 · k2 `adf2ab6` · 判据锚 **rev=2（MATCH，未动）** · 受审板 **`l7 c5a7df90aadb66e0`**
> 本件只写 `k2/docs/**` + 追加 `.omo/start-work/ledger.jsonl`；**未写 `.omo/supervision/**`**；未改 `criteria/**`。

---

## 0. 一句话

**§三 执行序的 ENG 面（1 · 2 · 5 · 6）已全部实跑完成并落件**（k2 `adf2ab6`；`_shared` `935fb25` → k2 pin `da1e364`）：
`l7 = c5a7df90aadb66e0`（3 跑逐字节同）· `SPEC rev-52` 同笔 · P3 图集重发（仅 J3/J4 变）· M-14 负控（置坏指针 ⇒ 链失败）成立。
**§三-3（`criteria` rev=3 安装）明文属 gate 属主 + 监理签认 —— ENG 只读 `criteria/`、不落件** ⇒ **§4（全链重锚 l7×rev=3）/§7（14 条闭环 + P4 关门判定）停等该步**。本件 §5 给**逐项可安装清单**（ENG 起草，非落件）。

---

## 1. §三-1 `M-14` fail-closed（`_shared`；已落件）

**口径（#K2-34 §一-3）**：`board_path` 基址 **钉死 = 项目根**（`PM_GATE_PROJECT_ROOT` / `discover_project_root()`）；解析失败 ⇒ `BoardPathError`（禁静默 `[]` / 禁 cwd-模块相对）。

### 1.1 逐件前 → 后（`_shared`，commit `935fb2563319f51d`；k2 pin `da1e364`）

| 件 | 前 sha16 | 后 sha16 | 改动 |
|---|---|---|---|
| `pm_gate/config.py` | `69780d363e47ba26` | `cef84b16c6f74c56` | +`BoardPathError` +`board_abspath()`（基址=项目根，目标非文件即抛） |
| `pm_gate/red_team.py` | `01e15ae8a2a96f64` | `e0eb99c73de9b33f` | R13 板守卫 / R14 同源取板：坏指针 ⇒ **报 finding**（原 `return out` = fail-OPEN） |
| `pm_gate/check_qa.py` | `c21ba8ae784c607f` | `4e4ab3ad6fd87cde` | 模块相对常量 `PCB_PATH` → 惰性 `pcb_path()`（基址=项目根）＋ PEP562 兼容名 |
| `pm_gate/falsify_service.py` | `cc31a57dbf5f69a7` | `e5da7aa6278e498f` | `_snapshot` 板解析改 `board_abspath`（显式根范式） |
| `pm_gate/cli.py` | `831177187d4b56d6` | `e76ba5f2577dc0cd` | `srun` 默认板经 `board_abspath`（解析失败 rc=1）；help 记基址 |
| `pm_gate/__init__.py` | `1964872be15ce8af` | `ca5e17cac9b025a7` | `__version__ 1.0.0 → 1.0.1` |

- **零单板特判**（容器 `AGENTS.md` §3）：改动全在通用层，无 K1/K2 分支。
- **不新增检查齿**：只把 6 处既有消费者的 fail-OPEN 改 fail-closed；未动 `criteria/` rev=2 锚（`d251bea7`/`1cda6852`/`568d2e93` 复测未变）。
- `_shared` 两工作树（容器 `_shared` / `k2/_shared`）**同 sha `935fb25` 无分叉**。

### 1.2 负控 / 正控 / 存活（实跑；`/tmp/opencode/m14fix/`）

| 臂 | 布景 | 读数 | 判 |
|---|---|---|---|
| **ARM2 负控** | 坏指针（`board_path=k2_v4_NOPE.kicad_pcb`，临时 root） | `BoardPathError`；`R13` finding ×1 + `R14` finding ×1 | **置坏指针 ⇒ 链失败 ✅**（M-14 根闭条件，`#K2-30 §2.3`） |
| ARM3 存活 | 板在 + 空 registry（临时 root） | `R13: …无合法写盘登记…` ×1 | 探测器活着 ✅ |
| ARM1 正控 | 真 k2 根 | `board_abspath = …/k2/k2_v4.kicad_pcb`；`R13 = []` | 无误报 ✅ |
| ARM5 | SPEC 在 + 板缺 | `check_qa.check_g41` ⇒ FAIL「施工产物路径解析失败（fail-closed）」 | fail-closed 正方向 ✅ |

- **回归**：前/后 `red_team.run_all(k2_v4)` **逐项同**（total 4 · `R13 []` · `R14` 1 条既有 infra 项）；`engine verify k2` = **3/3 PASS**；`cli status` rc=0（无 import 崩溃）。
- **旁证（具名，裁定范围外）**：证据包 §23.6 另列 `wp1_semantics_check.py:46` / `tools_measure_l1.py` / `tools_executor_single_pair.py:17` 同属「模块相对基址」族 —— #K2-34 §一-3 具名 6 处**未含**此三者，本笔**未动**（如需追改请具名授权）。

---

## 2. §三-2 `(i-a′)` 生成器 + ⑦ `lib_id` → `l7` + `SPEC rev-52`（同笔，已落件）

**落件提交** k2 `adf2ab6`（pre-commit：PCB 变更 1 ↔ SPEC 变更 2 · meta-gate · `k2 verify` 3/3 PASS）。

### 2.1 逐件前 → 后

| 件 | 前 sha16 | 后 sha16 | 说明 |
|---|---|---|---|
| `tools/k2_gen_v5.py` | `1ca5ac79698f5873` | **`bc5dbda29cb06da0`** | `(i-a′)`：pad `at` 发射 `%.6f` 去尾零（1 nm 分辨率）；**有效 2 处 = `:339`/`:345`**；`:319` 对现行输入几何 no-op（0/54，见 2.3） |
| `tools/k2_p3_drawings_v1.py` | `00bb3245d601d775` | **`c46c0fd0fd92ef4c`** | ⑦ **1 处**：YAML footprint 串降为交叉核对；解析源 = **受审板 as-built FPID**（失败才回退，非静默 None） |
| `hw/k2_v4_8L.l7.kicad_pcb` | `<new>` | **`c5a7df90aadb66e0`** | 链产物 |
| `hw/k2_v4_8L.l7.kicad_pro` | `<new>` | **`33b4eb6cae8359a9`** | = 链 pro + 两补丁（同 l6：`rule_severities` 9 条 ignore→warning；消顶层 `sheets:[]`；`meta.filename` 派生） |
| `…/L3/SPEC_k2_v4.spec-rev-52.json` | `<new>` | **`42f8485ee4d6b566`** | rev-51 原件**逐字节不改**；差异 = 3 处 live `board_sha16` + `_spec_rev_52` 卡 |
| `k2/pm_gate/project.yaml` | `c8bc9efd669f3c2d` | **`5ceebb58eadedf11`** | `spec_name` 指针 rev-51 → rev-52 |

### 2.2 链逐段 sha（同输入必同输出）

| 段 | 器 | sha16 |
|---|---|---|
| 段1 | `k2_gen_v5.py bc5dbda2` | **`2ec9434f6d7c4354`** |
| 段2+3 | `k2_route_segment_v1.py f28a4b5a --upto all` | **`c5a7df90aadb66e0`**（`zone_filled` 10/10 · nets 101 · fps 58 · tracks+vias 5766） |
| 生成器自检 | — | **6/6 PASS**；**54 器件 · 672 pads · 100 网 · 128 NO_CONNECT · G10 8-10-4 不变** |

### 2.3 与已批干跑 `(i-a′)` 的对齐（可复核）

- 干跑件 `K2-P4-U03-IA-DRYRUN-EVIDENCE-v1`：`(i-a′)`（3 处 strip）= s1 `67f0290a0b631c09`，W-8 = `51/2/4/1`。
- 本笔（**2 处**，`:319` 保持 `%.3f`）：s1 = `2ec9434f6d7c4354` —— **仅足迹原点文本不同**（`27.940` vs `27.94`，解析值同）；**W-8 读数与干跑逐字段相同**（见 2.4）。⇒ `:319` 确为几何 no-op，`l7` 几何 == 已批干跑几何。

### 2.4 `l7` 电气级实测（喂 `lib_electrical_level` 的同一器 `75404d70`）

| 读数 | `l6`（基线） | 干跑 `(i-a′)` | **`l7` 实测** |
|---|---|---|---|
| `n_electrical_identical` | 49 | 51 | **51** |
| `n_electrical_diff` | 5 | 2 | **2** |
| `n_pad_name_set_only` | 0 | 1 | **1** |
| diff refs | C85 J3 L1 U1 U6 | C85 J3 U1 | **C85 J3 U1** |

⇒ 量化类（`L1`/`U6`/`U1` 坐标）**归零**；残余 `C85`/`J3`（pad `rot` 板 0 vs 库 180，**矩形自对称** `rel_geom_same=True`）+ `U1`（库侧**无号 `F.Paste`**，`lib_only=[""]`）= 正是 **#K2-34 §一-6 (B)** 的三条具名口径（见 §5.2）。
⇒ **`lib_electrical_level` 由 rev=2 的 `5` 降为 `2 + 1`；须 (B) 口径随 rev=3 安装后方为 0**（`l7` 实测确认）。

### 2.5 `l7` DRC（新 work-dir，`--severity-all`）

`error 0` · `unconnected 0` · 违规 **167（全 warning）**；类型集合与 `l6` 相同，`track_not_centered_on_via` **30 → 33**（具名如实登记；皆在 #K2-34 §一-7 登记的 7 类内，登记制不豁免）。

---

## 3. §三-5 P3 图集重发（`l7`；与 ⑦ 同批，已落件）

- `…/L3/drawings/p3_drawings.json`：`e284e9afd9054408` → **`3f6a27046ba58945`**；`01_board_frame_and_holes.svg` · `05_pour_strategy.svg` 同步重发。
- **仅 J3/J4 的封装解析变**（`footprint` YAML 串 → 板 as-built `…_RASide__1`/`__2`；`footprint_file` → 对应 `__N` mod）；**其余 52 件 footprint 键逐件同值**（落件前 diff 断言，符合证据包 #2 §3）。
- `unresolved_footprint = 0`；无新增 `literal_mismatch`（`U1`/`U2` 为既有有向口径登记项）。
- **确定性**：同输入两次连跑（图集器）**逐字节同**（JSON + 7 SVG 全同）。

---

## 4. §三-6 确定性（链产物；已实跑）

| 跑 | 布景 | 段1 sha16 | 段2+3 sha16 |
|---|---|---|---|
| #1 落件跑 | 常态 | `2ec9434f6d7c4354` | `c5a7df90aadb66e0` |
| #2（RUN-A） | 常态 | `2ec9434f6d7c4354` | `c5a7df90aadb66e0` |
| #3（RUN-B） | **撤 `l4`/`l5` 三臂**（板+pro 移走） | `2ec9434f6d7c4354` | `c5a7df90aadb66e0` |

⇒ **两次连跑逐字节同 + 撤三臂同 sha**（链**不依赖** `l4`/`l5`）；`trap` 无条件还原后复核：`l4 pcb d4e81f64` ✓ · `l5 pcb dae8dc8d` ✓ · `l5 pro 35c8f34b` ✓。

---

## 5. **§三-3 停等：`criteria` rev=3 安装（gate 属主 + 监理签认；ENG 不落件）**

> 依据：#K2-34 §三-3。**ENG 只读 `criteria/`**（红线）⇒ 本节为 **ENG 起草的可安装清单**，供 gate 属主原子安装 + 监理签认 + 锚 rev=3。

### 5.1 `criteria/manifest.k2.yaml` rev=3 应含（6 项）

1. `density_and_clearance`：`enabled: false → true`；删 `pending`；`expect: "band_occupancy.max_ratio <= max_fp_per_cell ∧ min_copper_clearance_mm >= 0.100"`；阈值**沿用** `thresholds.density_and_clearance`（`cell_mm=10` · `cell_origin=frame_origin` · `max_fp_per_cell=8` · `min_copper_clearance_mm=0.100`；#K2-23 §二-9）。证据：`l6` `band_occupancy.max_ratio 0.07586`（3 带）· 最小铜间距 bracket **[0.100,0.105] ≥ 0.100**。
2. `ref_plane_continuity`：`enabled: false → true`；删 `pending`；**具名写入判别半径 `R=0.5 mm`**，口径 = **`non_antipad_gap == 0`**（#K2-34 §一-1）。监理独立复跑：`R=0.5 ⇒ 0.0`；`R=0.25 ⇒ 20.8905 FAIL`；负控冻结 `l4 ⇒ 798.17 mm² FAIL`。
3. `drc_warning_dispositions`：**+7 条**（登记制、**均不豁免**；字段同 rev=2 现行两条）：`silk_over_copper` · `silk_overlap` · `silk_edge_clearance`（丝印图形级，**P5 出图前处置**）· `track_not_centered_on_via` · `via_dangling` · `track_dangling` · `copper_sliver`（布线级，归链内路由器/PDN 步，逐条台账留痕）。可直接粘贴块见 `K2-P4-PRERULING-EVIDENCE-PACK-5-v1.md` §1.2。
4. **(B) 判据侧具名口径**（#K2-34 §一-6；**非新增齿、非缩口径**）：`lib_electrical_level` 消费 W-8 证据时按三条裁决 —— ① 审计容差 **≤0.0005 mm**（表示差异）；② **矩形 pad `rot 0≡180`**（`rel_geom_same=True`）；③ **无号 `F.Paste` 非电气**（`lib_only` 全空串 ⇒ 不计入 `n_pad_name_set_only`）。`l7` W-8 记录已足够实现：残余 3 件的 `diffs[].fields == ["rot"]` + `rel_geom_same=True`，`U1` `diffs[].lib_only == [""]`。
5. `board: k2_v4_8L.l5.kicad_pcb → k2_v4_8L.l7.kicad_pcb`（#K2-34 §三-3⑤；注意 `adjudicate.py` 的 verdict board 取 `--board` 实参，本字段为形式项）。
6. `countersigned_scope.covered`：`+ density_and_clearance + ref_plane_continuity`（=> covered 19 / uncovered 0）；bump `manifest_version`；`criteria/CHANGELOG` 追加 `rev=3` 条。

### 5.2 安装后 ENG 立即可执行的 §三-4/§7（就绪，勿需新裁定）

- §三-4 **全链重锚（`l7` × rev=3）**：19 维标准调用（期望 **0 FAIL**）· DRC · 5 件测量（`pads_within_outline` / `ref_plane` / `density` / `min_clearance` / W-8）· **测量册再重锚**（`…/L4/E3-standard-call-l7-<date>/`）· C1/C2/L-1 · `engine verify k2` ⇒ 逐项报前后 sha + PASS/FAIL 集。
- §三-7 **闭环表 14 条闭 + L-1 具名接受（C4）** ⇒ **P4 关门判定（报监理）**。
- 命令已由 `K2-P4-PRERULING-EVIDENCE-PACK-6-v1.md` §2.3 备好（本笔仅改板/pro/SPEC 指针；器 sha 未变）。

---

## 6. 边界（本笔）

- **已改**：`_shared/{config,red_team,check_qa,falsify_service,cli,__init__}.py`（`935fb25`）· k2 pin `_shared`（`da1e364`）· `k2_gen_v5.py` · `k2_p3_drawings_v1.py` · `hw/k2_v4_8L.l7.kicad_pcb` · `hw/k2_v4_8L.l7.kicad_pro` · `L3/SPEC_k2_v4.spec-rev-52.json` · `pm_gate/project.yaml` · `L3/drawings/{p3_drawings.json,01,05}` · 本件。
- **未改**：冻结四源（`l4 d4e81f64` · 设计源板 `fb07d25a` · 真源 `dd794c54` · 判据 rev=2 `d251bea7`/`1cda6852`/`568d2e93`）· 历史件 `l5`/`l5 pro` · 库快照 · `criteria/**` · 真源 yaml · 段2 器 `f28a4b5a`；**未出 Gerber**；**未派 WORKER**；未新增检查齿；未以「接近 0」充绿。
- **旁证**：① 容器超项目 pin（`_shared`/`k2`）**未由 ENG 提交** —— 容器根 pre-commit 的 affected 判定把 `_shared` 变更判给 k2 并以容器 cwd 跑 `engine verify`（路径基址 = 容器根 ⇒ `FileNotFoundError`），属**已知调用口径问题**（`K2-P4-CLOSURE-FORMALITY-FACTS-v1`），且 handoff §8-② 记「容器 `k2` 指针滞后（刻意，监理排程）」⇒ 循前例留监理/哨兵；② `hw/k2_v4_8L.l7.kicad_prl`（KiCad 本地态）**未跟踪、未入库**。

—— ENG（ARCHER）· 2026-09-19 · k2 `adf2ab6` · `_shared 935fb25` · 受审板 `l7 c5a7df90aadb66e0` · 判据锚 rev=2 · **停等 §三-3（gate 属主 rev=3）**
