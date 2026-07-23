# cn-economics-thesis-workflow-skill

**交互式中文经济学实证论文自动化工作流** — 一个 OpenCode / Claude Code / Codex / Cursor 等 AI 客户端的 Skill 包，引导 AI Agent 按 9 阶段交互式流程辅助用户完成从选题到排版成文的全过程。

## 工作流总览

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

## 核心特性

- **分步骤交互式**：每个阶段先问再回答再生成，用户全程主导
- **三档用户自适应**：L1 新手（含 mini 教学）/ L2 有基础 / L3 进阶
- **技术栈**：Python（数据清洗+可视化）+ Stata（核心计量 MCP）+ python-docx / Node.js（排版）
- **三线表 + GB/T 7714 参考文献**：格式规范参照 easy-paper Typst 模板
- **A/B 双路线排版**：Phase 9 支持 Python python-docx 或 Node.js docx-skill-4-cn-paper 两种方案
- **Stata MCP 集成**：通过 `mcp-for-stata` 在 Agent 中直接写 do file 并运行
- **模块化结构**：各 Phase 拆分为独立文件，降低单文件复杂度，提升维护性
- **状态持久化**：通过 `.thesis_state.json` 实现跨会话断点续传

## 安装

### 克隆到 skills 目录

**OpenCode 用户：**

```bash
git clone https://github.com/ZehChou/cn-economics-thesis-workflow-skill.git \
  ~/.config/opencode/skills/cn-economics-thesis-workflow-skill
```

**Claude Code 用户：**

```bash
git clone https://github.com/ZehChou/cn-economics-thesis-workflow-skill.git \
  ~/.claude/skills/cn-economics-thesis-workflow-skill
```

**Cline / Cursor / Windsurf 等其他客户端：**

将 `SKILL.md` 内容复制或引用到你的项目根目录，或按客户端指南配置规则文件路径。

### 使用方式

在对话中，Agent 会根据 `SKILL.md` 中的指令自动进入交互流程，从 Phase 0 开始引导你完成全部环节。各 Phase 的详细步骤存储在 `phases/` 目录中，附录信息存储在 `appendices/` 目录中。

## 项目结构

```
cn-economics-thesis-workflow-skill/
├── SKILL.md                        # 主入口：概述 + 路由（Agent 加载此文件）
├── phases/                         # 各阶段详细步骤
│   ├── 00-environment.md           # Phase 0：环境准备
│   ├── 01-topic.md                 # Phase 1：选题与文献定位
│   ├── 02-literature.md            # Phase 2：文献综述与理论框架
│   ├── 03-data.md                  # Phase 3：数据与变量
│   ├── 04-baseline.md              # Phase 4：基准回归
│   ├── 05-endogeneity.md           # Phase 5：内生性处理
│   ├── 06-robustness.md            # Phase 6：稳健性检验
│   ├── 07-mechanism.md             # Phase 7：机制检验
│   ├── 08-heterogeneity.md         # Phase 8：异质性分析
│   └── 09-writing.md               # Phase 9：论文撰写与排版成文
├── appendices/                     # 附录
│   ├── A-easypaper-format.md       # easy-paper 格式规范
│   ├── B-docx-helper.md            # docx 辅助函数接口定义
│   ├── C-stata-mcp.md              # Stata MCP 配置与使用指南
│   └── D-general-rules.md          # 通用规则、变量传递、错误处理
├── README.md                       # 本文件
├── opencode.jsonc                  # OpenCode 示例配置
└── .gitignore
```

## 前置依赖

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Python | ≥ 3.9 | 数据清洗、图表生成、A 路线排版 |
| Node.js | ≥ 18 | B 路线排版（可选） |
| Stata | ≥ 16 | 核心计量回归（需正版许可证） |
| uv | ≥ 0.4.0 | 安装 mcp-for-stata |
| pip | — | `python-docx`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `openpyxl` |
| npm | — | `docx`, `temml`, `fast-xml-parser`（B 路线） |

## 外部参考项目

| 仓库 | 定位 | 使用方式 |
|------|------|----------|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | 提取格式参数作为排版默认配置 |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | Phase 9 B 路线直接使用其辅助函数模式 |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | Phase 4-8 通过 MCP 写 do file 并运行 Stata |

## 许可证

MIT
