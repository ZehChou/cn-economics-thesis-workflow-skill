## 附录 F：分析脚本归档规范（Stata / Python）

> 本附录定义分析脚本的编写规范，以确保回归结果可复现、审稿人可检查。
> **按 `analysis_backend` 走对应小节**：F.1–F.5 为 Stata（后端 A），F.6 为 Python（后端 B，默认）。

### F.1 do file 通用规范

每个 do file 应遵循以下结构：

```stata
* ── 文件头 ──
* do/{文件名}.do
* 用途：{具体功能描述}
* 作者：{作者名}
* 创建日期：{YYYY-MM-DD}
* 最后修改：{YYYY-MM-DD}
* 依赖：cleaned/dataset.dta, do/{前置文件}.do

* ── 环境设置 ──
clear all
set more off
cd "$project_root"        // 由 master.do 定义；单独运行需先 global project_root "..."
cap log close
version 16               // 与使用的 Stata 版本一致（复现用）
* 若本文件含随机过程（安慰剂/Bootstrap/PSM 抽样），固定随机种子：
* set seed 20240601

* ── 日志文件 ──
log using "log/{文件名}.log", replace text

* ── 数据加载 ──
use "cleaned/dataset.dta", clear

* ── 核心代码 ──
* （回归代码，标注每个模型的用途）

* ── 输出 ──
* （结果输出到 output/tables/ 或 output/figures/）

* ── 结束 ──
log close
display "=== {文件名} 运行完成 ==="
```

### F.2 文件命名规范

```
do/
├── 00-setup.do              # 数据加载和预处理
├── 01-describe.do           # 描述性统计
├── 02-baseline.do           # 基准回归
├── 03-endogeneity.do        # 内生性处理
├── 04-robustness.do         # 稳健性检验
├── 05-mechanism.do          # 机制检验
├── 06-heterogeneity.do      # 异质性分析
└── master.do                # 主控文件，按顺序调用所有 do file
```

> 各 Phase 文件中的示例名（如 `baseline.do`、`endogeneity.do`）与本编号体系含义相同：统一以本前缀为准（`02`=基准回归、`03`=内生性、`04`=稳健性、`05`=机制、`06`=异质性），避免一个项目两套文件名。

### F.3 主控文件（master.do）

```stata
* master.do
* 主控文件：按顺序执行所有 do file
* 运行方式：在 Stata 中 do master.do

clear all
set more off

* 设置项目路径（用户需修改此行）
global project_root "YOUR_PROJECT_PATH"
cd "$project_root"

* ── 按顺序执行 ──
do "do/00-setup.do"
do "do/01-describe.do"
do "do/02-baseline.do"
do "do/03-endogeneity.do"
do "do/04-robustness.do"
do "do/05-mechanism.do"
do "do/06-heterogeneity.do"

display "=== 全部 do file 运行完成 ==="
```

### F.4 变量标签规范

```stata
* 变量标签必须包含中文标签和单位
label variable Y "企业绩效（ROA，%）"
label variable X "数字化投入（取对数）"
label variable controls1 "企业规模（员工数取对数）"
label variable controls2 "企业年龄（年）"

* 分类变量需标注类别含义
label define edu 1 "小学及以下" 2 "中学" 3 "大学及以上"
label variable education "教育程度"
label values education edu
```

### F.5 复现检查清单（Stata / 后端 A）

```
□ 所有 do file 可通过 master.do 一次运行
□ 所有文件路径使用相对路径
□ 所有变量有中文标签
□ 所有回归结果输出到 output/tables/
□ 每个 do file 生成独立的 log 文件
□ 数据文件放在 cleaned/ 目录（只读）
□ 原始数据文件放在 data/raw/ 目录（只读，不修改）
□ 项目路径可配置（全局变量 project_root，由 master.do 定义）
□ 每个 do file 顶部含 version 语句；记录所用包版本（`which reghdfe` 等）
□ 随机化过程（安慰剂/Bootstrap/PSM）固定 set seed 并记录种子
□ 所有尝试过的规格（含未报告的）记入 log/spec-search.csv，供附录全量披露
□ 回归表格附注说明标准误类型与聚类层级（esttab addnotes）
```

### F.6 Python 脚本规范（后端 B · 默认）

**文件命名**：与 Stata 版一一对应，前缀语义相同，只是目录换成 `scripts/`。

```
scripts/
├── _common.py              # 公共骨架：路径、读数据、spec_log、变量映射（附录 H.1）
├── _docx_table.py          # 三线表写入（附录 H.7）
├── _env_check.py           # 环境与接口自检（附录 H.0）
├── 00_setup.py             # 数据加载与预处理
├── 01_describe.py          # 描述性统计
├── 02_baseline.py          # 基准回归
├── 03_endogeneity_iv.py    # 内生性（按方法拆文件：_iv / _psm / _oster / _did）
├── 04_robustness.py        # 稳健性检验
├── 05_mechanism.py         # 机制检验
├── 06_heterogeneity.py     # 异质性分析
└── run_all.py              # 主控，对应 master.do
```

**脚本头部模板**

```python
"""02_baseline.py —— 基准回归
依赖：cleaned/dataset.dta、.thesis_state.json
运行：python scripts/02_baseline.py      或  python scripts/run_all.py
"""
from _common import load_data, spec_log, m, ROOT   # 路径/日志/变量映射统一走 _common
```

**与 Stata 的对应关系**

| do-file 里的做法 | Python 脚本里的对应 |
|---|---|
| `global controls "..."` | `_common.m()` 从 `.thesis_state.json` 读，不手写 |
| `log using "log/x.log"` | `log/env.txt` + 脚本 stdout 重定向；`spec_log()` 逐行落 `spec-search.csv` |
| `version 16` | `log/env.txt` 记录 Python 与各包版本（`_env_check.py`） |
| `set seed` | `SEED = 20240601` 常量，`np.random.seed(SEED)` |
| `master.do` | `run_all.py`（`subprocess` 顺序执行，遇非零退出码即停） |
| `esttab ... using x.rtf` | `pf.etable(..., type="df")` → `three_line_table()` 直写 docx |

**检查清单（Python / 后端 B）**

```
□ run_all.py 可一次完整运行全部脚本
□ log/env.txt 已记录 Python 与关键包版本
□ _common.py 是唯一的数据读取与 spec_log 入口，脚本内不重复造轮子
□ 所有随机过程固定 SEED，且种子写入日志
□ 所有尝试过的规格（含未报告的）记入 log/spec-search.csv
□ output/tables/*.csv 列名与正文表格一致，表注含标准误类型与聚类层级
□ 没有为使脚本"运行成功"而静默 dropna()/改写数据；任何行数变动必须打印并在日志留痕
```

### F.7 两套归档如何共存

- `analysis_backend` 只选一个，主交付只维护对应目录（`scripts/` 或 `do/`），避免两份代码漂移；
- 若中途切换后端（例如某张表需要 Bacon 分解而切到 Stata），**只新增那一张表所需的文件**，
  并在 `README.md` 的项目说明里写清楚"哪些表来自哪个后端"，防止复现时对不上号；
- `log/spec-search.csv` 是**跨后端共用**的：无论用哪个后端跑，都追加同一个文件，`phase` 列区分。

