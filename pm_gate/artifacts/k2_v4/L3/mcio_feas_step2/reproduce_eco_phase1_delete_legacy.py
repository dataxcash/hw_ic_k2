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
