"""Phase 7：机制检验（江艇两步法 + Sobel + Bootstrap 间接效应区间）。

对每个机制变量分别报告：政策对机制变量的影响、机制变量对结果变量的影响、
Sobel 统计量与 Bootstrap 区间。
"""
import numpy as np
import pandas as pd
from scipy import stats
import pyfixest as pf

from _common import load_data, spec_log, v, TAB, SEED, coef_row

np.random.seed(SEED)
df = load_data()
v = v()
CTRL = " + ".join([c for c in v["controls_list"] if c != "age"])
MECHS = v["mechanism"]


def fit(y, d=None):
    return pf.feols(f"{y} ~ {v['X']} + {CTRL} | {v['fe']}",
                    data=df if d is None else d, vcov={"CRV1": v["cluster"]})


path_rows, sobel_rows = [], []
for m in MECHS:
    # 第一步：X → M（江艇两步法只在此处做因果检验）
    f = fit(m)
    r1 = coef_row(f, v["X"])
    # 第二阶段系数：仅用于描述性补充，不作为中介效应成立的依据
    fb = pf.feols(f"{v['Y']} ~ {v['X']} + {m} + {CTRL} | {v['fe']}", data=df,
                  vcov={"CRV1": v["cluster"]})
    r2 = coef_row(fb, m)
    print(f"X → {m}: coef={r1['coef']:.4f}, se={r1['se']:.4f}, p={r1['p']:.4f} | "
          f"{m} → Y: coef={r2['coef']:.4f}, p={r2['p']:.4f}")

    path_rows.append({"机制变量": m, "路径": f"X→{m}", "系数": round(r1["coef"], 4),
                      "标准误": round(r1["se"], 4), "p值": round(r1["p"], 4)})
    path_rows.append({"机制变量": m, "路径": f"{m}→Y", "系数": round(r2["coef"], 4),
                      "标准误": round(r2["se"], 4), "p值": round(r2["p"], 4)})
    spec_log("P7", f"X → {m}", r1["coef"], r1["se"], r1["p"], True, "江艇两步法第一步")
    spec_log("P7", f"{m} → Y（含 X）", r2["coef"], r2["se"], r2["p"], True,
             "第二阶段补充回归，仅作描述")

    # Sobel 检验
    a, sa = r1["coef"], r1["se"]
    b, sb = r2["coef"], r2["se"]
    sobel_z = a * b / np.sqrt(b**2 * sa**2 + a**2 * sb**2)
    sobel_p = 2 * (1 - stats.norm.cdf(abs(sobel_z)))

    # Bootstrap 间接效应
    BOOT = 300
    boot = []
    for i in range(BOOT):
        d = df.sample(len(df), replace=True, random_state=SEED + i)
        af = fit(m, d)
        bf = pf.feols(f"{v['Y']} ~ {v['X']} + {m} + {CTRL} | {v['fe']}", data=d,
                      vcov={"CRV1": v["cluster"]})
        try:
            boot.append(float(af.tidy().loc[v["X"], "Estimate"]) *
                        float(bf.tidy().loc[m, "Estimate"]))
        except KeyError:
            continue
    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  Sobel z={sobel_z:.4f} (p={sobel_p:.4f})；Bootstrap 95% CI "
          f"[{lo:.4f}, {hi:.4f}]，含 0：{lo <= 0 <= hi}")

    sobel_rows.append({
        "机制变量": m, "a": round(a, 4), "se_a": round(sa, 4),
        "b": round(b, 4), "se_b": round(sb, 4), "p_b": round(r2["p"], 4),
        "sobel_z": round(sobel_z, 4), "sobel_p": round(sobel_p, 4),
        "boot_mean": round(float(boot.mean()), 4), "boot_lo": round(float(lo), 4),
        "boot_hi": round(float(hi), 4), "boot_reps": BOOT,
        "ci_contains_zero": bool(lo <= 0 <= hi),
    })
    spec_log("P7", f"Sobel（{m}）", sobel_z, None, sobel_p, True,
             "间接效应检验", stat_name="sobel_z")

pd.DataFrame(path_rows).to_csv(TAB / "mechanism.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(sobel_rows).to_csv(TAB / "sobel.csv", index=False, encoding="utf-8-sig")
print("机制检验完成")
