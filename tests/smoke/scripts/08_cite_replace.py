"""Phase 9：引用占位符替换与参考文献表生成（GB/T 7714-2015 顺序编码制）。

输入：src/lit_review.md（含 [CIT:key] 或 [CIT:key1;key2] 占位符）、references/citation_db.json
输出：thesis/lit_review_numbered.md（正文编号）、references/reference_list.txt（文末条目）、
      references/citation_order.json（键与编号映射）

规则：按正文首次出现顺序编号；条目格式按附录 A.5，西文作者姓全大写、名缩写无点；
缺失的引用键直接报错，不静默跳过。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"
REVIEW = ROOT / "src" / "lit_review.md"
OUT_MD = ROOT / "thesis" / "lit_review_numbered.md"
OUT_REF = REF / "reference_list.txt"
OUT_ORDER = REF / "citation_order.json"

DB = json.loads((REF / "citation_db.json").read_text(encoding="utf-8"))
text = REVIEW.read_text(encoding="utf-8")

PARTICLES = {"de", "van", "von", "der", "del", "da", "di", "la", "le", "dos"}


def fmt_author(name: str) -> str:
    """西文姓名转「姓全大写 + 名缩写」：默认「名 姓」顺序，保留 de/van 等前缀。"""
    parts = [p for p in name.replace(".", " ").split() if p]
    if not parts:
        return ""
    i = len(parts) - 1
    surname_parts = [parts[i]]
    j = i - 1
    while j >= 0 and parts[j].lower() in PARTICLES:
        surname_parts.insert(0, parts[j])
        j -= 1
    given = parts[: j + 1]
    initials = [p[0].upper() for p in given if p[0].isalpha()]
    surname = " ".join(surname_parts).upper()
    return f"{surname} {''.join(initials)}".strip()


def fmt_entry(n: int, rec: dict) -> str:
    authors = [fmt_author(a) for a in rec.get("authors", []) if a]
    if not authors:
        author_str = "佚名"
    elif len(authors) > 3:
        author_str = ", ".join(authors[:3]) + ", et al"
    else:
        author_str = ", ".join(authors)
    title = (rec.get("title") or "").rstrip(".")
    journal = rec.get("container") or ""
    year = rec.get("year") or ""
    vol = rec.get("volume") or ""
    issue = rec.get("issue") or ""
    fp, lp = rec.get("first_page") or "", rec.get("last_page") or ""
    pages = (fp if fp == lp else f"{fp}-{lp}") if fp and lp else (fp or "")
    loc = f"{vol}({issue})" if vol and issue else (vol or "")
    tail = f"{loc}: {pages}" if loc and pages else (loc or pages or "")
    doi = rec.get("doi") or ""
    body = f"{author_str}. {title}[J]. {journal}, {year}"
    if tail:
        body += f", {tail}"
    body += "."
    if doi:
        body += f" DOI: {doi}."
    return f"[{n}] {body}"


order: dict[str, int] = {}
pattern = re.compile(r"\[CIT:([^\]]+)\]")


def repl(match: re.Match) -> str:
    keys = [k.strip() for k in match.group(1).split(";") if k.strip()]
    nums = []
    for k in keys:
        if k not in DB:
            raise KeyError(f"引用键不存在于 citation_db：{k}")
        if k not in order:
            order[k] = len(order) + 1
        nums.append(order[k])
    nums = sorted(set(nums))
    return "[" + ",".join(str(n) for n in nums) + "]"


numbered = pattern.sub(repl, text)
OUT_MD.write_text(numbered, encoding="utf-8")

entries = [fmt_entry(order[k], DB[k]) for k in sorted(order, key=order.get)]
OUT_REF.write_text("\n".join(entries), encoding="utf-8")
OUT_ORDER.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")

missing_meta = [k for k in order if not DB[k].get("volume")]
print(f"正文引用 {sum(len(v) for v in [re.findall(pattern, text)])} 处，"
      f"唯一文献 {len(order)} 条")
print(f"缺卷期信息 {len(missing_meta)} 条（条目仍可生成，需以 DOI 补全）")
print(f"已写入 {OUT_MD.name} 与 {OUT_REF.name}")
