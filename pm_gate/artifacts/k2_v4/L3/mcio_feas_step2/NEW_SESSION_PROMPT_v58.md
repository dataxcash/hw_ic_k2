# NEW SESSION PROMPT — v57 板级意图生成器（承接设计细案 8da09ad，编码起点）

> 会话背景：用户连续裁决：① 审查不产生正确性，板级意图必须构造保证（L2 上一级）；
> ② 上游输入自洽门（85d2fcc）只是检查机制，需生成算法。设计细案已交付：
> `m13_v57_board_intent_generator_design.md`（8da09ad）。本卡 = 编码生成器 + B1 验收。

## 已核实状态（勿重验）
- k2 HEAD = 8da09ad；本会话 6 commit 全在本地未 push（6dd43cd S1设计 / 348c67d
  A1.1核门PASS / 38d7220 A1.3+A1.4门PASS / 987a42b 发射裁决+F-A/F-B / 85d2fcc
  上游自洽门FAIL38 / 8da09ad 板级意图设计细案）。
- _shared freeze locked；全前台零委派（用户既定）；勿动冻结区。
- 现有工具（tools/）：p3_v57_s1_page_manifest.py(.json 34页) / conservation.py
  (+_exhaustive_ref.py, A1.1 140/140 PASS) / invariants.py+a13_gate / a14_gate /
  input_selfcheck.py（当前 SPEC FAIL 38 项：G1 In6×2、G2 lane1.2×28、G2b REFCLK×8）。

## 本卡任务（按序，禁止跳步）
1. **B1 判定/构造核心**（新 tools/p3_v57_big_lane_kernel.py，纯函数）：
   输入 frame={span[y_lo,y_hi], margin, pitch=1.46, bands:[{id,n,edge:lo|hi}],
   refclk:{n_pairs, layer, need_iso} | null}。构造算法（设计细案 §3）：
   a) band 从各自 edge 向内以 pitch 等距铺 lane（edge=lo → y_lo+margin+i·pitch；
      edge=hi → y_hi−margin−i·pitch）；
   b) 数据带可行 ⇔ 两带占用不重叠且带间 gap ≥0；gap ≥ 2·pitch 时中央可容 REFCLK
      （距两侧数据 lane ≥ pitch）；
   c) REFCLK 层≠数据层（F.Cu 带外）时不占 In2 gap；
   d) 不可行 → 量化证书：{needed_mm, avail_mm, short_mm, escape_hatches}。
2. **独立穷举基准**（p3_v57_big_exhaustive_ref.py，结构独立）：对 span 内 0.01 网格
   枚举全部 lane 摆位（n≤6 小实例）求可行/最小 span，核==基准对照。
3. **B1.1 门**：合成随机 frame 两族 + 固定 seed 双跑字节一致；decision+证书一致
   PASS 才进 4。
4. **B1.3 不变量**（复用 p3_v57_s1_invariants.py 思路独立写 B 版）：输出 lane 两两
   ≥1.46、层∈{F.Cu,In2.Cu}、REFCLK 隔离、带序无交叉。
5. **B1.2**：三枚举序输出字节一致。**B1.4**：输入白名单 grep（零读 SPEC corridors
   现值/板铜/旧簿）。
6. **B1.5 K2 实跑**：frame 参数从板框+放置+端点锚派生（span = 走廊区可用 y，先按
   board.outline_y[33,79] 减器件/keepout 投影），跑出 lane 帧/证书；与手写 SPEC
   差异表落盘（authority-first）。
7. 全过 → lock 检查 + commit + push（k2；标注 B1.x 结果）。

## 编码前需裁决/取数（设计细案 §7；优先问用户）
- a) 走廊 x_range 派生常数（U6 出逃区宽/连接器隙安全距）——先以现 SPEC 值
   [105.25,132.65]/[65.05,82.35] 作输入参数跑，标注"待几何核验"；
- b) 带间隔离口径：默认同层 1.46（=对间距），文档注明；
- c) REFCLK F.Cu 带外禁入谓词数据：v0 先只做 In2 隔离带方案（可闭环），F.Cu 带外
  留 v1。

## 勿做
- 勿动 SPEC/冻结文件（板级意图修正=用户裁决后另卡）；勿改 _shared；勿整读
  hs_route_model/solve 历史模块；勿重推 S0 端点/S1 页清单。
- 勿把"检查门 PASS"当"构造正确"；B1.1 必须含独立穷举对照。

## 环境
- 工具/工件目录：k2/tools/、k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/。
- 本卡边界=板级意图生成器本体+B1 验收；图纸发射/施工消费不属本卡。
