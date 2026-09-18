# K2 · P4 · **`D-4b` 语义两案候选 ＋ 对照预演**（`cmd_verify` 是否执行 `checks`；3 引擎 × 2 探针）· v1 · 2026-09-18

> 缘起：handoff inc65 §6-3-(o)「`D-4b` **语义两案候选实现 + 对照预演**（§5-D(ii)：`cmd_verify` 跑**全部 phase** 的 `checks` vs **仅 verify phase**；参照 D-7 的开关式手法，出两案 `/tmp` 预演，**不落件**）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 引擎副本**，仓库零载体改动（仅新增本证据件）。
> 锚：repo 引擎 `_shared/eda_core/pipeline/engine.py` **`97baca95a0b9bda7`** · 案A 引擎见 inc57 §2 文本 ⇒ `/tmp/opencode/inc58/shared_full/…/engine.py` **`a015f8cfcc24c581`**（已在 inc58 端到端验证）· **案B 引擎（本件新增）`19ff1a882220ad25`** · `checks.py`（三案**同一份**）`0cbd9a478c694a12`（＝inc50 D-7 ① ② ③ 开关式 ＋ inc52 D-2 各处缺件 guard）。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/sandbox/sem/{caseRepo,caseB,root,root2,run.py,matrix.log}` · 矩阵日志 `matrix.log`（`P1` 语义探针 / `P2` 真承载体形状）。
> **归属**：`D-4b` 语义澄清＝**判据语义澄清域（#K2-19 §〇 二分）＝监理自有权**；ENG 只出候选与证据，**不择一**。

## 0. 结论（六条）

1. **两案都严格于原版**：原版引擎在**提交路径**（hook → `cmd_verify`）上 **`checks` 全不执行**（＝ `D-4b` fail-open）；案A/案B 至少让「声明了 `verify` 的 phase」的 `checks` 跑起来。
2. **两案的差异面可精确表述、且可观测**：唯一差异＝**「无 `verify` 的 phase」（如 `preflight`）的 `checks` 是否在提交路径执行**。
3. **P1 语义探针实测（决定性）**：`preflight.checks=[cmd:false]` ＋ `verify.checks=[cmd:true]` ＋ `verify.verify=[cmd:echo]`
   - **原版** rc=**0**，输出仅 `verify/cmd: PASS` ⇒ **checks 一行都不跑**（fail-open 复现）；
   - **案A** rc=**1**，`preflight/check[cmd]: FAIL` ⇒ 「全 phase checks」确被执行；
   - **案B** rc=**0**，`verify/check[cmd]: PASS` ＋ `verify/cmd: PASS` ⇒ 有 `verify` 的 phase 的 `checks` 跑了，**`preflight` 的 checks 未跑**。
4. **P2 真实承载体形状实测（变体②＝乙＋`D-7a`）**：三案 rc 均 **1**（唯一失败＝**⑤**，2 行）；**唯一输出差异**＝案A 多出 **`preflight/check[project_sch_coverage]: PASS`**；案B 与**原版完全同形**（该检查在提交路径仍不执行）。
   ⇒ **若采案B，本板 `project_sch_coverage` 这一必选 sch 检查在提交路径仍不执行**，即 **J-9「门禁接入＝必选检查真被执行」对本板仍不成立**（与 inc57 §2 判断一致）。**ENG 建议案A，但裁决归监理。**
5. **案A 的通用风险（须监理权衡）**：它会**无条件执行无 `cmd` 的 phase 的 `checks`**。若某 check 语义是「该 phase 的 `cmd` 跑完才成立」，在提交路径（不跑 `cmd`）就会**误 FAIL**。本板 `preflight` 无 `cmd`、其 check 为**声明覆盖类**、不依赖产物 ⇒ 无此风险；但**通用语义**须监理明确（这正是「仅 verify phase」口径的理由）。
6. **案B 的风险**：`preflight` 类前置门禁在提交路径**永不执行** ⇒ 「文件装了、检查没跑」的 **C-12 同型 fail-open 未被消除**。两案各有代价，故本件**不新增检查齿**（owner ②），只固化为可复现的两案。

## 1. 两案精确 diff（`engine.py::cmd_verify`）

**基线（repo 原版 `97baca95a0b9bda7`）**：`cmd_verify` 只遍历 `ph.get("verify", [])`，**从不读 `checks`**。

**案A `a015f8cfcc24c581`（＝inc57 §2 文本；遍历全部 phase 的 checks）**：
```diff
     for ph in cfg["phases"]:
+        # D-4b 修正: checks 是提交期前置门禁 ⇒ cmd_verify (hook 唯一入口) 必须先跑,
+        #            否则 checks 段在**提交路径**上永远是纯声明 (fail-open)
+        for spec in ph.get("checks", []):
+            ok, detail = _run_check(cfg, spec)
+            print(f"  {ph['id']}/check[{spec.get('type')}]: {'PASS' if ok else 'FAIL'}")
+            if not ok:
+                print("    " + detail.replace("\n", "\n    "))
+                return 1
         for spec in ph.get("verify", []):
             ok, detail = _run_check(cfg, spec)
             print(f"  {ph['id']}/{spec.get('type')}: {'PASS' if ok else 'FAIL'}")
```

**案B `19ff1a882220ad25`（本件新增；仅「含 verify 的 phase」才跑其 checks）**：
```diff
-        # D-4b 修正: checks 是提交期前置门禁 ⇒ cmd_verify (hook 唯一入口) 必须先跑,
-        #            否则 checks 段在**提交路径**上永远是纯声明 (fail-open)
-        for spec in ph.get("checks", []):
-            ok, detail = _run_check(cfg, spec)
-            print(f"  {ph['id']}/check[{spec.get('type')}]: {'PASS' if ok else 'FAIL'}")
-            if not ok:
-                print("    " + detail.replace("\n", "\n    "))
-                return 1
+        # D-4b【案B 口径】: 仅**声明了 verify 的 phase** 才在提交期跑其 checks
+        #                    ⇒ 无 verify 的 phase(如 preflight) 的 checks 仍不在提交路径执行
+        if ph.get("verify"):
+            for spec in ph.get("checks", []):
+                ok, detail = _run_check(cfg, spec)
+                print(f"  {ph['id']}/check[{spec.get('type')}]: {'PASS' if ok else 'FAIL'}")
+                if not ok:
+                    print("    " + detail.replace("\n", "\n    "))
+                    return 1
```

**两案在提交路径的检查集合**（`checks` 段语义）：

| `pipeline.yaml` 形状 | **原版** | **案A** | **案B** |
|---|---|---|---|
| `phase(preflight, checks=[X])` | X **不跑** | X **跑** | X **不跑** |
| `phase(verify, checks=[Y], verify=[Z])` | 仅 Z | Y ＋ Z | Y ＋ Z |
| `phase(gen, cmd=…, checks=[W])`（提交路径无 cmd） | W 不跑 | W **跑**（无 cmd 上下文） | W **不跑**（无 verify ⇒ 跳过） |

## 2. 复现矩阵（3 引擎 × 2 探针；`K2_NC_SOURCES=top,placements`）

```bash
cd /home/fila/jqdDev_2025/ic_hw && python3 /tmp/opencode/inc63/sandbox/sem/run.py
```
```
########## P1 ##########
--- 原版引擎+全修checks 97baca95: rc=0
    verify/cmd: PASS
    verify 完成: 1 项检查全 PASS
--- 案A 全phase a015f8cf: rc=1
    preflight/check[cmd]: FAIL
        cmd rc=1
--- 案B 仅verify-phase 19ff1a88: rc=0
    verify/check[cmd]: PASS
      verify/cmd: PASS
    verify 完成: 1 项检查全 PASS

########## P2 ##########
--- 原版引擎+全修checks 97baca95: rc=1
    verify/sch_structural: PASS
      verify/netlist_connect: FAIL
        netlist 连接校验失败 2 处:
          网 'PWR_5V_KEY' 在 KiCad netlist 中不存在
          非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单
--- 案A 全phase a015f8cf: rc=1
    preflight/check[project_sch_coverage]: PASS
      verify/sch_structural: PASS
      verify/netlist_connect: FAIL
        netlist 连接校验失败 2 处:
          网 'PWR_5V_KEY' 在 KiCad netlist 中不存在
          非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单
--- 案B 仅verify-phase 19ff1a88: rc=1
    verify/sch_structural: PASS
      verify/netlist_connect: FAIL
        netlist 连接校验失败 2 处:
          网 'PWR_5V_KEY' 在 KiCad netlist 中不存在
          非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单
```

**探针定义**：`P1`＝`preflight.checks=[{cmd: "false"}]` + `verify.checks=[{cmd: "true"}]` + `verify.verify=[{cmd: "echo VERIFY_RAN"}]`（把语义差异从 ⑤ 噪声中隔离）· `P2`＝真实承载体形状（`preflight.checks=[project_sch_coverage]` + `verify.verify=[sch_structural, netlist_connect(errata-1), bom_consistent]`）。
**三引擎同 checks**：`caseRepo`（原版 engine ＋ 全修 checks）· `caseA`（`a015f8cf`＋全修 checks）· `caseB`（`19ff1a88`＋全修 checks）⇒ 差异**只来自 engine**。

## 3. 影响面（通用）

1. **本板（k2 变体②）**：`project_sch_coverage` 位于 `preflight.checks` ⇒ **案A 才在提交路径执行**；案B 与原版同形。
2. **`cmd_run` / `cmd_preflight` 路径**：`checks` 由 **`D-4` 修正**（inc51，`cmd_run` 内）已在岗 ⇒ 本件两案只影响 `cmd_verify`（**hook 唯一入口**），两处**不会重复执行**（提交路径 `cmd_run` 不跑）。
3. **通用项目**：若项目把「生成前置输入检查」写在带 `cmd` 的 phase 的 `checks` 里，案A 会在提交路径无产物时执行它 ⇒ 可能误 FAIL；案B 无此风险但会让此类门禁在提交路径缺岗。**这是监理需在 `D-4b` 语义上拍板的唯一实质点。**
4. **与 `D-3`/`D-4`/`D-2`/`D-7` 的关系**：`D-3`（hook `affected`）决定「跑不跑」；`D-4`（`cmd_run`）/`D-4b`（`cmd_verify`）决定「`checks` 跑不跑」；`D-2`（缺件 guard）决定「缺件是干净 FAIL 还是抛异常」。四者须**同一笔共享层修**落库（inc57 §3 硬序）。

## 4. 与共享层一次派单件的关系

| 项 | 归属 | 本件贡献 |
|---|---|---|
| `D-4b` 修正本体（`cmd_verify` 读 `checks`） | 共享层属主 | 两案候选 + 隔离矩阵（**语义选择待监理**） |
| `D-4b` 语义（全 phase / 仅 verify phase） | **监理（判据语义澄清域）** | 本件 §0-5/§0-6 的代价分析 + P1 探针 |
| 与 `D-2/D-3/D-4/D-7` 合批 + `D-5` pin 前移 | 共享层属主 + 落件手续 | 顺序见 `K2-P4-G11-D3-D4-MERGED-LANDING-DRAFT-v1.md` §3 |

## 5. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/sandbox/sem/run.py            # 3 引擎 × P1/P2 矩阵（期望见 §2）
# 单案直跑（例：案B 在 P1）
python3 -c "import sys;sys.path.insert(0,'/tmp/opencode/inc63/sandbox/sem/caseB');from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))"   # 需在探针仓库根执行（/tmp/opencode/inc63/sandbox/sem/root）且 PYTHONPATH/SHARUN 与 §2 一致
sha256sum /tmp/opencode/inc58/shared_full/eda_core/pipeline/engine.py /tmp/opencode/inc63/sandbox/sem/caseB/eda_core/pipeline/engine.py | cut -c1-16
```

## 6. 边界

本件**只读 + `/tmp` 引擎副本/探针仓**：未改 `_shared/**`、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`、闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 案A `a015f8cfcc24c581` · 案B `19ff1a882220ad25` · repo `97baca95a0b9bda7`
