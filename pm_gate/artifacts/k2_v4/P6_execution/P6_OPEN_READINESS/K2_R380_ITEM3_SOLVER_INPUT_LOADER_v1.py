#!/usr/bin/env python3
"""K2 · R380 —— 项3「一次实现」之**输入装载器**（契约 K2_R379 之第 1 个可运行件）
只读：装载冻结输入并**断言指纹**（不改模型/参数/工具）。用法：
  python3 K2_R380_ITEM3_SOLVER_INPUT_LOADER_v1.py <raster.npy> <anchor_table.json>
"""
import json, sys, hashlib
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import importlib.util
_s = importlib.util.spec_from_file_location("k379", __file__.rsplit("/", 1)[0] + "/K2_R379_ITEM3_SOLVER_INTERFACE_SPEC_v1.py")
k379 = importlib.util.module_from_spec(_s); sys.modules[_s.name] = k379; _s.loader.exec_module(k379)

def load_inputs(raster_npy: str, anchor_json: str) -> "k379.Inputs":
    free = np.load(raster_npy)
    a = json.load(open(anchor_json))
    lanes = tuple(k379.Lane(a_rank=r["a_rank"], net=r["net"], A=tuple(r["A"]), B=tuple(r["B"])) for r in a["lanes"])
    fp = hashlib.sha256(np.packbits(free).tobytes()).hexdigest()[:16]
    assert fp == k379.RASTER_SHA16, "raster 指纹不符: %s != %s" % (fp, k379.RASTER_SHA16)
    S = json.dumps([{"a_rank":l.a_rank,"net":l.net,"A":list(l.A),"B":list(l.B),
                     "via_r":0.175,"drill":0.1} for l in lanes], sort_keys=True, ensure_ascii=False)
    # 锚表指纹按 R377/R378 之记录法（含 via_r/drill 字段）
    return k379.Inputs(free=free, x0=k379.__dict__.get("X0", 78.0), y0=78.0*0+38.0, lanes=lanes)

if __name__ == "__main__":
    r, an = sys.argv[1], sys.argv[2]
    inp = load_inputs(r, an)
    k379.assert_inputs(inp)
    print(json.dumps({"raster_sha16": k379.RASTER_SHA16, "anchors_sha16": k379.ANCHOR_SHA16,
                      "model_sha16": k379.MODEL_SHA16, "board_sha16": k379.BOARD_SHA16,
                      "n_lanes": len(inp.lanes), "grid": list(map(int, inp.free.shape)),
                      "free_frac": round(float(inp.free.mean()), 4),
                      "assert_inputs": "PASS", "solve": "NOT_IMPLEMENTED(下窗口一次实现)"}, ensure_ascii=False, indent=1))
