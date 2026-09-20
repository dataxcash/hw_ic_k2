# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
import pcbnew
BOARD='/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb'
DEL_REFS = set(['U3','U7']) | {f'C{i}' for i in range(17,33)} | {f'C{i}' for i in range(49,73)} \
    | {'R4','R5','R6','R7','R9','R10','R11','R12','R17','R18','R19','R20','R22','R23','R24','R25','R26','R27'}
bd = pcbnew.LoadBoard(BOARD)
deleted=[]
for fp in list(bd.GetFootprints()):
    if fp.GetReference() in DEL_REFS:
        bd.Remove(fp); deleted.append(fp.GetReference())
print('deleted:', len(deleted))
ok=pcbnew.SaveBoard(BOARD, bd)
print('saved:', ok)
