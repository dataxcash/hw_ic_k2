# CO-103 非执行者对抗复评（对象 = SPEC rev-12 新基线：CO-99 / CO-100 / CO-101 / CO-102 + 链 pin + 收口声明）

- 性质：L2 PDN · **非执行者会话**对抗复评（`L2/frozen/L2_STRUCTURE_v2.0.md:137` 禁自评；本件会话 ≠ CO-99..CO-102 执行者会话）。
- 裁定：**`PASS_WITH_FINDINGS`**（9 项机判全过；3 项声明/证据发现 F-A/F-B/F-C）。
- 边界：只读 canonical；仅写本件记录。**不改 SPEC / 板 / 阈值 / 冻结源**；不使用任何搜索式坐标（换序探针仅作评审证据）。
- 复评面 = handoff §6-1 五项（①②③④⑤）+ 本件增补 ⑥⑦。

## 复评面与结论

| # | 面 | 方法（可独立重算） | 结果 |
|---|---|---|---|
| ① | 重导坐标是否**只**来自声明 palette + 固定序（零坐标搜索红线） | 独立重放（同 palette / 同声明序 / 同检测器）逐项比对 CO-100 `rows`；全坐标集合枚举 palette 归属 | **PASS** — 61 ppc 位移恒 = `R+0.3`=0.475mm、5 stitch / 4 zone 恒 = 0.6mm，**0 项在 palette 之外**，重放与 CO-100 逐项一致 |
| ② | `clearance` 重算口径与 CO-91 一致性 | 对 185 entry 用 CO-91 `Scene` 独立重算 `min(via_clr, via_hole, stub_clr)`（`stub_width_mm` 取 SPEC 声明 0.2）与存储值比对；读 CO-91 记录 | **PASS** — 185/185 一致（0 偏差）；CO-91 = PASS（via 241 目标 0 违规 / 短段 185 目标 0 违规，`stub_w=0.2`） |
| ③ | 新增 blocked 登记完整性 | 台账差分 + 退役键留存比对 + 静默丢失扫描 + 计划集 `(net,x,y)` 去重 | **PASS** — 新增 4 ppc（U6 FB34/FF14/FF21/H12）+ 1 stitch；4 退役坐标全留存；0 静默丢失；0 重复计划孔；计划孔总数 241 |
| ④ | 链 pin 完整性 + co96 失效是否如实声明 | 8 个闸默认 spec 扫描 + 引擎 `FROZEN_SHA` + validator `FROZEN_SHA_PREFIX` + co96 pin 比对 | **PASS（pin）**：8/8 闸默认 rev-12、引擎/validator pin 一致；**但 co96 证书未如实声明自身失效**（⇒ F-C） |
| ⑤ | CO-102 是否只改施工口径、未夹带计划变更 | 冻结引擎 vs 项目内引擎各落一 scratch 板，比对 zone 多重集 / via `(net,x,y)` 集 / track 坐标集；重跑三态 DRC | **PASS** — 三者**集合逐元素相等**，唯一差异 = 185 条 ppc 短段宽 `0.5 → 0.2`；DRC baseline 42 / 冻结 **76(+34)** / 项目内 **42(+0)** |
| ⑥ | 声明漂移（6 项 vs 5 项 / 位置） | 收口件文本扫描 vs canonical 计数 | **FAIL(声明)** ⇒ **F-A** |
| ⑦ | 「U6 新增 blocked ⇒ via-in-pad / HDI」升级证据 | 对每个新增 blocked 复算「自身位置对板是否干净」+ 逐候选成因分类；固定序敏感性探针 | **证据不足** ⇒ **F-B** |

## 牙齿（负控，4/4 + 3 项检测器自证）

- `palette_membership`：合成点 `(1.2345,6.789)` ∉ palette，而样本原位 ∈ palette ⇒ 归属检测器双向有效。
- `hole_detector`：0.28 < 钻+0.25 判为冲突、0.55 放行 ⇒ 孔距判据有牙齿；另**实证注入** kicad-cli 对**同网** GND 孔对报 `hole_to_hole`（实测 0.080 < 0.2495）⇒ CO-99 的 A4 口径忠实、非过保守。
- `V6_drc_reproduced`：三态 DRC 与 CO-102 记录逐值一致 ⇒ 施工口径声明可复现。
- `co96_stale_detector` / `drift_detector`：对合成反例触发、对正例放行。

## 发现

### F-A（中）声明漂移：新增 blocked 记为 6 项，实为 5 项；位置误述
- 收口件 v1.68（标题 + §1 ㉝ + §6-22 + §6-23 残余句）称「**6 项新增 blocked（5 ppc + 1 stitch，全在 U6 0.5mm 场）**」。
- canonical 证据：CO-100 记录 tally = `ppc_blocked 4 / relocated 61 / kept 124`、`stitch_blocked 1 / relocated 5`（重跑**逐字节可复现**）；已施加 rev-12 = blocked 120→**124**（+4）、stitch blocked 60→**61**（+1）⇒ **5 项 = 4 ppc + 1 stitch**。
- 位置：第 5 项为 **J2 扇出** 的 GND stitch `(133.83,59.1)`（与 J2.56 计划孔 0.045mm、与同址重孔对），**非 U6 0.5mm 场**；"全在 U6 0.5mm 场" 仅对 4 项 ppc 成立。
- 同一收口件 v1.68 的 §1 ㉞ / §6-23（CO-101 条）写「新增 blocked **4**」⇒ **文件内自相矛盾**（旧 CO-100 拆分 126/58/5 为过期读数）。

### F-B（高）「U6 新增 blocked ⇒ via-in-pad（工艺）/ HDI（层数）」升级缺乏存在性证据
- 4 项 U6 新增 blocked ppc 的**自身 rev-11 位置对板铜完全干净**（`via_ok` 与 `stub_ok` 均为真；CO-99 A4 类检测器）。
- 其阻塞成因**全部**是 `plan_hole`：与**已接受的同网（GND）相邻 U6 计划 via** 孔距互障 ——
  `FB34↔FA32` d=0.403（触发位 0.255/0.378）、`FF14↔FC9` d=0.295/0.279/0.287、`FF21↔FC19` d=0.205/0.180/0.193、`H12↔E14` d=0.342/0.205/0.318（阈值 = 钻 0.2 + `min_hole_to_hole` 0.25 = **0.45mm**，net-agnostic）。球心距 0.60–1.04mm ⇒ **相邻 GND 球、共面**。
- 固定序敏感性探针（**同** palette / **同**检测器，仅换声明内次序）：blocked ppc = **8 / 13 / 13**（canonical 4 为所试最优），且**每对幸存的成员翻转** ⇒ 该 5 项属**同网冗余竞争**的声明-策略输出，而非「板铜不可连接」。
- ⇒ 与 **CO-94** 的 120 项板铜阻塞**不同类**，不得沿用其「保连接数须 VIP/HDI」的 L1/工艺升级；正确处置面 = L2 冗余归并（相邻 GND 球共用平面，择一/桥接）或按既有 `(a)` 显式登记接受，**而非以 HDI（层数）升 owner**。
- 本件**不**否定 CO-100 作为 declared-policy 输出的合法性，也不改 rev-12；仅否定其升级证据链。

### F-C（中）收口件 co95 身份引用陈旧 + CO-96 证书未声明自身失效 + CO-77 抓不到散文式引用
- v1.68 §1 ㉛ 与 §6-20 两处以**现行**口径称「co95 记录 sha 仍 `61db48a283beeaae`」，现盘实为 `f1c0c17ee7b379a4`（rev-11 期记录已被 rev-12 重基线取代）。
- CO-96 记录（`8b591e5030aca11d`）声明 `baseline_ok=true` / `REVIEW_DONE_FINDINGS_OPEN`，但 pin 的 `co95_json` 正是该陈旧 sha ⇒ **证书对自身失效不实**；重跑即 fail-closed 报 `BASELINE_MISMATCH`（机制有效）。
- CO-77 的 `CITE` 只匹配 `` `file` `sha16` `` **邻接**形式 ⇒ 上列散文式身份声明**结构上抓不到**；因此「co77 PASS」**不蕴含**收口件内所有当前态身份声明均为现行态。
- 附带：co96 无 `--out`，重跑会**就地改写历史件**（违「历史件不改」精神）并使 co77 翻为 `CITATION_MISMATCH`。

## 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co103_rev12_nonexecutor_review.py          # 期望 PASS_WITH_FINDINGS / 牙齿 teeth_ok
../AppDir/usr/bin/python3.11 tools/p3_v57_co103_rev12_nonexecutor_review.py --quick  # 跳过 scratch DRC 三态
python3 tools/p3_v57_co77_closure_declaration_sweep.py                               # 对象 = 最新 boundary（v1.69）⇒ 期望 PASS
```

## 非声明（non-claims）

- 独立重放**复用** CO-91 的几何原语：本件审「policy 施加」，原语本身由 CO-91 / CO-99 覆盖。
- 不重解、不改 SPEC/板/阈值；换序探针**仅为评审证据**，不得当作 canonical 决策依据。
- 一阶结论未经 SI9000 / 板厂券；F-B 的正确性不等于已选定归并方案（该选择仍需 L2 显式裁定与登记）。
