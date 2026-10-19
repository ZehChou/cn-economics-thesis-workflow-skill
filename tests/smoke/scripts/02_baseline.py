"""Phase 4：基准回归（四个模型，对应附录 H.2）。"""
import numpy as np
import pandas as pd
import pyfixest as pf

from _common import load_data, spec_log, v, TAB, coef_row

df = load_data()
v = v()

models = {
    "m1": pf.feols(f"{v['Y']} ~ {v['X']}", data=df, vcov="HC1"),
    "m2": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']}", data=df, vcov="HC1"),
    "m3": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']}",
                   data=df, vcov={"CRV1": v["cluster"]}),
    "m4": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']} + industry^year",
                   data=df, vcov={"CRV1": v["cluster"]}),
}

for k, fit in models.items():
    print(f"\n===== {k} =====")
    fit.summary()

tidy = models["m4"].tidy()
print("\nm4 系数表：")
print(tidy)

tab = pf.etable(list(models.values()), type="df")
tab.to_csv(TAB / "baseline.csv", encoding="utf-8-sig")

r = coef_row(models["m4"], v["X"])
for k, f in models.items():
    rr = coef_row(f, v["X"])
    spec_log("P4", f"baseline {k}", rr["coef"], rr["se"], rr["p"],
             k == "m4", "基准回归规格 " + k)

b = r["coef"]
sd_x, sd_y = df[v["X"]].std(), df[v["Y"]].std()
print(f"\n核心系数 {b:.4f}，标准误 {r['se']:.4f}，p = {r['p']:.4f}")
print(f"标准化效应 = {b * sd_x / sd_y:.4f}")
print(f"半弹性解释：政策实施使被解释变量提高约 {(np.exp(b) - 1) * 100:.2f}%")

# 共线性核查：age 与 id+year 固定效应完全共线，若被剔除需明确记录
dropped = [t for t in v["controls_list"] if t not in models["m3"].tidy().index]
print("因共线被剔除的控制变量：", dropped if dropped else "无")

pd.DataFrame([{"model": k, "coef": coef_row(f, v["X"])["coef"],
               "se": coef_row(f, v["X"])["se"],
               "p": coef_row(f, v["X"])["p"],
               "n": int(f._N), "r2": float(f._r2)}
              for k, f in models.items()]
             ).to_csv(TAB / "baseline_coef.csv", index=False, encoding="utf-8-sig")
pd.DataFrame({"dropped_controls": [",".join(dropped)]}).to_csv(
    TAB / "baseline_notes.csv", index=False, encoding="utf-8-sig")
