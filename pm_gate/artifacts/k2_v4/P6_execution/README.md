# P6_execution/ —— **P6 / 学习环批 2 的可执行仪器**（计划态，**不施工**）

> 性质：**计划件 + 只读仪器**。**不属于交付锚**（不在 `L6/jlc_package/`、不入 `MANIFEST.json`、不入 tarball）。
> 与 `L6/first_article/` 平级同构：`CHECKLIST.md`（人读）· `results_template.json`（机读）· `INSTRUMENT_SELFCHECK.json`（只读机核）。
> 依据：**#K2-40 §四-1**（具名动作 + 责任 + 可复现验收命令 + fail-closed 门 + 授权项单列）· `k2/docs/K2-P6-LEARNING-LOOP-BATCH2-AND-CAPABILITY-GAP-CLOSURE-PLAN-v3.md` · owner #14。
> 红线：P6 **未开** ⇒ 本目录**只准**放计划/仪器/只读基线，**禁**放任何施工产物（#K2-40 §四-3）。

| 件 | 用途 |
|---|---|
| `CHECKLIST.md` | 人读勾选表（含授权门、fail-closed 期望值、签字栏） |
| `results_template.json` | 机读结果表（status/measured/evidence + 判据原文），施工后逐项回填 |
| `INSTRUMENT_SELFCHECK.json` | **机核**：计划所引载体/行号/符号此刻是否真实存在 + 基线可否复现（fail-closed） |
| `BASELINE_pm_gate_k1_k2_readonly_v1.json` | **改前**只读基线（K1/K2 两维度 pm_gate 现状读数 + 锚 sha） |

## 复现命令（只读）

```bash
# ① 基线捕获（容器根 ic_hw；pcbnew 仅 AppDir 解释器可用 ⇒ 用它）
PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p6_readonly_baseline_v1.py --out /tmp/opencode/k2_p6_baseline.json
# 判据：与 BASELINE_pm_gate_k1_k2_readonly_v1.json **逐字节同**（两次连跑亦须逐字节同）

# ② 仪器自检（机核载体/行号/符号 + 基线可复现；FAIL ⇒ 退出码非 0）
PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p6_instruments_selfcheck_v1.py
```
