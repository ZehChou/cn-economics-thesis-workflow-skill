## Phase 7：机制检验

> 本阶段遵循主 Skill 中定义的**通用交互模式：计量分析流程**，且基于 Phase 5 模型框架。

### Step 7.1：研究假设回顾

AI 回顾 Phase 2 推导的研究假设：

```
待检验的机制假设：
  H1: X → Y（已在 Phase 4-6 验证）
  H2a: X → M1 → Y（中介效应）
  H2b: X → M2 → Y（中介效应）
  H3: Z 调节 X → Y 的关系
```

### Step 7.2：方法推荐

```
推荐机制检验方案
═══════════════════════════════════════

1. 中介效应（H2a / H2b）
   方法 A：Baron & Kenny 三步法 + Sobel 检验
   方法 B：Bootstrap 中介检验（推荐，500/1000 次）
   方法 C：江艇（2022）两步法（适合面板数据）

2. 调节效应（H3）
   Y = α + β1*X + β2*Z + β3*X×Z + γ*Controls + ε
   关注 β3 的符号和显著性

建议：{根据数据结构和假设类型推荐最佳方法}
```

### Step 7.3：机制变量状态检查

```
机制变量状态检查：
  □ M1（{变量名}）— {已有/需补充}
  □ M2（{变量名}）— {已有/需补充}
  □ Z（{调节变量}）— {已有/需补充}

如需补充，推荐构造方案：
  • {变量名}：{构造方法和计算说明}
```

### Step 7.4：写 do file

```stata
* do/mechanism.do
* 机制检验
* 基于 Phase 5 模型框架

use "cleaned/dataset.dta", clear

* ── 主效应（Phase 5 验证通过）──
* ...

* ── 中介效应：X → M ──
* reg M X $controls i.id i.year, vce(cluster id)

* ── 中介效应：X + M → Y ──
* reg Y X M $controls i.id i.year, vce(cluster id)

* ── Sobel 检验（如适用）──
* sgmediation Y, mv(M) iv(X) cv($controls)

* ── 调节效应 ──
* reg Y c.X##c.Z $controls i.id i.year, vce(cluster id)

* ── 输出表格 ──
* esttab ... using "output/tables/mechanism.rtf", replace
```

### Step 7.5：结果解读

```
机制检验结果
═══════════════════════════════════════

中介效应检验：
  • X → M：系数 = {value}，{p-value} → {显著/不显著}
  • X + M → Y：X 系数下降至 {value}，{仍显著/不显著}
  • Sobel Z = {value}，p = {p-value}
  • 结论：{中介效应成立/不成立}

调节效应检验：
  • X×Z 交互项系数 = {value}，{p-value}
  • 结论：{Z 强化/弱化/不影响 X 对 Y 的关系}

机制解释：
  {从经济学角度解读为什么存在这样的机制}
```

### 状态更新

Phase 7 完成后，更新 `.thesis_state.json`：
- `current_phase`: 7 → 8
- `mechanism_results`: 记录机制检验结果
