# M13 v16 续接 — series_cap_wall 施工完成 + 假成功纠正 + 摆件问题定性

> 权威承接（按序读）：
> ① `m13_mcio_escape_landing_gap_problem.md`（GAP 问题定义 v1）
> ② `m13_v15_session_handoff.md`（上一 session：PEX8748 案例 + AC_CAP_WALL 设计定稿）
> ③ `_shared/docs/AC_CAP_WALL_ESCAPE_CONSTRAINT.md`（series_cap_wall 约束设计，本 session 已修正 crossing_dir 笔误）
> ④ `_shared/docs/LAYER3_FEASIBILITY_CLOSURE_DESIGN.md`（D1-D4 闭环设计）

## 0. 本 session 已完成并 commit（勿重做）

| 仓 | commit | 内容 |
|---|---|---|
| _shared | `26b9931` | escape_landing 串联电容墙感知 gate：region 可选段 series_cap_wall 解析 + analyze_pad_heap gap 列表化（旧键保留，缺省逐字节不回归）+ 网级 staggered `_wall_boundary`（墙 pad ∩ 网名自关联）+ 候选循环 gate（increasing/decreasing 方向参数化）+ `blocked_by.series_cap_wall` 证据 + `past_cap_wall` 标记；测试 t15-t19（解析校验/墙感知正向/墙前-only fail-closed/缺省不回归/方向参数化），19+45+62 绿；AC_CAP_WALL doc §3 crossing_dir 笔误修正（decreasing→increasing） |
| k2 | `e2aef60` | harness `derive_cap_wall_pads`（真板 footprint_ref C17-C32 ∩ _MCIO 网 → 16 墙 pad，SPEC refdes 声明零坐标）+ spec.derived.cap_wall_pads_MCIO + route_model_config MCIO region 声明 series_cap_wall + 真板重跑报告 |

## 1. 表层验收（已达成，但见 §2 假成功纠正）

- MCIO 落点 x 69.8 → **86.875**（16/16 ASSIGNED，全 past_cap_wall=true），J2/U3 零回归
- ③→⑤ U_TO_MCIO 数据流断层 gap 消失（归因收敛到 solve 层）

## 2. 假成功纠正（★ 本 session 最重要结论，下一 session 必读）

表层"落点移到墙后"是**假成功**。深挖后发现的真问题：

1. **落点形态荒谬**：16 个 via 全挤 x=86.875 单列，**差分对 P/N 换层点相距 6.3~44mm**（DN1 的 P y=51.5 / N y=70.4，隔 18.95mm）。差分对必须成对换层（中心距 ≤1~2mm），这形态物理不可能。
2. **solve 16/18 INFEASIBLE**，reason = "落点驱动逃逸无净空 / via 换层 P/N 极性不一致(flip)"——不是层4 形态缺口（D4 触发条件 (a) 表象），**真根因是摆件**。

## 3. 摆件问题实测数据（★ 布局可行性未做，几何已探明）

K2 真板（k2_v4.kicad_pcb，BoardParser 实测）：

| 项 | 值 | 含义 |
|---|---|---|
| 电容墙 | 2 行（y=57.8 上 C17-C24 / y=68.0 下 C25-C32），每行 8 颗 | 服务 DN_OUT0-3 / DN_OUT4-7 |
| 电容中心距 | 1.3mm，pad 宽 0.4 | 首尾相连 9.8mm 实墙 |
| 电容 pad 间空隙 | **0.2~0.3mm** | 塞不进 via |
| via 占位 | 外径 0.35 + 净空 0.1×2 = **0.55mm** | manufacturing 规则 |
| 电容右缘 → U3 左缘 | **3.45mm**（85.15→88.6） | 换层扇出区 |
| 两行电容之间走廊 | y 宽 **10.2mm** | 换层唯一通道 |
| 差分对间距 | inter_pair_spacing 0.875，p_width 0.205 / p_gap 0.175 | — |

样板对比（PEX8748 真板 /tmp/opencode/pex8748_imported.kicad_pcb 实测）：
电容 pad 0.508×0.457，**不同电容中心距 1.01~3.66mm（稀疏）**——样板"via 贴电容下游 0.38-2.2mm"可行，K2 密集墙无此空间。

SPEC via1 冻结坐标校验：9 个里 8 个净空 OK，1 个（DN_OUT2_N via1=(79.38,57.55)）距电容 0.13mm 冲突（SPEC 自身瑕疵）。

## 4. 四层工程框架（用户定稿，下一 session 沿用）

```
【布局阶段】
  1. 摆件方案（合理性）  = 学习样板 + 评估本板卡几何约束
  2. 布局可行性          = 纯几何求解           ← K2 漏了这步
【施工阶段】
  3. 施工合理性          = 学样板工程规范 + 特殊处理手法
  4. 施工可行性          = 几何求解
```

每步都是"几何确定性 + 样板参考"双介入。**K2 病根 = 跳过第 2 步（布局可行性几何求解），摆件直接冲施工，导致施工可行性（第 4 步）怎么算都死路。**

## 5. 下一步（新 session 入口）

**补做第 2 步：布局可行性几何求解。** 精确算：8 对差分线（DN_OUT0-7 到 U3）的换层点空间需求 vs 当前摆件供给（电容-U3 3.45mm × 走廊 10.2mm），得出"差多少 / 无解"的确定数字。产出后按框架决定：可行性无解 → 回第 1 步改摆件（电容墙拉开间距 / 电容与芯片拉开距离）；可行 → 才谈施工。

注意：不要误以为 series_cap_wall 施工已解决 MCIO——落点 86.875 是假解，须在布局可行性结论出来后再决定 escape_landing 的落点策略是否需要回退/修正。

## 6. 临时资产（/tmp/opencode，未 commit，勿删）

- `pex8748_imported.kicad_pcb`（11.77MB）PEX8748 唯一有效转换真板（学习参考，重生成法见 m13_v15 §3）
- `pex8748_structure4.json`、`stat_via_dists.py`、`verify_direction.py`

## 7. 铁律提醒（继承）

零单板特判 / 确定性 / 假成功零容忍（本 session 已踩过一次：落点 86.875 是假成功）/ 问题回模型 / 学案例 ≠ 修引擎 / 改 _shared 保持通用。
