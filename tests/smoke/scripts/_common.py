"""公共骨架：路径、数据读取、规格日志、变量映射（对应附录 H.1）。"""
from pathlib import Path
import json
import datetime

import numpy as np
import pandas as pd
import pyfixest as pf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "cleaned" / "dataset.dta"
LOG = ROOT / "log"
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
for _d in (LOG, TAB, FIG):
    _d.mkdir(parents=True, exist_ok=True)

STATE = json.loads((ROOT / ".thesis_state.json").read_text(encoding="utf-8"))
SEED = 20240601
RUN_ID = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_data() -> pd.DataFrame:
    df = pd.read_stata(DATA)
    return df


def spec_log(phase: str, spec: str, coef, se, p, adopted: bool, reason: str,
             stat_name: str = "coef") -> None:
    """每个回归规格登记一行，供定稿时全量披露（附录 D.5）。

    追加 run_id 以便区分多次运行；stat_name 用于标识非系数类统计量（如 Sobel z）。
    """
    row = pd.DataFrame([{
        "run_id": RUN_ID,
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "phase": phase,
        "spec": spec,
        "stat_name": stat_name,
        "coef": None if coef is None else round(float(coef), 6),
        "se": None if se is None else round(float(se), 6),
        "p": None if p is None else round(float(p), 6),
        "adopted": int(bool(adopted)),
        "reason": reason,
    }])
    f = LOG / "spec-search.csv"
    row.to_csv(f, mode="a", header=not f.exists(), index=False, encoding="utf-8-sig")


def v() -> dict:
    """从 state 读取变量与模型设定，返回公式片段。"""
    var = STATE["variables"]
    mf = STATE.get("model_framework") or {}
    fe = mf.get("fe", ["id", "year"])
    return {
        "Y": var["Y"],
        "Y_alt": var.get("Y_alt"),
        "X": var["X"],
        "controls": " + ".join(var["controls"]),
        "controls_list": list(var["controls"]),
        "fe": " + ".join(fe),
        "cluster": mf.get("cluster", "id"),
        "mechanism": var.get("mechanism", []),
        "heterogeneity": var.get("heterogeneity", []),
    }


def save_state(**kw) -> None:
    STATE.update(kw)
    (ROOT / ".thesis_state.json").write_text(
        json.dumps(STATE, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def coef_row(fit, term: str) -> dict:
    """从 pyfixest 估计结果中取出指定变量的系数、标准误与 p 值。"""
    tidy = fit.tidy()
    if term not in tidy.index:
        raise KeyError(f"结果中不存在变量 {term}；实际包含：{list(tidy.index)}")
    r = tidy.loc[term]
    return {
        "coef": float(r["Estimate"]),
        "se": float(r["Std. Error"]),
        "p": float(r["Pr(>|t|)"]),
    }
