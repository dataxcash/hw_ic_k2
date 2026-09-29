# 卡点报告 · EDGE IV 步(B)＋硬修＋静态闸 — #K2-396 §二

- 授权：#K2-396 §二（**(B) 一次有界扩集**（预授权）＋ `exam_a_chain` **硬修** ＋ **静态未定义名闸**）
- 本窗**零 exam 跑**；件：`L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_BOUNDED_INFEASIBILITY_CERTIFICATE_v1.json` · 方案件 `…PLAN… :: edge_iv_B_status`

## 一、已交（硬修 ＋ 闸 ＋ 单源）

| 项 | 交付 |
|---|---|
| `exam_a_chain` 未定义名硬修 | 补 `blocked = []` ＋ `rp = <work>/s3_routes.json`（`json.dump(plans,…)`，照 relocate_* 链同法）⇒ 全包 AST 扫描 **{}** |
| **静态未定义名闸**（生产链本体） | 新测 `test_static_gate_no_undefined_names_in_the_eda_eng_package`（**全包**逐函数扫描；`exam_a_chain` 即先 RED 后 GREEN 用例） |
| 检测器**唯一源**（`M-ENG-DETECTOR-DUAL-SOURCE`） | 新测 `test_M_ENG_DETECTOR_DUAL_SOURCE_precheck_uses_the_maze_model`（禁旁路几何规则；不实规则不得入库） |
| 套件 | **89/89 PASS** |

## 二、(B) 已实现并实测 ⇒ **对本 7 条无对象**

| 项 | 读数 |
|---|---|
| `regen.member_expansion`（radius 1.0mm，5 个框内埋压点） | **added = 0**（**1mm 内无非成员 footprint**）· `rect2=[22.45,32.45,52.0,67.35]` · **`hs_clear = True`**（C7 重校过） |
| 追加技：**路由次序**（在册确定性档） | `dist_asc` blocked **7**（最优）· `dist_desc` 8 · `hard` 9 ⇒ **次序不是杠杆**（已测已否） |

## 三、为何不通 / 缺口在哪层（四问）

- **层**：**端点拥塞**（迷宫 snap 层）——非布局闸、非判据、**非容量**（93.5% 空闲）。
- **资源**：这些端点处**符合迷宫间隙模型的空网格格**。
- **占用者**：迷宫**自身障碍模型**所见的外网铜（端点格被剪）。
- **为何任何分配都不可能（在冻结手段内）**：四个候选杠杆**均已实测且无对象** ——
  ① 开端口：**无变更集铜可消费**（#K2-395 已修正）；② 扩成员集：**无可并入者**（本件）；③ 次序：**dist_asc 已最优**；④ 接受拥塞格：**#K2-395 已驳回**（会制造间距违例）。

## 四、结论与请示

- **本件出《有界不可行证书》**（具名 7 条 ＋ 四杠杆实测否证）：载 `L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_BOUNDED_INFEASIBILITY_CERTIFICATE_v1.json`。
- 依 #K2-396 §二.4：**按 #K2-372 通道走偏离处理（工程层自治）**；**触及需求/接口才升 owner**。
- **未申请末跑**（现在跑仍 C1=7 ⇒ 同因重跑，违 §二.4）。**请裁**：是走 #K2-372 偏离（例如放宽"框内仅成员"的端点策略 / 引入受控的端点让位），还是就此进入 owner 级（`frozen-set`）。
- 板面冻结 · 四源 4/4 · 判据表一毫米不改 · 禁 WORKER · **本窗零考跑**。
