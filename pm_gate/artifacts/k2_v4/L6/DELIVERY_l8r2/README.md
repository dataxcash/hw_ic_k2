# K2 P5 交付封装 — `k2_v4_8L.l8r2`（受审板 `7a5c89913d6e5d0a`）

| 件 | 说明 |
|---|---|
| `k2_v4_8L.l8r2_gerber_package.tar.gz` | 完整交付包（= `../jlc_package_l8r2/`，53 件 + MANIFEST.json） |
| `SHA256SUMS.txt` | 逐件 sha256（相对 `L6/`） |
| `../jlc_package_l8r2/MANIFEST.json` | 机读 MANIFEST（board/pro sha · 命令 · 件表 · DFM 汇总） |
| `../jlc_package_l8r2/ORDER_NOTES.md` | 制造备注（JLC HDI 通道） |
| `../jlc_package_l8r2/DISCLOSURE.md` | 具名披露（170 warning / OUT #5 / F-9 / L-1 / P5 新项） |

- DFM 对 JLC HDI 通道：**16 PASS / 1 ACCEPT / 0 FAIL**；N-01：平面层 4/4 `G36>0`；钻孔 754 孔。
- 判据锚 rev=6 · 冻结四源未动 · 打包确定性（固定 mtime/uid/gid ⇒ tar sha 可复现）。
- 下单/报价/交期 = 商务，不在 ENG 范围（#15）。
