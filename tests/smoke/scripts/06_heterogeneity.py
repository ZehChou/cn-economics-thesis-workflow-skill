"""Phase 8：异质性分析（全交互模型 + 交互项检验 + FDR 校正）。"""
import numpy as np
import pandas as pd
import pyfixest as pf
from statsmodels.stats.multitest import multipletests

from _common import load_data, spec_log, v, TAB, coef_row

df = load_data()
v = v()
CTRL = " + ".join([c for c in v["controls_list"] if c != "age"])
DIMS = ["soe", "heavy"]

rows = []
for g in DIMS:
    # 全交互扩展模型：组间差异由交互项检验，而非比较分组显著性
    f = pf.feols(f"{v['Y']} ~ {v['X']}*{g} + {CTRL} | {v['fe']}", data=df,
                 vcov={"CRV1": v["cluster"]})
    print(f"\n===== 交互模型：{g} =====")
    print(f.tidy())

    inter = [t for t in f.tidy().index if ":" in str(t) and g in str(t)]
    if not inter:
        inter = [t for t in f.tidy().index if ":" in str(t)]
    term = inter[0]
    r = coef_row(f, term)
    rows.append({"维度": g, "交互项": term, "系数": round(r["coef"], 4),
                 "标准误": round(r["se"], 4), "p值": round(r["p"], 4), "N": int(f._N)})
    spec_log("P8", f"{g} 交互项", r["coef"], r["se"], r["p"], True, "全交互模型组间差异检验")

    # 分组系数（仅用于展示组内效应，不作为组间差异证据）
    for gv in sorted(df[g].dropna().unique()):
        sub = df[df[g] == gv]
        fs = pf.feols(f"{v['Y']} ~ {v['X']} + {CTRL} | {v['fe']}", data=sub,
                      vcov={"CRV1": v["cluster"]})
        rs = coef_row(fs, v["X"])
        rows.append({"维度": g, "交互项": f"组内系数({g}={gv})", "系数": round(rs["coef"], 4),
                     "标准误": round(rs["se"], 4), "p值": round(rs["p"], 4),
                     "N": len(sub)})

res = pd.DataFrame(rows)
main = res[~res["交互项"].str.contains("组内系数")].copy()
rej, p_adj, _, _ = multipletests(main["p值"].fillna(1), alpha=0.05, method="fdr_bh")
main["p_fdr"] = np.round(p_adj, 4)
print("\n交互项检验与 FDR 校正：")
print(main.to_string(index=False))

res.to_csv(TAB / "heterogeneity.csv", index=False, encoding="utf-8-sig")
main.to_csv(TAB / "heterogeneity_interactions.csv", index=False, encoding="utf-8-sig")
print("异质性分析完成")