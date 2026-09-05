import sys, sqlite3, json
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core import knowledge_base as kb
DB = "/home/fila/jqdDev_2025/ic_hw/_shared/knowledge/kb.sqlite3"
tmpl = {
  "template_id": "corridor_pair_ds320pr1601_dual_band",
  "category": "corridor_pair",
  "name": "DS320PR1601 双向单芯片 — 双带走廊 + In2 翼带穿越 + Intel retimer common footprint 逃逸",
  "applicability": {
    "chip": "TI DS320PR1601 (nfBGA-354 22.9x9.0)",
    "footprint": "Intel PCIe5 retimer common footprint (354 ball 8.9x22.8, 非均匀分组逃逸优化)",
    "board_mm": [120, 46], "layers": 6, "stackup": "F/G/S/G/P/B",
    "corridor_pairs_per_side": 16, "band_topo": "dual_band", "band_pairs": 8,
    "refclk": "direct_bypass (redriver 零 REFCLK)", "single_side": True, "b_cu_empty": True,
    "cap_wall": "removed (64 AC integrated in TX)"
  },
  "structure": {
    "corridor": "F.Cu 8对/带 x 2带/侧 + In2 翼带 8对/翼 (穿越 50%) + REFCLK In2 S翼分带包地",
    "escape": "Intel retimer common footprint lane分组+组间通道(0.3/0.4/0.8/1.2 TYP), 每差分对单层逃逸设计目标",
    "col_bands": {"A_PER": [1,2], "B_PET": [7,10], "A_PET": [26,29], "B_PER": [34,35]},
    "via_policy": "F->In2->F, <=2/网, 受控, 背钻, GND伴行",
    "orient": "orient-0 (col1-10 西 MCIO, col26-35 东 J2), 输出组就近连接器"
  },
  "params": {
    "track_width_mm": 0.205, "intra_gap_mm": 0.175,
    "inter_pair_spacing_mm": 0.875,  # 语义待裁定: 0.875中心距/0.875铜边->1.46中心距/1.08轨距
    "band_pairs_mm": 10.80, "chip_center": [93.8, 53.7], "board_edge": [23,143,33,79]
  },
  "validation": {
    "source": "k2_v4 v21 (m13 MCIO 布局可行性 ECN)",
    "produced": False,
    "drc_passed": None, "skew_ok": None,
    "closure": "结构预检闭合 + 走廊闭合 + 逃逸封装设计级(Intel common footprint 逃逸优化); 未做工具精确逐球求解(资产缺)",
    "known_gaps": [
      "DS320PR1601 物理球栅坐标无公开源(需 Intel PCIe5 retimer spec 图/TI EVM), 逃逸精确求解未实证=本模板 produced=false",
      "inter_pair_spacing 语义三值未裁定(引擎 0.875 中心距 / 强条 R3-2 0.875 铜边→1.46中心 / 冻结轨距 1.08), 跑容量/工具前须对账"
    ]
  },
  "provenance": {
    "origin": "project_k2", "board": "k2_v4",
    "spec_ref": "L1_TOPOLOGY_v2.0 / L2_STRUCTURE_v2.0 (v21 ECN)",
    "datasheet": "TI SNLS683 Table 5-1 (列带逐球解析, 全16 lane一致)",
    "refs": ["librarian footprint 核破: Intel PCIe5 retimer common footprint", "v21_realroute/*"],
    "cap_wall_ac": "本板关闭 (AC 集成芯片, 32x0402 墙移除)"
  },
  "version": 1
}
conn = sqlite3.connect(DB)
res = kb.put_template(conn, tmpl)
print("put_template result:", json.dumps(res, ensure_ascii=False, indent=1)[:400] if isinstance(res,(dict,list)) else res)
conn.commit()
# 验证
g = kb.get_template(conn, "corridor_pair_ds320pr1601_dual_band")
print("get back:", g["template_id"], "| produced:", json.loads(g["validation"])["produced"] if isinstance(g["validation"],str) else g["validation"].get("produced"))
conn.close()
print("KB writeback OK: DS320PR1601 corridor template 落库")
