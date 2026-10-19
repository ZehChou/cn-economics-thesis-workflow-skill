## 附录 I：计量执行后端 A — Stata（可选）

> **适用**：`.thesis_state.json` 中 `analysis_backend = "stata"`（Phase 0 Step 0.3 由用户显式选择）。
>
> **定位**：本附录是后端 A 的**代码唯一真源**。MCP 安装/工具名/安全机制见附录 C；归档规范见附录 F。
> 默认后端是 Python（附录 H）——只有当用户明确要求 Stata，或需要 Python 生态缺失的估计量（Goodman-Bacon 分解、rdrobust）时才走这里。

### I.0 何时应该选后端 A

| 场景 | 是否选 A |
|---|---|
| 导师/学院要求提交 do-file 与复现包 | ✅ 选 |
| 需要 Goodman-Bacon 分解、rdrobust、xtabond2 面板 GMM | ✅ 选 |
| 需要 Callaway–Sant'Anna 的 `csdid` 官方实现 | ✅ 选 |
| 用户已熟悉 Stata、想自己改代码 | ✅ 选 |
| 只做 TWFE / DID / IV / PSM / 机制 / 异质性 | ❌ 使用默认 Python 更为简便（无需许可证与 MCP） |

### I.1 前置：包清单

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install winsor2, replace
ssc install ivreg2, replace
ssc install ranktest, replace
ssc install psmatch2, replace
ssc install sgmediation, replace
ssc install boottest, replace
ssc install csdid, replace
ssc install bacondecomp, replace
ssc install eventstudyinteract, replace
ssc install psacalc, replace
```

> `reghdfe` 后做 Oster 检验需社区版 **psacalc2**（官方 psacalc 只认 `reg` 类 `e()`）：
> GitHub `ArthurHowardMorris/psacalc_supports_reghdfe`。

### I.2 公共骨架：每个 do file 的头部

```stata
* ── 文件头 ──
* do/{文件名}.do
* 用途：{具体功能}
* 创建：{YYYY-MM-DD}
* 依赖：cleaned/dataset.dta
version 16
clear all
set more off
cd "$project_root"            // 由 master.do 定义；单独运行请先 global project_root "..."
global controls "size lev roa growth age cash board"   // ← 从 .thesis_state.json 回填
global fe "i.id i.year"
global cluster "id"
set seed 20240601             // 含随机过程的文件必设
cap log close
log using "log/{文件名}.log", replace text
```

> ⚠️ `$controls` 未定义时会**静默展开为空**，回归不报错但结果全错。每个 do file 头部必须显式定义。

### I.3 Phase 4：基准回归

```stata
* do/02-baseline.do
use "cleaned/dataset.dta", clear

eststo clear
eststo m1: reg Y X, robust
eststo m2: reg Y X $controls, robust
eststo m3: reghdfe Y X $controls, absorb($fe) vce(cluster $cluster)
eststo m4: reghdfe Y X $controls, absorb(i.id i.year i.industry#i.year) vce(cluster $cluster)

esttab m1 m2 m3 m4 using "output/tables/baseline.rtf", replace ///
    b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) ///
    stats(N r2 r2_a F, fmt(0 3 3 2)) ///
    title("基准回归结果") mtitles("(1)" "(2)" "(3)" "(4)") ///
    addnotes("注：括号内为标准误；*** p<0.01, ** p<0.05, * p<0.1；m3-m4 标准误聚类到个体。")

log close
```

### I.4 Phase 5：内生性处理

#### I.4.1 工具变量（2SLS + 检验）

```stata
* do/03-endogeneity-iv.do
ivreg2 Y $controls (X = Z1 Z2), cluster($cluster) first
* 弱工具：第一阶段 F（first 选项输出）
* 过度识别：Hansen J（工具数 > 内生变量数时）
* 内生性：Durbin-Wu-Hausman
eststo iv

esttab iv using "output/tables/endogeneity_iv.rtf", replace ///
    b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) ///
    addnotes("注：工具变量为 {Z}；第一阶段 F = {F}；Hansen J p = {p}。")
```

#### I.4.2 PSM

```stata
* do/03-endogeneity-psm.do
set seed 20240601
psmatch2 treat $controls, out(Y) logit neighbor(1) caliper(0.05) common ties
pstest $controls, both graph          // 平衡性检验，图存 output/figures/
psgraph

* 匹配后回归（仅保留 on_support 样本）
reghdfe Y X $controls if _weight != ., absorb($fe) vce(cluster $cluster)
```

#### I.4.3 Oster 检验（两步法）

```stata
* do/03-endogeneity-oster.do
* 第一步：完整模型（含控制变量与固定效应）
reghdfe Y X $controls, absorb($fe) vce(cluster $cluster)

* 第二步：读取上一回归结果。控制变量已在模型中，勿再以位置参数传入；无 treat() 选项。
* 若第一步是 reghdfe，必须用 psacalc2；官方 psacalc 会报 e() 类型不符。
psacalc2 beta X, delta(1) rmax(1)
* Rmax ≤ 1；常见取 Rmax = min(1.3 × 全模型 R², 1)

* 对照：不含控制变量的短回归
reghdfe Y X, absorb($fe) vce(cluster $cluster)
```

#### I.4.4 交叠 DID（Callaway–Sant'Anna）

```stata
* do/03-endogeneity-did.do
* gvar 编码：未处理单元 first_treat = 0
csdid Y X $controls, ivar(id) time(year) gvar(first_treat)   // 默认对照 = not-yet-treated
estat event                      // 动态效应汇总（含置信带），必做
csdid_plot, graphregion(color(white))
graph export "output/figures/csdid_event.png", replace

* 敏感性与分解
bacondecomp Y X $controls, ddetail
eventstudyinteract Y, cohort(first_treat) control_cohort(never_treat) ///
    absorb(i.id i.year) vce(cluster id)   // Sun & Abraham 对照
```

### I.5 Phase 6：稳健性检验

```stata
* do/04-robustness.do
set seed 20240601

* 基准
reghdfe Y X $controls, absorb($fe) vce(cluster $cluster)
eststo base

* 1) 缩尾
winsor2 Y X $controls, cuts(1 99) replace
reghdfe Y X $controls, absorb($fe) vce(cluster $cluster)
eststo win

* 2) 替换度量 / 换样本 / 换 FE 规格：逐个 eststo

* 3) 安慰剂：随机置换处理状态 500 次，系数分布写入文件
tempname pf
postfile `pf' b_placebo using "output/tables/placebo_dist.dta", replace
forvalues i = 1/500 {
    quietly {
        preserve
        gen double treat_fake = treat if 0
        * 在个体层面整体置换处理状态，保证组内一致性
        bysort id (year): gen byte _first = (_n == 1)
        gen double _u = runiform() if _first
        bysort id (year): replace _u = _u[1]
        by id: egen double _rank = rank(_u) if _first
        bysort id (year): replace _rank = _rank[1]
        * 按原处理组规模随机指定新的处理组
        count if treat == 1
        local n1 = r(N)
        gen byte treat_perm = (_rank <= `n1')
        reghdfe Y treat_perm $controls, absorb($fe) vce(cluster $cluster)
        post `pf' (_b[treat_perm])
        restore
    }
}
postclose `pf'
use "output/tables/placebo_dist.dta", clear
summarize b_placebo, detail
histogram b_placebo, ///
    xline(`real_beta', lcolor(red) lpattern(dash)) ///
    title("安慰剂检验：500 次随机置换的处理效应") ///
    graphregion(color(white))
graph export "output/figures/placebo.png", replace

esttab base win using "output/tables/robustness.rtf", replace ///
    b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) ///
    addnotes("注：所有规格均沿用 Phase 5 模型框架（同 FE、同聚类层）。")
```

> 安慰剂循环建议单独写进 `do/04b-placebo.do`，用 `postfile` 收集 500 个系数后 `histogram` 出图，
> 并在 do-file 头部固定 `set seed`（附录 D.5 第 8 条）。

### I.6 Phase 7：机制检验

```stata
* do/05-mechanism.do

* ── 方法一：江艇 (2022) 两步法（推荐）──
* 第一步：X → M
foreach m in M1 M2 {
    reghdfe `m' X $controls, absorb($fe) vce(cluster $cluster)
    eststo med_`m'
}
* 第二步：M → Y 由文献论证，不把 X 与 M 同时放进 Y 方程

* ── 方法二：Sobel / Bootstrap ──
sgmediation Y, mv(M1) iv(X) cv($controls)    // Sobel 检验
bootstrap r(indirect) r(direct), reps(1000) seed(20240601): ///
    sgmediation Y, mv(M1) iv(X) cv($controls)

* ── 方法三：调节效应 ──
reghdfe Y c.X##c.Z $controls, absorb($fe) vce(cluster $cluster)
eststo mod

esttab med_M1 mod using "output/tables/mechanism.rtf", replace ///
    b(3) se(3) star(* 0.1 ** 0.05 *** 0.01)
```

### I.7 Phase 8：异质性分析

```stata
* do/06-heterogeneity.do

* 字符串分组变量先编码
encode group_str, gen(group)

* ── 全交互扩展模型（唯一推荐的组间差异检验）──
reghdfe Y c.X##i.group $controls, absorb($fe) vce(cluster $cluster)
test 1.group#c.X                  // 组间差异的正式检验
eststo inter

* ── 分组估计（仅用于展示组内系数，不能据此宣称组间差异）──
foreach g in 0 1 {
    preserve
    keep if group == `g'
    reghdfe Y X $controls, absorb($fe) vce(cluster $cluster)
    eststo grp`g'
    restore
}

* ⚠️ 不应用 suest：suest 只接受 regress 类估计结果，与 reghdfe 的 absorb 不兼容。
* 高维固定效应下的组间差异一律用上面的全交互 + test。
```

### I.8 后端 A 的独有能力

| 能力 | 命令 | 后端 B 状态 |
|---|---|---|
| Goodman-Bacon 分解 | `bacondecomp` | ❌ 无 Python 实现 |
| 断点回归 | `rdrobust`（`ssc install rdrobust`） | ⚠️ 需自写 |
| 面板 GMM | `xtabond2` | ✅ linearmodels 可替代 |
| wild cluster bootstrap | `boottest` | ⚠️ 依赖 `wildboottest` 包 |
| 交叠 DID 官方实现 | `csdid` | ⚠️ 无官方 Python 包 |

### I.9 验收清单

```
□ 所有 do file 可由 master.do 一次完整运行
□ 每个 do file 头部有 version / 显式 $controls / set seed（含随机过程时）
□ 包版本已记录（which reghdfe / which csdid 等）
□ 所有规格写入 log/spec-search.csv（含未采纳的）
□ output/tables/*.rtf 已生成，列数与正文表格一致
□ 若用了 psacalc2，已在复现说明中注明来源与安装方式
□ 未使用 suest 做 reghdfe 的组间差异检验
```
