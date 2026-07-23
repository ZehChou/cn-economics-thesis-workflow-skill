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

| 仓库 | 定位 | 使用方式 |
|------|------|----------|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | **设计参考**：提取格式参数（字号/行距/三线表/公式编号），在 Phase 9 中作为排版默认配置 |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | **路线 B 工具链**：Phase 9 的 Node.js 路线直接使用其辅助函数模式 |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | **计量执行引擎**：Phase 4-8 通过 MCP 写 do file 并运行 Stata |

### 通用交互模式：计量分析流程

Phase 4-8 共享以下交互循环，各 Phase 仅需指定**方法列表**、**数据检查清单**和**解读模板**：

```
┌─────────────────────────────────────────────────────┐
│ ① 方法推荐 ── AI 基于数据/文献推荐 3-5 种方法       │
│ ② 用户确认 ── 用户选择 1-3 种方法                   │
│ ③ 数据缺口检查 ── 检查所需变量/数据是否就绪          │
│ ④ 写 do file ── 生成 Stata do file 并通过 MCP 执行  │
│ ⑤ 结果解读 ── AI 解读输出并给出结论                  │
│ ⑥ 用户确认 ── 满意 → 下一 Phase / 不满意 → 迭代     │
└─────────────────────────────────────────────────────┘
```

### 状态持久化

每次 Phase 完成后，AI 应将状态写入 `project_root/.thesis_state.json`：

```json
{
  "user_level": "L2",
  "current_phase": 5,
  "model_framework": { "method": "2SLS", "controls": ["..."] },
  "data_path": "cleaned/dataset.dta",
  "citation_db": {}
}
```

后续启动时读取该文件恢复状态，避免跨会话丢失。

---

## 阶段导航

| 阶段 | 文件 | 内容概要 |
|------|------|----------|
| Phase 0 | [phases/00-environment.md](phases/00-environment.md) | 环境准备：依赖检测、项目初始化、Stata MCP 配置 |
| Phase 1 | [phases/01-topic.md](phases/01-topic.md) | 选题与文献定位：用户输入、文献搜索、选题评估报告 |
| Phase 2 | [phases/02-literature.md](phases/02-literature.md) | 文献综述与理论框架：分类精读、综述生成、机制推演 |
| Phase 3 | [phases/03-data.md](phases/03-data.md) | 数据与变量：数据来源、变量构造、描述统计 |
| Phase 4 | [phases/04-baseline.md](phases/04-baseline.md) | 基准回归：方法推荐、do file、结果解读、显著性改善 |
| Phase 5 | [phases/05-endogeneity.md](phases/05-endogeneity.md) | 内生性处理：来源诊断、IV/PSM/DID/GMM 等方法、模型框架确立 |
| Phase 6 | [phases/06-robustness.md](phases/06-robustness.md) | 稳健性检验：替换度量/样本/方法、安慰剂检验 |
| Phase 7 | [phases/07-mechanism.md](phases/07-mechanism.md) | 机制检验：中介效应、调节效应、分组回归 |
| Phase 8 | [phases/08-heterogeneity.md](phases/08-heterogeneity.md) | 异质性分析：分组回归、组间系数差异检验 |
| Phase 9 | [phases/09-writing.md](phases/09-writing.md) | 论文撰写与排版成文：A/B 路线、大纲、正文、图表、排版 |

## 附录导航

| 附录 | 文件 | 内容概要 |
|------|------|----------|
| A | [appendices/A-easypaper-format.md](appendices/A-easypaper-format.md) | easy-paper 格式规范 |
| B | [appendices/B-docx-helper.md](appendices/B-docx-helper.md) | docx 辅助函数接口定义 |
| C | [appendices/C-stata-mcp.md](appendices/C-stata-mcp.md) | Stata MCP 配置与使用指南 |
| D | [appendices/D-general-rules.md](appendices/D-general-rules.md) | 通用规则、变量传递、错误处理、时间估计 |
