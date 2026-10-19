---
name: economics-thesis
description: 经济学实证论文自动化工作流——从选题到排版成文的全流程交互式指导
---

# 经济学实证论文自动化工作流 (Economics Thesis Workflow)

## 概述

本 Skill 定义了一套**分步骤交互式**工作流，让 AI Agent 引导用户从零完成一篇完整的中文经济学实证学位论文。

### 核心契约（设计目标，所有改动朝此对齐）

> **用户只提供两样东西：数据 + 对选择题的回答。**
> **Agent 负责其余全部：检索文献、清洗数据、跑计量、解读结果、撰写正文、排版成文。**
> **交付物是一份对齐范文结构与版式的 `.docx` 学位论文。**

一切设计取舍以此为准：

- **不让用户写代码、不应求用户装环境、不做数据质量审查**（用户给什么就用什么，除非用户主动要求）；
- **能自动的绝不追问**，只在真正需要判断的节点设 CHECKPOINT（选方法、定变量、认模型、选稳健性、定异质性维度、认大纲）；
- **代码不是给用户看的**，是给 Agent 跑的——因此集中放附录，Phase 只讲"做什么、验收什么"。

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
| **L1（新手）** | 第一次做实证论文，需要 mini 教学 | 每个阶段解释核心概念（点到为止，用户反问再深入）；推荐执行路径偏保守（默认选项）；提示每一步的常见问题 |
| **L2（有基础）** | 有计量经济学基础，做过基本回归 | 跳过概念解释；直接输出方案和技术细节；用户自主选择分支 |
| **L3（进阶）** | 熟悉高级计量方法，追求深度 | 推荐前沿方法（如异质性处理效应、机器学习辅助 IV）；讨论模型识别假设的深层问题；提供更多自定义选项 |

### 外部参考仓库与工具链

| 仓库/工具 | 定位 | 使用方式 |
|------|------|----------|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | **设计参考**：格式参数作为无范文时的排版默认值（附录 A） |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | **排版路线 N**：Phase 9 直接使用其辅助函数模式（附录 B） |
| [pyfixest](https://github.com/py-econometrics/pyfixest) | Python 高维固定效应回归 | **后端 B 主力**：`feols` 对应 reghdfe，`sunab` 对应 Sun–Abraham（附录 H） |
| [pyalex](https://github.com/J535D165/pyalex) | OpenAlex 客户端 | **文献元数据 L0**：题录、摘要、引用网络（附录 J.2） |
| [translators_CN](https://github.com/qnscholar/translators_CN) | Zotero 中文抓取器 | **中文文献 L1**：知网/万方/维普一键入库（附录 J.3） |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | **后端 A（可选）**：仅当用户显式选择 Stata 时才配置（附录 C/I） |

### 通用交互模式：计量分析流程

Phase 4-8 共享以下交互循环，各 Phase 仅需指定**方法列表**、**数据检查清单**和**解读模板**：

```
┌──────────────────────────────────────────────────────────┐
│ ① 方法推荐 ── AI 基于数据/文献推荐 3-5 种方法            │
│ ② 🔴 CHECKPOINT 用户确认 ── 用户选择 1-3 种方法          │
│ ③ 变量就绪检查 ── 确认所需变量能定位到（不做质量审查）    │
│ ④ 写分析脚本并运行 ── 后端 B: scripts/*.py（附录 H）     │
│                     后端 A: do/*.do（附录 I）            │
│    🛟 失败分支：读错误栈修复重试；同一错误连续 2 次 → 暂停，│
│    交用户确认数据结构/环境（错误处理见附录 D.2）          │
│ ⑤ 结果解读 ── AI 解读输出并给出结论                       │
│ ⑥ 🔴 CHECKPOINT 用户确认 ── 满意 → 下一 Phase；           │
│    不满意 → 回到 ①（先把本轮规格记入 log/spec-search.csv，│
│    禁止无记录地换规格；研究诚信红线见附录 D.5）            │
└──────────────────────────────────────────────────────────┘
```

### 状态持久化

每次 Phase 完成后，AI 应将状态写入 `project_root/.thesis_state.json`：

```json
{
  "user_level": "L2",
  "analysis_backend": "python",
  "current_phase": 5,
  "model_framework": { "method": "TWFE", "fe": ["id", "year"], "cluster": "id" },
  "data_path": "cleaned/dataset.dta",
  "citation_db": {}
}
```

> `analysis_backend` 决定 Phase 4-8 取附录 H（`python`，默认）还是附录 I（`stata`）。
> 字段含义见附录 D.1。

后续启动时读取该文件恢复状态，避免跨会话丢失。

---

## 阶段导航

| 阶段 | 文件 | 内容概要 |
|------|------|----------|
| Phase 0 | [phases/00-environment.md](phases/00-environment.md) | 环境准备：契约对齐、**执行后端选择**、依赖检测、范文提取、状态初始化 |
| Phase 1 | [phases/01-topic.md](phases/01-topic.md) | 选题与文献定位：用户输入、文献搜索、选题评估报告 |
| Phase 2 | [phases/02-literature.md](phases/02-literature.md) | 文献综述与理论框架：分类精读、综述生成、机制推演 |
| Phase 3 | [phases/03-data.md](phases/03-data.md) | 数据与变量：数据来源、变量构造、描述统计 |
| Phase 4 | [phases/04-baseline.md](phases/04-baseline.md) | 基准回归：方法推荐、分析脚本（附录 H/I）、结果解读、显著性改善 |
| Phase 5 | [phases/05-endogeneity.md](phases/05-endogeneity.md) | 内生性处理：来源诊断、IV/PSM/DID/GMM 等方法、模型框架确立 |
| Phase 6 | [phases/06-robustness.md](phases/06-robustness.md) | 稳健性检验：替换度量/样本/方法、安慰剂检验 |
| Phase 7 | [phases/07-mechanism.md](phases/07-mechanism.md) | 机制检验：中介效应、调节效应、分组回归 |
| Phase 8 | [phases/08-heterogeneity.md](phases/08-heterogeneity.md) | 异质性分析：预先指定维度、全交互 + 交互项检验、多重检验校正 |
| Phase 9 | [phases/09-writing.md](phases/09-writing.md) | 论文撰写与排版成文：排版路线 P/N、大纲、正文、图表、排版 |

## 附录导航

| 附录 | 文件 | 内容概要 |
|------|------|----------|
| A | [appendices/A-easypaper-format.md](appendices/A-easypaper-format.md) | 版式规范（无范文时的默认基准） |
| B | [appendices/B-docx-helper.md](appendices/B-docx-helper.md) | docx 辅助函数接口定义 |
| C | [appendices/C-stata-mcp.md](appendices/C-stata-mcp.md) | **后端 A** 的 Stata MCP 配置（仅选 Stata 时需要） |
| D | [appendices/D-general-rules.md](appendices/D-general-rules.md) | 通用规则、状态字段、错误处理、时间估计、研究诚信红线 |
| E | [appendices/E-reviewer-qa.md](appendices/E-reviewer-qa.md) | 审稿人/答辩常见问题应对策略 |
| F | [appendices/F-analysis-archive.md](appendices/F-analysis-archive.md) | 分析脚本归档规范（Stata `do/` + Python `scripts/`） |
| G | [appendices/G-reference-management.md](appendices/G-reference-management.md) | 参考文献管理建议 |
| **H** | [appendices/H-analysis-backend-python.md](appendices/H-analysis-backend-python.md) | **后端 B（默认）代码真源**：Phase 4-8 全套 Python |
| **I** | [appendices/I-analysis-backend-stata.md](appendices/I-analysis-backend-stata.md) | **后端 A（可选）代码真源**：Phase 4-8 全套 Stata |
| **J** | [appendices/J-literature-acquisition.md](appendices/J-literature-acquisition.md) | 文献获取：OpenAlex/Crossref/S2 + Zotero 中文抓取 + PDF 提取 |

### 代码真源规则（避免两份代码漂移）

```
Phase 4-8 的 .md 文件里不出现可运行代码。
所有代码只在两个附录里维护：
  后端 B → 附录 H（默认）      后端 A → 附录 I（可选）
Phase 文件只保留：方法列表 / CHECKPOINT / 表格形态 / 解读模板 / 验收清单
```
