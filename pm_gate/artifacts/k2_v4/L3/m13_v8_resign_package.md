# M13 v8 重签包 — sch_k2 出图门禁 5 条 C 类 STALE（呈 PM 裁决/签署）

> 日期：2026-08-26 ｜ 性质：只读分析 + 待执行签署包（**未代签、未动任何主链文件**）
> 触发：Card 1.2 步骤⑨ CLI 口径 22 PASS/5 STALE/3 SKIP vs 落盘 `gate_reports/sch_k2.gate.json`（13:18:36）27 PASS/3 SKIP/gate=PASS 的矛盾。

---

## 一、口径分析（代码级）

### 1.1 STALE 判定：唯一裁决层 = 签署账本的基线锚点（不是时间戳、不是语义）

判定链：`gate_schematic.py:run_gate()` C 类分支 → `manifest.effective_status(rule_id, sch_hash)`
（`_shared/eda_core/sch_gate/manifest/reviewer.py` L94-103）：

```python
def effective_status(self, rule_id, current_hash):
    status = self.status_of(rule_id)          # 签署账本: sign_off[rule].status
    if status == "PASS" and not self.baseline_matches(current_hash):
        return "STALE", "图已变更…"            # 锚点失效 → 旧签作废
    return status, ""
```

`baseline_matches`（L90-92）= `baseline.sch_hash` 非空 **且** == 当前 `sch_sha256(根页+全部 Sheetfile 子页)`。

**出 STALE 的充要条件（三条同时成立）：**
1. 该规则在签署账本 `sign_off` 里状态为 PASS（已签过）；
2. manifest 顶层 `baseline.sch_hash` 锚点已建立；
3. 当前图的哈希 ≠ 锚点哈希（图被改过，或锚点指向另一棵树）。

**不参与判定的量（关键结论）：** 签署日期（date 字段）、reviewer 身份、note 语义、
外部事实（签注所指的拓扑是否已作废）**全部不被代码读取**。时间戳只是记录，不是裁决依据。
因此：**"签了一个后来被证伪/回退的拓扑"这种语义失效，门禁机器层看不见** —— 只要图哈希回到锚点值，
旧签照样机器 PASS；反之图一变，哪怕语义没变也判 STALE。这是设计意图（锚点闭环防旧签冒充新图），
语义正确性由签署人负责。

### 1.2 CLI 与落盘 JSON 不一致的根因：两次不同树状态下的运行，不是同一次的两个口径

| 运行 | 时刻 | 树状态 | sch_k2 哈希 | 锚点 | 5 条 C 类裁决 |
|---|---|---|---|---|---|
| 落盘 `sch_k2.gate.json` | 13:18:36（14:25 随 dfc76cb 提交） | M13 v6（M-D lane 分工 ECO 已进图） | f2303c8b… == 锚点 | f2303c8b… | PASS → 27/0/3, gate=PASS |
| Card 1.2 步骤⑨ CLI（/tmp/opencode/gate_report.json 20:51 同构） | 20:5x | M13 v8 回退后工作树（未提交） | 8e1810ac…（sch_k2）/ b9e1e3fd…（sch/）≠ 锚点 | f2303c8b… | STALE → verdict=FAIL → 22/5/3, gate=FAIL |

代码级佐证：
- STALE 在报告 summary 中**没有独立计数桶**（`summary` 只有 pass/fail/pending/skip）；
  STALE 项经 `gate_schematic.py` L148 折入 `verdict=FAIL` → fail=5。"22 PASS/5 STALE/3 SKIP"
  是按 evidence 字段（`"issue": "STALE (签署锚点失效)"`）的人工口径表述；落盘 JSON 的
  27 PASS 是锚点命中时的另一次运行。**两数不矛盾，是两次运行。**
- 旧签盘踞原因：`--emit-signature` 在 gate=FAIL 时会**删除**旧签名文件（L291-294）；
  步骤⑨ 的运行未带 `--emit-signature`（默认 `--out=/tmp/opencode/gate_report.json`），
  所以 13:18:36 的陈旧签名仍留在 `gate_reports/sch_k2.gate.json`。
- 留盘风险：`verify_signature.py`（PM 验收兜底 + 服务端 hook 同规则）按
  `gate==PASS 且 sig.sch_hash==当前图哈希` 验签 —— 该旧签对当前树**必然验签失败**
  （签名=f2303c8b… vs 实际=8e1810ac…），push/交付验收会被拒。重签后复跑门禁
  （带 --emit-signature）会用新报告覆盖它。

### 1.3 语义失效（机器层之外的第二重失效，重签的直接动因）

5 条旧签注均为 `reviewer=PM-M13v6, note="M13v6 拓扑重排 ECO: U7/U3 lane 分工 + 节点归属/ERC/LOGIC-05 已验证"`，
锚定的是 **M-D lane 分工拓扑**（U7=lane0-3 / U3=lane4-7 混合分工，nets 48+16 处修订）。该拓扑已被证伪并回退：
- `m13_v8_directionality_addendum.md`：DS160PR810 RX/TX 焊盘分列封装两侧 → 单芯 8 通道只能整体服务同一流向；
  M-C/M-D 混合分工在任何旋转组合下必有一半通道方向错误（可行性矩阵 §2）；v6 全量求解 17/18 INFEASIBLE，
  全板 SOLVED 段全是纯方向段（§3）。
- `m13_v7_capacity_conflict_report.md` + commit 2e8eb11：上行电容墙未随 M-D 迁移、U3 rot=180 TX 朝左与
  UP_OUT4-7→J2 右侧的根本矛盾（三层根因实证）。
- M13 v8 已执行方案 B 回退：纯方向分工（U7 rot=0=UP0-7 / U3 rot=180=DN0-7）+ J2 端方向映射保持。
- `card1_1/card1_2` 归属声明口径："M-D 基线数字全部作废"、"M-D '全链绿' 系 8-20 陈旧产物"。

**结论：5 条签注在机器层（锚点）与语义层（拓扑作废）双重失效，必须重签，且签注必须换发 v8 口径。**

---

## 二、5 条在 M13 v8 现产物下的真实状态

前提核验（Card 1.2 步骤⑨ 运行，当前工作树）：
- A/B 类机检 **22 PASS**，3 SKIP 全部带理由（LINK-01/STRAP-01 无板卡 YAML 声明、SYM-01 符号库不可读），
  0 FAIL；ERC 0 error、LOGIC-05 PASS、结构三基础/节点归属经 Card 1 链验证。
- 5 条 C 类规则 `checker=reviewer`，**本身无机检项**，纯人工视巡。

| 判定 | 结论 |
|---|---|
| 机检是否全绿 | 是（22 PASS/3 有理由 SKIP，无机器层 FAIL） |
| 是否只差签署锚点更新 | **机器层：是** —— 唯一阻塞 = baseline f2303c8b… ≠ 当前 8e1810ac…；`--sign` 即写锚即解除 |
| 语义层是否可沿用旧签注 | **否** —— 旧签注指向已证伪/回退的 M-D 拓扑，重签必须换 v8 口径（纯方向分工 + Connectors/Power 列修订） |
| 签署前置 | ① 当前树为最终态（签署后再改图必然再废签，5 条须一次性签完）；② DOC-01 须先从当前图重出交付 PDF 并 Ctrl+F 抽检；③ eco_state 处 ECO-S3（归属声明口径 "输入又改, S2 复证先行"），ECO 状态机责任链与门禁并行，不属本包范围但请 PM 知悉 |

当前哈希（重签锚点，`--sign` 会按签署时刻自动重新锚定）：
- `sch_k2` 根：**8e1810ac31f59ed1723195e4be187fa7232e3c314afdfdc3ae1a7a674cd4a890**
- 旧锚点（作废）：f2303c8b241acb66d5be229f341ff74f2aea2e436f6e32cbdedf95d16aa95ad0

---

## 三、重签包（5 条，待 PM 亲自执行 —— 禁止代签/伪签）

统一建议新签注（5 条同注，与既有签署实践一致）：

> `M13 v8 回退重签: 纯方向分工 U7 rot=0=UP0-7 / U3 rot=180=DN0-7 (M-D lane 分工已证伪回退) + Connectors 列 3→2 / Power 列 2→3 修订; 机检 22 PASS/3 SKIP 全绿; gate hash 8e1810ac`

（注内 hash 为人读记录；机器锚点以 `--sign` 写入的 baseline 为准。若签署前树再变，先重算哈希再改签注。）

| # | 项 | 规则语义 | 机检现状 | 旧签注（作废） | 签署前人工视巡要点 |
|---|---|---|---|---|---|
| 1 | LAYOUT-03 | 模块化与流动方向（左进右出/上电源下接地/功能分区） | 无独立机检；整机 22 PASS；Card 1.2 预扫 6/6 页布局 PASS | PM-M13v6 "M13v6 拓扑重排 ECO: U7/U3 lane 分工…"（锚 f2303c8b） | 各页功能分区/流向（v8 页面计划：Connectors/AC-Down/AC-Up/MCU/PowerDecoupling/Power(12V)） |
| 2 | LAYOUT-04 | 密布度适中（50%~80%，无单页挤爆/大留白） | 无独立机检；预扫各页 x/y extent 全部在纸幅内（如 Connectors [27.9,500.4]<579） | 同上 | 逐页密度视巡（预扫证据见 card1_2 ③ 表） |
| 3 | POWER-02 | 上拉/下拉电阻垂直放置（电源朝上/地朝下） | 无独立机检；Power 页列 2→3 修订后 extent [30.5,271.8]×[17.8,162.6] < A4 界 | 同上 | Power 页电阻朝向视巡（唯一纯视巡硬项） |
| 4 | LAYOUT-06 | 高速信号流连贯（AC 耦合串联/TVS 就近） | LOGIC-05 PASS（差分链驱动）；AC 耦合 32×220nF 在链；v8 纯方向分工恢复原生拓扑 | 同上 | AC 页 U3/U7 信号流视巡 |
| 5 | DOC-01 | 矢量 PDF 文本可搜索 | 无机检；**前置：交付 PDF 须从当前树重出**，PM Ctrl+F 抽检网络名 | 同上 | PDF 抽检（未出 PDF 不得签） |

### 待执行签署命令（PM 本人执行；CWD = 容器根 `/home/fila/jqdDev_2025/ic_hw`）

`--sign` 语义（代码级）：写 `sign_off[规则]=PASS + reviewer + date(当天) + note`，**并把
baseline 锚定到当前图哈希**（签署即锚定；此后图一变本签自动作废）。

```bash
# 5 条逐一签署（reviewer 必须 PM 实名，禁止代签）
for R in LAYOUT-03 LAYOUT-04 POWER-02 LAYOUT-06 DOC-01; do
  python3 eda_core/sch_gate/gate_schematic.py \
    --sch strix-halo-ioconvert/revA/sch_k2/strix-halo-ioconvert.kicad_sch \
    --manifest strix-halo-ioconvert/revA/gate_reports_manifest.yaml \
    --sign "$R" --reviewer '<PM 实名>' \
    --note 'M13 v8 回退重签: 纯方向分工 U7 rot=0=UP0-7 / U3 rot=180=DN0-7 (M-D lane 分工已证伪回退) + Connectors 列 3→2 / Power 列 2→3 修订; 机检 22 PASS/3 SKIP 全绿; gate hash 8e1810ac'
done
```

### 签署后：复跑门禁刷新落盘签名（覆盖 13:18:36 陈旧签名；仅 gate=PASS 才写）

```bash
python3 eda_core/sch_gate/gate_schematic.py \
  --sch strix-halo-ioconvert/revA/sch_k2/strix-halo-ioconvert.kicad_sch \
  --manifest strix-halo-ioconvert/revA/gate_reports_manifest.yaml \
  --emit-signature strix-halo-ioconvert/revA/gate_reports \
  --out /tmp/opencode/gate_report.json
# 预期: gate=PASS, 27 PASS/0 FAIL/3 SKIP, baseline 锚定 8e1810ac…
# 验收复核: python3 eda_core/sch_gate/verify_signature.py --sig strix-halo-ioconvert/revA/gate_reports/sch_k2.gate.json
```

### 红线
- 本包**未执行任何签署**、未改门禁代码、未动 `sch/`、`gate_reports/`、manifest 任何文件。
- 未经 PM 明确要求不得 commit（当前工作树含 v8 回退未提交变更）。
- 若签署前任一输入再变（ECO S2 复证改图），本包哈希失效，须重出包。

---

## 附：证据索引
- 落盘旧签：`revA/gate_reports/sch_k2.gate.json`（dfc76cb, 13:18:36）
- 签署账本：`revA/gate_reports_manifest.yaml`（baseline=f2303c8b…）
- 步骤⑨ 同构运行：`/tmp/opencode/gate_report.json`（20:51, 22/5/3, 5×STALE）
- 判定代码：`_shared/eda_core/sch_gate/gate_schematic.py` L124-150/L283-294、`manifest/reviewer.py` L90-103
- 证伪/回退：`artifacts/k2_v4/L3/m13_v8_directionality_addendum.md`、`m13_v7_capacity_conflict_report.md`、commit 2e8eb11/dfc76cb
- 归属口径：`card1_1_connectors_columns_attribution.md`、`card1_2_fix_attribution.md`
