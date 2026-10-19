"""Phase 3：描述性统计、相关系数矩阵与分布图。"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from _common import load_data, v, TAB, FIG

# 中文字体（Windows 自带）
for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]:
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

df = load_data()
v = v()
cols = [v["Y"], v["Y_alt"], v["X"], *v["controls_list"], *v["mechanism"], *v["heterogeneity"]]
cols = [c for c in dict.fromkeys(cols) if c in df.columns]

# 描述性统计
desc = pd.DataFrame({
    "观测值": df[cols].count(),
    "均值": df[cols].mean(),
    "标准差": df[cols].std(),
    "最小值": df[cols].min(),
    "最大值": df[cols].max(),
}).round(4)
desc.to_csv(TAB / "desc.csv", encoding="utf-8-sig")
print(desc.to_string())

# 相关系数矩阵
corr = df[[v["Y"], v["X"], *v["controls_list"]]].corr().round(3)
corr.to_csv(TAB / "corr.csv", encoding="utf-8-sig")

# 图 1：核心变量分布
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
axes[0].hist(df[v["Y"]].dropna(), bins=30, color="#4C72B0", edgecolor="white")
axes[0].set_title(f"{v['Y']} 分布")
axes[1].hist(df[v["X"]].dropna(), bins=2, color="#55A868", edgecolor="white")
axes[1].set_title(f"{v['X']} 分布")
fig.tight_layout()
fig.savefig(FIG / "dist.png", dpi=200)
plt.close(fig)

# 图：处理组与控制组的绿色创新均值趋势
trend = df.groupby(["year", v["X"]])[v["Y"]].mean().unstack()
trend.columns = ["控制组", "处理组"] if list(trend.columns) == [0, 1] else trend.columns
trend.plot(marker="o", figsize=(6, 3.5))
plt.ylabel(v["Y"])
plt.title("分组均值趋势")
plt.tight_layout()
plt.savefig(FIG / "trend.png", dpi=200)
plt.close()

print("描述统计与图形已输出")
