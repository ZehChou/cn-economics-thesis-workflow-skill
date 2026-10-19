## Phase 0：环境准备

### 契约（每次对话开始时重述一次，30 秒内说完）

> **你只需做两件事：① 把数据交给我（`.dta` / `.xlsx` / `.csv` 均可）；② 在关键节点回答选择题。**
> **其余（检索、清洗、跑回归、解读、成文、排版）我来做，最终交付一份对齐范文格式的 `.docx` 学位论文。**

### Step 0.1：目标对齐与执行后端选择

先确认三件事，一次问完：

```
1. 数据在哪个路径？（示例：D:/thesis/data/raw/xx.xlsx，或直接拖进来）
2. 参考范文放哪了？（可选；有范文时成品的章节结构与排版会对齐它）
3. 计量执行后端（直接回车 = 默认 Python）：
   [默认] Python —— 无需 Stata 许可证、无需 MCP 配置，无需额外配置
   A.     Stata —— 需已装 Stata 16+，会额外配置 Stata MCP（附录 C）
```

写入 `.thesis_state.json` 的 `analysis_backend` 字段（`"python"` / `"stata"`）。

**后端分工**（两者都覆盖 Phase 4-8 全部方法）：

| | 后端 B · Python（默认） | 后端 A · Stata |
|---|---|---|
| 代码真源 | 附录 H | 附录 I |
| 前置依赖 | `pip install` 即可 | Stata 许可证 + `uvx stata-mcp` + SSC 包 |
| 独有能力 | 无 | Goodman-Bacon 分解、rdrobust、csdid |
| 归档 | `scripts/*.py` + `run_all.py` | `do/*.do` + `master.do` |

> 若用户不选，**不应反复追问**：按 Python 继续，并在第一次跑回归前告知"当前用 Python 后端，如需 Stata 可随时切换（附录 I）"。

### Step 0.2：项目文件夹初始化

在工作目录下创建以下结构：

```
project_root/
├── data/raw/                   # 原始数据（只读）
├── cleaned/                    # 清洗后数据（dataset.dta / dataset.csv）
├── scripts/                    # Python 分析脚本（后端 B）
├── do/                         # Stata do files（后端 A）
├── output/
│   ├── tables/                 # 回归表格（.csv / .rtf）
│   └── figures/                # 图形（.png / .pdf）
├── thesis/                     # 论文 docx 输出目录（范文也放这里）
├── references/                 # 文献 PDF + Zotero 导出
├── log/                        # 运行日志 + spec-search.csv
├── .thesis_state.json
├── .gitignore
└── README.md
```

### Step 0.3：依赖检测（按已选后端）与 MCP 配置

#### 后端 B（Python，默认）

**macOS / Linux**：
```bash
python3 --version                       # ≥ 3.9
pip3 list 2>/dev/null | grep -iE "pandas|numpy|scipy|statsmodels|pyfixest|linearmodels|scikit-learn|openpyxl|python-docx|pypdf|pdfplumber"
node --version                          # ≥ 18（仅 Phase 9 走排版路线 N 时需要）
```

**Windows（PowerShell）**：
```powershell
python --version                        # Windows 通常无 python3 别名
python -m pip list | Select-String "pandas|numpy|scipy|statsmodels|pyfixest|linearmodels|scikit-learn|openpyxl|python-docx|pypdf|pdfplumber"
node --version
```

缺什么装什么：

```bash
pip install pandas numpy scipy statsmodels pyfixest linearmodels scikit-learn openpyxl python-docx pypdf pdfplumber
```

装完跑一次接口自检（附录 H.0），把版本写入 `log/env.txt`。**不需要 MCP，跳过本节剩余内容。**

#### 后端 A（Stata，可选）

```bash
uv --version                            # ≥ 0.4.0
stata-mp --version || stata --version   # 或 stata-se / StataMP
uvx stata-mcp doctor                    # 确认路径 / 许可证 / 端点
```

按用户客户端配置 MCP（完整步骤见附录 C）：

| 客户端 | 安装命令 |
|--------|----------|
| Claude Code | `claude mcp add stata-mcp --scope user -- uvx stata-mcp` |
| OpenCode | `uvx stata-mcp install -c opencode` |
| Codex | `uvx stata-mcp install -c codex` |
| 其他 | `uvx stata-mcp install -c <client-name>` |

> 会话开始时先枚举客户端实际暴露的 MCP 工具，与附录 C.3 表格对不上的以实际为准。常见报错处理见附录 D.2。

### Step 0.4：参考范文（成品的"目标形态"）

范文不是装饰，是**验收标准**。问一次即可：

```
有参考范文（.docx 或 .pdf）吗？
有  → 放到 thesis/ 或给路径；我提取：
      ① 章节骨架（几章、每章几节）
      ② 版式参数（页边距、字号、行距、三线表样式、图表编号规则）
      ③ 论证密度（每节大致篇幅、图表数量、参考文献规模）
      ④ 表图呈现方式（回归表是几列、星号与括号标准误的摆放）
没有 → 用附录 A 的 easy-paper 默认版式
```

**提取方法**：
- `.docx`：`python-docx` 读 `styles` 与段落 `runs`，导出 `thesis/_template_spec.json`；
- `.pdf`：`pypdf` 抽目录页与版式特征；扫描版范文需用户提供可复制版本。

> 后续 Phase 9 排版以 `_template_spec.json` 为准；附录 A.2 是**无范文时的默认基准**，两者冲突时以范文为准。
> 范文的**内容**不复制、不改写、不扩写——只学结构与版式（附录 D.5 第 3/7 条）。

### Step 0.5：用户水平确认

```
请选择你的水平（直接回车 = L2）：
  L1. 新手——第一次做实证论文，希望有引导和概念解释
  L2. 有基础——上过计量课，做过基本回归
  L3. 进阶——熟悉高级计量方法，追求深度
```

确认后写入 `user_level`，后续所有决策按此自适应（见附录 D.3）。

### Step 0.6：状态持久化初始化

```json
{
  "user_level": "L2",
  "analysis_backend": "python",
  "current_phase": 0,
  "project_root": ".",
  "data_path": null,
  "model_framework": null,
  "citation_db": {}
}
```

> 每次 Phase 完成后更新此文件；后续启动时读取恢复，避免跨会话丢失。字段说明见附录 D.1。
