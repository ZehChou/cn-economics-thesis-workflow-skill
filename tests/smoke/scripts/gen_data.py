"""生成合成面板数据（仅用于冒烟测试，非真实数据）。

数据生成过程（DGP）：
- 500 家企业，2010—2022 年，非平衡面板（随机缺失年份）
- 城市层面按三批低碳城市试点（2010/2012/2017）与从未试点四类分配处理队列
- 真实政策效应：did 对绿色创新的系数约为 0.12
- 机制变量：融资约束 fc 下降、绿色注意力 gi 上升
- 异质性：非国有企业与重污染行业的效应更强

输出：data/raw/synthetic_firms.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 20240601
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "synthetic_firms.csv"

N_FIRMS = 500
YEARS = list(range(2010, 2023))
N_CITY = 60
N_IND = 20

# ── 城市与处理队列 ──
cities = [f"C{i:03d}" for i in range(1, N_CITY + 1)]
municipalities = {"C001", "C002", "C003", "C004"}
cohort_map = {}
city_list = cities.copy()
rng.shuffle(city_list)
cohort_map.update({c: 2010 for c in city_list[:18]})
cohort_map.update({c: 2012 for c in city_list[18:32]})
cohort_map.update({c: 2017 for c in city_list[32:42]})
cohort_map.update({c: 0 for c in city_list[42:]})   # 0 = 从未试点

# ── 企业层面属性 ──
firm_id = np.arange(1, N_FIRMS + 1)
firm_city = rng.choice(cities, size=N_FIRMS)
firm_ind = rng.integers(1, N_IND + 1, size=N_FIRMS)
firm_est = rng.integers(1950, 2015, size=N_FIRMS)
firm_soe = rng.binomial(1, 0.35, size=N_FIRMS)
# 重污染行业：行业代码 1—4 视为重污染
firm_heavy = np.isin(firm_ind, [1, 2, 3, 4]).astype(int)
firm_fe = rng.normal(0, 0.45, size=N_FIRMS)          # 企业不可观测异质性
firm_ipr = rng.normal(0, 1, size=N_FIRMS)            # 地区知识产权保护强度（标准化）

rows = []
for i in range(N_FIRMS):
    fid = int(firm_id[i])
    city = firm_city[i]
    cohort = cohort_map[city]
    # 非平衡面板：随机缺失约 5% 的年份
    keep = rng.random(len(YEARS)) > 0.05
    for y, k in zip(YEARS, keep):
        if not k:
            continue
        did = int(cohort > 0 and y >= cohort)
        # 控制变量
        size = 22.0 + 0.35 * firm_fe[i] + 0.12 * (y - 2010) + rng.normal(0, 0.55)
        lev = np.clip(0.42 + 0.05 * firm_fe[i] + rng.normal(0, 0.16), 0.05, 0.95)
        roa = 0.04 + 0.012 * firm_fe[i] + rng.normal(0, 0.045)
        growth = 0.12 + rng.normal(0, 0.22)
        age = y - firm_est[i]
        cash = np.clip(0.18 + rng.normal(0, 0.09), 0.005, 0.75)

        # 机制变量
        fc = 3.20 - 0.085 * did - 0.06 * size + rng.normal(0, 0.22) + 0.10 * firm_fe[i]
        gi = 0.90 + 0.105 * did + 0.04 * size + rng.normal(0, 0.25)

        # 绿色创新（对数）：真实政策效应 0.12，重污染行业更强
        eff = 0.12 * did * (1 + 0.35 * firm_heavy[i]) * (1 - 0.20 * firm_soe[i])
        green_pat = (0.30 + eff + 0.28 * size - 0.35 * lev + 0.90 * roa
                     + 0.05 * growth - 0.004 * age + 0.35 * cash
                     + 0.55 * firm_fe[i] + 0.02 * (y - 2010)
                     + 0.22 * firm_ipr[i] + rng.normal(0, 0.30))

        # 替换被解释变量：绿色发明专利（高度相关但含独立噪声）
        green_inv = green_pat * 0.72 + rng.normal(0, 0.28)

        rows.append({
            "id": fid, "year": y, "industry": int(firm_ind[i]),
            "city": city, "province": city, "first_treat": cohort,
            "did": did, "green_pat": round(green_pat, 4), "green_inv": round(green_inv, 4),
            "size": round(size, 4), "lev": round(lev, 4), "roa": round(roa, 4),
            "growth": round(growth, 4), "age": int(age), "cash": round(cash, 4),
            "fc": round(fc, 4), "gi": round(gi, 4),
            "soe": int(firm_soe[i]), "heavy": int(firm_heavy[i]), "ipr": round(firm_ipr[i], 4),
            "is_municipality": int(city in municipalities),
        })

df = pd.DataFrame(rows).sort_values(["id", "year"]).reset_index(drop=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"合成面板已生成：{OUT}")
print(f"观测值 {len(df)}，企业 {df['id'].nunique()} 家，年份 {df['year'].min()}–{df['year'].max()}")
print("处理队列分布（企业数）：")
print(df.drop_duplicates("id")["first_treat"].value_counts().sort_index().to_string())
print(f"处理组观测占比：{df['did'].mean():.3f}")
