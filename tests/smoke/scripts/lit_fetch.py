"""Phase 1—2 文献获取（L0 官方接口）：OpenAlex 精确短语检索 + 本地相关性过滤。

关键经验（已写入附录 J.2）：宽泛的 `search=` 参数配合按被引排序会产生严重主题漂移
（实测返回癌症、移动边缘计算等高被引但与主题无关的文献）。正确做法是使用
`filter=title_and_abstract.search:"<精确短语>"` 限定主题，再按被引数排序。

输出：
- references/lit_raw.csv       候选池（含摘要、引用数、OA 链接）
- references/citation_db.json  结构化题录（对齐附录 J.5 字段）
- references/lit_summary.txt   检索统计
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
REF.mkdir(parents=True, exist_ok=True)
MAIL = "smoke-test@example.com"

# (标签, 精确短语, 本地必须命中的关键词, 主题定位)
QUERIES = [
    ("Q1", "low-carbon city pilot", ["green innovation", "innovation"], "core"),
    ("Q2", "low-carbon city pilot", [], "core"),
    ("Q3", "environmental regulation", ["innovation"], "context"),
    ("Q4", "financing constraints", ["innovation", "green"], "mechanism"),
    ("Q5", "staggered difference-in-differences", [], "method"),
    ("Q6", "event study", ["treatment", "difference-in-differences"], "method"),
]


def get(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": f"thesis-workflow-smoke/1.0 (mailto:{MAIL})",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def abstract_from_inverted(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def fetch(tag: str, phrase: str, require: list[str], per_page: int = 60) -> list[dict]:
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "filter": f'type:article,publication_year:2010-2026,title_and_abstract.search:"{phrase}"',
        "sort": "cited_by_count:desc",
        "per-page": per_page,
        "mailto": MAIL,
    })
    data = get(url)
    out = []
    for w in data.get("results", []):
        title = re.sub(r"\s+", " ", w.get("title") or "").strip()
        abstract = abstract_from_inverted(w.get("abstract_inverted_index"))
        blob = f"{title} {abstract}".lower()
        if require and not any(k in blob for k in require):
            continue
        src = ((w.get("primary_location") or {}).get("source") or {})
        out.append({
            "tag": tag,
            "phrase": phrase,
            "oa_id": (w.get("id") or "").rsplit("/", 1)[-1],
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "title": title,
            "year": w.get("publication_year"),
            "venue": src.get("display_name") or "",
            "cites": w.get("cited_by_count") or 0,
            "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])],
            "abstract": abstract,
            "oa_url": (w.get("open_access") or {}).get("oa_url") or "",
            "n_refs": len(w.get("referenced_works") or []),
            "volume": (w.get("biblio") or {}).get("volume") or "",
            "issue": (w.get("biblio") or {}).get("issue") or "",
            "first_page": (w.get("biblio") or {}).get("first_page") or "",
            "last_page": (w.get("biblio") or {}).get("last_page") or "",
        })
    return out


rows, report = [], []
for tag, phrase, require, role in QUERIES:
    try:
        got = fetch(tag, phrase, require)
        print(f"{tag} 「{phrase}」+过滤{require} → {len(got)} 条")
        report.append((tag, phrase, role, len(got)))
        rows.extend(got)
    except Exception as exc:  # noqa: BLE001
        print(f"{tag} 失败：{exc}")
    time.sleep(1.2)

df = pd.DataFrame(rows)
print(f"\n候选池 {len(df)} 条")


def norm_title(t: str) -> str:
    return re.sub(r"[\W_]+", "", (t or "").lower())


df["_key"] = df["doi"].where(df["doi"].astype(bool), df["title"].map(norm_title))
df = df.drop_duplicates("_key").sort_values("cites", ascending=False).reset_index(drop=True)
print(f"去重后 {len(df)} 条")

ROLE = {t: rl for t, _, rl, _ in report}


def read_level(r) -> str:
    role = ROLE[r["tag"]]
    if role == "core" and r["cites"] >= 50:
        return "H"
    if role in ("core", "mechanism"):
        return "M"
    if role == "method" and r["cites"] >= 300:
        return "H"
    return "L"


df["read_level"] = df.apply(read_level, axis=1)

STOP = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "with", "from", "by",
        "does", "do", "is", "are", "evidence", "china", "chinese"}


def make_key(r) -> str:
    first = (r["authors"][0].split()[-1] if r["authors"] else "Anon")
    first = re.sub(r"[^A-Za-z]", "", first) or "Anon"
    words = [w for w in re.findall(r"[A-Za-z]+", r["title"].lower()) if w not in STOP]
    tag = "".join(w.capitalize() for w in words[:2])[:18]
    return f"{first}{int(r['year']) if r['year'] else 0}_{tag}"


df["key"] = df.apply(make_key, axis=1)
df["key"] = df["key"] + "_" + df.groupby("key").cumcount().astype(str)

df.to_csv(REF / "lit_raw.csv", index=False, encoding="utf-8-sig")

db = {}
for _, r in df.iterrows():
    db[r["key"]] = {
        "title": r["title"],
        "authors": r["authors"],
        "year": int(r["year"]) if r["year"] else None,
        "container": r["venue"],
        "type": "J",
        "doi": r["doi"],
        "cites": int(r["cites"]),
        "oa_url": r["oa_url"],
        "abstract": r["abstract"],
        "read_level": r["read_level"],
        "tag": r["tag"],
        "volume": r["volume"],
        "issue": r["issue"],
        "first_page": r["first_page"],
        "last_page": r["last_page"],
        "source": "OpenAlex",
        "verified": "题录来自 OpenAlex 官方接口；卷期页码以 DOI 为准，引用前须二次核对",
    }
(REF / "citation_db.json").write_text(
    json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

summary = [
    f"检索式 {len(QUERIES)} 组，候选池 {len(df)} 条",
    "分组命中：" + "；".join(f"{t}={n}" for t, _, _, n in report),
    "阅读分级：" + str(df["read_level"].value_counts().to_dict()),
    f"有摘要 {int((df['abstract'].str.len() > 0).sum())} 条；有 DOI {int(df['doi'].astype(bool).sum())} 条",
    f"年份范围 {int(df['year'].min())}—{int(df['year'].max())}",
]
(REF / "lit_summary.txt").write_text("\n".join(summary), encoding="utf-8")
print("\n".join(summary))
