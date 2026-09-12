# CO-104 L2 自裁（过孔策略 / PDN）：rev-12 新增 5 项 blocked 的裁定 = `ACCEPT_L2_NO_HDI`

- 依据：`LAYOUT_CONSTITUTION` 第二章 —— 过孔策略 / PDN 承载属 **L2**（不由 owner 裁）；层数（HDI）才是 L1。
- 起因：CO-103（非执行者对抗复评）F-B 已证明该 5 项**不是**「板铜不可连接」（CO-94 类），而是**同网 GND 计划件孔距竞争**。
- 裁定：**接受** 4 项 U6 ppc blocked（`FB34/FF14/FF21/H12`）+ 1 项 J2 扇出 GND stitch blocked；**不采 via-in-pad、不升 HDI、不改 palette、不重基线**。
- 效果：**rev-12 不变**（SPEC/板/阈值/冻结源零改动）；不需重跑全链；**本项不再构成 L1 问题**。

## 证据（三条出路逐条量化，均为机判）

| 面 | 判据 | 结果 |
|---|---|---|
| V1 归属 | 4 项自身 rev-11 位置对板铜是否干净 + 同网计划孔距归属 | **干净**（via/stub 皆合法），阻塞**全部**来自同网 GND 计划孔（`FB34↔FA32`/`FF14↔FC9`/`FF21↔FC19`/`H12↔E14`，球心距 0.60–1.04mm）；第 5 项为 J2 扇出 stitch 同址重孔对 |
| V2 出路 A：共享单孔 | 两 pad 中心**中点**派生位（零自由度、非搜索）+ 双短段，按 CO-91 同一检测器 | 仅 **1/4 对**可行（`FB34~FA32`）；其余 3 对的中点正落在 U6 另一球 pad 上（`FF11`/`FF18`/`E11`）⇒ 收益 = 1 个 GND 球 |
| V3 出路 B：改声明固定序 | 同 palette、同检测器，仅换 4 种固定序 | canonical **4** vs 13 / 8 / 13 ⇒ canonical 已最优，换序更差；全序/全组合优化 = 搜索（禁） |
| V4 出路 C：加宽 palette / VIP / HDI | 政策闸 | 加宽 palette = 把搜索写进决策（CO-93/CO-94 已驳回）；VIP 需工艺 + SI/PI 证据（无）；HDI = L1 层数且本件已证「须 HDI」不成立 |
| V5 接受口径一致性 | 与既有接受态对齐 | rev-12 blocked = **124**（既有 120 已由 CO-94 裁定维持 + 新增 4），stitch blocked = 61；接受 = 与既有同类处理，且**显式登记不静默** |

牙齿 4/4：共享单孔检测器双向（`FB34~FA32` 放行 / `FF14~FC9`、`FF21~FC19` 挡下）、换序检测器有区分度、自身位置干净检测器。

## 代价与残余

- 代价：4 个 U6 GND 球无独立 via（GND 平面网；与既有 120 项 blocked 同类），1 项 stitch 冗余；**不损任何非 GND 连接**，不影响 G4..G7 与 SI/DFM 读数。
- 保留候选（deferred，**未施加**）：出路 A 的那 1 对（`FB34~FA32`）可按**声明规则**「同网孔距冲突对 → 取两 pad 中心中点派生位共享单孔 + 双短段」在未来重基线时一并施加；若 R3/PDN 要求「U6 GND 球 100% 独立 via」成为硬需求，须走 SPEC 变更 + 全链重基线 + **换会话复评**。

## 附带加固（CO-103 F-C 收口）

`p3_v57_co96_nonexecutor_review_pass4.py` 增加 fail-closed 守卫：默认落点改为**重跑件**
`m13_v57_co96_nonexecutor_review_pass4_rerun.json`；显式指向历史证书路径时**拒绝写入**（`rc=2`），除非加 `--overwrite-canonical`。
实测：canonical 证书 `8b591e5030aca11d` **未被改动**；重跑件 = `m13_v57_co96_nonexecutor_review_pass4_rerun.json` `636b1ad728f0fa91`
（verdict `BASELINE_MISMATCH`，mismatch = `co95_json` 61db48a283beeaae → f1c0c17ee7b379a4），即 CO-96 失效的**机判化如实声明**。

## 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co104_pdn_blocked_ruling.py          # 期望 ACCEPT_L2_NO_HDI / V1..V5 ok / A feasible 1/4 / reorder 4,13,8,13
../AppDir/usr/bin/python3.11 tools/p3_v57_co96_nonexecutor_review_pass4.py    # 写重跑件（BASELINE_MISMATCH）
../AppDir/usr/bin/python3.11 tools/p3_v57_co96_nonexecutor_review_pass4.py --out <canonical>   # 期望 rc=2 拒绝
python3 tools/p3_v57_co77_closure_declaration_sweep.py                        # 对象 = 最新 boundary（v1.70）⇒ 期望 PASS
```

## 非声明

- 本裁定**不**否定 CO-100/CO-101 的声明-策略输出合法性，也**不**改 rev-12；只对「出路选择」作 L2 裁定。
- 出路 A 的可行性判定使用 CO-91 同一几何原语（不重审原语）。
- 一阶结论未经 SI9000 / 板厂券；PDN 压降与热仍为 PM 外部输入项（CO-87 两项 NOT_DEMONSTRATED）。
