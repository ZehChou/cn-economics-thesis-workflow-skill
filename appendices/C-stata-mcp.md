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

### C.5 常用 Stata 包

AI 在 Phase 4 首次使用 Stata MCP 前，应通过 `stata_run_command` 检查以下包是否安装：

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
