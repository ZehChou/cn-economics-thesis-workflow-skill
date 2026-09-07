## Phase 0：环境准备

### Step 0.1：依赖检测

AI 自动检测以下环境是否就绪（按你的操作系统执行对应命令；命令不存在时把报错发给 AI，由 AI 给出本机安装指引）：

**macOS / Linux（bash）**：
```bash
python3 --version                       # 需 ≥ 3.9
pip3 list 2>/dev/null | grep -iE "python-docx|openpyxl|pandas|numpy|matplotlib|seaborn|scipy|statsmodels"
node --version                          # 需 ≥ 18（B 路线）
npm list -g docx 2>/dev/null
uv --version                            # 需 ≥ 0.4.0（mcp-for-stata）
stata-mp --version || stata --version   # 或 stata-se / StataMP
```

**Windows（PowerShell）**：
```powershell
python --version                        # Windows 通常无 python3 别名
python -m pip list | Select-String "python-docx|openpyxl|pandas|numpy|matplotlib|seaborn|scipy|statsmodels"
node --version
npm list -g docx
uv --version
# Stata：Windows 无统一命令行别名，用 GUI 或控制台版（按实际安装路径）：
# & "C:\Program Files\StataMP64\StataMP-64.exe" /version
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
请问你当前使用的是哪个 AI 客户端？

  A. Claude Code（终端版/VS Code 扩展）
  B. OpenCode
  C. Codex Desktop / CLI
  D. 其他（Cursor / Cline / Windsurf 等）
  E. 我还未确定 / 帮我推荐一种
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

### Step 0.6：状态持久化初始化

在项目根目录创建 `.thesis_state.json`，记录当前阶段和配置：

```json
{
  "user_level": "L2",
  "current_phase": 0,
  "project_root": ".",
  "data_path": null,
  "model_framework": null,
  "citation_db": {}
}
```

> 每次 Phase 完成后，AI 应更新此文件。后续启动时读取该文件恢复状态，避免跨会话丢失。
