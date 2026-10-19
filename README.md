# cn-economics-thesis-workflow-skill

**交互式中文经济学实证论文自动化工作流** — 一个 OpenCode / Claude Code / Codex / Cursor 等 AI 客户端的 Skill 包，引导 AI Agent 按 9 阶段交互式流程完成从选题到排版成文的全过程。

> **设计契约**：用户只提供 **数据 + 对选择题的回答**；Agent 负责检索、清洗、跑计量、解读、撰写、排版；交付物是**对齐范文结构与版式的 `.docx` 学位论文**。
> 用户不需要写代码、不需要装 Stata、不需要自己检查数据。

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
- **双计量后端，用户自选**：**Python（默认，零配置）** 或 **Stata（可选，需 MCP）**；两者都覆盖 Phase 4-8 全部方法，代码分别集中在附录 H / I
- **数据即用**：用户给什么用什么，不主动做数据质量审查（除非用户要求）
- **技术栈**：Python（数据清洗 + 计量 + 可视化 + docx 排版）；Stata 仅在显式选择后端 A 时使用
- **三线表 + GB/T 7714 参考文献**：格式规范参照 easy-paper Typst 模板，回归结果直写 docx 三线表
- **范文驱动排版**：提取范文的章节骨架与版式参数作为验收标准；无范文时回退附录 A 默认版式
- **模块化结构**：各 Phase 拆分为独立文件，Phase 只留"做什么/验收什么"，代码集中在附录
- **状态持久化**：通过 `.thesis_state.json` 实现跨会话断点续传（含 `analysis_backend`）
- **文献获取三层**：OpenAlex / Crossref / Semantic Scholar（L0 官方 API）+ Zotero 中文抓取（L1，知网/万方/维普）+ 人工检索（L2）；不内置爬虫与 Sci-Hub
- **前沿计量方法**：交叠 DID、Oster 系数稳定性检验、合成控制法、因果中介分析等
- **审稿人/答辩问答库**：附录集成 12 个常见审稿问题的标准应对策略
- **研究诚信纪律**：附录 D.5 红灯清单禁止 p-hacking / 编造结果 / 无记录换规格 / 静默删样本；回归尝试写入 `log/spec-search.csv` 并全量披露
- **可复现分析脚本**：Python 走 `run_all.py`、Stata 走 `master.do`，均含版本锁定与随机种子记录
- **引用体系自洽**：默认 GB/T 7714 顺序编码制（著者-出版年制可选），`[CIT:]` 占位符按所选体制统一替换，两制不混用

## 内容亮点

### 文献检索（Phase 1-2）
- 三层获取：L0 官方 API（OpenAlex 含摘要与引用网络 / Crossref 补 DOI / Semantic Scholar 补引文）→ L1 Zotero 一键抓知网（机构 IP）→ L2 人工检索
- 文献量按学位层次区分：硕士 40-60 篇 / 博士 80-100 篇；扫描版 PDF 单独标记，不假装精读

### 分析方法（Phase 4-8）
- **双后端等价**：Python（pyfixest / linearmodels）与 Stata（reghdfe / ivreg2 / csdid）产出同一张表结构
- **经济显著性评估**：标准化系数、效应量对比、与文献对标
- **内生性前沿**：交叠 DID、Oster (2019) 检验（Python 侧自实现）、SCM
- **能力边界透明**：Goodman-Bacon 分解、rdrobust 仅后端 A 支持；附录 H.9 有完整对照表
- **机制检验**：主推江艇 (2022) 两步法 + 因果中介分析（Imai et al. 2010）
- **异质性规范**：预先指定分组、多重假设检验校正、全交互 + 交互项检验（不使用不兼容的 suest）

### 写作指导（Phase 9）
- **叙事结构**：每章明确叙事目标（引言→为什么重要，设计→识别策略可信度）
- **写作顺序**：建议"结果先行，引言收尾"，避免反复修改

### 附录体系
- 审稿人/答辩常见问题应对策略（12 个高频问题）
- 分析脚本归档规范（Stata `do/` + Python `scripts/` 双套）
- 通用规则：研究诚信红灯清单（D.5，9 条）、12 类失败模式 fallback、状态字段说明
- 文献获取操作手册（J）：API 代码、Zotero 配置、PDF 提取、合规边界
- 参考文献管理建议（Zotero + Jasminum + GB/T 7714）

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
├── appendices/                     # 附录（10 个）
│   ├── A-easypaper-format.md       # 版式规范（无范文时的默认基准）
│   ├── B-docx-helper.md            # docx 辅助函数接口定义
│   ├── C-stata-mcp.md              # 后端 A：Stata MCP 配置（可选）
│   ├── D-general-rules.md          # 通用规则、状态字段、错误处理
│   ├── E-reviewer-qa.md            # 审稿人/答辩常见问题应对策略
│   ├── F-analysis-archive.md       # 分析脚本归档规范（Stata + Python）
│   ├── G-reference-management.md   # 参考文献管理建议
│   ├── H-analysis-backend-python.md# 后端 B（默认）代码真源
│   ├── I-analysis-backend-stata.md # 后端 A（可选）代码真源
│   └── J-literature-acquisition.md # 文献获取操作手册
├── README.md                       # 本文件
├── opencode.jsonc                  # OpenCode 示例配置
└── .gitignore
```

## 前置依赖

**后端 B · Python（默认，无需其他软件）**

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Python | ≥ 3.9 | 数据清洗、计量、图表、docx 排版 |
| pip 包 | — | `pandas` `numpy` `scipy` `statsmodels` `pyfixest` `linearmodels` `scikit-learn` `openpyxl` `python-docx` `pypdf` `pdfplumber` |
| Node.js | ≥ 18 | 仅 Phase 9 走路线 N（docx-skill-4-cn-paper）时需要 |
| OpenAlex API Key | 免费 | 文献元数据检索（2026-02 起必需，见附录 J.2） |

**后端 A · Stata（可选，仅当用户显式选择时）**

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Stata | ≥ 16 | 核心计量回归 |
| uv | ≥ 0.4.0 | 安装 mcp-for-stata |
| SSC 包 | — | `reghdfe` `ftools` `estout` `ivreg2` `csdid` `bacondecomp` `psacalc2` 等（附录 I.1） |

## 外部参考项目

| 仓库 | 定位 | 使用方式 |
|------|------|----------|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | 提取格式参数作为排版默认配置 |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | Phase 9 路线 N 直接使用其辅助函数模式 |
| [pyfixest](https://github.com/py-econometrics/pyfixest) | Python 高维 FE 回归 | 后端 B 主力估计器（附录 H） |
| [pyalex](https://github.com/J535D165/pyalex) | OpenAlex 客户端 | 文献元数据检索（附录 J.2） |
| [translators_CN](https://github.com/qnscholar/translators_CN) | Zotero 中文抓取器 | 知网/万方/维普一键入库（附录 J.3） |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | 仅后端 A 使用（附录 C） |

## 许可证

MIT
