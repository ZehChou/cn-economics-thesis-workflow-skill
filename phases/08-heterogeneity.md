## Phase 8：异质性分析

> 本阶段遵循主 Skill 中定义的**通用交互模式：计量分析流程**，且基于 Phase 5 模型框架。

### Step 8.1：可用分组变量扫描

AI 自动扫描数据结构中可用的分类/分组变量：

```
数据结构中可用分组变量：
─────────────────────────────────
1. {变量名} — {描述} — {类别数} 个类别
   示例类别：{A, B, C}
   经济含义：{代表什么层面差异}

2. {变量名} — {描述} — {类别数} 个类别
   ...

3. {变量名（连续变量可二分）} — {描述}
   建议分组方式：{按中位数/均值/三分位分组}
   ...
─────────────────────────────────
```

### Step 8.2：维度推荐

AI 基于文献和逻辑推荐 3-5 个分组维度：

```
推荐异质性分析维度
═══════════════════════════════════════

维度 1：{分类依据}
  • 理论依据：{为什么在这个维度上可能存在异质性}
  • 预期：{A 组效应大于 B 组}

维度 2：{分类依据}
  • 理论依据：{为什么在这个维度上可能存在异质性}
  • 预期：{具体方向}

维度 3：{分类依据}
  • 理论依据：{为什么在这个维度上可能存在异质性}
  • 预期：{具体方向}

（可选）维度 4-5：{额外建议}
```

用户选择 2-3 个维度。

### Step 8.3：写 do file

```stata
* do/heterogeneity.do
* 异质性分析
* 基于 Phase 5 模型框架

use "cleaned/dataset.dta", clear

* ── 分组回归 ──
* 维度 1：{Group variable}

* 子组 A
preserve
keep if group == "A"
reghdfe Y X $controls, absorb(i.id i.year) vce(cluster id)
eststo groupA
restore

* 子组 B
preserve
keep if group == "B"
reghdfe Y X $controls, absorb(i.id i.year) vce(cluster id)
eststo groupB
restore

* ── 组间系数差异检验 ──
* 方法：引入交互项 + 似无相关模型 (SUR) 检验
```

### Step 8.4：结果解读

```
异质性分析结果
═══════════════════════════════════════

维度 1：{Group variable}
  • A 组：β = {value}，{p-value}，样本量 N = {n}
  • B 组：β = {value}，{p-value}，样本量 N = {n}
  • 组间差异检验：{Chi2/p-value}
  • 结论：{解读}

维度 2：{Group variable}
  • ...

整体解读：
  {X 的效应在哪些群体中更强/更弱的总结性结论}
  {政策含义：针对性的建议}
```

### 状态更新

Phase 8 完成后，更新 `.thesis_state.json`：
- `current_phase`: 8 → 9
- `heterogeneity_results`: 记录异质性分析结果
