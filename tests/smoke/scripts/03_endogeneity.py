"""Phase 5：内生性处理（Oster 检验 + 事件研究 + 平行趋势联合检验）。

对应附录 H.3.3 与 H.3.4（按本次冒烟测试实测接口修订）。
"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pyfixest as pf

from _common import load_data, spec_log, v, TAB, FIG, save_state, coef_row

for name in ["Microsoft YaHei", "SimHei"]:
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

df = load_data()
v = v()
COHORT = "first_treat"

# 相对时间：从未处理组取哨兵值 -999（不可用 NaN，pyfixest 的 Rust 去均值会崩溃）
df["rel_time"] = np.where(df[COHORT] > 0, df["year"] - df[COHORT], -999)


def r2_of(fit) -> float:
    for attr in ("_r2", "_r2_within", "r2"):
        val = getattr(fit, attr, None)
        if val is not None:
            return float(val)
    raise RuntimeError("无法取得 R²")


def oster(uncontrolled, controlled, xvar, delta=1.0, rmax=None) -> dict:
    b0 = float(uncontrolled.tidy().loc[xvar, "Estimate"])
    b1 = float(controlled.tidy().loc[xvar, "Estimate"])
    r0, r1 = r2_of(uncontrolled), r2_of(controlled)
    rmax = min(1.3 * r1, 1.0) if rmax is None else rmax
    bias = delta * (b0 - b1) * (rmax - r1) / (r1 - r0) if r1 > r0 else np.nan
    bstar = b1 - bias
    return {
        "beta_tilde": b1, "beta_star": bstar,
        "r2_uncontrolled": r0, "r2_controlled": r1, "rmax": rmax,
        "interval_low": min(b1, bstar), "interval_high": max(b1, bstar),
        "contains_zero": bool(min(b1, bstar) <= 0 <= max(b1, bstar)),
    }


unc = pf.feols(f"{v['Y']} ~ {v['X']} | {v['fe']}", data=df, vcov={"CRV1": v["cluster"]})
ctr = pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']}", data=df,
               vcov={"CRV1": v["cluster"]})
oster_res = oster(unc, ctr, v["X"])
print("Oster 检验：", {k: (round(x, 4) if isinstance(x, float) else x) for k, x in oster_res.items()})
pd.DataFrame([oster_res]).to_csv(TAB / "oster.csv", index=False, encoding="utf-8-sig")
spec_log("P5", "Oster 检验（δ=1）", oster_res["beta_star"], None, None, True,
         f"识别区间 [{oster_res['interval_low']:.3f}, {oster_res['interval_high']:.3f}]",
         stat_name="beta_star")

# ── 事件研究：TWFE + 相对时间虚拟变量 ──
# age 与 id+year 固定效应完全共线，本规格剔除
ctrl = " + ".join([c for c in v["controls_list"] if c != "age"])
es = pf.feols(f"{v['Y']} ~ i(rel_time, ref=-1) + {ctrl} | {v['fe']}",
              data=df, vcov={"CRV1": v["cluster"]})
names = list(es.tidy().index)
pre = [x for x in names if x.startswith("rel_time::-")]
post = [x for x in names if x.startswith("rel_time::") and "::-" not in x]
print(f"\n事件期系数：政策前 {len(pre)} 个，政策后 {len(post)} 个")

R = np.zeros((len(pre), len(names)))
for i, term in enumerate(pre):
    R[i, names.index(term)] = 1.0
wald = es.wald_test(R, np.zeros(len(pre)))
print(f"平行趋势联合检验：统计量 {wald['statistic']:.3f}，p = {wald['pvalue']:.4f}")
pd.DataFrame([{"wald_stat": float(wald["statistic"]), "p_value": float(wald["pvalue"]),
               "n_pre_periods": len(pre)}]).to_csv(
    TAB / "pretrend_test.csv", index=False, encoding="utf-8-sig")

ev = es.tidy().loc[pre + post].copy()
ev["period"] = [int(str(i).split("::")[-1]) for i in ev.index]
ev = ev.sort_values("period")
ev.to_csv(TAB / "event_study.csv", encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.errorbar(ev["period"], ev["Estimate"], yerr=1.96 * ev["Std. Error"],
            fmt="o-", color="#C44E52", capsize=3, label="估计值及 95% 置信区间")
ax.axhline(0, color="grey", lw=0.8, ls="--")
ax.axvline(-0.5, color="black", lw=0.8, ls=":")
ax.set_xlabel("相对政策实施年份")
ax.set_ylabel("处理效应估计值")
ax.set_title("事件研究：平行趋势与动态效应")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "event_study.png", dpi=200)
plt.close(fig)

twfe = pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']}", data=df,
                vcov={"CRV1": v["cluster"]})
r_twfe = coef_row(twfe, v["X"])
print(f"TWFE 基准系数 {r_twfe['coef']:.4f}（se {r_twfe['se']:.4f}）")

post_coef = ev[ev["period"] >= 0]["Estimate"].mean()
spec_log("P5", "事件研究（TWFE, rel_time i(), ref=-1）", post_coef, None, None, True,
         "政策后各期系数均值；逐期系数与标准误见 output/tables/event_study.csv",
         stat_name="post_avg")
spec_log("P5", "TWFE 对照", r_twfe["coef"], r_twfe["se"], r_twfe["p"], True,
         "与事件研究并列报告，二者规格一致")

# 预趋势检验的覆盖范围：2010 队列在样本首年即已处理，无政策前观测
cohort_n = df.drop_duplicates("id")["first_treat"].value_counts().sort_index()
pre_obs = df[df["rel_time"] < 0].shape[0]
print(f"\n队列分布：{cohort_n.to_dict()}")
print(f"政策前观测数：{pre_obs}（占全样本 {pre_obs / len(df) * 100:.1f}%）；"
      f"2010 队列为始终处理组，不参与预趋势检验")
pd.DataFrame([{"cohort": int(k), "firms": int(v_)} for k, v_ in cohort_n.items()]).to_csv(
    TAB / "cohort_dist.csv", index=False, encoding="utf-8-sig")

# 稳健性：剔除始终处理组（2010 队列）
d_ex = df[df[COHORT] != 2010]
ex = pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']}", data=d_ex,
              vcov={"CRV1": v["cluster"]})
r_ex = coef_row(ex, v["X"])
print(f"剔除 2010 队列后：系数 {r_ex['coef']:.4f}（se {r_ex['se']:.4f}），N = {int(ex._N)}")
spec_log("P5", "剔除始终处理组（2010 队列）", r_ex["coef"], r_ex["se"], r_ex["p"], True,
         "排除始终处理组对 TWFE 权重的影响")

save_state(
    model_framework={
        "method": "TWFE + 事件研究",
        "fe": ["id", "year"],
        "cluster": v["cluster"],
        "cohort_var": COHORT,
        "pretrend_p": float(wald["pvalue"]),
    },
    endogeneity_results={
        "oster": {k: (float(x) if isinstance(x, (int, float, np.floating, np.bool_)) else x)
                  for k, x in oster_res.items()},
        "twfe_coef": r_twfe["coef"],
        "pretrend_p": float(wald["pvalue"]),
    },
)
print("模型框架已锁定")
