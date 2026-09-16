# P1 执行证据：判据体系落地 + 正/负控 + 权限隔离（D-1 落地版 v2）

- **依据**：#K2-07 §二「**P1 即刻放行**（D-1 已批）—— 按计划 P1 的四项完工判据执行」+ owner 裁定 D-1 = 批准**执行主体分离**（独立账号 / CI 持有判据与账本）
- **本件性质**：ENG 侧实现（起草判定器 + 建 gate 账号 + 移交判据归属）+ 只读取证 + 文档。**未改判据内容、未改板、未改生成器、未改 SPEC/原理图。**
- **冻结件 sha**：`k2/hw/k2_v4_8L.l4.kicad_pcb` = `d4e81f647be7f9809aef72affb55fdf442a0cf743baead02d8e44fb130de18fc`（未变）

## 0. 结论表（P1 四项完工判据 · 隔离改造**后**复跑）

| # | 判据 | 结果 | 原始证据 |
|---|---|---|---|
| 1 | **负控**：判定器跑冻结板 → `rc≠0` 且失败项 ⊇ 6 类 | **PASS**（rc=1，命中 **9 类**，含要求的全部 6 类） | `controls_after.txt` [1] |
| 2 | **正控**：伪造的绿必须被拒 | **PASS**（rc=1，`verdict_schema` 抓出 `fake_green.json`） | `controls_after.txt` [2] |
| 3 | **权限**：ENG 不可写判据 | **PASS（literal）** `test -w` × 3 全 rc=1；普通写入被拒 | `controls_after.txt` [3] |
| 4 | **fail-closed**：缺件 / 无门禁 → FAIL（不得跳过） | **PASS**（FC-1/2/3 全 rc=1） | `controls_after.txt` [4] |

> **附**：判据可**在隔离域执行** —— `sudo -u ic_hw_gate python3 criteria/adjudicate.py …` rc=1，与 ENG 侧同结论（`controls_after.txt` [3']）。
> **限定**：manifest 仍 `not_countersigned: true` ⇒ 判定器输出标注 **PROVISIONAL**；**请监理签认**后转为正式判定（判据 1–4 的机制结论不因此改变）。

## 1. 交付物（ENG 侧）

| 文件 | 归属 | 状态 |
|---|---|---|
| `criteria/adjudicate.py`（333 行，sha256 见下） | **ENG 起草**（裁定 §四-2） | 待监理以正/负控**验收后冻结** |
| `criteria/manifest.k2.yaml` | **监理持有**（应然值/豁免） | **`not_countersigned: true`**；ENG 仅**转写**登记册 §C，未新增判据维度 |
| `/tmp/opencode/k2p1/controls_before.txt` · `controls_after.txt` | 证据 | 改造前 / 改造后四组原始输出 |
| `/tmp/opencode/k2p1/measure_k2.json` · `verdict_k2.json` | 测量/判定 | **测量件不含 `verdict` 字段**（C4） |

## 2. D-1 落地记录（**本轮新增**：执行主体分离）

| 项 | 值 |
|---|---|
| gate 账号 | `ic_hw_gate`（`uid=998(ic_hw_gate) gid=998(ic_hw_gate)`，system、`/usr/sbin/nologin`、home `/var/lib/ic_hw_gate`） |
| 判据归属 | `criteria/` 属主 `ic_hw_gate:ic_hw_gate`；目录 `dr-xr-xr-x (0555)`；`adjudicate.py` / `manifest.k2.yaml` `-r--r--r-- (0444)` |
| ENG 侧实复测 | `test -w criteria/manifest.k2.yaml` → **rc=1**；`test -w criteria/adjudicate.py` → **rc=1**；`test -w criteria` → **rc=1**；`echo x >> criteria/manifest.k2.yaml` → **被拒** |
| 判据账本位 | `.omo/supervision/ledger/adjudication-ledger.jsonl` **尚未建立**（该路径属 `.omo/supervision/**`，ENG 红线内**不可写**，须由监理/gate 侧建立）；`test -w` 现 rc=1 |

## 3. 残余提权面（**诚实取证；决定 ⑥ 的真实强度**）

隔离改造后，**工作账号 `fila` 仍有 3 条独立 root 通路**，实测全部可用：

```
$ sudo -n true                                  -> rc=0        （/etc/sudoers.d/fila = fila ALL=(ALL) NOPASSWD:ALL）
$ sudo -n -u ic_hw_gate id                      -> uid=998(ic_hw_gate) ...   （可**变成判据属主**）
$ timeout 10 docker ps                          -> rc=0        （docker server 28.2.2；docker 组 ≈ root 等价）
$ timeout 10 virsh -c qemu:///system list       -> rc=0        （libvirt 组可用）
$ groups                                        -> fila adm sudo kvm lpadmin docker libvirt davfs2
```

**结论（工程事实）**：`chown/chmod` 把判据放进了独立账号，**挡住了普通写与误写**；但只要 `fila` 保有 **sudo / docker / libvirt** 任一条通路，**结构性隔离不成立**——同一账号可 `sudo -u ic_hw_gate`（或经 docker 挂载宿主根）改回属主与权限位。

⇒ 本件**不把 ⑥ 包装成"已完成"**。三条通路**全部**属于**用户环境级改动**（会取消该账号的 sudo / docker / virsh 使用能力），**ENG 不单方面执行**。

| 选项 | 做法 | 强度 | 代价 |
|---|---|---|---|
| **(a) 全面收回** | 删/禁 `/etc/sudoers.d/fila` + 移出 `docker` 组 + 移出 `libvirt` 组 | **强**（本机唯一强解） | 该账号失去 sudo / docker / virsh；须另备 root 入口 |
| **(b) 离机 CI** | 判据与判定器跑在 CI runner | **强** | 需搭建 runner/凭据（本机无 runner） |
| **(c) 角色纪律** | ENG 只交测量件；判定由监理在自身会话执行 | **中**（自觉条款，须如实标注） | 最低 |

## 4. 附带发现（跨板，供 §⑦ 使用）

`pipeline_present` 的 fail-closed 扫描命中 **6 个目录**含 `.kicad_sch` 却无 `pipeline.yaml`：
```
k1/sch, k2/hw/sch, pciesw4/aic, pciesw4/aic/sch_kicad, pciesw4/gpu
```
⇒ `pciesw4` 亦属同源缺陷（跨板覆盖范围应从 K1 扩到 pciesw4）。

## 5. 待监理动作

1. **签认 manifest**：`criteria/manifest.k2.yaml` → `not_countersigned: false`（该文件现属 `ic_hw_gate`，ENG 侧不可写；请以 gate/root 主体改）；
2. **验收判定器**（正/负控已按四项判据复跑通过，请复核是否达到冻结标准）；
3. **裁定 §3 的隔离强度**（(a) 全面收回 / (b) 离机 CI / (c) 角色纪律），我据此收口计划 §6.3。

---
**复跑命令（可逐条复核）**
```bash
ARGS="--project k2 --board k2/hw/k2_v4_8L.l4.kicad_pcb --pro k2/hw/k2_v4_8L.l4.kicad_pro \
      --nets k2/hw/data/k2_sch.yaml --sch-dir k2/hw/sch"
python3 criteria/adjudicate.py $ARGS --out /tmp/opencode/k2p1/verdict_k2.json                 # [1] 负控 → rc=1
python3 criteria/adjudicate.py $ARGS --artifacts /tmp/opencode/k2p1/fake_green.json           # [2] 正控 → rc=1
test -w criteria/manifest.k2.yaml ; echo $?                                                   # [3] 权限 → 非 0
python3 criteria/adjudicate.py --project k2 --manifest /tmp/opencode/nonexistent.yaml          # [4] FC-1 → rc=1
```

## 6. ENG 自述：需求 → 实现 映射（**供监理验收冻结**，2026-09-16）

> 本表是 ENG 对自身起草件的**自述**，供监理逐条验收；**阶段门由监理判定，ENG 不自判**。
> 认定「已实现」的证据均在 §2 / §5 的原始输出中可复跑。

| 计划要求（出处） | 实现位置 `criteria/adjudicate.py` | 状态 |
|---|---|---|
| §三-1 判据放只读位 | 非代码：文件系统属主 `ic_hw_gate` + `0555/0444` | **已落地**（ENG `test -w` × 3 全 rc=1） |
| §三-1 运行副本置 ENG 写域外（D-1） | `sudo -u ic_hw_gate python3 criteria/adjudicate.py …` | **已落地**（隔离域可运行，rc=1 同结论） |
| §三-2 变更留痕 `criteria/CHANGELOG` | **无**（文件不存在） | **FINDING-1（未实现）** |
| §三-2 判定器校验 manifest sha ↔ 账本锚 | **无**（全文件无 `sha`/`anchor`/`ledger` 逻辑） | **FINDING-2（未实现）** |
| §三-3 产物无 `verdict` 字段 | `scan_verdict_keys()` → `verdict_schema` | 已实现（正控实测抓出 `fake_green.json`） |
| §三-3 交付包内**唯一** verdict | **无**（无交付包级检查） | **FINDING-3（未实现）** |
| §三-4 deny-by-default（`ignore` 无台账 → FAIL） | `manifest.rule_severity_exemptions` + `rule_severity_manifest` | 已实现（负控实测 9 条全判 FAIL） |
| C1 判据不在被审对象里 | 以「`.kicad_pro` 的 ignore 集 == manifest 豁免集」**集合比对**实现（`measure_rule_severities`） | **部分**：`ignore` 面已结构性封死；计划 §3.4 所述「**副本上覆盖 severity 后跑 DRC**」未实现 ⇒ **FINDING-4** |
| C2 豁免须登记 | 同 §三-4（空豁免集 = 不许任何 ignore） | 已实现 |
| C3 fail-closed（缺件/未接线 ⇒ FAIL） | `main()` 缺 manifest/board ⇒ rc=1；`pipeline_present` 扫描 | 已实现（FC-1/2/3 实测） |
| C4 产物无 verdict | 测量件 `_note` 明示不含 verdict；`scan_verdict_keys` | 已实现 |
| C5 交付包唯一 verdict | **无** | **FINDING-3（未实现，与 §三-3 交付包检查同项）** |

**FINDING 汇总（交监理处置：采纳 / 退回 / 转下阶段；ENG 不自行修补）**

- **FINDING-1** `criteria/CHANGELOG` 缺件。草稿已产出：`/tmp/opencode/k2p1/CHANGELOG.draft`（含规则 + 两条初始条目），**待以 gate 主体安装为 `criteria/CHANGELOG`（0444）**。理由：`criteria/` 属 gate，ENG 侧只读（红线），故 ENG 只交草稿。
- **FINDING-2** manifest sha ↔ 账本锚未实现。依赖 `.omo/supervision/ledger/adjudication-ledger.jsonl`（**监理写域，不存在**）⇒ 现阶段无可校验之锚。
- **FINDING-3** C5「交付包内唯一 verdict」未实现（无交付包级扫描）。
- **FINDING-4** C1 的「副本覆盖 severity 后跑 DRC」未实现；现形态**只覆盖 `ignore` 语义**（把 severity 改成 `ignore` 必被抓住；改成其他档位不被抓）。

> 上述 FINDING 均**未**影响 P1 四项完工判据的实测结果（§0），但属**计划 §3.4 设计要求与实现的差距**，如实登记，供监理验收时裁定。

## 7. 交接清单（三项均非 ENG 可独立完成）

| # | 事项 | 主体 | 说明 |
|---|---|---|---|
| H1 | 签认 `criteria/manifest.k2.yaml`（`not_countersigned` → `false`） | 监理 | 该文件现属 `ic_hw_gate`（0444），须以 gate/root 主体改 |
| H2 | 验收并冻结 `criteria/adjudicate.py`；建 `criteria/CHANGELOG`；建 `.omo/supervision/ledger/adjudication-ledger.jsonl` | 监理（gate 写域） | CHANGELOG 草稿见 `/tmp/opencode/k2p1/CHANGELOG.draft` |
| H3 | 裁定 ⑥ 隔离强度：(a) 全面收回 `fila` 的 sudo+docker+libvirt ／(b) 离机 CI ／(c) 角色纪律 | **owner** | 见 §3；ENG 不单方面执行用户环境级改动 |
