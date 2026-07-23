## 附录 F：Stata do file 归档规范

> 本附录定义了 do file 的编写规范，以确保回归结果可复现、审稿人可检查。

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
cd "{project_root}"
cap log close

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

### F.5 复现检查清单

```
□ 所有 do file 可通过 master.do 一次性运行
□ 所有文件路径使用相对路径
□ 所有变量有中文标签
□ 所有回归结果输出到 output/tables/
□ 每个 do file 生成独立的 log 文件
□ 数据文件放在 cleaned/ 目录（只读）
□ 原始数据文件放在 data/raw/ 目录（只读，不修改）
□ 项目路径可配置（全局变量 project_root）
□ 记录 Stata 版本和使用的包版本
```
