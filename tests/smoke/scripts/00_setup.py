"""Phase 3：数据交接与变量登记。

- 读取原始 CSV，写为 Stata .dta（两个后端均可读取）
- 登记变量清单与模型框架到 .thesis_state.json
- 不做数据质量审查（附录 D / Phase 3 契约）
"""
from pathlib import Path
import json

import pandas as pd

from _common import ROOT, STATE, save_state

RAW = ROOT / "data" / "raw" / "synthetic_firms.csv"
DEC = json.loads((ROOT / "decisions.json").read_text(encoding="utf-8"))

df = pd.read_csv(RAW, encoding="utf-8-sig")
print(f"读入 {len(df)} 行 × {df.shape[1]} 列")

# 面板标识与类别变量整理
df["id"] = df["id"].astype(int)
df["year"] = df["year"].astype(int)
df["industry"] = df["industry"].astype("category")
df["city"] = df["city"].astype(str)

out = ROOT / "cleaned" / "dataset.dta"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_stata(out, write_index=False, version=118)
print(f"已写入 {out}")

var = DEC["phase3_variables"]
save_state(
    current_phase=3,
    data_path="cleaned/dataset.dta",
    variables={
        "Y": var["Y"],
        "Y_alt": var["Y_alt"],
        "X": var["X"],
        "controls": var["controls"],
        "mechanism": var["mechanism"],
        "heterogeneity": var["heterogeneity"],
    },
    model_framework={
        "method": "TWFE + Sun-Abraham",
        "fe": DEC["phase4_baseline"]["fe"],
        "cluster": DEC["phase4_baseline"]["cluster"],
        "cohort_var": DEC["phase5_endogeneity"]["cohort_var"],
    },
)
print("变量清单与模型框架已登记")

# 仅确认变量能否定位，不做质量评价
missing = [c for c in [var["Y"], var["Y_alt"], var["X"], *var["controls"], *var["mechanism"]]
           if c not in df.columns]
print("缺失变量：", missing if missing else "无")
