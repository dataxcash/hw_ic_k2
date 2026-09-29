# 卡点报告 · #K2-403 owner 直令两项 — 常设合理性闸（已交）＋ ERASE+ADD（已立案）

- 件：`tools/k2_layout_reasonableness_v1.py`（**常设闸**）· 测试 `test_C403_…` · 本报告
- 本窗**零考跑 · 零板改**（板只在 `/tmp`）

## 一、① 布局合理性**常设二值闸**（#K2-403 §二.B）＝ **已交（真接线 · 非纸闸）**
- **机算行（基线相对，基准＝冻结 l14）**：
  - **R6 无重叠** ＝ DRC `courtyards_overlap` ≤ 基线；
  - **R4 孔/边距/连接器对齐** ＝ DRC `hole_clearance + edge_clearance + pth_inside_courtyard` ≤ 基线；
  - **R3 密度均衡** ＝ `regen.density_quadrants` 最挤象限面积占比 ≤ 基线＋0.02。
- **目视行（双轨）**：**R1 主器件-流向对应 · R2 高低速分区 · R5 无逆流长绕** ⇒ 显式 **`RENDER_REQUIRED`**（**不以"只注声称"代替** · 承 C20）。
- **入口**：`python3 tools/k2_layout_reasonableness_v1.py --board <pcb> [--drc <json>] [--json-out P]` ⇒ **PASS/FAIL 二值**（l14 实跑 = **PASS**，R3 最挤象限 46.81%）。
- **测试**：`test_C403_layout_reasonableness_gate_is_a_standing_binary_check` ⇒ 套件 **92/92**。
- **后续（每窗强制）**：收执须附**九行判卷 ＋ 合理性二值行**；**任一 FAIL ＝ 回修禁呈**。

## 二、② 连接器变更＝**ERASE+ADD**（#K2-403 §二.A）＝ **已立案 · 待实现（零考跑）**
- **废除**「经放置流水线挪 footprint」路线（**禁**再对连接器用 `mech_probe`/`edit_placement`）。
- **ERASE（板级直改）**：`J9`、`J6` **整件删除**；`J11`（网表侧已删）**板面同步删**。
- **ADD**：按 **N8 规律**仅保留 `J2/J3/J4/J12/J13`；`J13`（生产编程口）如需调位 ⇒ **删旧 ADD 新**（同封装新坐标），**位置由合理性闸出**。
- **随动**：净表／丝印／文档随动。
- **实现路径（本仓在册手法）**：`k2_p4_build_l9_v1.py` 的**阶段式板级编辑**（`--stages`）＋ `_shared/eda_core/dfm_repair.py` 的删件/重铺手法；**禁**绕判据、**禁**改判据表。
- **门**：ERASE+ADD 后须过 **① 合理性二值闸 ＋ 九行判卷**。

## 三、exam A⁵ 重述（ERASE+ADD 版 · 替代 A⁴ 家族 · 待实现后申请跑）
1. ERASE：块内 `J9/J6/J11` footprint 删除；
2. **保留成员按真实可动集**（18 件下移或留守如实）；**U1 困局**按 **#K2-397 证书通道独立评**（**不再阻塞本卷**）；
3. wipe-resolve 重解块内网 → refill；
4. **M4 九行 ＋ 合理性二值行** ⇒ 过 ⇒ exam B（H4）。

## 四、纪律
板面冻结 · 无 ECO 不动板 · 冻结四源 4/4 · C13 · 禁 WORKER · Gerber/下单停线 · 对表闸不变 · **本窗零考跑** · 收尾脚本每收执一次。
