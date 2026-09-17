#!/usr/bin/env python3
"""K2 · P4 · 「判据集 == manifest 应然集」覆盖率闸（只读，可复跑）。

应然集（权威来源，ENG 不新增）：
  - 登记册 §C 冻结维度 J-1..J-10（`.omo/supervision/ledger/K2-DEFECT-REGISTER-v1.md`）
  - 计划 §3.3 V 类可机判项 V1..V3（`k2/docs/K2-RECTIFICATION-PLAN-v1.md`）
  - 计划 §P4 三项「前置」：铺铜 / 钻孔 / 平面落图

用法：
  python3 k2/tools/k2_p4_gate_coverage_v1.py \
      --verdict /tmp/opencode/v3_POS.json \
      --verdict-option-a /tmp/opencode/optiona_verdict.json
  （缺任一件时对应列显示 `-`；两件均由草案判定器产出，非本工具自判。）
"""
import argparse, json, os, sys

# 权威判据 -> (语义, [manifest check id...], 备注)
MATRIX = [
 ("J-1",  "DRC error = 0（warning 逐项有处置结论）", ["drc_errors", "drc_warning_disposition"],
  "前半=error 计数；后半=逐条处置台账（监理登记 drc_warning_dispositions）"),
 ("J-2",  "连通 = 0（补铜后）", ["unconnected_zero"], "补铜后全量、范围=权威网表全集（禁裁剪）"),
 ("J-3",  "铺铜全填充", ["zone_filled"], "分母=可填充 zone（非 keepout）；与 §P4 铺铜前置同式"),
 ("J-4",  "丝印检查全开且 0 违规", ["rule_severity_manifest", "drc_warning_disposition"],
  "全开=无未登记 ignore（WS 台账）；0 违规须先全开（现行 9 条 ignore 含 silk_over_copper/silk_overlap/missing_courtyard）"),
 ("J-5",  "走线仅 45°（非 45° 段 = 0）", ["non45_segments"], "本板 0/4705"),
 ("J-6",  "板↔原理图一致（refdes/封装/pad 集）", ["refdes_sets_equal", "pin_map_complete"],
  "refdes 差集须先剔除 mechanical_refdes（H1..H4 固定孔）"),
 ("J-7",  "封装 = 库（mismatch/issues = 0 且 fp-lib-table 存在）", ["lib_footprint_electrical", "fp_lib_table_present"],
  "电气级口径（pad 数/名/形状/尺寸/钻孔/自转/局部位置）；无库链接件按 lib_footprint_link_policy（null ⇒ fail-closed）"),
 ("J-8a", "每器件 pad 数 ≥1", ["device_has_pads"], "审计 §10.8 L2-8 子项字母"),
 ("J-8b", "器件不重叠", [], "由 DRC `courtyards_overlap`（severity=error，现 0 条）经 J-1/drc_errors 覆盖"),
 ("J-8c", "出框 = 0（P3-4 口径）", ["board_frame_and_keepout"], ""),
 ("J-8d", "回避区生效 / 密度分布 / 关键间距", ["board_frame_and_keepout", "density_and_spacing"],
  "回避区=C5b/IN-7（每区 ≥1 非 allowed，5 开关含 copperpour）；密度/关键间距阈值待监理填"),
 ("J-8e", "固定孔 / 钻孔（NPTH≥4、PTH≥插件引脚数）", ["drill_count"], "计划 §P4 钻孔前置"),
 ("J-9",  "门禁接入（pipeline.yaml 存在且 ④段判据全机判）", ["pipeline_present"], "W-9：scope=k2（#K2-19 §二）"),
 ("J-10", "完工定义可复现（命令+阈值+原始输出）", ["verdict_schema"], "产物 schema 无 verdict 字段；命令/阈值留痕见本表与计划"),
 ("V1",   "网表闭合：每条声明网有实现 + 补铜后全量 unconnected = 0", ["net_declared_realized", "unconnected_zero"],
  "范围=权威网表全集，禁裁剪"),
 ("V2",   "引脚映射：每 (ref,pin) 有焊盘；pad 数 == 符号引脚数", ["pin_map_complete"], ""),
 ("V3",   "参考连续性：每段高速走线相邻层有连续参考平面", ["v3_reference_continuity"], "逐段投影采样 0.2mm"),
 ("§P4-1","铺铜前置（计划 §P4）", ["zone_filled"], "与 J-3 同式"),
 ("§P4-2","钻孔前置（计划 §P4）", ["drill_count"], "与 J-8e 同式"),
 ("§P4-3","平面落图前置（计划 §P4）：平面层 Gerber G36 > 0", ["gerber_plane_g36"], "v3 新增转写；层集合=In1/In3/In6 GND + In4 电源"),
]

def load(p):
    if not p or not os.path.exists(p): return None
    v = json.load(open(p, encoding='utf-8'))
    st = {r['check']: r for r in v.get('oks', []) + v.get('fails', [])}
    return v, st

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verdict', default='/tmp/opencode/v3_POS.json', help='草案 v3 对现板（37019705ef994ccc）')
    ap.add_argument('--verdict-option-a', default='/tmp/opencode/optiona_verdict.json', help='草案 v3 对 W-8 选项(甲′) 预览板')
    a = ap.parse_args()
    A, sa = load(a.verdict); B, sb = load(a.verdict_option_a)

    def cell(st, ids):
        if st is None: return '-'
        sym = []
        for i in ids:
            r = st.get(i)
            sym.append('OK' if (r and r['ok']) else ('FAIL' if r else '?'))
        return '/'.join(sym)

    print(f"{'权威判据':8s} {'语义':46s} {'v3 ID':24s} {'现板':10s} {'选项(甲′)':10s}")
    for cid, sem, ids, note in MATRIX:
        print(f"{cid:8s} {sem[:44]:46s} {(','.join(ids) or '(经DRC覆盖)')[:22]:24s} {cell(sa,ids):10s} {cell(sb,ids):10s}")
    want = sorted({i for _, _, ids, _ in MATRIX for i in ids})
    got = sorted(sa.keys()) if sa else (sorted(sb.keys()) if sb else [])
    print()
    print(f"应然 check id（去重）= {len(want)}: {want}")
    if got:
        print(f"manifest v3 check id   = {len(got)}")
        print(f"缺失（应然有、manifest 无）= {sorted(set(want) - set(got))}")
        print(f"越界（manifest 有、应然无）= {sorted(set(got) - set(want))}")
    if A: print(f"现板   : PASS {A['n_pass']} / FAIL {A['n_fail']}  (FAIL: {[f['check'] for f in A['fails']]})")
    if B: print(f"(甲′)  : PASS {B['n_pass']} / FAIL {B['n_fail']}  (FAIL: {[f['check'] for f in B['fails']]})")
    return 0

if __name__ == '__main__':
    sys.exit(main())
