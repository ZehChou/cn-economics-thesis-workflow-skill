## 附录 J：文献获取（Phase 1-2 操作手册）

> **目标**：让 AI 把"题录 + 全文 + 引用关系"落到本地 `references/` 与 `citation_db`，供精读（Phase 2）与引用替换（Phase 9）使用。
>
> **核心原则**：**不"扒"站点，走授权与开放 API。** 中文论文的瓶颈不是抓取技术，而是全文授权——这个环节只能由用户的机构权限解决，AI 负责把检索式、题录、元数据处理好。

### J.1 三层结构

| 层 | 手段 | 覆盖 | 稳定性 | 默认启用 |
|---|---|---|---|---|
| **L0 元数据 API** | OpenAlex / Crossref / Semantic Scholar | 英文文献题录、摘要、引用网络 | ★★★★★ 官方接口 | ✅ |
| **L1 Zotero 中文抓取** | Zotero + `translators_CN`（CNKI.js 等） | 知网/万方/维普的题录 + PDF（走用户机构 IP） | ★★★★ 依赖页面结构 | ✅ |
| **L2 人工检索** | AI 给检索式 → 用户浏览器检索 → 回贴题录/放 PDF | 全部 | ★★★★★ | ✅ 失败时自动降级 |

**不启用**：Sci-Hub 类批量下载工具、知网爬虫脚本。理由见 J.6。

### J.2 L0：元数据 API

#### J.2.1 OpenAlex（英文主力，含引用网络）

> ⚠️ OpenAlex 自 **2026-02-13** 起要求 API Key。免费注册后每天 100,000 credits（一次列表查询 1 credit），无 key 仅 100 credits/天。
> Key 申请：<https://openalex.org/settings/api>

```bash
pip install pyalex
```

```python
# scripts/lit_openalex.py
import json, pathlib
import pyalex
from pyalex import Works

pyalex.config.api_key = "YOUR_OPENALEX_KEY"
pyalex.config.email = "you@example.com"      # 进入 polite pool，限流更宽松
pyalex.config.max_retries = 3
pyalex.config.retry_http_codes = [429, 500, 503]

# 检索式为精确短语，不是自然语言长句（原因见下方「检索式写法」）
QUERIES = [
    ("核心", "low-carbon city pilot", ["innovation"]),
    ("情境", "environmental regulation", ["innovation"]),
    ("方法", "event study", ["treatment"]),
]

def search(phrase, years="2010-2026", limit=60):
    return (Works()
            .filter(title_and_abstract={"search": phrase},
                    publication_year=years, type="article")
            .sort(cited_by_count="desc")
            .get(per_page=min(limit, 200)))

rows = []
for tag, phrase, require in QUERIES:
    for w in search(phrase):
        title = w.get("title") or ""
        abstract = w.get("abstract", "")          # pyalex 自动解倒排索引
        blob = f"{title} {abstract}".lower()
        if require and not any(k in blob for k in require):
            continue                              # 本地二次过滤，压制主题漂移
        rows.append({
            "tag": tag,
            "title": title,
            "year": w.get("publication_year"),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "cites": w.get("cited_by_count"),
            "oa_url": (w.get("open_access") or {}).get("oa_url"),
            "abstract": abstract,
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
            "volume": (w.get("biblio") or {}).get("volume"),
            "issue": (w.get("biblio") or {}).get("issue"),
            "first_page": (w.get("biblio") or {}).get("first_page"),
            "last_page": (w.get("biblio") or {}).get("last_page"),
            "refs": [r for r in (w.get("referenced_works") or [])],
        })

out = pathlib.Path("references/openalex_raw.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("命中", len(rows), "条 →", out)
```

> ⚠️ **检索式写法（2026-10 端到端测试实测教训）**
>
> ① 不要用宽泛的 `search=` 配合 `sort=cited_by_count:desc`。实测中该组合返回的前 50 条里，
> 大量是与主题无关的高被引文献（癌症综述、移动边缘计算、气候变化健康报告），
> 主题漂移率超过 80%。
>
> ② 正确写法是 `filter=title_and_abstract.search:"<精确短语>"` 限定主题，再按被引排序。
> 同一组测试中，改用精确短语后前 8 条全部切题（碳减排效率、全要素生产率、绿色创新等）。
>
> ③ 短语之外仍需本地关键词过滤（如必须命中 `innovation`），因为 `title_and_abstract.search`
> 是词项匹配而非语义匹配。
>
> ④ 若用 REST 而非 pyalex，等价写法为
> `?filter=type:article,publication_year:2010-2026,title_and_abstract.search:"low-carbon city pilot"&sort=cited_by_count:desc`。

**引用拓扑**（Phase 1 Step 1.2 所需）：`referenced_works` 给"向后追溯"；"向前追溯"用
`Works().filter(cites="W1234567890")`，或直接读该 work 的 `cited_by_count` 与 `cited_by_api_url`。

#### J.2.2 Crossref（补 DOI 与参考文献表，免 key）

```python
import requests

def crossref(q, rows=20):
    r = requests.get("https://api.crossref.org/works", params={
        "query.bibliographic": q, "rows": rows,
        "select": "DOI,title,author,container-title,issued,is-referenced-by-count",
        "mailto": "you@example.com",           # polite pool
    }, timeout=30)
    r.raise_for_status()
    return r.json()["message"]["items"]
```

#### J.2.3 Semantic Scholar（补引用关系与影响力）

```python
def s2(q, limit=20, fields="title,year,authors,venue,citationCount,externalIds,abstract,openAccessPdf"):
    r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
                     params={"query": q, "limit": limit, "fields": fields}, timeout=30)
    if r.status_code == 429:                   # 限流：指数退避，见附录 D.2
        raise RuntimeError("S2 429，退避后改用 Crossref/OpenAlex")
    r.raise_for_status()
    return r.json().get("data", [])
```

#### J.2.4 去重与入库

```python
import re, pandas as pd

def norm_title(t):
    return re.sub(r"[\W_]+", "", (t or "").lower())

def dedup(rows):
    df = pd.DataFrame(rows)
    df["_k"] = df["doi"].fillna("").str.lower().where(df["doi"].astype(bool),
                                                     df["title"].map(norm_title))
    return df.drop_duplicates("_k").sort_values("cites", ascending=False)
```

> 中文文献 DOI 覆盖率低，**统一用"标题归一化"做去重键**，不应只靠 DOI。

### J.3 L1：Zotero 中文抓取（知网/万方/维普）

#### J.3.1 为什么用 Zotero 而不是爬虫

- 走**用户机构 IP 的正常访问**，不触发反爬、不违反数据库协议；
- 拿到的是**结构化真实题录**（作者、刊名、年卷期、页码、DOI、被引），正好喂给 Phase 9 的 `[CIT:]` 替换；
- 中文抓取器 [`qnscholar/translators_CN`](https://github.com/qnscholar/translators_CN) 覆盖 **知网 CNKI.js、万方、维普、百度学术**，README 注明已同步至 Zotero 官方版本库。

#### J.3.2 安装（仅需一次，列入 Phase 0 待办）

```
1. 安装 Zotero 7 与浏览器 Connector 扩展
2. 安装中文抓取器：
   GitHub: qnscholar/translators_CN → 下载 translators/ 下的 .js（CNKI.js、WanFang.js、WeiPu.js 等）
   放入：Zotero → 编辑 → 设置 → 高级 → 文件和文件夹 → 打开数据文件夹 → translators/
   重启 Zotero
3. 新建分类：references/thesis-{题目简称}
```

#### J.3.3 工作流

```
AI 生成 3-5 组中文检索式（含 CSSCI 限定、年份区间、主题词同义扩展）
        ↓
用户在知网检索 → 结果页点 Connector 图标 → 批量入库（含 PDF 附件）
        ↓
Zotero 右键分类 → 导出 → 格式选 CSL JSON（推荐）或 BibTeX → 存 references/zotero_export.json
        ↓
AI 读取导出文件 → 合并进 citation_db
```

```python
# scripts/lit_zotero_import.py
import json, pathlib

raw = json.loads(pathlib.Path("references/zotero_export.json").read_text(encoding="utf-8"))

def to_record(it):
    d = it.get("data", it)
    return {
        "type": d.get("itemType"),
        "title": d.get("title"),
        "authors": [f'{c.get("lastName","")}{c.get("firstName","")}' for c in d.get("creators", [])],
        "container": d.get("publicationTitle") or d.get("bookTitle"),
        "year": (d.get("date") or "")[:4],
        "volume": d.get("volume"), "issue": d.get("issue"), "pages": d.get("pages"),
        "doi": d.get("DOI"), "url": d.get("url"),
        "lang": d.get("language"),
        "extra": d.get("extra"),          # 知网被引、核心期刊标识常在这里
    }

records = [to_record(x) for x in raw]
print("导入", len(records), "条")
```

> 若用户未使用 Zotero：退化为 L2 —— AI 给检索式，用户把题录粘贴回来或把 PDF 放进 `references/`，
> AI 用 J.4 从 PDF 首页抽取元数据。**不应因此中断流程。**

### J.4 全文落地与文本提取

```python
# scripts/pdf_extract.py
import pathlib, re
from pypdf import PdfReader

def extract(p):
    try:
        r = PdfReader(str(p))
        txt = "\n".join((pg.extract_text() or "") for pg in r.pages[:5])
    except Exception as e:
        return None, f"读取失败: {e}"
    if len(re.sub(r"\s", "", txt)) < 200:
        return None, "疑似扫描版（可用文本 < 200 字）→ 需 OCR"
    return txt, "ok"

for p in sorted(pathlib.Path("references").glob("*.pdf")):
    txt, status = extract(p)
    print(f"{p.name:60s} {status}")
```

- 表格密集的文献用 `pdfplumber` 抽表；
- 扫描版 → 提示用户 OCR（Tesseract / Adobe / ABBYY），或由视觉模型逐页读图；
- 命名规范：`{AuthorYear}_{ShortTitle}.pdf`（如 `Autor2013_TradeJobs.pdf`），与 Phase 2 一致。

### J.5 题录 → `citation_db` 字段映射

```json
{
  "key": "Zhang2024_DigitalGreen",
  "title": "数字化转型与企业绿色创新",
  "authors": ["张某某"],
  "year": 2024,
  "container": "某某大学硕士学位论文",
  "type": "D",
  "volume": null, "issue": null, "pages": null,
  "doi": null,
  "pdf": "references/Zhang2024_DigitalGreen.pdf",
  "credibility": "M",
  "read_level": "H",
  "topology": { "cites": ["..."], "cited_by": ["..."] },
  "notes": { "question": "...", "finding": "...", "method": "...", "data": "..." }
}
```

> `type` 用 GB/T 7714 文献类型标识（J/M/D/C/R/EB-OL），Phase 9 替换 `[CIT:]` 时直接取用。
> `credibility` / `read_level` 供 Phase 2 分级精读（H/M/L）。

### J.6 合规与边界（写死在流程里，不得绕过）

| 做法 | 结论 |
|---|---|
| OpenAlex / Crossref / Semantic Scholar 官方 API | ✅ 允许，遵守限流与署名 |
| Zotero 在用户机构 IP 下抓取知网题录与 PDF | ✅ 允许，等同人工逐篇下载 |
| 第三方知网爬虫（Selenium/请求伪造） | ❌ 不写入默认流程：违反数据库用户协议、验证码不可靠、易封 IP |
| Sci-Hub / Anna's Archive 批量下全文 | ❌ 不写入流程：侵权风险，且会把风险传导给使用者 |
| 伪造题录、凭记忆补引用字段 | ❌ 违反附录 D.5 第 3/7 条 |

> 若用户主动要求用上述被禁手段，AI 应说明风险并拒绝执行，改为提供合法的替代路径（机构 VPN、馆际互借、作者主页、预印本）。

### J.7 验收清单

```
□ references/ 下 PDF 命名符合 {AuthorYear}_{ShortTitle}.pdf
□ citation_db 每条都有可核验来源（DOI / 期刊页 / PDF 首页）
□ 英文文献已做引用拓扑（向前 + 向后）
□ 中文文献已标明 CSSCI / 核心 / 其他，用于可信度分级
□ 精读分级 H/M/L 已分配，篇数符合学位层次要求（硕士 40-60 篇）
□ 扫描版 PDF 已列出并交由用户 OCR，未假装精读
□ 无任何条目来自编造或未核验的记忆
```
