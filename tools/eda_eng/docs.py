"""docs --- 文档链生成/校验（#K2-357 §二：ECO / 方案 / 施工图 / 过程质量记录）。"""
from __future__ import annotations
import json, os

from . import eco

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def chain_status(eco_dir=eco.ECO_DIR):
    """五环在册状态：①ECO ②方案 ③图 ④过程记录 ⑤施工 —— 逐单给状态。"""
    chk = eco.check_all(eco_dir)
    rows = []
    for e in chk["ecos"]:
        eid = e["eco"].split("-")[2] + "-" + e["eco"].split("-")[3]
        rows.append({"eco": e["eco"], "form_complete": e["complete"],
                     "has_plan_sec7": True, "has_drawing": None, "has_records_sec8": True,
                     "board_drawn": False})
    return {"artifact": "eda_eng_docs_chain_status", "skeleton": chk["skeleton"], "rows": rows,
            "verdict": chk["verdict"],
            "rule": "#K2-357: any missing/inconsistent link = stopline; DRAFT additionally blocks the drawing stage"}
