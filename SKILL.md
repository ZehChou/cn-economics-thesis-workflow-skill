---
name: economics-thesis
description: 经济学实证论文自动化工作流——从选题到排版成文的全流程交互式指导
---

# 经济学实证论文自动化工作流 (Economics Thesis Workflow)

## 概述

本 Skill 定义了一套**分步骤交互式**工作流，让 AI Agent 引导用户从零完成一篇完整的中文经济学实证学位论文。用户仅需提供研究想法和数据，AI 负责搜索文献、清洗数据、运行计量模型、撰写正文并排版成 `.docx`。

### 工作流总览

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4
环境准备      选题与         文献综述       数据与         基准回归
             文献定位        与理论框架     变量
                                               │
                         Phase 5 ◄─────────────┘
                         内生性处理
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
               Phase 6  Phase 7  Phase 8
               稳健性   机制检验  异质性
               检验               分析
                    │      │      │
                    └──────┼──────┘
                           ▼
                       Phase 9
                   论文撰写与排版成文
```

### 用户水平分档

首次使用本 Skill 时，AI 应询问用户水平，后续全程按该档位自适应：

| 档位 | 定位 | AI 行为 |
|------|------|---------|
| **L1（新手）** | 第一次做实证论文，需要 mini 教学 | 每个阶段解释核心概念（点到为止，用户反问再深入）；推荐执行路径偏保守（默认选项）；提示每一步的常见坑 |
| **L2（有基础）** | 有计量经济学基础，做过基本回归 | 跳过概念解释；直接输出方案和技术细节；用户自主选择分支 |
| **L3（进阶）** | 熟悉高级计量方法，追求深度 | 推荐前沿方法（如异质性处理效应、机器学习辅助 IV）；讨论模型识别假设的深层问题；提供更多自定义选项 |

### 外部参考仓库

本 Skill 在设计上参考了以下三个开源项目：

| 仓库 | 定位 | 使用方式 |
|------|------|----------|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | **设计参考**：提取格式参数（字号/行距/三线表/公式编号），在 Phase 9 中作为排版默认配置 |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | **路线 B 工具链**：Phase 9 的 Node.js 路线直接使用其辅助函数模式 |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | **计量执行引擎**：Phase 4-8 通过 MCP 写 do file 并运行 Stata |

---

## Phase 0：环境准备

### Step 0.1：依赖检测

AI 自动检测以下环境是否就绪：

```bash
# Python
python3 --version               # 需 ≥ 3.9
pip3 list 2>/dev/null | grep -i "python-docx\|openpyxl\|pandas\|numpy\|matplotlib\|seaborn\|scipy\|statsmodels"

# Node.js（B 路线需要）
node --version                  # 需 ≥ 18
npm list -g docx 2>/dev/null

# Stata（计量运行需要）
stata --version                 # 或 stata-mp / stata-se

# uv（mcp-for-stata 安装需要）
uv --version                    # 需 ≥ 0.4.0
```

缺失项由 AI 提示安装命令。

### Step 0.2：项目文件夹初始化

在工作目录下自动创建以下结构：

```
project_root/
├── data/
│   └── raw/                    # 原始数据（只读）
├── cleaned/                    # 清洗后数据
├── do/                         # Stata do files
├── output/
│   ├── tables/                 # 回归表格（.rtf / .csv）
│   └── figures/                # 图形（.png / .pdf）
├── thesis/                     # 论文 docx 输出目录
├── references/                 # 用户下载的 PDF 文献
├── scripts/                    # Python 辅助脚本
├── log/                        # 运行日志
├── .gitignore
└── README.md
```

### Step 0.3：MCP 客户端检测与 Stata MCP 配置

AI 必须询问用户当前使用的 AI 客户端环境，然后按对应方式配置 Stata MCP：

```
┌─────────────────────────────────────────────────────────┐
│ 请问你当前使用的是哪个 AI 客户端？                      │
│                                                         │
│  A. Claude Code（终端版/VS Code 扩展）                  │
│  B. OpenCode                                             │
│  C. Codex Desktop / CLI                                 │
│  D. 其他（Cursor / Cline / Windsurf 等）                │
│  E. 我还未确定 / 帮我推荐一种                           │
└─────────────────────────────────────────────────────────┘
```

按用户选择的客户端执行对应安装命令：

| 客户端 | 安装命令 |
|--------|----------|
| A. Claude Code | `claude mcp add stata-mcp --scope user -- uvx stata-mcp` |
| B. OpenCode | `uvx stata-mcp install -c opencode` |
| C. Codex | `uvx stata-mcp install -c codex` |
| D. 其他 | 手动配置：`uvx stata-mcp install -c <client-name>` |

安装后运行诊断：

```bash
uvx stata-mcp doctor
```

诊断应确认：Stata 可执行路径有效、Stata 许可证有效、MCP 端点可连通。

> **安全说明**：mcp-for-stata 内置安全检查——耗时超过 60 秒的查询弹出确认提示；可读写/执行的文件范围限定在工作目录内。默认启用，无需额外配置。

### Step 0.4：参考范文读取

询问用户是否提供参考范文 `.docx`：

```
是否有一篇参考范文 .docx 可以提供？
- 范文用于提取格式模板（样式、字体、字号、行距、页边距）
- 范文也用于参考写作风格（章节组织、论证方式、语言习惯）
- 范文放在 thesis/ 目录下即可
```

如用户提供，AI 使用 `python-docx` 读取范文的样式定义并应用到 Phase 9 输出。

### Step 0.5：用户水平确认

```
请选择你的水平，这将影响后续环节的详细程度：
  L1. 新手——第一次做实证论文，希望有引导和概念解释
  L2. 有基础——上过计量课，做过基本回归
  L3. 进阶——熟悉高级计量方法，追求深度
```

确认后存入上下文变量 `{{user_level}}`，后续所有决策按此自适应。

---

## Phase 1：选题与文献定位

### 流程

```
用户输入 X / Y / 中介变量 / 研究题目 / 水平
        │
        ▼
AI 搜索 Semantic Scholar API
        │
        ▼
AI 抓取开放获取全文（NBER / SSRN / arXiv）
        │
        ▼
AI 精读 5-10 篇核心文献
        │
        ▼
AI 生成：
  ① 文献知识库（关键文献摘要+贡献+方法+数据+结论）
  ② 选题评估报告（可行性 / 创新点 / 数据可得性 / 潜在问题）
        │
        ▼
用户确认 → 进入 Phase 2
```

### Step 1.1：用户输入

AI 引导用户提供以下信息：

1. **被解释变量 (Y)**：是什么？核心测度指标？
2. **核心解释变量 (X)**：是什么？变动的来源？
3. **潜在机制/中介变量 (M)**（可选）：可能通过什么渠道影响？
4. **研究题目/方向描述**：一句话概括
5. **所属学科领域**：劳动经济学 / 产业组织 / 发展经济学 / 金融 / 国际贸易 / 其他

L1 用户额外询问：是否有感兴趣的具体问题或现象？

### Step 1.2：AI 搜索文献

使用 Semantic Scholar API（通过 WebFetch）搜索核心文献：

- 搜索关键词：由 AI 基于用户输入生成 3-5 组
- 每组成果筛选：按引用数排序，取 top 20
- 优先关注：近 5 年发表、高引用、发表在顶级期刊的研究

对于识别到的核心文献（5-10 篇），尝试通过以下开放获取渠道抓取全文：

- **NBER**（`nber.org/papers/wXXXX`）：经济学工作论文，免费开放
- **SSRN**（`papers.ssrn.com`）：社会科学研究网络，多数免费
- **arXiv**（`arxiv.org`）：部分经济学论文，纯开放获取
- **作者个人主页**：多数经济学家会挂自己的工作论文

### Step 1.3：生成文献知识库

对每篇精读文献，AI 提取以下结构化信息：

```
文献知识库格式（每篇一条）：
────────────────────────────────────────
标题：{Title}
作者：{Authors}（{Year}）
期刊/来源：{Journal/Source}
引用数：{Citations}
────────────────────────────────────────
研究问题：{Research Question}
核心发现：{Main Findings}
数据来源：{Data Source}
方法：{Methodology}
估计策略：{Identification Strategy}
与本题关联：{Relevance to Our Topic}
────────────────────────────────────────
关键引用句（可直接用于文献综述的段落）：
"{Quote}"
────────────────────────────────────────
可信度评估：[H/M/L]
  H = 顶级期刊 / 高引用 / 方法严谨
  M = 领域内重要但存在方法争议
  L = 低质量 / 非学术来源
```

### Step 1.4：生成选题评估报告

AI 基于文献扫描结果生成：

```
选题评估报告
═══════════════════════════════════════

1. 可行性评估
   • 已有文献基础：{已有多少相关研究}
   • 创新空间：{已有研究的缺口，本题的新颖之处}
   • 数据可得性：{常见数据来源建议}
   • 方法可行性：{可用的识别策略}

2. 潜在贡献
   • 理论贡献：{对机制/理论的推进}
   • 实证贡献：{对估计策略/数据的改进}
   • 政策贡献：{对现实问题的启示}

3. 风险提示
   • {潜在的内生性问题}
   • {可能的数据限制}
   • {领域内竞争程度}
   • {其他需要注意的问题}

4. 与范文的比较
   • {范文的定位与本选题的异同}
```

### Step 1.5：用户确认

用户阅读后可以：
- ✅ **确认**——进入 Phase 2
- ✏️ **修改**——调整题目方向或变量
- ❌ **放弃**——重新选题

---

## Phase 2：文献综述与理论框架

### Step 2.1：核心文献获取

AI 推荐搜索关键词和文献获取渠道：

```
推荐搜索关键词（共 3-5 组）：
  Group 1: {keyword set 1}
  Group 2: {keyword set 2}
  ...

推荐文献获取渠道：
  • Google Scholar: https://scholar.google.com/
    下载方式：搜索 → 引用下的 PDF/All versions 链接
  • CNKI (知网): https://www.cnki.net/
    下载方式：搜索 → 选择「PDF 下载」（不接受 CAJ 格式）
  • NBER: https://www.nber.org/papers
  • SSRN: https://papers.ssrn.com/
  • 参考文献追溯：从已有关键文献的参考文献列表中
    反向查找高引文献

下载建议：每篇 PDF 文件名格式为
  {AuthorYear}_{ShortTitle}.pdf
  例如：Autor2013_TradeJobs.pdf

目标数量：约 80-120 篇
  - H 级（核心）：15-20 篇（必须精读）
  - M 级（相关）：30-40 篇（阅读摘要+结论）
  - L 级（背景）：剩余篇目（扫描摘要即可）
```

### Step 2.2：分类精读

AI 按优先级处理用户下载的 PDF：

```
H 级（15-20 篇）：全文精读
  → 提取完整文献笔记：研究问题、理论框架、数据、方法、发现、局限

M 级（30-40 篇）：摘要+结论精读
  → 提取核心发现和方法特点

L 级（剩余篇目）：摘要扫描
  → 仅记录主题方向和研究结论
```

精读方法：AI 使用 `python-docx` 或文本提取工具读取 PDF，按段落级别分析内容。

### Step 2.3：生成文献综述

AI 参考用户提供的范文格式和写作风格，输出文献综述 `.docx`：

```
文献综述结构（自动生成）
═══════════════════════════════════════

1. 引言段
   - 研究领域的背景和重要性
   - 已有研究的主要脉络
   - 本研究要填补的缺口

2. {主题词1} 相关文献
   - 按时间/学派/方法组织
   - 每段：前人做了什么 → 发现什么 → 还有什么问题

3. {主题词2} 相关文献
   - 同上结构

4. {X-Y 关系} 相关文献
   - 直接相关的实证研究
   - 识别策略的演进

5. 研究述评
   - 总结已有贡献
   - 指出不足和研究空白
   - 本研究的定位和创新点
```

**排版要求**：
- 套用范文的样式集（若用户提供范文）
- 若未提供范文，使用 easy-paper 格式规范（见附录）
- 图表引用：`(Author, Year)` 格式，放在标点前
- 中文摘要在前，英文翻译在后

### Step 2.4：理论机制推演

文献综述经用户确认后，AI 推导理论机制和研究假设：

```
理论框架
═══════════════════════════════════════

机制图（以文字描述）：
  X ──(渠道A)──→ M1 ──→ Y
  X ──(渠道B)──→ M2 ──→ Y
  X ──(调节)──→ Z × X ──→ Y
  ...

研究假设：
  H1: X 对 Y 有正向/负向影响
  H2a: X 通过 M1 影响 Y（中介效应）
  H2b: X 通过 M2 影响 Y（中介效应）
  H3: Z 强化/弱化了 X 对 Y 的影响（调节效应）

各假设的理论依据（引用文献支持）
```

研究假设将作为 Phase 7（机制检验）的输入。

---

## Phase 3：数据与变量

### Step 3.1：入口分叉

AI 首先询问用户的数据状态：

```
请问你的数据来源是？

A. 已有数据
   → 我已有 Stata .dta 或 Excel 格式的数据文件

B. 不知从何获取
   → 我需要 AI 推荐数据来源
```

### 分支 A：已有数据

1. 用户提供数据文件路径（支持 `.dta` / `.xlsx` / `.xls` / `.csv`）
2. AI 读取数据结构（变量名、标签、类型、缺失率、描述统计）
3. 输出数据摘要报告

### 分支 B：推荐数据来源

AI 根据研究主题推荐数据来源：

| 数据需求 | 推荐来源 | 说明 |
|----------|----------|------|
| 上市公司财务数据 | **CSMAR** / Wind / CCER | 最全面的中国上市公司数据 |
| 家庭/个人微观数据 | **CFPS**（中国家庭追踪调查）/ CHFS / CHIP | 北大/西南财大等发布 |
| 城市/地区宏观数据 | **统计年鉴** / 城市统计年鉴 / 中国数据在线 | 国家统计局发布 |
| 企业数据 | 中国工业企业数据库 / 税务调查 / 经济普查 | 需申请 |
| 国际贸易数据 | **海关数据库** / BACI / UN Comtrade | 反映企业进出口 |
| 国际比较数据 | World Bank WDI / IMF IFS / PWT | 跨国面板 |

> 所有数据获取后，用户需统一转换为 `.dta` 格式（通过 Python pandas `.to_stata()` 或 Stata 直接导入），以便后续计量分析。

### Step 3.2：变量推荐

AI 基于文献综述的结果，推荐核心变量集合：

```
变量推荐方案
═══════════════════════════════════════

被解释变量 (Y)
  • {变量1}：{定义和构造方法}
  • {变量2}：{定义和构造方法}（稳健性替换）

核心解释变量 (X)
  • {变量1}：{定义和构造方法}
  • {变量2}：{定义和构造方法}（替代度量）

控制变量
  • 个体层面：{变量列表及理由}
  • 企业层面：{变量列表及理由}
  • 地区层面：{变量列表及理由}
  • 时间/行业固定效应：{建议}

机制变量 (M)
  • {变量1}：{对应假设 H2a}
  • {变量2}：{对应假设 H2b}
```

用户确认变量清单后，进入下一步。

### Step 3.3：变量构造执行

AI 询问用户的选择：

```
请选择变量构造方式：

A. AI 生成 Python 构造脚本
   → 将原始数据清洗为回归就绪格式，保存为 cleaned/dataset.dta
   依赖：pandas / numpy / openpyxl

B. 用户自行处理
   → 用户提供已构造好的 cleaned/dataset.dta
```

选择 A 时，AI 生成 Python 脚本并执行，包括：
- 数据合并（多表/多年份）
- 变量生成（对数化、标准化、交互项、滞后项等）
- 缺失值处理
- 异常值处理
- 标签添加
- 导出为 `.dta`

### Step 3.4：描述统计方案

```
描述统计生成方案
─────────────────────────────────

推荐输出（一次性生成所有）：

1. 描述性统计表
   • 样本量、均值、标准差、最小值、最大值
   • 按处理/控制组分组的均值比较
   • 关键变量的时间趋势

2. 相关性矩阵
   • 皮尔逊相关系数
   • 标注显著性水平

3. 可视化
   • 核心变量的核密度图/直方图
   • Y 和 X 的散点图+拟合线
   • 分组箱线图
   • 时间趋势图

请确认以上方案是否符合需求？
─────────────────────────────────
```

用户确认后，AI 一次性生成表格和图表，存入 `output/tables/` 和 `output/figures/`。

### Step 3.5：数据就绪检查清单

```
□ 数据完整性：各变量有效样本量足够
□ 无极端异常值：关键变量在合理范围内
□ 变量标签完整：所有变量有中文标签
□ 类别变量编码正确：虚拟变量/定序变量已标识
□ 面板结构标识：个体 ID + 时间 ID 唯一标识观测量
□ 数据格式：已导出为 .dta，Stata 可正常读取
```

---

## Phase 4：基准回归

### Step 4.1：方法推荐

AI 基于数据结构推荐基准回归策略：

| 数据结构 | 推荐方法 | 说明 |
|----------|----------|------|
| 截面数据 | OLS | 线性回归，异方差稳健标准误 |
| 面板数据 | 固定效应 (FE) / 随机效应 (RE) | Hausman 检验决定 |
| 二值因变量 | Logit / Probit | 报告边际效应 |
| 计数数据 | Poisson / 负二项 | |
| 多期面板 | 双向固定效应 (TWFE) | 个体+时间固定效应 |

L1 用户：AI 简要解释所选方法的适用性
L2/L3 用户：AI 同时讨论模型假设和识别条件

### Step 4.2：全流程说明

在写 do file 之前，AI 先向用户说明完整流程：

```
基准回归流程说明
═══════════════════════════════════════

1. 模型设定
   Y_it = α + β*X_it + γ*Controls_it + μ_i + λ_t + ε_it

   • β 是核心估计量，预期方向：{正/负}
   • 控制变量已包含：{控制变量列表}
   • 个体固定效应 μ_i：控制不随时间变化的不可观测因素
   • 时间固定效应 λ_t：控制年度宏观冲击
   • 标准误在 {个体/年份} 层面聚类

2. 回归序列
   (1) 仅 X：Y = α + β*X
   (2) 加入控制变量
   (3) 加入固定效应
   (4) 完整模型（最终基准）

3. 输出
   • 回归系数表（output/tables/baseline.rtf）
   • 各模型 R²、F 统计量
   • 如有需要，输出边际效应图

确认后开始写 do file？
─────────────────────────────────
```

### Step 4.3：写 do file

AI 通过 Stata MCP 的 `stata_run_file` 工具执行 do file。在写 do file 之前，先通过 `stata_run_command` 快速检测数据加载是否正常：

```stata
* do/baseline.do
* 基准回归
* 生成时间：{date}

* ── 环境设置 ──
clear all
set more off
cd "{project_root}"

* ── 加载数据 ──
use "cleaned/dataset.dta", clear

* ── 变量标签 ──
* (自动生成的标签代码)

* ── 回归序列 ──
* Model 1: 仅核心变量
eststo m1: reg Y X, robust

* Model 2: 加入控制变量
eststo m2: reg Y X $controls, robust

* Model 3: 加入固定效应
eststo m3: reghdfe Y X $controls, absorb(i.id i.year) vce(cluster id)

* ... 完整模型

* ── 输出表格 ──
esttab m1 m2 m3 using "output/tables/baseline.rtf", replace ///
    b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) ///
    stats(N r2 F, fmt(0 3 2)) ///
    title("基准回归结果") ///
    mtitles("(1)" "(2)" "(3)" "(4)")
```

### Step 4.4：结果解读

AI 贴出回归结果后，逐项解读：

```
基准回归结果解读
═══════════════════════════════════════

1. 核心变量 X
   • 系数 β = {value}，在 {p-value} 水平上显著
   • 经济含义：X 每变化一个标准差，Y 变化 {effect_size} 个标准差
   • 与预期方向 {一致/不一致}

2. 控制变量
   • {控制变量1}：{显著方向和经济含义}
   • {控制变量2}：{显著方向和经济含义}
   ...

3. 模型拟合度
   • R² = {value}，F 统计量显著
   • 说明模型解释了 Y 变异的 {percent}

4. 检查点
   □ 系数方向与理论预期一致
   □ 核心系数在统计上显著
   ☐ p > 0.1 时：AI 应推荐改善方案（见下方）
```

### Step 4.5：显著性改善方案

若核心变量 p > 0.1，AI 按优先级推荐以下方案：

```
建议改善方案：
1. 检查数据量是否充足 → {样本量是否够}
2. 检查变量定义 → {是否有测量误差}
3. 考虑更高维固定效应 → {如行业×年份 FE}
4. 考虑更优标准误聚类 → {如行业层面聚类}
5. 检查离群值影响 → {缩尾处理}
6. 考虑非线性效应 → {引入平方项}
7. 更换估计方法 → {更换为更适合的方法}

请选择要尝试的方案（可多选）：A / B / C / ...
```

用户选择后，AI 更新 do file 重新运行，直至用户对结果满意。

---

## Phase 5：内生性处理

> **关键设计**：Phase 5 处理内生性后所确立的模型框架，将被 Phase 6-8 继承使用。所有的后续回归都基于处理内生性后的模型，不退回 OLS。

### Step 5.1：内生性来源诊断

AI 从三个维度汇合识别内生性来源：

```
内生性诊断报告
═══════════════════════════════════════

1. 遗漏变量偏差
   • 可能遗漏的重要因素：{变量列表}
   • 方向判断：{遗漏变量与 X 和 Y 的相关方向}
   • 影响：{高估/低估} X 的效应

2. 反向因果
   • X → Y 还是 Y → X？
   • 经济逻辑判断：{具体分析}
   • 可能存在的原因：{具体机制}

3. 测量误差
   • X 的测量方式：{当前测量}
   • 可能的误差来源：{具体描述}
   • 误差类型：{经典 / 非经典}
```

### Step 5.2：方法推荐

AI 推荐内生性处理方法：

| 场景 | 推荐方法 | 适用前提 |
|------|----------|----------|
| 遗漏变量 | **工具变量 (IV-2SLS)** | 找到满足外生性和相关性的工具变量 |
| 自选择偏误 | **PSM** / **Heckman 两步法** | 足够的可观测变量构造倾向得分 |
| 样本选择偏误 | **Heckman 选择模型** | 有排他性约束变量 |
| 面板数据内生性 | **系统 GMM** / **差分 GMM** | T 相对较小，N 较大 |
| 自然实验/准实验 | **DID** / **断点回归 (RDD)** | 有外生政策冲击或分配阈值 |

### Step 5.3：数据缺口检查

AI 检查识别策略所需的数据是否就绪：

```
数据缺口检查
─────────────────────────────────

推荐方法：{IV / PSM / Heckman / GMM / DID / RDD}

所需额外数据/变量：
  □ {变量1} — 当前状态：{已有/需要构造/需用户提供}
  □ {变量2} — 当前状态：{已有/需要构造/需用户提供}
  ...

若需用户提供新数据：
  • 数据描述：{具体需要什么样的数据}
  • 推荐来源：{建议去哪里获取}
  • 格式要求：{dta / xlsx / csv}
─────────────────────────────────
```

### Step 5.4：额外变量推荐

如果需要额外变量，AI 推荐具体的构造方案：

```
变量构造方案
─────────────────────────────────

变量1（工具变量/排他性约束变量）：
  • 定义：{变量经济含义}
  • 构造方法：{如何从原始数据构造}
  • 预期相关性：{与 X 相关的原因}
  • 预期外生性：{与 Y 不直接相关的原因}
  • 文献依据：{哪些文章用了类似 IV}

变量2：
  ...
─────────────────────────────────
```

用户确认后，AI 生成构造代码或指导用户准备数据。

### Step 5.5：写 do file

```
内生性处理 do file（do/endogeneity.do）
═══════════════════════════════════════

* ── 模型标注 ──
* 本 do file 产出的模型框架将在 Phase 6-8 中被继承
* Phase 6（稳健性检验）将基于此框架
* Phase 7（机制检验）将基于此框架
* Phase 8（异质性分析）将基于此框架

* ── 第一阶段（IV）或 倾向得分估计（PSM）──
* ...

* ── 第二阶段或匹配后估计 ──
* ...

* ── 与基准回归对比 ──
* 将基准回归结果保存在 output/tables/baseline.rtf
* 将内生性处理结果保存在 output/tables/endogeneity.rtf
```

### Step 5.6：结果解读

```
内生性处理结果解读
═══════════════════════════════════════

1. 第一阶段结果（如适用）
   • F 统计量 = {value}（>10 说明工具变量不弱）
   • 工具变量与 X 的相关性：{正/负} 显著

2. 第二阶段结果
   • 核心系数 β_IV = {value}，与基准 β_OLS = {value} 对比
   • 差异方向：{β_IV > β_OLS / β_IV < β_OLS}
   • 经济含义：{解读}

3. 模型诊断
   • 过度识别检验（若 IV 数量 > 内生变量数）：{p-value}
   • DWH 检验：{p-value}，{支持/不支持} 外生性假设
   • 弱工具变量检验：{Cragg-Donald / Kleibergen-Paap 统计量}

4. 最终结论
   • 内生性处理后 X 对 Y 的效应仍 {显著/不显著}
   • 基准回归的估计方向 {是/否} 稳健
```

### Step 5.7：确立最终模型框架

用户确认结果后，AI 记录**最终模型框架**，供 Phase 6-8 使用：

```
最终模型框架（Phase 6-8 继承）
═══════════════════════════════════════

数据集：cleaned/dataset.dta
估计方法：{2SLS / PSM / Heckman / GMM / DID / RDD / FE}
核心解释变量：X
被解释变量：Y
控制变量：{控制变量列表}
固定效应：{个体/年份/行业等}
标准误聚类：{聚类层级}
工具变量（如有）：{IV list}

Phase 5 产出 do file：do/endogeneity.do
Phase 5 产出表格：output/tables/endogeneity.rtf
```

---

## Phase 6：稳健性检验

### Step 6.1：方法推荐

基于 Phase 5 确立的模型框架，推荐 4-6 种稳健性检验方法：

```
推荐稳健性检验方案
═══════════════════════════════════════

适用方案（推荐 4-6 种，用户从中选 2-3 种）：

1. 更换被解释变量度量
   • 当前：{变量定义}
   • 替换为：{替代度量方案}
   • 预期：方向不变

2. 更换核心解释变量度量
   • 当前：{变量定义}
   • 替换为：{替代度量方案}
   • 预期：方向不变

3. 更换样本范围
   • 剔除 {直辖市/省会/异常值} 后重估
   • 预期：系数变化在可接受范围内

4. 更换估计方法
   • 当前：{方法}
   • 替换为：{替代方法}
   • 预期：结论不变

5. 更换固定效应规格
   • 加入更高维固定效应：{行业×年份 / 地区×年份}
   • 预期：系数稳健

6. 安慰剂检验（置换检验）
   • 随机分配处理状态，重复 500/1000 次
   • 预期：基准系数在安慰剂分布之外

7. 排除极端值
   • 对连续变量进行 {1% / 5%} 缩尾处理
   • 预期：系数方向不变

8. 子样本分析
   • 按 {地区/规模/所有制} 分组
   • 预期：组间方向一致
```

> 注意：所有检验均使用 Phase 5 的模型框架（相同的数据集、固定效应、标准误聚类等）。

### Step 6.2：用户选择

用户从推荐列表中选取 2-3 种方法，AI 确认选择。

### Step 6.3：数据缺口检查

```
数据/变量需求检查：
  □ {方法1} — 所需变量/数据：{已有/需构造}
  □ {方法2} — 所需变量/数据：{已有/需构造}
  ...
```

### Step 6.4：写 do file

```stata
* do/robustness.do
* 稳健性检验
* 基于 Phase 5 模型框架

use "cleaned/dataset.dta", clear

* ── 基准模型（Phase 5）──
* {Phase 5 主模型代码}

* ── 稳健性 1：更换 Y 度量 ──
* ...

* ── 稳健性 2：缩尾处理 ──
* winsor2 X, cuts(1 99)
* ...

* ── 稳健性 3：排除特定样本 ──
* ...
```

### Step 6.5：结果解读与对比

```
稳健性检验结果
═══════════════════════════════════════

基准系数：β = {value}，{显著水平}

稳健性检验 1（更换 Y 度量）：
  • β = {value}，{显著水平}
  • 与基准系数方向 {一致/不一致}
  • 结论：{稳健/不稳健}

稳健性检验 2（缩尾处理）：
  • β = {value}，{显著水平}
  • 与基准系数方向 {一致/不一致}
  • 结论：{稳健/不稳健}

稳健性检验 3（子样本）：
  • β = {value}，{显著水平}
  • 与基准系数方向 {一致/不一致}
  • 结论：{稳健/不稳健}

综合判断：{X 对 Y 的效应通过/未通过稳健性检验}
```

---

## Phase 7：机制检验

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

### Step 7.3：中介变量回顾性检查

AI 检查 Phase 3 构造的机制变量是否就绪，或是否需要补充：

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
```

### Step 7.5：结果解读

```
机制检验结果
═══════════════════════════════════════

H2a: X → M1 → Y
  • X → M1：系数 β = {value}，{显著/不显著}
  • M1 → Y（含 X）：系数 = {value}，{显著/不显著}
  • Sobel Z = {value}，p = {value}
  • {支持/不支持} H2a

H2b: X → M2 → Y
  • ...

H3: Z 的调节效应
  • 交互项系数 β3 = {value}，{显著/不显著}
  • 方向：{正向/负向} 调节
  • {支持/不支持} H3

机制总结：{X 通过什么渠道影响 Y 的整体结论}
```

---

## Phase 8：异质性分析

### Step 8.1：自动扫描分组维度

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

---

## Phase 9：论文撰写与排版成文

### Step 9.0：路线选择

进入 Phase 9 时，AI 首先询问排版路线：

```
论文文档生成路线选择
═══════════════════════════════════════

请选择文档生成方式：

A. Python 路线（python-docx）
   依赖：Python 3.9+，pip install python-docx
   特点：纯 Python 生态，与数据分析流水线同语言，易于维护
   公式支持：通过 latex2mathml 或 python-docx 原生公式

B. Node.js 路线（docx-skill-4-cn-paper）
   依赖：Node.js 18+，npm install docx temml fast-xml-parser
   特点：原生公式支持（temml → MathML → Word 原生公式），
         直接使用 docx-skill-4-cn-paper 辅助函数体系
   公式管道：LaTeX → temml → MathML → OMML（Word 原生）

建议：如果你熟悉 Node.js 或需要高质量公式渲染，选 B。
      如果希望保持全流程 Python 统一，选 A。

你的选择：[A / B]
```

### Step 9.1：素材读取

AI 从以下来源读取素材：

| 来源 | 内容 | 读取方式 |
|------|------|----------|
| Phase 1-8 产出 | 回归结果表、统计描述表、图表 | `output/tables/` + `output/figures/` |
| 文献知识库 | 文献引用语句、综述草稿 | 上下文变量 |
| 参考范文 .docx（如有） | 样式定义、格式模板 | `python-docx` 读取样式 |
| 用户补充 | 特定需要写进论文的内容 | 用户提供 |

### Step 9.2：范文格式提取

若用户提供了参考范文，AI 提取其格式参数：

```python
# AI 使用 python-docx 读取范文样式
from docx import Document
doc = Document("thesis/reference.docx")

# 提取默认样式参数
default_style = doc.styles['Normal']
heading1_style = doc.styles['Heading 1']
# ... 提取字体、字号、行距、颜色、段落间距等

# 提取页面设置
section = doc.sections[0]
page_width = section.page_width
page_height = section.page_height
margin_left = section.left_margin
# ...
```

输出格式参数供后续使用。

若未提供范文，使用 easy-paper 格式规范（见附录）。

### Step 9.3：大纲先行

AI 先生成全文大纲：

```
论文大纲（用户确认后撰写正文）
═══════════════════════════════════════

第一章 引言
  1.1 研究背景（约 1 页）
  1.2 研究问题与意义（约 0.5 页）
  1.3 研究方法（约 0.5 页）
  1.4 主要发现与贡献（约 0.5 页）
  1.5 论文结构安排（约 0.25 页）

第二章 文献综述
  2.1 {主题1} 相关研究（约 1.5 页）
  2.2 {主题2} 相关研究（约 1.5 页）
  2.3 {理论机制} 相关研究（约 1 页）
  2.4 研究述评与本文定位（约 0.5 页）

第三章 理论机制与研究假设
  3.1 理论分析框架（约 1 页）
  3.2 机制分析与研究假设（约 1 页）

第四章 研究设计
  4.1 数据来源与处理（约 1 页）
  4.2 变量定义与描述统计（约 1.5 页）
  4.3 计量模型设定（约 1 页）

第五章 实证结果分析
  5.1 基准回归（约 1.5 页）
  5.2 内生性处理（约 2 页）
  5.3 稳健性检验（约 1.5 页）
  5.4 机制检验（约 1.5 页）
  5.5 异质性分析（约 1.5 页）

第六章 结论与政策建议
  6.1 主要结论（约 1 页）
  6.2 政策建议（约 1 页）
  6.3 研究局限与未来展望（约 0.5 页）

（约 15-20 页正文 + 附录）
```

用户确认大纲后进入正文撰写。

### Step 9.4：正文撰写（占位符策略）

正文撰写采用 **`[CIT:关键词]` 占位符**策略：

- 所有引用位置写作：`研究指出，X 对 Y 有显著正向影响[CIT:Author2020_keyfinding]`
- 占位符格式：`[CIT:关键词1;关键词2]`（用于需要合并多篇文献的表述）
- 不插入具体引文格式，避免后续替换时污染格式
- 每章分步骤撰写，完成后用户可以分段确认

撰写顺序：
1. 实证结果章节（第五章）— 最确定，最先写
2. 研究设计章节（第四章）
3. 理论机制章节（第三章）— 结合 Phase 2
4. 文献综述章节（第二章）
5. 引言章节（第一章）— 最后写，统领全文
6. 结论章节（第六章）
7. 中英文摘要 — 最后浓缩

### Step 9.5：补充推荐文献

正文初稿完成后，AI 基于 `[CIT:]` 占位符的使用情况，识别是否需要补充文献：

```
补充文献建议
─────────────────────────────────

以下位置占位符较多，建议补充阅读：
  • 第 2.1 节 — {主题} — 现有 {n} 条，建议补充至 {m} 条
  • 第 5.3 节 — {主题} — 需要对比文献

推荐补充搜索关键词：
  • {关键词组合 1}
  • {关键词组合 2}

用户将补充文献 PDF 放入 references/ 目录。
─────────────────────────────────
```

### Step 9.6：引文标注（占位符替换）

用户补充文献后，AI 重新精读所有引用到的 PDF，提取准确引用信息：

```
引用信息标注（每条占位符替换）
─────────────────────────────────
[CIT:Author2020_keyfinding]
  → (王某某等, 2020) 或
  → (Smith et al., 2020) 或
  → 多篇合并时：研究指出...（王某某等, 2020; Smith et al., 2020）
─────────────────────────────────
```

批量替换所有 `[CIT:...]` 占位符为 `(Author, Year)` 格式。

同时生成参考文献列表（GB/T 7714 格式）。

### Step 9.7：图表推荐与插入

AI 检查论文中需要图表的位置，询问用户：

```
论文图表插入建议
═══════════════════════════════════════

第 4 章（研究设计）：
  □ 表 1：描述性统计表 ✓（已存在 output/tables/desc.rtf）
  □ 表 2：相关性矩阵 ✓（已存在）
  □ 图 1：核心变量分布图 ✓（已存在 output/figures/dist.png）

第 5 章（实证结果）：
  □ 表 3：基准回归结果 ✓（已存在 output/tables/baseline.rtf）
  □ 表 4：内生性处理结果 ✓（已存在 output/tables/endogeneity.rtf）
  □ 表 5：稳健性检验结果 ✓（已存在）
  □ 表 6：机制检验结果 ✓（已存在）
  □ 表 7：异质性分析结果（分维度）✓（已存在）
  □ 图 2：机制路径图（需新建）

请确认以上图表是否需要全部插入？
如需调整或新增，请说明。
═══════════════════════════════════════
```

用户确认后，AI 通过 python-docx（A 路线）或 docx npm（B 路线）将图表插入对应章节位置。

图表排版格式（三线表标准）：
- 表题在上：小五号黑体，居中
- 表格为三线表（顶线 1.5pt / 栏目线 0.75pt / 底线 1.5pt）
- 表注在下：小五号宋体
- 图题在下：小五号黑体，居中

### Step 9.8：最终排版

AI 执行最终排版流程：

```
最终排版清单
═══════════════════════════════════════

□ 封面——按范文/学校模板生成
□ 中文摘要——300-500 字 + 3-5 个关键词
□ 英文摘要——对应翻译
□ 目录——生成文本占位目录（用户后续 Word "更新域"）
□ 正文章节——已完成撰写
□ 参考文献——GB/T 7714 格式，按字母/拼音排序
□ 附录——留空（论文答辩后补充）
□ 致谢——留空
□ 页码——从正文开始阿拉伯数字，封面+摘要用罗马数字
□ 页眉页脚——按范文设置
□ 版面——A4 纸，默认页边距
```

A 路线（python-docx）示例代码：

```python
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

# 页面设置
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)

# 正文样式
style = doc.styles['Normal']
style.font.name = '宋体'
style.font.size = Pt(10.5)  # 五号
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
pf = style.paragraph_format
pf.line_spacing = 1.5
pf.first_line_indent = Pt(21)  # 首行缩进 2 字符

# 辅助函数定义
def add_heading1(text):
    """一级标题"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(15)  # 小三
    run.font.name = '黑体'
    run.bold = True
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

def add_heading2(text):
    """二级标题"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(12)  # 四号
    run.font.name = '黑体'
    run.bold = True
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

def add_body(text):
    """正文段落"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = '宋体'
    run.font.size = Pt(10.5)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

def add_three_line_table(headers, rows, caption):
    """三线表"""
    # 表题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(caption)
    run.font.size = Pt(9)
    run.font.name = '黑体'
    run.bold = True

    # 表格
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # 表头
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        # 表头格式

    # 数据行
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = str(val)

    # 三线表边框设置
    # 顶线 1.5pt / 栏目线 0.75pt / 底线 1.5pt
    # （具体 XML 操作省略）

    # 表注
    p = doc.add_paragraph()
    run = p.add_run("注：*** p<0.01, ** p<0.05, * p<0.1，括号内为聚类稳健标准误。")
    run.font.size = Pt(9)
    run.font.name = '宋体'
```

B 路线（Node.js docx-skill-4-cn-paper）示例：

```javascript
const { h1, h2, body, formula, threeLineTable, ref } = require('./scripts/new_doc');

h1("第一章 引言");
body("研究背景段落...");
body("研究问题段落...");

h2("1.1 研究背景");
body("具体内容...");

formula("Y_{it} = \\alpha + \\beta X_{it} + \\gamma Controls_{it} + \\mu_i + \\lambda_t + \\varepsilon_{it}", "(1)");

threeLineTable(
  ["变量", "样本量", "均值", "标准差"],
  [
    ["Y", "5000", "3.25", "1.02"],
    ["X", "5000", "2.18", "0.85"],
  ],
  "表 1 主要变量描述性统计"
);
```

### 输出

论文最终输出为 `thesis/论文题目_终稿.docx`。

---

## 附录 A：格式规范参考（源自 easy-paper）

以下参数从 [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) Typst 模板中提取，作为无范文时的默认值。如果有范文，以范文样式为准。

### A.1 页面设置

| 参数 | easy-paper 默认值 | 备注 |
|------|--------------------|------|
| 纸张 | A4（21.0cm × 29.7cm） | |
| 上边距 | 2.5cm | |
| 下边距 | 2.5cm | |
| 左边距 | 2.5cm | |
| 右边距 | 2.5cm | |
| 页眉 | 1.5cm | |
| 页脚 | 1.75cm | |

### A.2 字体与字号

| 层级 | easy-paper 值 | 中文惯用值 | 说明 |
|------|---------------|-----------|------|
| 正文 | 10.5pt | 10.5pt（五号） | 宋体 |
| 一级标题 | 15pt | 15pt（小三） | 黑体，居中 |
| 二级标题 | 12pt | 12pt（四号） | 黑体，左对齐 |
| 三级标题 | 10.5pt | 10.5pt（五号） | 黑体，左对齐 |
| 表题/图题 | 9pt | 9pt（小五） | 黑体，居中 |
| 表注/图注 | 9pt | 9pt（小五） | 宋体 |
| 参考文献 | 9pt | 9pt（小五） | 宋体 |
| 脚注 | 9pt | 9pt（小五） | 宋体 |

### A.3 段落与间距

| 参数 | easy-paper 值 | 说明 |
|------|---------------|------|
| 正文行距 | 1.02em | 中文通常用 1.25-1.5 倍 |
| 首行缩进 | 2em | 中文字符缩进 2 字 |
| 标题前间距 | 6pt | |
| 标题后间距 | 3pt | |
| 段间距 | 0pt | 由缩进区分段落 |

### A.4 表格规范（三线表）

```
三线表结构：
────────────────────── 顶线（1.5pt）
 表头 | 表头 | 表头
────────────────────── 栏目线（0.75pt）
 数据 | 数据 | 数据
 数据 | 数据 | 数据
 数据 | 数据 | 数据
────────────────────── 底线（1.5pt）

注：表注内容
```

- 表中文字：小五号宋体或 8-9pt
- 表头加粗
- 表中不要竖线
- 表注字体小五号

### A.5 公式规范

```
居中显示公式，右对齐编号：
                    Y = α + βX + ε          (1)

引用方式：
  如公式 (1) 所示...
```

### A.6 引用格式（GB/T 7714）

```
中文文献：
  作者（年份）. 文献标题[J]. 期刊名, 卷(期): 页码.

英文文献：
  Author, A. (Year). Title[J]. Journal, Vol.(No.): Pages.

正文引用：
  单一文献：张三等（2020）或（张三等, 2020）
  多篇合并：张三等（2020）、李四（2021）或（张三等, 2020; Li, 2021）
```

---

## 附录 B：辅助函数 API 规约（源自 docx-skill-4-cn-paper）

以下接口是从 [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) 项目中提取的辅助函数体系。A 路线（Python）和 B 路线（Node.js）各自实现这组接口。

### B.1 文本类函数

```python
# ── Python 路线实现接口 ──
# 每个函数在下方给出原型签名

def heading1(doc, text: str) -> None:
    """一级标题（自动编号 第一章/第二章...）
       - 字体：黑体 15pt 居中
       - 前后间距：6pt / 3pt"""

def heading2(doc, text: str) -> None:
    """二级标题（自动编号 1.1/1.2...）
       - 字体：黑体 12pt 左对齐
       - 前后间距：6pt / 3pt"""

def heading3(doc, text: str) -> None:
    """三级标题（自动编号 1.1.1/1.1.2...）
       - 字体：黑体 10.5pt 左对齐"""

def body(doc, text: str) -> None:
    """正文段落
       - 自动检测文本中是否包含公式、引用标记
       - 首行缩进 2 字符
       - 字体：宋体 10.5pt
       - 行距：1.5 倍"""

def formula(doc, latex: str, tag: str = "") -> None:
    """居中公式 + 右对齐编号
       - A 路线：通过 latex2mathml 转换为 Word 公式
       - B 路线：通过 temml → MathML → OMML"""

def caption_figure(doc, text: str) -> None:
    """图题（下方居中）
       - 字体：黑体 9pt 居中"""

def caption_table(doc, text: str) -> None:
    """表题（上方居中）
       - 字体：黑体 9pt 居中"""

def note(doc, text: str) -> None:
    """图注/表注
       - 字体：宋体 9pt
       - 位于图/表下方"""

def abstract_cn(doc, text: str, keywords: list) -> None:
    """中文摘要 + 关键词
       - 摘要正文：宋体 10.5pt
       - 关键词格式："关键词：词1；词2；词3""""

def abstract_en(doc, text: str, keywords: list) -> None:
    """英文摘要 + 关键词"""
```

### B.2 表格类函数

```python
def three_line_table(doc, headers: list, rows: list, caption: str) -> None:
    """三线表
       - 顶线 1.5pt / 栏目线 0.75pt / 底线 1.5pt
       - 表头加粗，表中文字 9pt
       - 自动编号"""

def stat_table(doc, headers: list, rows: list, caption: str,
               note_text: str = "") -> None:
    """统计表格（描述性统计 / 相关性矩阵）
       - 继承三线表格式
       - 数字右对齐，文字左对齐"""
```

### B.3 图表类函数

```python
def insert_figure(doc, image_path: str, caption: str,
                  width: float = None) -> None:
    """插入图片
       - 居中显示
       - 自动编号图序
       - width 参数控制显示宽度（厘米）"""

def regression_table(doc, results_files: list, caption: str) -> None:
    """插入回归结果表
       - 从 esttab 输出的 RTF 读取
       - 转换为 docx 三线表格式
       - 保留显著性星号标注"""
```

### B.4 排版类函数

```python
def page_setup(doc, margins: dict = None) -> None:
    """页面设置（A4、页边距、页眉页脚）"""

def toc(doc) -> None:
    """生成目录占位符（用户 Word 中更新域）
       - A 路线：插入 TOC 域代码
       - B 路线：同"""

def header_footer(doc, header_text: str = "",
                  page_number: bool = True) -> None:
    """页眉页脚 + 页码"""

def reference_list(doc, references: list) -> None:
    """参考文献列表（GB/T 7714）
       - 按拼音/字母排序
       - 字体 9pt 宋体"""

def cover_page(doc, title: str, author: str, **kwargs) -> None:
    """封面页（按学校/范文模板）"""
```

### B.5 路线差异对照

| 功能 | A 路线（Python） | B 路线（Node.js） |
|------|-----------------|-------------------|
| 库依赖 | `python-docx` | `docx` (npm) |
| 公式渲染 | `latex2mathml` 或 `python-docx` OMML | `temml` → MathML → `docx` OMML |
| 读取模板样式 | `docx.Document()` 直接读取 | `docx.Document()` 读取 |
| 辅助函数 | 自行实现上述接口 | 直接调用 `scripts/new_doc.js` 中的已实现函数 |
| 代码位置 | `scripts/generate_thesis.py` | `scripts/generate_thesis.js` |
| 运行命令 | `python scripts/generate_thesis.py` | `node scripts/generate_thesis.js` |

---

## 附录 C：Stata MCP 配置与使用指南

### C.1 安装

```bash
uvx stata-mcp install -c <client-name>
# 或
uv tool install stata-mcp
```

### C.2 客户端配置

按客户端类型配置 mcp-for-stata：

| 客户端 | 配置文件 | 配置内容 |
|--------|----------|----------|
| Claude Code | `~/.claude/settings.json` | `{"mcpServers": {"stata-mcp": {"command": "uvx", "args": ["stata-mcp"]}}}` |
| OpenCode | `~/.config/opencode/opencode.jsonc` | 同上 |
| Codex | `~/.codex/settings.json` | 同上 |
| Cursor | Cursor Settings → MCP | 同上 |

### C.3 可用工具

mcp-for-stata 提供以下工具（AI 在 Phase 4-8 中使用）：

| 工具名 | 功能 | 使用场景 |
|--------|------|----------|
| `stata_run_command` | 执行单行 Stata 命令 | 数据加载检查、快速查询 |
| `stata_run_file` | 执行 do file | 运行完整回归 do file（Phase 4-8 核心） |
| `stata_get_output` | 获取 Stata 输出结果 | 读取回归结果 |
| `stata_list_datasets` | 查看已加载数据 | 检查数据结构 |

### C.4 安全机制

- 耗时 > 60 秒的操作弹出确认提示
- 可读/写/执行的文件范围限定在工作目录内
- 工作目录外的文件操作被拦截
- RAM 使用监控，防止 Stata 内存溢出

### C.5 常用 Stata 包（需用户预装）

```stata
ssc install reghdfe        // 高维固定效应回归
ssc install ftools         // reghdfe 依赖
ssc install estout         // 输出回归表格
ssc install winsor2        // 缩尾处理
ssc install ivreg2         // IV 回归
ssc install ranktest       // 弱工具变量检验
ssc install psmatch2       // PSM
ssc install sgmediation    // Sobel 中介检验
ssc install boottest       // Bootstrap 检验
```

AI 在 Phase 4 首次使用 Stata MCP 前，应通过 `stata_run_command` 检查上述包是否安装，提示缺失的包。

---

## 附录 D：通用规则与注意事项

### D.1 阶段间变量传递

- `{{user_level}}`：用户水平（L1/L2/L3），Phase 1 设定，全程继承
- `{{model_framework}}`：最终模型框架，Phase 5 产出，Phase 6-8 继承
- `{{data_path}}`：清洗后数据路径，Phase 3 设定，后续继承
- `{{thesis_outline}}`：论文大纲，Phase 9.3 确认，后续继承
- `{{citation_db}}`：引用数据库，Phase 1-2 构建，Phase 9.6 使用

### D.2 错误处理

- **Stata do file 运行失败**：AI 读取错误日志，定位问题（常见：包缺失/路径错误/变量名不匹配），修复后重试
- **数据读取错误**：检查数据路径、格式、编码
- **文献 PDF 不可读**：提示用户检查 PDF 是否为文字版（非扫描版），建议用 OCR 预处理
- **python-docx 渲染异常**：降级为文本占位，提示用户手动修复

### D.3 L1 新手 mini 教学原则

- 每个核心概念用一句话解释 + 一个类比
- 示例：什么是固定效应？"固定效应就像给每个个体配一个专属截距，控制那些不随时间变化的个体特征（比如管理能力）"
- 用户反问再深入，不要单向灌输
- 默认选项标注为"推荐"
- 所有代码操作分步说明做了什么

### D.4 时间估计

| Phase | 预估耗时 | 用户参与度 |
|-------|----------|-----------|
| Phase 0 | 30 min | 高（环境配置） |
| Phase 1 | 1-2 小时 | 中（提供输入+确认） |
| Phase 2 | 2-4 小时 | 中+（下载文献+确认） |
| Phase 3 | 1-2 小时 | 中（提供数据+确认） |
| Phase 4 | 1-2 小时 | 低（AI 自动运行+解读） |
| Phase 5 | 2-4 小时 | 中（讨论 IV 策略+确认） |
| Phase 6 | 1-2 小时 | 低（AI 自动运行+选择） |
| Phase 7 | 1-2 小时 | 低（AI 自动运行+解读） |
| Phase 8 | 1 小时 | 低（选择维度+确认） |
| Phase 9 | 3-6 小时 | 高（审阅+修改每一章） |

**总预估**：12-24 小时（取决于数据就绪程度和文献获取速度）
