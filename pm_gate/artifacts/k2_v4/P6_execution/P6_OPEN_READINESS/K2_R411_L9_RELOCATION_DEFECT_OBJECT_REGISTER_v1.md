# K2 · R411 —— l9 落搬迁缺陷**逐对象登记**（uuid/坐标级）+ 可施工性

- **ts** 2026-09-22T23:0x+0800 · **from** ENG·ARCHER（续接 · 应 #K2-142 §四 只读残余）· **to** 监理 · **owner 闸口 0**
- **authority**：#K2-142 §四（准只读残余测量）· owner #14⑥（不 park）· owner ⑧（可施工性字段）· R410 之延伸
- **边界**：纯只读。未修复、未烙板、未改受审板/pro/生成器/SPEC/原理图/真源/`criteria/**`、未派 WORKER、未变体重跑。

## 0. 方法与归因（先给）
- 配准：原始 DRC（59 error，`drc_raw_board_l9_77aaa63f.json`）vs **铺铜回填后** DRC（/tmp 副本，38 error），按 (type, 对象 uuid 集) ⇒ **真冲突 38**（35 精确配对 + 3 同物理冲突因配对对象改挂）· **陈旧铺铜 21**（59−38；本登记表按精确配对列出 24 条『仅原始有』，含配对改挂者）。
- **关键归因**：**59/59 处 error 至少一端为 `new_in_l9` 对象**（真冲突 35/35 · 陈旧 24/24）⇒ 100% 指向 #K2-137 项2 落搬迁之新生/改动铜；l8 既有铜（PCIE_UP/DN 走线、U6 pad、P3V3/GND 过孔）仅作受害端。

## 1. 真冲突（38）分型
| 型 | n |
|---|---|
| genuine `shorting_items` | 16（本表） |
| genuine `clearance` | 11（本表） |
| genuine `hole_clearance` | 5（本表） |
| genuine `tracks_crossing` | 3（本表） |

## 2. 陈旧铺铜假违例（21）分型
| 型 | n |
|---|---|
| stale `clearance` | 10（本表） |
| stale `hole_clearance` | 8（本表） |
| stale `shorting_items` | 3（本表） |
| stale `tracks_crossing` | 3（本表） |

## 3. 修复簇（可施工性）
| 簇 | 真冲突 n | 肇事（new_in_l9） | 动作 |
|---|---|---|---|
| **C1** | 20 | `DS320_STRAP_B_ADDR1_7-0` In2 4 段（9135a302 / 36f39a62 / 1c91d21e / ee5e408e）+ `ADDR0_15-8` | 改走/让位：避 `PCIE_UP0_N/1_N/2_P/3_P/4_N/5_N`（In2 走线 + F.Cu→In2 盲孔）与 `ADDR1_15-8` |
| **C2** | 5 | `I2C1_SDA` via + B.Cu stub（4eb7ffcb） | 移 via + 改 stub：避 `PCIE_DN_OUT7_P_MCIO`(B.Cu 26b8261c) 与 U6.`BT29` |
| **C3** | 13 | `DS320_STRAP_B_ADDR0_15-8` F/B.Cu stub（8404eb3a / bb00ecfb / c5ce85d2 / e0b5ce17 / 01b66748 / 13a01fd2 / 807aeaff）+ via c055112a | 移 stub/via：避 `DN_OUT7_N_MCIO`(B.Cu) · `P3V3` via · `GND` via |
| **C0** | 0（程序） | 全板 18 区铺铜 | **落搬迁后回填铺铜**（消除 21 处） |

## 4. 非 45° 段（11 · 全为 new_in_l9）
| net | layer | start → end | len | 角 |
|---|---|---|---|---|
| `DS320_STRAP_B_ADDR1_7-0` | In2.Cu | [83.66, 50.28] → [93.4, 51.06] | 9.7712 | 4.579° |
| `DS320_STRAP_B_ADDR1_7-0` | In2.Cu | [93.4, 51.06] → [108.94, 50.06] | 15.5721 | 176.318° |
| `DS320_STRAP_B_ADDR1_7-0` | In2.Cu | [108.94, 50.06] → [110.26, 51.66] | 2.0742 | 50.477° |
| `DS320_STRAP_B_ADDR1_7-0` | In2.Cu | [110.26, 51.66] → [99.84, 60.78] | 13.8474 | 138.806° |
| `DS320_STRAP_B_ADDR0_15-8` | F.Cu | [105.08, 51.54] → [105.12, 51.3] | 0.2433 | 99.462° |
| `DS320_STRAP_B_ADDR0_15-8` | F.Cu | [105.12, 49.86] → [103.86, 48.7] | 1.7127 | 42.634° |
| `DS320_STRAP_B_ADDR0_15-8` | F.Cu | [103.86, 48.7] → [98.3, 48.68] | 5.56 | 0.206° |
| `DS320_STRAP_B_ADDR0_15-8` | B.Cu | [103.14, 54.26] → [102.32, 53.52] | 1.1045 | 42.064° |
| `DS320_STRAP_B_ADDR0_15-8` | B.Cu | [97.92, 53.52] → [97.06, 52.62] | 1.2448 | 46.302° |
| `DS320_STRAP_B_ADDR0_15-8` | B.Cu | [97.06, 52.62] → [96.2, 52.56] | 0.8621 | 3.991° |
| `DS320_STRAP_B_ADDR0_15-8` | B.Cu | [94.08, 51.26] → [93.98, 51.04] | 0.2417 | 65.556° |

## 5. 人类语义 / 施工队问答
**不能直接连。** 修复目标集 = 本件 `culprit_objects_new_in_l9`（`new_in_l9=true` 且见于真冲突者）；**不动** l8 既有铜。审批：**#K2-142 §四 禁烙板在效** ⇒ 须监理放行（已见 PENDING_RULINGS v62）；锚变更连带 SPEC rev-55 board_sha16 声明 ×3 与 P4 派生模型指纹重锚。

## 6. 件
`K2_R411_L9_RELOCATION_DEFECT_OBJECT_REGISTER_v1.json`（全量表：真冲突 35 条 + 陈旧 24 条 + 11 非 45° + 肇事对象 uuid 集）· `.sha16.txt`。

—— ENG（ARCHER）· 2026-09-22 · 只读 · 未烙板 · owner 闸口 0
