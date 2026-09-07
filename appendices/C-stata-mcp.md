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

mcp-for-stata 提供以下工具（AI 在 Phase 4-8 中使用）。⚠️ **工具名随上游版本演进**（早期版本名为 `stata_run_command` / `stata_run_file` / `stata_get_output` / `stata_list_datasets`，现已更名）；**每次会话开始时先枚举客户端实际暴露的 MCP 工具，与下表不一致时以实际为准并回填本表**：

| 工具名（上游当前核心工具） | 功能 | 使用场景 |
|--------|------|----------|
| `stata_do` | 执行 do-file 并取回日志 | 运行完整回归 do file（Phase 4-8 核心） |
| `read_log` | 读取 Stata 运行日志/输出 | 定位 do-file 报错原因 |
| `get_data_info` | 查看已加载数据的结构与摘要 | 数据加载检查、变量名确认 |
| `help` | 查询 Stata 命令帮助 | 写 do-file 前核对命令语法 |
| `ado_package_install` | 安装 Stata 外部包（通常需显式允许） | 首次安装 reghdfe/estout 等（见 C.5） |

### C.4 安全机制

- 耗时 > 60 秒的操作弹出确认提示
- 可读/写/执行的文件范围限定在工作目录内
- 工作目录外的文件操作被拦截
- RAM 使用监控，防止 Stata 内存溢出

### C.5 常用 Stata 包

AI 在 Phase 4 首次使用 Stata MCP 前，应检查以下包是否安装（缺失时通过 MCP 包安装工具安装，或提示用户在 Stata 中执行 `ssc install ...`）：

```stata
ssc install reghdfe        // 高维固定效应回归
ssc install ftools         // reghdfe 依赖
ssc install estout         // 输出回归表格（esttab/eststo）
ssc install winsor2        // 缩尾处理
ssc install ivreg2         // IV 回归
ssc install ranktest       // 弱工具变量检验
ssc install psmatch2       // PSM
ssc install sgmediation    // Sobel 中介检验
ssc install boottest       // Bootstrap / wild cluster bootstrap
ssc install csdid          // 交叠 DID（Callaway & Sant'Anna, Phase 5）
ssc install bacondecomp    // Goodman-Bacon 分解（Phase 5）
ssc install eventstudyinteract // Sun & Abraham 交互加权估计（Phase 5）
ssc install psacalc        // Oster 检验（reghdfe 估计后请用 psacalc2，见 Phase 5.3）
```

> psacalc2（社区版，支持 reghdfe）不在 SSC 上，需按 GitHub 仓库 ArthurHowardMorris/psacalc_supports_reghdfe 的说明安装。
