# K2 · R427 —— **路线 R 之交付件已在仓内**：`l8r3` 包即锚 l8 之可制造 Gerber（只读核证）

- **ts** 2026-09-22T23:59:29 · **from** ENG·ARCHER（续接 · 承 handoff R423）· **to** 监理 · **owner 闸口 0**
- **authority**：owner ③（完工定义）· owner #14⑥ · #K2-142 §四 · handoff R423 §8.4 · 先例 **#K2-38**
- **边界**：**只读核证**。**未重建包**（承 #K2-38 §二「交付锚冻结 · 勿重建」）· 未改任何件 · 未出包 · 未烙板。

## 0. 一句话
**路线 R（受审板回 l8）之交付件，仓里已经有了** —— `L6/jlc_package_l8r3`（+ `DELIVERY_l8r3`）：锚 **`l8 = 7a5c89913d6e5d0a`** · pro `c0090580…` · **SPEC rev-54** · criteria rev=6 · **DFM 16 PASS / 1 ACCEPT / 0 FAIL** · **55/55 sha256 本会话只读复算 OK**。**仓内没有任何 l9 交付包。**

## 1. 包之锚（包内 `07_verify/anchor_selfcheck.json` 逐字节复算）
| 项 | 值 |
|---|---|
| 受审板 | `k2/hw/k2_v4_8L.l8.kicad_pcb` **`7a5c89913d6e5d0a`**（= 现行 l8） |
| pro | `k2_v4_8L.l8.kicad_pro` **`c009058005829f09`** |
| SPEC | `SPEC_k2_v4.spec-rev-54.json` **`f3a48b866983c8db…`** |
| 判据 | **rev=6** |
| 件数 / 钻 | 53 件 · 754 孔 · 非通孔 455/734（62%）⇒ HDI 多层层压 |

## 2. **owner ③ 逐项**（对着包内实件点）
| owner ③ 要求 | 包内 | 判 |
|---|---|---|
| **8 铜层 Gerber** | `01_gerber_rs274x/`：F · In1 · In2 · In3 · In4 · In5 · In6 · B = **8/8** | ✓ |
| 阻焊 / 丝印 / 边框 / job | F_Mask · B_Mask · F_Silkscreen · B_Silkscreen · Edge_Cuts · `.gbrjob` | ✓ |
| **Excellon 钻孔（含 HDI 盲埋孔）** | `02_drill_excellon/` **8 个 `.drl`**（front-in1 171 · front-in2 132 · front-in4 4 · front-in5 19 · **in2-in5 92** · back-in5 37 · …）+ 逐孔对 census + report + 6 张 map | ✓ |
| **叠层图** | `03_stackup/HDI_stage_diagram.svg` + `JLC08161H_stackup.svg` | ✓ |
| **阻抗表** | `04_impedance/impedance_table.json` + `.md`（85Ω 差分 ±10% · 含 as-built 具名偏差） | ✓ |
| **MANIFEST** | `MANIFEST.json` + `SHA256SUMS.txt` + `DELIVERY_l8r3/*.tar.gz` | ✓ |
| **DFM 逐项对 JLC HDI 全 PASS** | **16 PASS / 1 ACCEPT / 0 FAIL**（ACCEPT = 阻焊坝 9 处 <0.09 ⇒ 随单评审 · 承 CO-147 R3；回退修法已实证但属**改板**） | ✓（**无 FAIL**） |
| 随包具名披露 | `DISCLOSURE.md`（170 warning 全量 · OUT #5 · F-9 · L-1 · P5 新项）· `ORDER_NOTES.md` | ✓ |

## 3. **关键对齐：路线 R 之锚 = 本包之锚**
路线 R 之落地要求（**R426**）= `pm_gate/project.yaml::spec_name` 指回 **rev-54**；而**本包正是以 rev-54 构建**。
⇒ **回退后之 SPEC 状态，与交付包构建时之 SPEC 状态一致** —— 无「须重出才对齐」之物证。

## 4. 在册先例
**#K2-38**（2026-09-20 · l7 时代）监理判 **ENG 交付闭环 = 通过**：可制造 Gerber 包在库并经验证（同结构 · 同 `DFM 16 PASS / 1 ACCEPT / 0 FAIL` 汇总 · 判据锚 MATCH）⇒「本类包 = owner ③ 之交付物本体」**有在册先例**。

## 5. 本件**不主张**什么
**不主张交付已生效/已合格** —— 阶段门与交付判定属监理职权，且现行 gate 链态为 **P4 HOLDS**。本件只报**在册事实 + 在册锚 + 完整性只读复算**。

## 6. 请监理（自裁面）
- **Q5**：`l8r3` 包在 owner 裁「甲」后**是否仍为有效交付物**（⇒ 完工已满足 · 仅须判据/DRC/DFM 复核）？抑或**须随回退重出**（⇒ item13 仍为待办）？
- **Q6**：若须重出，请指定重出时点与属主（生成器 `k2/tools/k2_p5_jlc_package_l8r3_v1.py` 在册可复用；**ENG 未获批不自跑**）。

## 7. 诚实边界
未重建包（#K2-38 §二：交付锚冻结 · 勿重建）· 未改 `criteria/`（rev=6 MATCH）/SPEC/生成器/原理图 · 未出包 · 未烙板 · 未派工 · 未写 `.omo/supervision/**` · **未裁**「②-UP 条款之违背是否使该包失效」（= owner #K2-142 取舍所系）。

---
—— ENG（ARCHER）· 2026-09-22T23:59 · 只读 · owner 闸口 0 · sha16 `38f4bfb9fa91fbe7`
