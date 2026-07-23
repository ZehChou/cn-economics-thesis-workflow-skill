## 附录 G：参考文献管理建议

> 本附录提供 PDF 文献的组织管理和引用建议。

### G.1 推荐工具链

| 工具 | 用途 | 推荐理由 |
|------|------|----------|
| **Zotero** | 参考文献管理（免费开源） | 支持中文文献元数据抓取、PDF 管理、自动生成 GB/T 7714 引用 |
| **Zotero Connector** | 浏览器插件 | 一键从 CNKI/Google Scholar 抓取元数据 |
| **Zotero 插件 - Jasminum** | 增强中文文献管理 | 提升 CNKI 元数据抓取质量 |
| **Better BibTeX for Zotero** | 导出引用键 | 自动生成 `AuthorYear` 格式的引用键 |
| **Mendeley** | 备选参考文献管理 | 有桌面端和 Web 端 |

### G.2 文献组织规范

```
references/ 目录组织结构：
─────────────────────────────────

建议按研究主题分层组织：

references/
├── core/                          # H 级核心文献
│   ├── Autor2013_TradeJobs.pdf
│   ├── Acemoglu2019_AI.pdf
│   └── ...
├── related/                       # M 级相关文献
│   ├── ...
├── background/                    # L 级背景文献
│   └── ...
├── review/                        # 文献综述类文献
│   └── ...
└── methodology/                   # 方法论文献
    └── ...

PDF 文件名格式：{AuthorYear}_{ShortTitle}.pdf
  示例：Autor2013_TradeJobs.pdf
  注意：文件名中不要包含空格 / 特殊字符
```

### G.3 Zotero 配置建议

```
Zotero 配置步骤：
1. 安装 Zotero（https://www.zotero.org/download/）
2. 安装 Zotero Connector 浏览器插件
3. 安装 Jasminum 插件（提升 CNKI 兼容性）
4. 安装 Better BibTeX 插件（自动生成引用键）
5. 设置引用格式：GB/T 7714-2015（在 Zotero 中搜索安装）
6. 设置 Zotero 文件存储路径指向 project_root/references/
```

### G.4 引用格式说明

本 skill 在 Phase 9 中使用 `[CIT:AuthorYear_关键词]` 占位符策略，最终替换为 GB/T 7714 格式引文：

```
GB/T 7714-2015 常见格式：

期刊论文：
  张三, 李四, 王五. 数字化转型对全要素生产率的影响[J]. 经济研究, 2020, 55(1): 45-60.

专著：
  张三. 计量经济学[M]. 北京: 北京大学出版社, 2019.

学位论文：
  李四. 人工智能对劳动力市场的影响研究[D]. 北京: 北京大学, 2022.

英文文献：
  Autor, D. H., Dorn, D., & Hanson, G. H. The China syndrome: Local labor market effects
  of import competition in the United States[J]. American Economic Review, 2013, 103(6): 2121-2168.
```

### G.5 文献检索与去重建议

```
文献管理注意事项：
─────────────────────────────────

1. 去重：同一文献可能从多个渠道下载，下载前先检查是否已存在
   - 检查 references/ 目录中是否已有同名/同作者 PDF
   - 使用 Zotero 的重复文献检测功能

2. 版本跟踪：工作论文可能后续正式发表
   - 优先使用正式发表的版本（有卷期号）
   - 如只有工作论文，标注来源（NBER / SSRN / 作者主页）

3. 补充阅读：在 Phase 2 精读过程中发现的额外文献
   - 及时下载并放入对应分类目录
   - 更新文献知识库
```
