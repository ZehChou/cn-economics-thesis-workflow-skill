# cn-economics-thesis-workflow-skill

面向中文经济学实证研究的学位论文工作流 Skill 包，适用于 OpenCode、Claude Code、Codex、Cursor 等支持 Skill 或规则文件的 AI 客户端。包内以九个阶段组织从选题到成文的完整流程，每个阶段包含交互节点、方法清单、验收标准与可复现的分析脚本模板。

## 功能范围

本工作流处理以下环节：

| 环节 | 内容 | 产物 |
|---|---|---|
| 选题 | 主题定位、文献扫描、可行性评估 | 选题评估报告 |
| 文献 | 英文元数据检索、中文题录抓取、分级精读、引用拓扑 | `citation_db`、文献综述初稿 |
| 数据 | 变量推荐、构造脚本、描述性统计 | `cleaned/dataset.dta`、描述统计表与图 |
| 计量 | 基准回归、内生性、稳健性、机制、异质性 | 回归表（`.csv` / `.rtf`）、事件研究图 |
| 成文 | 大纲、正文、三线表、引文替换、版式 | `.docx` 学位论文 |

计量结果的数值来源限定为脚本输出，正文数字与 `output/tables/` 下的文件保持一致。

## 工作流结构

```
Phase 0  环境准备与后端选择
   │
Phase 1  选题与文献定位
   │
Phase 2  文献综述与理论框架
   │
Phase 3  数据与变量
   │
Phase 4  基准回归
   │
Phase 5  内生性处理 ──→ 锁定模型框架
   │
   ├── Phase 6  稳健性检验
   ├── Phase 7  机制检验
   └── Phase 8  异质性分析
   │
Phase 9  论文撰写与排版成文
```

Phase 4 至 Phase 8 共用一套交互循环：方法推荐、节点确认、变量就绪检查、脚本编写与运行、结果解读、结果确认。每个阶段文件只描述任务与验收标准，可运行代码集中在附录 H（Python）与附录 I（Stata）。

## 计量后端

工作流提供两套等价的计量执行后端，在 Phase 0 选择，默认 Python。选择结果写入 `.thesis_state.json` 的 `analysis_backend` 字段，供后续阶段读取。

| 维度 | 后端 B：Python（默认） | 后端 A：Stata（可选） |
|---|---|---|
| 代码位置 | 附录 H | 附录 I |
| 主要依赖 | pyfixest、linearmodels、statsmodels | Stata 16 及以上、mcp-for-stata |
| 回归表输出 | DataFrame 直写 docx 三线表 | esttab 输出 rtf |
| 独有能力 | 无 | Goodman-Bacon 分解、rdrobust、csdid |
| 归档方式 | `scripts/*.py`、`run_all.py` | `do/*.do`、`master.do` |

两套后端的方法覆盖范围与能力差异见附录 H.9。对于 Python 生态缺失的估计量，附录 H.3.4 规定了处理方式：不得以简化估计量静默替代，须向使用者说明并按需切换后端。

## 文献获取

文献获取分三层，按可得性依次降级：

| 层级 | 手段 | 覆盖 | 备注 |
|---|---|---|---|
| L0 | OpenAlex、Crossref、Semantic Scholar 官方接口 | 英文题录、摘要、引用网络 | OpenAlex 自 2026 年 2 月起要求免费 API Key |
| L1 | Zotero 配合 translators_CN 抓取器 | 知网、万方、维普的题录与 PDF | 需机构网络权限 |
| L2 | 生成检索式，由使用者在浏览器中检索 | 全部 | 前两层不可用时采用 |

工作流不包含 Sci-Hub 类全文下载工具，也不包含绕过访问控制的站点爬虫。相关边界见附录 J.6。

## 关键约定

- **研究诚信**：附录 D.5 列明九类禁止行为，包括为达到显著性更换规格、选择性报告稳健性结果、编造数据或文献条目、静默删除观测。所有运行过的规格写入 `log/spec-search.csv`，定稿时全量披露。
- **状态持久化**：阶段进度、变量清单、模型框架、引用库写入 `.thesis_state.json`，支持跨会话续作。
- **版式基准**：提供参考范文时，以其章节结构与版式参数为准；未提供时使用附录 A 的默认版式。
- **引用体系**：默认采用 GB/T 7714—2015 顺序编码制，著者-出版年制为备选，全文只采用一种。正文以 `[CIT:key]` 占位，由脚本统一替换编号并生成条目。
- **数据交接**：仅读取数据结构以确定变量名与类型，不执行数据质量审查；诊断仅在脚本报错或使用者要求时进行。

## 目录结构

```
cn-economics-thesis-workflow-skill/
├── SKILL.md                         # 入口文件：概述与路由
├── phases/                          # 九个阶段的步骤说明
│   ├── 00-environment.md
│   ├── 01-topic.md
│   ├── 02-literature.md
│   ├── 03-data.md
│   ├── 04-baseline.md
│   ├── 05-endogeneity.md
│   ├── 06-robustness.md
│   ├── 07-mechanism.md
│   ├── 08-heterogeneity.md
│   └── 09-writing.md
├── appendices/                      # 附录，共 10 个
│   ├── A-easypaper-format.md        # 版式规范
│   ├── B-docx-helper.md             # docx 辅助函数接口
│   ├── C-stata-mcp.md               # 后端 A 的 MCP 配置
│   ├── D-general-rules.md           # 状态字段、错误处理、研究诚信
│   ├── E-reviewer-qa.md             # 审稿与答辩问答
│   ├── F-analysis-archive.md        # 分析脚本归档规范
│   ├── G-reference-management.md    # 文献管理建议
│   ├── H-analysis-backend-python.md # 后端 B 代码
│   ├── I-analysis-backend-stata.md  # 后端 A 代码
│   └── J-literature-acquisition.md  # 文献获取操作手册
├── tests/smoke/                     # 端到端冒烟测试
├── README.md
├── opencode.jsonc                   # OpenCode 配置示例
└── .gitignore
```

## 安装

将仓库克隆至客户端的 skills 目录。

OpenCode：

```bash
git clone https://github.com/ZehChou/cn-economics-thesis-workflow-skill.git \
  ~/.config/opencode/skills/cn-economics-thesis-workflow-skill
```

Claude Code：

```bash
git clone https://github.com/ZehChou/cn-economics-thesis-workflow-skill.git \
  ~/.claude/skills/cn-economics-thesis-workflow-skill
```

Cline、Cursor、Windsurf 等客户端：将 `SKILL.md` 放置于项目的规则文件路径，或按客户端文档配置引用。

## 使用

客户端加载 `SKILL.md` 后，按其中的路由读取 `phases/` 与 `appendices/` 下的对应文件。Phase 0 依次确认数据路径、参考范文与计量后端，并初始化项目目录与状态文件，随后进入 Phase 1。

## 前置依赖

后端 B（Python，默认）：

| 依赖 | 版本 | 用途 |
|---|---|---|
| Python | ≥ 3.9 | 数据清洗、计量、图表、docx 排版 |
| pip 包 | — | pandas、numpy、scipy、statsmodels、pyfixest、linearmodels、scikit-learn、openpyxl、python-docx、pypdf、pdfplumber |
| Node.js | ≥ 18 | 仅在 Phase 9 采用路线 N（docx-skill-4-cn-paper）时需要 |
| OpenAlex API Key | 免费 | 文献元数据检索，2026 年 2 月起必需，申请方式见附录 J.2 |

后端 A（Stata，可选）：

| 依赖 | 版本 | 用途 |
|---|---|---|
| Stata | ≥ 16 | 计量回归 |
| uv | ≥ 0.4.0 | 安装 mcp-for-stata |
| SSC 包 | — | reghdfe、ftools、estout、ivreg2、csdid、bacondecomp、psacalc2 等，清单见附录 I.1 |

## 测试

`tests/smoke/` 提供一次端到端冒烟测试，使用合成面板数据（500 家企业、6191 个观测）覆盖 Phase 3 至 Phase 9，并由子代理模拟节点选择。测试结果与缺陷记录见 `tests/smoke/REPORT.md`。

```bash
cd tests/smoke
python scripts/gen_data.py
python scripts/run_all.py            # 需联网，约 2 至 3 分钟
python scripts/run_all.py --offline  # 复用已有文献快照
```

## 已知限制

- 中文文献全文的获取依赖机构订阅，工作流只提供检索式与抓取工具，不代为获取。
- 后端 B 无法产出 Sun–Abraham 总体处理效应与 Callaway–Sant'Anna 估计量，相关表格需使用后端 A。
- 冒烟测试的正文篇幅约为学位论文要求的十分之一，用于验证结构与数值贯通，不用于验证写作质量。
- 参考文献条目由官方接口题录生成，卷期页码与作者拼写仍需以原文核对。

## 外部参考项目

| 项目 | 定位 | 用途 |
|---|---|---|
| [easy-paper](https://github.com/Dawnfz-Lenfeng/easy-paper) | Typst 中文论文模板 | 版式参数的参考来源 |
| [docx-skill-4-cn-paper](https://github.com/Gostyan/docx-skill-4-cn-paper) | Node.js docx 辅助函数集 | Phase 9 路线 N |
| [pyfixest](https://github.com/py-econometrics/pyfixest) | Python 高维固定效应回归 | 后端 B 的估计器 |
| [pyalex](https://github.com/J535D165/pyalex) | OpenAlex 客户端 | 文献元数据检索 |
| [translators_CN](https://github.com/qnscholar/translators_CN) | Zotero 中文站点抓取器 | 中文题录与 PDF 入库 |
| [mcp-for-stata](https://github.com/SepineTam/mcp-for-stata) | Stata MCP 服务器 | 后端 A |

## 许可证

MIT
