# cap_wall_v8 — restore（一行恢复命令）

## 本次板状态

**板未被改动**（求解失败 → 无布局 → 未 apply → 无回滚需求）。
`/tmp/opencode/boards/k2_v6.kicad_pcb` 保持任务开始前原样
（sha256 `aa8b3f07883c49a00cdfc1b06ccde5feed160199a84d389b0e74d90d538d2173`，
101 器件 / 32 颗目标电容原位 / rot 全 0）。

## 恢复命令（若板丢失或需重建，一行）

```bash
cd /home/fila/jqdDev_2025/ic_hw/strix-halo-ioconvert/revA/pcb && K2_OUT_PCB=/tmp/opencode/boards/k2_v6.kicad_pcb python3 eda_core/k2_gen_v5.py
```

> 依据：m13_v8_session_handoff.md §5「板重生成」与 §2.4（K2_OUT_PCB 环境变量覆盖，
> 默认输出零变化）。重建后应复核：101 器件 / 508 pads / rotation_changes=0 /
> k2_v5_v6_diff_report.json 口径（PASS）。
