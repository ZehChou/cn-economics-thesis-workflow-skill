## 附录 H：计量执行后端 B — Python（默认）

> **适用**：`.thesis_state.json` 中 `analysis_backend = "python"`（Phase 0 Step 0.3 选择，默认值）。
>
> **定位**：本附录是 Phase 4-8 的**代码唯一真源**。Phase 文件只描述"做什么、验收什么"，可运行代码全部在此。后端 A（Stata）的等价代码见附录 I。
>
> **为什么默认 Python**：零许可证、零 MCP 配置、报错栈可读、与 Phase 3 数据清洗同语言、表格可直写 python-docx 三线表，不必经 .rtf 中转。

### H.0 依赖与接口自检（必须第一步执行）

```bash
pip install pyfixest linearmodels statsmodels pandas numpy scipy scikit-learn openpyxl
pip install pypdf pdfplumber python-docx      # 文献精读与排版
```

```python
# scripts/_env_check.py —— 首次会话必跑，把结果回填到 log/env.txt
import sys, subprocess, importlib

REQUIRED = ["pandas", "numpy", "scipy", "statsmodels",
            "pyfixest", "linearmodels", "sklearn", "docx"]
OPTIONAL = ["pypdf", "pdfplumber", "pyalex", "wildboottest"]

print(sys.version)
for m in REQUIRED + OPTIONAL:
    try:
        mod = importlib.import_module(m)
        print(f"[OK] {m:16s} {getattr(mod, '__version__', 'n/a')}")
    except Exception as e:
        tag = "MISSING" if m in REQUIRED else "OPTIONAL-MISSING"
        print(f"[{tag}] {m:16s} {e}")
```

> ⚠️ **接口随版本漂移**。本附录的代码按 pyfixest ≥ 0.20 书写。若报 `AttributeError`，先执行
> `python -c "import pyfixest as pf; print([x for x in dir(pf) if not x.startswith('_')])"`，
> 以实际暴露的接口为准并回填本附录（与附录 C.3 对 Stata MCP 的处理方式一致）。
> 三条高频差异：`etable` 的参数名、`feols` 的 `vcov` 写法、IV 公式的管段顺序。

### H.1 公共骨架：每个阶段脚本都以此开头

> **占位变量约定**：下文代码中的 `Y` / `X` / `controls` / `fe` / `cluster` / `cont_vars` / `Z` 等
> 都指代 `.thesis_state.json` 里的**实际列名**，落地时统一从 `_common.m()` 取，不应直接沿用字面量。

```python
# scripts/_common.py —— 所有分析脚本 import 它，避免五份重复
from pathlib import Path
import json, datetime
import pandas as pd
import numpy as np
import pyfixest as pf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "cleaned" / "dataset.dta"
LOG = ROOT / "log"
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
for d in (LOG, TAB, FIG):
    d.mkdir(parents=True, exist_ok=True)

STATE = json.loads((ROOT / ".thesis_state.json").read_text(encoding="utf-8"))

# ── 随机种子：所有含随机过程的脚本必设（附录 D.5 第 8 条）──
SEED = 20240601

def load_data():
    return pd.read_stata(DATA)

def spec_log(phase: str, spec: str, coef, se, p, adopted: bool, reason: str):
    """每跑一个规格就登记一行；论文定稿时全量披露（附录 D.5 / Phase 4.5）"""
    row = pd.DataFrame([{
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "phase": phase, "spec": spec,
        "coef": coef, "se": se, "p": p,
        "adopted": int(adopted), "reason": reason,
    }])
    f = LOG / "spec-search.csv"
    row.to_csv(f, mode="a", header=not f.exists(), index=False, encoding="utf-8-sig")

def m(name: str):
    """把 state 里的变量名映射成 pyfixest 公式片段"""
    v = STATE["variables"]
    return {
        "Y": v["Y"], "X": v["X"],
        "controls": " + ".join(v.get("controls", [])) or "1",
        "fe": " + ".join(STATE["model_framework"].get("fe", ["id", "year"])),
        "cluster": STATE["model_framework"].get("cluster", "id"),
    }
```

### H.2 Phase 4：基准回归

```python
# scripts/02_baseline.py
import pyfixest as pf
from _common import load_data, spec_log, m, ROOT

df = load_data()
v = m("baseline")

# 四个模型：(1) 仅 X  (2) +控制  (3) +双向FE  (4) +行业×年份FE
models = {
    "m1": pf.feols(f"{v['Y']} ~ {v['X']}", data=df, vcov="HC1"),
    "m2": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']}", data=df, vcov="HC1"),
    "m3": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']}",
                   data=df, vcov={"CRV1": v["cluster"]}),
    "m4": pf.feols(f"{v['Y']} ~ {v['X']} + {v['controls']} | {v['fe']} + industry^year",
                   data=df, vcov={"CRV1": v["cluster"]}),
}

for k, fit in models.items():
    fit.summary()                     # 日志里留完整输出

tidy = models["m4"].tidy()            # DataFrame: Estimate / Std. Error / Pr(>|t|)
print(tidy)

# 表格 → DataFrame（再交给 H.7 写 docx 三线表）
base_tab = pf.etable(list(models.values()), type="df")
base_tab.to_csv(ROOT / "output/tables/baseline.csv", encoding="utf-8-sig")

row = tidy.loc[v["X"]]
spec_log("P4", "baseline m4 (TWFE)",
         float(row["Estimate"]), float(row["Std. Error"]), float(row["Pr(>|t|)"]),
         adopted=True, reason="预设定基准规格，未做规格搜索")
```

**结果解读必须计算的三个量**（写进 Step 4.4 模板）：

```python
b = float(tidy.loc[v["X"], "Estimate"])
sd_x, sd_y = df[v["X"]].std(), df[v["Y"]].std()
print("标准化效应 =", b * sd_x / sd_y)                 # 经济显著性
print("相对均值 =", b * sd_x / df[v["Y"]].mean() * 100, "%")
```

### H.3 Phase 5：内生性处理

#### H.3.1 工具变量（2SLS）

pyfixest 的三段式公式：`Y ~ 外生控制 | 固定效应 | 内生变量 ~ 工具变量`

```python
# scripts/03_endogeneity_iv.py
import pyfixest as pf
from _common import load_data
df = load_data()

iv = pf.feols(
    f"{Y} ~ {controls} | {fe} | {X} ~ {' + '.join(Z)}",
    data=df, vcov={"CRV1": cluster},
)
iv.summary()

# 第一阶段与弱工具判断：单独回归 X 对 Z
fs = pf.feols(f"{X} ~ {controls} + {' + '.join(Z)} | {fe}", data=df, vcov={"CRV1": cluster})
fs.tidy()          # 看 Z 的 t 值；F 统计量见 summary
```

> 经验阈值：第一阶段 F > 10（单工具）。多工具需报告过度识别检验。
> pyfixest 不直接给 Kleibergen-Paap，需在附录注明"以第一阶段 F + 稳健性论证替代"，或改用 `linearmodels.iv.IV2SLS` 取 `sargan`。

#### H.3.2 PSM（自实现，不依赖第三方匹配库）

```python
# scripts/03_endogeneity_psm.py
import numpy as np, pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LogisticRegression
import pyfixest as pf
from _common import load_data, SEED

np.random.seed(SEED)
df = load_data()

# 1) 倾向得分
Xc = df[controls].assign(**{X: df[X]})
ps_model = LogisticRegression(max_iter=2000).fit(Xc, df["treat"])
df["_ps"] = ps_model.predict_proba(Xc)[:, 1]

# 2) 1:1 最近邻（卡尺 0.05），无放回
t = df[df.treat == 1].copy()
c = df[df.treat == 0].copy()
nn = NearestNeighbors(n_neighbors=1).fit(c[["_ps"]])
dist, idx = nn.kneighbors(t[["_ps"]])
ok = dist.ravel() <= 0.05
matched = pd.concat([t[ok], c.iloc[idx.ravel()[ok]].assign(treat=0)])
print("匹配后样本量:", len(matched), " 处理组保留:", ok.sum(), "/", len(t))

# 3) 匹配后回归（与基准同规格）
fit = pf.feols(f"{Y} ~ {X} + {controls} | {fe}", data=matched, vcov={"CRV1": cluster})
fit.summary()
```

**平衡性检验**（必须报告）：逐协变量比较匹配前后处理/控制组均值差异，输出 `output/tables/psm_balance.csv`。

#### H.3.3 Oster (2019) 系数稳定性检验（Python 无现成包，自实现）

公式（δ=1）：

```
β* = β̃ − δ · (β° − β̃) · (R_max − R̃) / (R̃ − R°)
```

其中 β° 为**不含控制变量**的系数与 R²，β̃ 为**含全部控制变量**的系数与 R²。

```python
# scripts/03_endogeneity_oster.py
import numpy as np
import pyfixest as pf
from _common import load_data

df = load_data()

def r2_of(fit):
    for attr in ("_r2", "_r2_within", "r2"):
        v = getattr(fit, attr, None)
        if v is not None:
            return float(v)
    raise RuntimeError("取不到 R²，请按 fit 的实际属性调整 r2_of()")

def oster(uncontrolled, controlled, xvar, delta=1.0, rmax=None):
    b0, r0 = float(uncontrolled.coef()[xvar]), r2_of(uncontrolled)
    b1, r1 = float(controlled.coef()[xvar]), r2_of(controlled)
    rmax = min(1.3 * r1, 1.0) if rmax is None else rmax
    bias = delta * (b0 - b1) * (rmax - r1) / (r1 - r0) if r1 > r0 else np.nan
    bstar = b1 - bias
    # 识别区间：δ=1 与 δ=∞（即 β 全部被解释）两个端点的包络
    return {"beta_tilde": b1, "beta_star": bstar,
            "r2_uncontrolled": r0, "r2_controlled": r1, "rmax": rmax,
            "interval": tuple(sorted([b1, bstar])),
            "contains_zero": min(b1, bstar) <= 0 <= max(b1, bstar)}

unc = pf.feols(f"{Y} ~ {X} | {fe}", data=df, vcov={"CRV1": cluster})
ctr = pf.feols(f"{Y} ~ {X} + {controls} | {fe}", data=df, vcov={"CRV1": cluster})
res = oster(unc, ctr, X)
print(res)
```

> 判断：`contains_zero = True` → 结果对遗漏变量敏感，必须在正文承认；`False` → 稳健。
> 该实现与 Stata `psacalc beta X, delta(1) rmax(...)` 等价，但**不替代** psacalc2 对 reghdfe 的内部处理，差异点见 H.9。

#### H.3.4 交叠 DID 与事件研究

> ⚠️ **接口已于 2026-10 冒烟测试中实测修订。** pyfixest 0.60 已移除公式内的 `sunab()`，
> DID 相关功能迁至 `pyfixest.did` 子模块；早期版本（≤0.4x）的 `sunab(cohort, period)` 写法不再可用。
> 本节按 0.60 的实测行为书写，并给出在该版本下可稳定运行的最小路径。

**第一步：构造相对时间。** 从未处理组**不应**设为 `NaN`——pyfixest 的 Rust 去均值器会在含缺失的
因子变量上触发 panic（`called Option::unwrap() on a None value`）。改用哨兵值，其虚拟变量会因与
个体固定效应共线而被自动剔除。

```python
# scripts/03_endogeneity_did.py —— 事件研究（TWFE 规格）
import numpy as np
import pyfixest as pf
from _common import load_data, spec_log

df = load_data()
COHORT = "first_treat"
df["rel_time"] = np.where(df[COHORT] > 0, df["year"] - df[COHORT], -999)

ctrl = " + ".join([c for c in controls if c != "age"])   # 与 FE 共线的控制变量须剔除
es = pf.feols(f"{Y} ~ i(rel_time, ref=-1) + {ctrl} | {fe}",
              data=df, vcov={"CRV1": cluster})
es.tidy().to_csv("output/tables/event_study.csv", encoding="utf-8-sig")
```

**第二步：平行趋势的联合检验。** `wald_test` 只接受矩阵形式的约束（传字典会报
`'dict' object has no attribute 'ndim'`）。

```python
names = list(es.tidy().index)
pre = [t for t in names if t.startswith("rel_time::-")]

R = np.zeros((len(pre), len(names)))
for i, term in enumerate(pre):
    R[i, names.index(term)] = 1.0

out = es.wald_test(R, np.zeros(len(pre)))
print(f"平行趋势联合检验：统计量 {out['statistic']:.3f}，p = {out['pvalue']:.4f}")
```

**第三步：异质性稳健估计量。** 0.60 的 DID 子模块提供 `SaturatedEventStudy`、`did2s`、
`lpdid`、`event_study`，但在非平衡面板上的实测表现如下（同一份 6,191 观测、500 企业的数据）：

| 接口 | 实测结果 |
|---|---|
| `pf.did.SaturatedEventStudy(...).estimate()` | 可估计，输出"队列×相对期"系数；`aggregate()` 报 `AttributeError: 'NoneType' object has no attribute 'keys'`，无法取得总体 ATT |
| `pf.did.did2s(...)` | 报 `ValueError: operands could not be broadcast together`（单例固定效应剔除后样本长度不一致） |
| `pf.did.lpdid(...)` | 触发 Rust 去均值器 panic，进程中断 |
| `pf.did.event_study(..., estimator="twfe")` | 可运行，但只返回平均处理效应 `is_treated`，不返回逐期系数 |

结论：**在后端 B 下，本工作流以 TWFE 事件研究作为主路径**，把异质性稳健估计量列为"已知缺口"，
在正文的方法说明与研究不足中如实披露。需要正式报告 Sun–Abraham 或 Callaway–Sant'Anna 估计量时，
按下一步处理。

**遇到上述缺口时的处理（不得静默替换）**

```
1. 明确告知用户：当前 Python 后端无法产出该估计量；
2. 给出两个选项：①该张表切后端 A（csdid / eventstudyinteract，附录 I.4.4）；
                ②保留 TWFE 事件研究，但在正文写入该局限；
3. 无论选哪个，都要把尝试过程与失败原因写入 log/spec-search.csv，
   并在 .thesis_state.json 记录 method_switch 及用户确认方式。
```

> 🛟 该节是本附录中最易随版本变化的部分。每次会话首次使用前，先执行
> `python -c "import pyfixest as pf; print([x for x in dir(pf.did) if not x.startswith('_')])"`，
> 以实际暴露的接口为准并回填本表（与附录 C.3 对 Stata MCP 的处理方式一致）。


#### H.3.5 模型框架锁定

```python
# scripts/03_lock_framework.py
import json
from _common import ROOT, STATE

STATE["model_framework"] = {
    "method": "TWFE",                 # 或 2SLS / PSM / DID / sunab
    "fe": ["id", "year"],
    "cluster": "id",
    "controls": STATE["variables"]["controls"],
    "backend": "python",
}
(ROOT / ".thesis_state.json").write_text(
    json.dumps(STATE, ensure_ascii=False, indent=2), encoding="utf-8")
```

### H.4 Phase 6：稳健性检验

```python
# scripts/04_robustness.py
import numpy as np, pandas as pd
import pyfixest as pf
from _common import load_data, spec_log, SEED, ROOT

np.random.seed(SEED)
df = load_data()

def fit(d, y=Y, x=X):
    return pf.feols(f"{y} ~ {x} + {controls} | {fe}", data=d, vcov={"CRV1": cluster})

# 1) 缩尾（1%/99%）—— 自实现替代 winsor2
def winsorize(s, lo=0.01, hi=0.99):
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)

df_w = df.copy()
for c in cont_vars:
    df_w[c] = winsorize(df_w[c])

# 2) 替代度量 / 换样本 / 换 FE：各跑一次，结果并排
rob = {
    "基准":       fit(df),
    "缩尾":       fit(df_w),
    "替换Y":      fit(df, y="Y_alt"),
    "剔除直辖市":  fit(df[~df.city.isin(municipalities)]),
    "行业×年份FE": pf.feols(f"{Y} ~ {X} + {controls} | {fe} + industry^year",
                          data=df, vcov={"CRV1": cluster}),
}

# 3) 安慰剂：随机打乱处理状态 500 次，统计系数分布
placebo = []
for i in range(500):
    d = df.copy()
    d["treat_fake"] = np.random.permutation(d["treat"].values)
    f = pf.feols(f"{Y} ~ treat_fake + {controls} | {fe}", data=d, vcov={"CRV1": cluster})
    placebo.append(float(f.coef()["treat_fake"]))
placebo = np.array(placebo)
print("安慰剂均值/标准差:", placebo.mean(), placebo.std())
print("置换 p 值:", (np.abs(placebo) >= abs(real_beta)).mean())

pd.DataFrame({"placebo_beta": placebo}).to_csv(
    ROOT / "output/tables/placebo_dist.csv", index=False, encoding="utf-8-sig")
```

> 安慰剂图：直方图 + 竖线标注真实系数，存 `output/figures/placebo.png`。
> **所有跑过的规格逐行 `spec_log(...)`，含不显著的**（附录 D.5 第 4 条）。

### H.5 Phase 7：机制检验

```python
# scripts/05_mechanism.py
import numpy as np, pandas as pd
from scipy import stats
import pyfixest as pf
from _common import load_data, SEED

np.random.seed(SEED)
df = load_data()

# ── 方法一：江艇 (2022) 两步法（推荐）──
# 第一步：X → M（因果检验只做到这里）
for med in mechanism_vars:
    f = pf.feols(f"{med} ~ {X} + {controls} | {fe}", data=df, vcov={"CRV1": cluster})
    f.summary()
# 第二步：M → Y 由文献与理论论证，不在本文回归里同时放 X 和 M

# ── 方法二：Sobel 检验（需同时估 a、b 两条路径）──
a_fit = pf.feols(f"{M} ~ {X} + {controls} | {fe}", data=df, vcov={"CRV1": cluster})
b_fit = pf.feols(f"{Y} ~ {X} + {M} + {controls} | {fe}", data=df, vcov={"CRV1": cluster})
a, sa = float(a_fit.coef()[X]), float(a_fit.se()[X])
b, sb = float(b_fit.coef()[M]), float(b_fit.se()[M])
sobel_z = a * b / np.sqrt(b**2 * sa**2 + a**2 * sb**2)
print("Sobel z =", sobel_z, " p =", 2 * (1 - stats.norm.cdf(abs(sobel_z))))

# ── 方法三：Bootstrap 间接效应（替代 Sobel 的分布假设）──
boot = []
for _ in range(1000):
    d = df.sample(len(df), replace=True)
    af = pf.feols(f"{M} ~ {X} + {controls} | {fe}", data=d, vcov={"CRV1": cluster})
    bf = pf.feols(f"{Y} ~ {X} + {M} + {controls} | {fe}", data=d, vcov={"CRV1": cluster})
    boot.append(float(af.coef()[X]) * float(bf.coef()[M]))
lo, hi = np.percentile(boot, [2.5, 97.5])
print("间接效应 95% CI:", (lo, hi), " 是否含 0:", lo <= 0 <= hi)

# ── 调节效应 ──
mod = pf.feols(f"{Y} ~ {X}*{Z} + {controls} | {fe}", data=df, vcov={"CRV1": cluster})
mod.summary()
```

> pyfixest 公式里 `A*B` 展开为主效应 + 交互项；`A:B` 只要交互项。分组为类别变量时写 `i.group`。

### H.6 Phase 8：异质性分析

```python
# scripts/06_heterogeneity.py
import pandas as pd
import pyfixest as pf
from statsmodels.stats.multitest import multipletests
from _common import load_data, ROOT

df = load_data()
rows = []

for g in ["soe", "heavy_pollution", "high_ipr"]:
    # 全交互扩展模型：直接检验组间差异（不应通过分组回归后目测系数大小来判断）
    f = pf.feols(f"{Y} ~ {X}*i.{g} + {controls} | {fe}",
                 data=df, vcov={"CRV1": cluster})
    f.summary()
    # 取出交互项（组间差异的正式检验）
    for k, v in f.tidy().iterrows():
        if f":{g}" in k or f"{g}:" in k or ":" in k:
            rows.append({"group": g, "term": k,
                         "coef": v.get("Estimate"), "p": v.get("Pr(>|t|)")})

res = pd.DataFrame(rows)
# 多重假设检验校正（维度 > 3 或交互项 > 3 时必做）
rej, p_adj, _, _ = multipletests(res["p"].fillna(1), alpha=0.05, method="fdr_bh")
res["p_fdr"] = p_adj
res.to_csv(ROOT / "output/tables/heterogeneity.csv", index=False, encoding="utf-8-sig")
```

> **不应使用分组回归后比较显著性的方式宣称组间差异**——这属于"显著性差异的谬误"。唯一规范做法是全交互 + 交互项检验。
> Python 侧没有 suest 的对应物，也不需要（原 Stata 版的 suest 已因与 reghdfe 不兼容而废弃）。

### H.7 回归表 → docx 三线表

```python
# scripts/_docx_table.py
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def _border(cell, edge, sz):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders"); tcPr.append(borders)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(sz))
    borders.append(el)

def three_line_table(doc, df, caption, note="", font_size=10.5):
    """df: 第一列为变量名，其余为各模型列；写标准三线表（顶线1.5pt/栏目线0.75pt/底线1.5pt）"""
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.font.name = "黑体"; r.font.size = Pt(font_size)
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    t = doc.add_table(rows=df.shape[0] + 1, cols=df.shape[1])
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, col in enumerate(df.columns):
        t.cell(0, j).text = str(col)
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, v in enumerate(row):
            t.cell(i, j).text = "" if v is None else str(v)

    for j in range(df.shape[1]):
        _border(t.cell(0, j), "top", 12)       # 顶线 1.5pt
        _border(t.cell(0, j), "bottom", 6)     # 栏目线 0.75pt
        _border(t.cell(df.shape[0], j), "bottom", 12)  # 底线 1.5pt

    if note:
        p = doc.add_paragraph()
        r = p.add_run(note)
        r.font.name = "宋体"; r.font.size = Pt(9)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
```

用法（Phase 9 直接调用）：

```python
import json, pandas as pd
from docx import Document
from _docx_table import three_line_table

tab = pd.read_csv("output/tables/baseline.csv", index_col=0)
doc = Document("thesis/模板.docx")
three_line_table(doc, tab, "表 5-2 基准回归结果",
                 "注：括号内为标准误；*** p<0.01, ** p<0.05, * p<0.1；标准误聚类到个体。")
doc.save("thesis/论文题目_终稿.docx")
```

### H.8 一键复现

```python
# scripts/run_all.py —— 对应附录 F 的 master.do
import subprocess, sys, pathlib
for s in ["00_setup.py", "01_describe.py", "02_baseline.py",
          "03_endogeneity_iv.py", "04_robustness.py",
          "05_mechanism.py", "06_heterogeneity.py"]:
    p = pathlib.Path(__file__).parent / s
    if not p.exists():
        print(f"[SKIP] {s}"); continue
    print(f"[RUN ] {s}")
    rc = subprocess.run([sys.executable, str(p)]).returncode
    if rc != 0:
        print(f"[FAIL] {s} 退出码 {rc}"); sys.exit(rc)
print("=== 全部脚本运行完成 ===")
```

### H.9 与 Stata 后端的能力差异（必须对用户透明）

| 能力 | Python | Stata | 建议 |
|---|---|---|---|
| 高维 FE + 聚类 | ✅ pyfixest，速度通常更快 | ✅ reghdfe | 等价 |
| 回归表输出 | ✅ DataFrame → docx 三线表 | ✅ esttab → rtf | Python 少一次格式转换 |
| 2SLS | ✅ pyfixest / linearmodels | ✅ ivreg2 | Python 缺 Kleibergen-Paap，需替代论证 |
| PSM | ✅ 自实现最近邻 | ✅ psmatch2 | 结果可能微差，需报告匹配算法与卡尺 |
| Oster 检验 | ⚠️ 本附录自实现 | ✅ psacalc2 | 公式等价；点估计可能因 R² 口径差异微调 |
| Sun–Abraham | ⚠️ `SaturatedEventStudy` 可估计但 `aggregate()` 在 0.60 报错 | ✅ eventstudyinteract | 需报告 ATT 时切后端 A |
| Callaway–Sant'Anna | ❌ 无官方实现（`did2s`/`lpdid` 在非平衡面板上报错或崩溃） | ✅ csdid | 切后端 A |
| Goodman-Bacon 分解 | ❌ | ✅ bacondecomp | 切后端 A |
| 面板 GMM | ✅ linearmodels | ✅ xtabond2 | 等价 |
| 断点回归 | ⚠️ 需自写 | ✅ rdrobust | 建议切后端 A |

**结论**：硕士论文的常规配置（TWFE / 事件研究 / IV / PSM / 机制 / 异质性）Python 全覆盖；
异质性稳健的交叠 DID 估计量（Sun–Abraham 的 ATT、Callaway–Sant'Anna）与 Bacon 分解、
断点回归需走后端 A。该结论由 2026-10 的端到端冒烟测试实测得出，详见 `tests/smoke/REPORT.md`。

### H.10 验收清单（每个 Phase 结束时逐条打勾）

```
□ scripts/ 下对应脚本存在，且可由 run_all.py 一次完整运行
□ log/env.txt 记录 Python 与关键包版本
□ 每个含随机过程的脚本固定 SEED，且种子写入 log
□ 所有跑过的规格都在 log/spec-search.csv 有记录（含未采纳的）
□ output/tables/*.csv 已生成，且列名与正文表格一致
□ 结果解读中的每个数字都能在 csv 或日志里找到出处
□ 若用到 H.9 中标 ⚠️/❌ 的方法，已在正文说明替代方案或其局限
```
