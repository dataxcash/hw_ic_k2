# K2 · P1–P5 阶段门回溯 + C-1 落件前控 + 非 HS 回归旁证（2026-09-21）

**性质**：只读实测报告（handoff §8 无裁定路 ①②③）。**未改**任何真源 / 判据 / 生成器；`criteria/` ENG 仍只读；批 6 落件候选 **未落**（待监理放行）。
**裁定依据**：最新权威裁定 = **#K2-43**（2026-09-20 16:55）；`.ruling-ids/k2-44..47` 为**空登记**（无对应裁定件）⇒ 非放行；故走 handoff §8「无裁定路」。

## 0. 本会话唯一流程动作（非只读）
**推 origin（补备份）**：#K2-15 §三 要求 —— 落件前该仓有未推送提交，工作成果**无备份**。
- `_shared` `fc59771..02459f5` · `k1` `16d7b7c..dc720fd` · `k2` `f308222..8637aad`（共 68 笔）⇒ 全部推送成功（pre-push meta-gate 通过）。

## 1. 阶段门状态表（live 实测）
| 阶段 | 判据 | 本会话实测 | 判 |
|---|---|---|---|
| **P0** | 基线账本 + 冻结件未动 | `l4 d4e81f64…` · 设计源 `fb07d25a…` · `k2_sch dd794c54…` · `l7 c5a7df90…` 逐字节同 | **HOLDS** |
| **P1** | 负控/正控/权限/fail-closed + rev=3 | 负控：冻结 **l4** 跑判定器 ⇒ **rc=1 FAIL**（`zone_filled 0/9`·`device_has_pads 5 颗`·`drill_count 0/0`·`net_declared_realized 10 条`·`pin_map 50 节点`+10 项）· 正控：**伪造 verdict 件被拒**（`verdict_schema` FAIL rc=1）· 权限：`criteria/` **444/555 ic_hw_gate** · fail-closed：缺测量件 4 维拒 · `verify k2` PASS | **HOLDS** |
| **P2** | 四等式 0 差异 | #K2-15 关门；现行 l7 上 `refdes_sets_equal` 差 0 · `net_declared_realized` 0 · `pin_map_complete` 0 | **HOLDS**（见下注） |
| **P3** | 板框/NPTH/出框/keepout/走廊口径 | `SPEC_k2_v4.json` `outline_x[23,143]`·`outline_y[33,79]` ⇒ **120×46** ✓ · l7 **NPTH=4×Ø3.2** ✓ · 出框 0/0/0 ✓ · keepout 8 区无 all-allowed ✓ · 走廊口径 = #K2-28 | **HOLDS** |
| **P4** | 全 J 类 + V1/V2/V3 绿 | **canonical 19 本会话实跑 = 19 OK/0 FAIL** · verdict **`190b73be0f728a56`**（= 签认值）· 铺铜 10/10 · NPTH=4/PTH=16 · 平面 G36：In1/In3/In6 各 1、In4 9 · DFM **16 PASS/1 ACCEPT/0 FAIL** · 包 53 件 | **HOLDS** |
| **P5** | V4–V7 外部实测 | `L6/first_article/results_template.json`：**全 NOT_RUN** · 实测方 = 外部 · 判 = 监理 | **PENDING_EXTERNAL**（#K2-38/39） |
| **P6** | ① k1 四项同源命中 ② 模板 ignore 集 == 应然集 | **② LIVE PASS**：`k2_p6_2_acceptance_v1.py` ⇒ k2 模板 `ignore=0` · 差异 0/10 · 对空应然集差异 0/10 ⇒ `PASS(state)`。 **① LIVE PASS**（**新读数**）：以**现行** `criteria/manifest.k1.yaml`（`c175be51` · countersigned）重出 k1 verdict（`provisional=False`）⇒ `k2_p6_1_acceptance_v1.py` **四项命中全 OK + dim_set 19 + manifest_countersigned OK ⇒ PASS（rc=0）** | **判据面 PASS · 覆盖待放行** |

### 两个口径观察（**不新增检查齿**，owner ②）
1. **P1 判据① 第 6 类 `ignore_without_ruling(9)` 在 k2 侧已消失**：模板整改（O1）已落件 ⇒ 缺陷不存在（l4 读数 `rule_severity_manifest 0/62`）。属「修好了」，**不得**为凑负控新增齿。
2. **P2 原命令 `criteria/measure_source_reconcile.py` 从未落件**：四等式现由 rev=3 三维（`refdes_sets_equal`/`net_declared_realized`/`pin_map_complete`）承接 ⇒ 判据「换址」，非缺失。（属口径澄清 = **监理自裁项**。）

### 越阶段风险
无。P1→P4 判据全在岗且 live 复现、值未动；P5 未被跳过（保持 NOT_RUN）；P6 判据面 PASS 而覆盖面待放行 ⇒ **未见「未过门先开工」**。

## 2. C-1 落件前控复跑（§8②，不写 `criteria/`）
以已落件 checker（`_shared/eda_core/truth_binding.py` · `02459f5`）在**真实数据**上复跑：
| 控制 | 读数 | 判 |
|---|---|---|
| 正控（17 条拟声明） | `17/19 已声明` · 17 条**零违规**；仅剩 2 维无外部真源 | ✅ 与提案一致 |
| 负控·包内自证 | `density_and_clearance` 真源落交付包内 ⇒ **拦住** | ✅ |
| 负控·现行 rev=3 | `0/19 已声明 · 19 违规`（= before 读数） | ✅ |
| 负控·真源=受审板 | **拦住**（自证循环） | ✅ |
| 负控·真源缺件 | **拦住**（fail-closed） | ✅ |
⇒ **C-1 真残面 = 「2 维缺外部真源件」，非 checker 缺齿**；gate 属主 4 步动作不变。

## 3. 非 HS 网/对回归旁证（§8③）
- **改动面**：v4 只动 `_shared/eda_core/hs_route_model.py`（10 hunk）；`pristine dcd1f65f… → patched c9e1c3b4…`（**本会话 `patch -p1` 镜像复现，逐字节同**）。
- **入口范围**：`route_model_config.json` `hs_prefixes = [PCIE, REFCLK]` ⇒ 模型只走 HS 前缀网。
- **网普查**：`k2_sch.yaml` 101 网 = HS 68 + **非 HS 33**（GND/P3V3/I2C/UART/SWD/strap…）⇒ **无一条落在被改代码路径内**。
- **动态面**：canonical 19 逐字节同等 · `test_hs_route_model.py` 2F/61P/12S 与 pristine 同 · 两处共享路径改动均以 `v4_project_dim()=="k1"` 显式域限定 ⇒ K2 域 no-op。
⇒ **旁证成立**：非 HS 网既有读数不因 v4 落件而变。

## 4. 交件
- `P1_P5_STAGE_GATE_RETROSPECT_20260921_v1.json`（`62659de5313635d2`）
- `C1_DIM_CHECKER_CONTROLS_RERUN_20260921_v1.json`（`cd04b7da7d00ffe9`）
- `NONHS_SCOPE_CENSUS_20260921_v1.json`（`786d86afac55dee0`）

## 5. 仍未闭（待监理裁 · 均为 L2/机制面，非 owner 闸口）
① 放行 **批 6 v4 落件**（`3ded8584bb74461f` → `c9e1c3b4ca208482`；手册 7 步已备）② R-5/C-1 2 维落件（gate 属主 4 步）③ R-4 批 5 暂缓 ④ R-8 三选一 ⑤ (c)/alloc 授权。**无 owner 项**。
