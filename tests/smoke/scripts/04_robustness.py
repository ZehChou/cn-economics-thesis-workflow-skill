"""Phase 6：稳健性检验（缩尾、替换被解释变量、剔除直辖市、安慰剂检验）。"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pyfixest as pf

from _common import load_data, spec_log, v, TAB, FIG, SEED, coef_row

for name in ["Microsoft YaHei", "SimHei"]:
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

np.random.seed(SEED)
df = load_data()
v = v()
CTRL = " + ".join([c for c in v["controls_list"] if c != "age"])


def fit(d, y=None):
    y = y or v["Y"]
    return pf.feols(f"{y} ~ {v['X']} + {CTRL} | {v['fe']}", data=d,
                    vcov={"CRV1": v["cluster"]})


def winsorize(s, lo=0.01, hi=0.99):
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)


results = {}

base = fit(df)
results["基准"] = {**coef_row(base, v["X"]), "n": int(base._N)}

# 1) 缩尾 1%
df_w = df.copy()
for c in [v["Y"], v["X"], *v["controls_list"], *v["mechanism"]]:
    if df_w[c].dtype.kind in "fiu":
        df_w[c] = winsorize(df_w[c])
f_win = fit(df_w)
results["缩尾 1%"] = {**coef_row(f_win, v["X"]), "n": int(f_win._N)}

# 2) 替换被解释变量
f_alt = fit(df, y=v["Y_alt"])
results["替换被解释变量"] = {**coef_row(f_alt, v["X"]), "n": int(f_alt._N)}

# 3) 剔除直辖市
f_mun = fit(df[df["is_municipality"] == 0])
results["剔除直辖市"] = {**coef_row(f_mun, v["X"]), "n": int(f_mun._N)}

# 4) 安慰剂检验：随机置换处理状态 500 次
REPS = 500
placebo = []
cohort_unit = (df[["id", "first_treat"]].drop_duplicates("id")
               .sort_values("id").reset_index(drop=True))

for _ in range(REPS):
    # 在企业层面置换处理队列（保留队列规模与年份分布），再据此生成虚拟处理状态
    fake = cohort_unit.copy()
    fake["fake_cohort"] = np.random.permutation(fake["first_treat"].to_numpy())
    d = df.merge(fake[["id", "fake_cohort"]], on="id", how="left")
    d["did_fake"] = ((d["fake_cohort"] > 0) & (d["year"] >= d["fake_cohort"])).astype(int)
    f = pf.feols(f"{v['Y']} ~ did_fake + {CTRL} | {v['fe']}", data=d,
                 vcov={"CRV1": v["cluster"]})
    placebo.append(float(f.tidy().loc["did_fake", "Estimate"]))

placebo = np.array(placebo)
real = results["基准"]["coef"]
n_ge = int((np.abs(placebo) >= abs(real)).sum())
p_perm = n_ge / REPS
p_report = f"<{1 / (REPS + 1):.4f}" if n_ge == 0 else f"{p_perm:.4f}"
print(f"安慰剂：均值 {placebo.mean():.4f}，标准差 {placebo.std():.4f}，"
      f"{REPS} 次中不小于真实值的次数 {n_ge}，置换 p = {p_report}")
pd.DataFrame({"placebo_coef": placebo}).to_csv(
    TAB / "placebo_dist.csv", index=False, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(6, 3.4))
ax.hist(placebo, bins=40, color="#8C8C8C", edgecolor="white")
ax.axvline(real, color="#C44E52", ls="--", lw=1.4, label=f"真实估计值 {real:.3f}")
ax.set_xlabel("随机置换后的估计系数")
ax.set_ylabel("频数")
ax.set_title("安慰剂检验（500 次随机置换）")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "placebo.png", dpi=200)
plt.close(fig)

tab = pd.DataFrame([
    {"检验": k, "系数": round(x["coef"], 4), "标准误": round(x["se"], 4),
     "p值": round(x["p"], 4), "观测值": x["n"]} for k, x in results.items()
])
tab.loc[len(tab)] = {"检验": "安慰剂置换 p 值", "系数": None, "标准误": None,
                     "p值": p_report, "观测值": REPS}
tab.to_csv(TAB / "robustness.csv", index=False, encoding="utf-8-sig")
print(tab.to_string(index=False))

for k, x in results.items():
    spec_log("P6", k, x["coef"], x["se"], x["p"], True, "预设稳健性检验，全部报告")
spec_log("P6", f"安慰剂 {REPS} 次（企业层面置换队列）", None, None, p_perm, True,
         f"置换 p 报告为 {p_report}；n_ge={n_ge}")
print("稳健性检验完成")
