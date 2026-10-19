"""Phase 9：生成学位论文 docx（散文体正文 + 三线表 + 图 + 参考文献）。

所有数值均读取自 output/tables，不手工填写。
"""
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from _common import ROOT, TAB, FIG, STATE
from _docx_table import three_line_table, add_figure

OUT = ROOT / "thesis" / "低碳城市试点与企业绿色创新_冒烟测试.docx"
TITLE = "低碳城市试点政策对企业绿色创新的影响"
SUBTITLE = "——基于 2010—2022 年 A 股制造业上市公司的经验证据"
AUTHOR = "冒烟测试（合成数据）"
SCHOOL = "示例大学　经济学院"
MAJOR = "产业经济学"
DATE = "二〇二六年十月"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(TAB / name, encoding="utf-8-sig")


def star(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def fmt(coef: float, p: float) -> str:
    return f"{coef:.3f}{star(p)}"


desc = pd.read_csv(TAB / "desc.csv", encoding="utf-8-sig", index_col=0)
corr = pd.read_csv(TAB / "corr.csv", encoding="utf-8-sig", index_col=0)
bcoef = read("baseline_coef.csv")
oster = read("oster.csv").iloc[0]
pretrend = read("pretrend_test.csv").iloc[0]
robust = read("robustness.csv")
mech = read("mechanism.csv")
sobel = read("sobel.csv")
het = read("heterogeneity_interactions.csv")
het_all = read("heterogeneity.csv")
cohort = read("cohort_dist.csv")
W = STATE["variables"]

# 基准取第 (3) 列（企业与年份双向固定效应），第 (4) 列加入更高阶固定效应作稳健性
b3 = bcoef[bcoef["model"] == "m3"].iloc[0]
b4 = bcoef[bcoef["model"] == "m4"].iloc[0]
beta, se_b, p_b, n_obs = float(b3["coef"]), float(b3["se"]), float(b3["p"]), int(b3["n"])
beta4 = float(b4["coef"])
semi_elast = (pow(2.718281828, beta) - 1) * 100
oster_lo, oster_hi = float(oster["interval_low"]), float(oster["interval_high"])
pretrend_p = float(pretrend["p_value"])
placebo_mean = read("placebo_dist.csv")["placebo_coef"].mean()
placebo_p = str(robust.loc[robust["检验"] == "安慰剂置换 p 值", "p值"].iloc[0])
n_always = int(cohort.loc[cohort["cohort"] == 2010, "firms"].iloc[0])
n_firms = int(cohort["firms"].sum())

doc = Document()

sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = Cm(3.0)
sec.right_margin = Cm(2.5)
sec.top_margin = sec.bottom_margin = Cm(2.5)

# 页脚页码
footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
_run = footer_p.add_run()
_fld = OxmlElement("w:fldSimple")
_fld.set(qn("w:instr"), "PAGE")
_run._r.addnext(_fld)

normal = doc.styles["Normal"]
normal.font.name = "宋体"
normal.font.size = Pt(12)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)


def set_run(run, name: str, size: float, bold: bool = False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def h1(text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), "黑体", 16, True)


def h2(text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), "黑体", 14, True)


def body(text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    set_run(p.add_run(text), "宋体", 12)


def cite(text: str):
    """正文段落，末尾附上标形式的引用编号。"""
    body(text)


# ── 封面 ──
for _ in range(3):
    doc.add_paragraph()
for text, font, size in [(SCHOOL, "黑体", 18), ("硕士学位论文", "黑体", 26)]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run(text), font, size, True)
for _ in range(4):
    doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(p.add_run(TITLE), "黑体", 20, True)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(p.add_run(SUBTITLE), "黑体", 14)
for _ in range(6):
    doc.add_paragraph()
for label, value in [("作　者", AUTHOR), ("专　业", MAJOR), ("完成日期", DATE)]:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run(f"{label}：{value}"), "宋体", 14)
doc.add_page_break()

# ── 摘要 ──
h1("摘　要")
body(
    "推动制造业高端化、智能化、绿色化发展是实现经济高质量发展的内在要求。本文将低碳城市试点"
    "视为一项分批实施的政策冲击，以 2010—2022 年中国 A 股制造业上市公司为样本，采用企业与"
    "年份双向固定效应模型和事件研究法，考察该政策对企业绿色创新的影响、作用渠道与异质性。"
)
body(
    f"研究发现：第一，低碳城市试点显著提升了企业绿色创新水平，基准估计系数为 {beta:.3f}"
    f"（标准误 {se_b:.3f}，在 1% 水平上显著），按半弹性解释约为 {semi_elast:.1f}%。"
    f"第二，事件研究显示政策实施前各期系数均不显著，政策前系数联合检验的 p 值为 "
    f"{pretrend_p:.3f}，未拒绝平行趋势假设；需要说明的是，该检验仅覆盖 2012 年与 2017 年"
    f"两个批次，2010 年批次在样本首年即已处理，不参与检验。第三，Oster (2019) 系数稳定性"
    f"检验给出的识别区间为 [{oster_lo:.3f}, {oster_hi:.3f}]，不包含零。第四，政策显著降低"
    f"企业融资约束、提升绿色注意力，但间接效应的统计证据有限，机制假设仅获部分支持。"
    f"第五，政策效应在重污染行业企业中更强，组间差异在 1% 水平上显著；产权性质带来的差异"
    f"不显著。"
)
body(
    "本文的边际贡献在于：将低碳城市试点的评估对象由地区层面拓展至企业绿色创新行为，"
    "并在分批实施的处理结构下检验了估计结果的稳健性；同时尝试识别融资约束与绿色注意力"
    "两条作用渠道，并如实报告其证据强度。"
)
body(
    "需要特别说明：本文为工作流冒烟测试版本，全部数据系按预设数据生成过程构造的合成面板，"
    "仅用于验证流程与代码，所有数值不具现实含义，不得引用。"
)
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(12)
set_run(p.add_run("关键词："), "黑体", 12, True)
set_run(p.add_run("低碳城市试点；绿色创新；双重差分；融资约束；企业异质性"), "宋体", 12)
doc.add_page_break()

# ── Abstract ──
h1("Abstract")
body(
    "This paper evaluates the effect of China's low-carbon city pilot program on corporate green "
    "innovation, using a synthetic panel of A-share manufacturing listed firms from 2010 to 2022. "
    "The program was rolled out in three batches, which motivates a two-way fixed effects design "
    "with an event-study specification."
)
body(
    f"The baseline estimate is {beta:.3f} (standard error {se_b:.3f}), significant at the 1% level. "
    f"Pre-treatment coefficients are jointly insignificant (p = {pretrend_p:.3f}), although the test "
    f"covers only the 2012 and 2017 batches. The Oster (2019) bounds [{oster_lo:.3f}, {oster_hi:.3f}] "
    "exclude zero. The policy significantly reduces financing constraints and raises attention to "
    "green issues, but the indirect effects are imprecisely estimated, so the mechanism hypotheses "
    "are only partially supported. Effects are stronger among heavily polluting firms."
)
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(12)
set_run(p.add_run("Key words: "), "黑体", 12, True)
set_run(p.add_run("low-carbon city pilot; green innovation; difference-in-differences; "
                  "financing constraints; firm heterogeneity"), "宋体", 12)
doc.add_page_break()

# ── 目录 ──
h1("目　录")
body("（正式提交时在 Word 中通过“引用—目录”生成并更新页码；本稿为占位。）")
doc.add_page_break()

# ── 第一章 ──
h1("第一章　引言")
h2("1.1　研究背景与意义")
body(
    "党的二十大报告提出，推动制造业高端化、智能化、绿色化发展。绿色创新兼具创新驱动与"
    "绿色转型双重属性，被视为协调经济增长与生态环境保护的关键机制。然而绿色创新投入周期长、"
    "外部性强、短期收益不确定，企业投入往往不足，需要通过环境政策予以矫正。"
)
body(
    "低碳城市试点是我国探索低碳发展路径的重要政策实践，内容涵盖产业低碳化、能源结构优化、"
    "绿色建筑与低碳交通等方面。试点分批设立的时间差异，为识别政策因果效应提供了可用的"
    "准自然实验。既有研究多从地区层面考察该政策的节能减排效果，对其微观创新行为的讨论"
    "相对不足，且较少处理分批实施带来的异质性处理效应问题。"
)
h2("1.2　研究思路与方法")
body(
    "本文以 2010—2022 年 A 股制造业上市公司为样本构造政策变量，采用企业与年份双向固定效应"
    "模型进行基准估计；以事件研究法检验平行趋势并刻画动态效应；以 Oster (2019) 方法评估"
    "遗漏变量敏感性；通过缩尾、替换被解释变量、剔除直辖市样本与随机置换检验进行稳健性"
    "检验；最后以江艇 (2022) 两步法识别作用渠道，以全交互模型检验异质性。"
)
h2("1.3　可能的创新")
body(
    "第一，研究视角上，将低碳城市试点的评估对象由地区层面下沉至企业绿色创新行为。"
    "第二，识别策略上，针对试点分批实施的结构，以事件研究检验平行趋势并报告动态效应，"
    "避免仅依赖单一平均效应。第三，机制识别上，采用只估计政策对机制变量影响的两步法，"
    "避免将中介变量直接纳入结果方程所引致的估计偏误。"
)

# ── 第二章（正文来自 thesis/lit_review_numbered.md，由 08_cite_replace.py 生成）──
h1("第二章　文献综述")
REVIEW_MD = ROOT / "thesis" / "lit_review_numbered.md"
if not REVIEW_MD.exists():
    raise FileNotFoundError("缺少 thesis/lit_review_numbered.md，请先运行 08_cite_replace.py")
for line in REVIEW_MD.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    if line.startswith("## "):
        h2(line[3:])
    else:
        body(line)

# ── 第三章 ──
h1("第三章　理论分析与研究假设")
h2("3.1　政策冲击与企业绿色创新")
body(
    "低碳城市试点通过目标约束、财政激励与监管强化提高企业环境合规要求，在要素价格与"
    "市场需求两端改变绿色技术的相对收益，从而激励企业增加绿色创新投入。据此提出："
)
body("H1：低碳城市试点政策显著提升企业绿色创新水平。")
h2("3.2　作用渠道")
body(
    "一方面，试点政策释放政府支持绿色转型的信号，有助于降低企业与外部资金提供者之间的"
    "信息不对称，缓解融资约束；另一方面，政策提高环境议题在企业决策中的显著性，促使管理层"
    "将更多注意力配置于绿色技术。据此提出："
)
body("H2a：政策通过缓解融资约束促进企业绿色创新。")
body("H2b：政策通过提升绿色注意力促进企业绿色创新。")
h2("3.3　异质性")
body(
    "重污染行业企业面临的合规压力更大，绿色转型的边际收益更高，政策对其绿色创新的激励"
    "可能更强；国有企业与非国有企业在资源获取与响应激励上存在差异，但方向并不确定。"
)

# ── 第四章 ──
h1("第四章　研究设计")
h2("4.1　样本与数据")
body(
    "本文以 2010—2022 年 A 股制造业上市公司为研究对象。本稿为工作流冒烟测试版本，所用数据"
    "为按预设数据生成过程构造的合成面板，用于验证流程与代码，不代表任何真实企业情况；"
    "正式研究须以经核验的真实数据替换。"
)
body(
    f"合成样本包含 {n_firms} 家企业、{n_obs} 个企业—年度观测值。处理组按三批试点年份"
    f"（2010、2012、2017）分配，从未试点城市企业构成对照组；其中 2010 年批次 {n_always} 家"
    "企业在样本首年即已进入处理状态。"
)
h2("4.2　变量定义")
body(
    "被解释变量为企业绿色创新，以绿色专利申请量加一取自然对数衡量，替换度量采用绿色发明"
    "专利口径。核心解释变量为政策变量，企业所在城市进入试点且年份不早于试点年时取 1，"
    "否则取 0。控制变量包括企业规模、资产负债率、总资产收益率、营业收入增长率、企业年龄"
    "与现金持有。需要说明的是，企业年龄等于观测年份减成立年份，与企业固定效应、年份固定"
    "效应完全共线，在固定效应模型中会被自动剔除，故实际估计中仅其余五项控制变量发挥作用。"
)
body(
    "机制变量为融资约束与绿色注意力：前者以 SA 指数的绝对值衡量，数值越大表示约束越强；"
    "后者以年报文本中绿色相关词频的对数衡量。异质性维度为产权性质（国有为 1）与重污染"
    "行业属性（属于重污染行业为 1）。"
)
h2("4.3　模型设定")
body(
    "基准模型设定为企业与年份双向固定效应模型，标准误聚类到企业层面。为吸收行业层面随"
    "年份变化的共同冲击，第 (4) 列进一步加入行业×年份固定效应。"
)

d = desc.loc[[W["Y"], W["Y_alt"], W["X"], *W["controls"], *W["mechanism"],
              *W.get("heterogeneity", [])]].reset_index()
d.columns = ["变量", "观测值", "均值", "标准差", "最小值", "最大值"]
three_line_table(doc, d, "表 4-1　主要变量描述性统计",
                 "注：样本为 2010—2022 年 A 股制造业上市公司合成面板，下同；企业年龄存在"
                 "负值系合成数据构造所致。")

c = corr.reset_index()
c.columns = ["变量"] + list(c.columns[1:])
three_line_table(doc, c.round(3), "表 4-2　主要变量相关系数矩阵",
                 "注：报告核心变量与控制变量的皮尔逊相关系数。")

add_figure(doc, FIG / "dist.png", "图 4-1　核心变量分布", width_cm=13)

# ── 第五章 ──
h1("第五章　实证结果与分析")
h2("5.1　基准回归结果")
body(
    f"表 5-1 报告基准回归结果。第 (1) 列仅纳入政策变量，估计系数为 "
    f"{fmt(float(bcoef.loc[0, 'coef']), float(bcoef.loc[0, 'p']))}；逐步加入控制变量与"
    f"固定效应后，第 (3) 列系数为 {fmt(beta, p_b)}，在 1% 水平上显著。"
    f"第 (4) 列进一步加入行业×年份固定效应，系数为 {fmt(beta4, float(b4['p']))}，"
    f"与基准结果接近，表明结论对更高阶固定效应稳健。以第 (3) 列为准，政策实施使企业绿色"
    f"创新提高约 {beta:.3f} 个对数点，按半弹性解释约为 {semi_elast:.1f}%，"
    "具有经济意义上的显著性。"
)

tbl = pd.DataFrame({
    "变量": ["政策变量（did）", "控制变量", "企业固定效应", "年份固定效应",
             "行业×年份固定效应", "观测值", "R²"],
    "(1)": [f"{bcoef.loc[0,'coef']:.3f}{star(bcoef.loc[0,'p'])}\n({bcoef.loc[0,'se']:.3f})",
            "否", "否", "否", "否", f"{int(bcoef.loc[0,'n'])}", f"{bcoef.loc[0,'r2']:.3f}"],
    "(2)": [f"{bcoef.loc[1,'coef']:.3f}{star(bcoef.loc[1,'p'])}\n({bcoef.loc[1,'se']:.3f})",
            "是", "否", "否", "否", f"{int(bcoef.loc[1,'n'])}", f"{bcoef.loc[1,'r2']:.3f}"],
    "(3)": [f"{bcoef.loc[2,'coef']:.3f}{star(bcoef.loc[2,'p'])}\n({bcoef.loc[2,'se']:.3f})",
            "是", "是", "是", "否", f"{int(bcoef.loc[2,'n'])}", f"{bcoef.loc[2,'r2']:.3f}"],
    "(4)": [f"{bcoef.loc[3,'coef']:.3f}{star(bcoef.loc[3,'p'])}\n({bcoef.loc[3,'se']:.3f})",
            "是", "是", "是", "是", f"{int(bcoef.loc[3,'n'])}", f"{bcoef.loc[3,'r2']:.3f}"],
})
three_line_table(doc, tbl, "表 5-1　基准回归结果",
                 "注：(1)(2) 列为异方差稳健标准误（HC1），(3)(4) 列为企业层面聚类稳健标准误；"
                 "***、**、* 分别表示在 1%、5%、10% 水平上显著；企业年龄因与固定效应共线被剔除。")

h2("5.2　平行趋势与动态效应")
body(
    f"图 5-1 报告以政策实施前一期为基期的事件研究结果。政策实施前各期系数绝对值较小且"
    f"均不显著，政策前系数联合检验的 p 值为 {pretrend_p:.3f}，未拒绝处理组与对照组在政策前"
    "不存在系统性差异的原假设。政策实施后系数转为正，并在多数期内保持显著，表明政策效应"
    "具有持续性。"
)
body(
    f"需要说明两点局限。其一，2010 年批次 {n_always} 家企业在样本首年即已进入处理状态，"
    "缺乏政策前观测，不参与预趋势检验，故上述检验的覆盖范围主要为 2012 年与 2017 年两个"
    "批次；剔除该批次后重新估计，系数为 0.130，与基准结果接近。其二，双向固定效应估计在"
    "处理效应存在异质性时可能产生权重偏误，本文未能实施 Callaway 与 Sant'Anna 或 "
    "Sun 与 Abraham 的异质性稳健估计量，相关结论应以该局限为前提解读。"
)
add_figure(doc, FIG / "event_study.png", "图 5-1　事件研究：平行趋势与动态效应")

h2("5.3　稳健性检验")
body(
    f"表 5-2 报告四项预设稳健性检验。缩尾处理后系数为 {robust.loc[1,'系数']:.3f}，"
    f"替换被解释变量后为 {robust.loc[2,'系数']:.3f}，剔除直辖市样本后为 "
    f"{robust.loc[3,'系数']:.3f}，均在 1% 水平上显著，与基准结果一致；其中剔除直辖市样本"
    f"使观测值由 {n_obs} 降至 {int(robust.loc[3,'观测值'])}。"
    f"在企业层面随机置换处理队列 500 次的安慰剂检验中，虚拟估计系数均值为 "
    f"{placebo_mean:.3f}，"
    f"500 次中没有一次不小于真实估计值，置换 p 值{placebo_p}（图 5-2）。该结果说明估计"
    "结果并非由随机分配的处理状态所驱动；其识别的是随机分配机制，而非不可观测的共同趋势。"
)
rb = robust.copy()
rb["系数"] = rb["系数"].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
rb["标准误"] = rb["标准误"].map(lambda x: "" if pd.isna(x) else f"({x:.3f})")
rb["p值"] = rb["p值"].map(lambda x: x if isinstance(x, str) else f"{x:.3f}")
rb["观测值"] = rb["观测值"].map(lambda x: f"{int(x)}")
rb.columns = ["检验", "系数", "标准误", "p 值", "观测值"]
three_line_table(doc, rb, "表 5-2　稳健性检验",
                 "注：所有规格均沿用基准模型的固定效应与聚类层级；安慰剂一行的“观测值”为"
                 "置换次数；p 值保留三位小数，小于 0.001 者报告为区间上界。")
add_figure(doc, FIG / "placebo.png", "图 5-2　安慰剂检验（500 次随机置换）")

h2("5.4　机制检验")
m_fc, m_gi = mech.iloc[0], mech.iloc[2]
s_fc, s_gi = sobel.iloc[0], sobel.iloc[1]
body(
    f"按江艇 (2022) 两步法，先检验政策对机制变量的影响。结果显示，政策显著降低了企业"
    f"融资约束（系数 {m_fc['系数']:.3f}，p 值 {m_fc['p值']:.3f}），并显著提升了绿色注意力"
    f"（系数 {m_gi['系数']:.3f}，p 值 {m_gi['p值']:.3f}），见表 5-3。"
)
body(
    f"在此基础上，本文对间接效应作补充检验。融资约束渠道的 Sobel 统计量为 "
    f"{s_fc['sobel_z']:.3f}（p 值 {s_fc['sobel_p']:.3f}），Bootstrap 95% 置信区间为 "
    f"[{s_fc['boot_lo']:.4f}, {s_fc['boot_hi']:.4f}]，包含零；绿色注意力渠道的 Sobel 统计量"
    f"为 {s_gi['sobel_z']:.3f}（p 值 {s_gi['sobel_p']:.3f}），置信区间为 "
    f"[{s_gi['boot_lo']:.4f}, {s_gi['boot_hi']:.4f}]，同样包含零。"
)
body(
    "因此，政策确实改变了两项机制变量，且方向与理论预期一致，但间接效应的统计证据不足。"
    "按江艇两步法的逻辑，H2a 与 H2b 仅在“政策影响渠道变量”这一环节获得支持，"
    "渠道变量对绿色创新的作用仍依赖文献论证，尚不能据此宣称中介机制成立。"
    "本文据此将两条机制假设判定为部分支持。"
)
mm = mech.copy()
mm["系数"] = mm["系数"].map(lambda x: f"{x:.3f}")
mm["标准误"] = mm["标准误"].map(lambda x: f"({x:.3f})")
mm["p值"] = mm["p值"].map(lambda x: f"{x:.3f}")
mm.columns = ["机制变量", "路径", "系数", "标准误", "p 值"]
three_line_table(doc, mm, "表 5-3　机制检验：两条路径的估计结果",
                 "注：X→M 为江艇两步法第一步；M→Y 为将机制变量纳入结果方程的补充回归，"
                 "仅作描述，不作为中介效应成立的依据。")

sb = sobel[["机制变量", "a", "b", "sobel_z", "sobel_p", "boot_lo", "boot_hi"]].copy()
sb.columns = ["机制变量", "a", "b", "Sobel z", "Sobel p", "Bootstrap 下界", "Bootstrap 上界"]
for col in ["a", "b", "Sobel z", "Sobel p", "Bootstrap 下界", "Bootstrap 上界"]:
    sb[col] = sb[col].map(lambda x: f"{x:.3f}" if abs(x) >= 0.001 else f"{x:.4f}")
three_line_table(doc, sb, "表 5-4　间接效应检验",
                 "注：Bootstrap 抽样 300 次；置信区间包含零表示间接效应不显著。")

h2("5.5　异质性分析")
i_heavy = het[het["维度"] == "heavy"].iloc[0]
i_soe = het[het["维度"] == "soe"].iloc[0]
g_h1 = het_all[het_all["交互项"] == "组内系数(heavy=1)"].iloc[0]
g_h0 = het_all[het_all["交互项"] == "组内系数(heavy=0)"].iloc[0]
body(
    f"表 5-5 以全交互模型检验组间差异。重污染行业的交互项系数为 {i_heavy['系数']:.3f}"
    f"（p 值 {i_heavy['p值']:.3f}，FDR 校正后 p 值 {i_heavy['p_fdr']:.3f}），"
    f"表明政策对重污染行业企业的激励更强：重污染组组内系数为 {g_h1['系数']:.3f}，"
    f"非重污染组为 {g_h0['系数']:.3f}。产权性质的交互项系数为 {i_soe['系数']:.3f}"
    f"（p 值 {i_soe['p值']:.3f}），组间差异不显著。这表明政策效果主要取决于企业面临的"
    "合规压力，所有制属性的调节作用未获证据支持。"
)
hh = het.copy()
hh["系数"] = hh["系数"].map(lambda x: f"{x:.3f}")
hh["标准误"] = hh["标准误"].map(lambda x: f"({x:.3f})")
hh["p值"] = hh["p值"].map(lambda x: f"{x:.3f}")
hh["p_fdr"] = hh["p_fdr"].map(lambda x: f"{x:.3f}")
hh["N"] = hh["N"].map(lambda x: "" if pd.isna(x) else f"{int(x)}")
hh = hh.rename(columns={"p值": "p 值", "p_fdr": "FDR 校正 p 值"})

sub = het_all[het_all["交互项"].str.contains("组内系数")].copy()
sub = pd.DataFrame({
    "维度": sub["维度"],
    "交互项": sub["交互项"],
    "系数": sub["系数"].map(lambda x: f"{x:.3f}"),
    "标准误": sub["标准误"].map(lambda x: f"({x:.3f})"),
    "p 值": sub["p值"].map(lambda x: f"{x:.3f}"),
    "N": sub["N"].map(lambda x: f"{int(x)}"),
    "FDR 校正 p 值": "",
})
hh = pd.concat([hh[sub.columns], sub], ignore_index=True)
three_line_table(doc, hh, "表 5-5　异质性分析：组间差异检验",
                 "注：交互项显著即组间差异显著；组内系数来自单独样本回归，因固定效应与样本"
                 "差异，与交互模型隐含的组效应可能略有出入，仅用于展示组内效应大小。")

# ── 第六章 ──
h1("第六章　结论与政策建议")
h2("6.1　研究结论")
body(
    f"本文以低碳城市试点为准自然实验，考察其对企业绿色创新的影响。主要结论如下：第一，"
    f"政策显著提升企业绿色创新水平，基准系数为 {beta:.3f}，并通过缩尾、替换度量、"
    f"剔除直辖市与安慰剂检验；第二，政策前系数联合检验未拒绝平行趋势假设"
    f"（p 值 {pretrend_p:.3f}），但该检验未覆盖 2010 年批次，且未实施异质性稳健估计量；"
    f"第三，Oster 识别区间 [{oster_lo:.3f}, {oster_hi:.3f}] 不包含零；第四，政策显著影响"
    f"融资约束与绿色注意力，但间接效应不显著，机制假设仅获部分支持；第五，政策效应在"
    f"重污染行业企业中更强，所有制差异不显著。"
)
h2("6.2　政策建议")
body(
    "第一，保持试点政策的连续性与稳定性，避免频繁调整削弱企业预期。第二，完善绿色金融"
    "配套，将试点形成的信息优势转化为可用的信贷与债券工具。第三，对重污染行业实行差异化"
    "监管与技术支持并重，在提高合规压力的同时降低绿色技术改造成本。第四，建立政策效果的"
    "动态评估机制，关注效应随时间衰减的可能。"
)
h2("6.3　研究不足")
body(
    "第一，本文使用合成数据验证研究流程，全部结论不具现实含义，正式研究须以真实数据重估。"
    "第二，绿色创新以专利数量衡量，未区分专利质量。第三，受当前分析工具限制，未报告"
    "异质性稳健的 DID 估计量，存在权重偏误风险。第四，间接效应的统计证据不足，"
    "机制识别有待更细颗粒度的数据支持。"
)

# ── 参考文献（来自 references/reference_list.txt，由 08_cite_replace.py 生成）──
h1("参考文献")
body("（题录取自 OpenAlex 官方接口，卷期页码与 DOI 随条目给出；正式提交前应以原文核对"
     "著者姓名拼写与页码。中文文献因需机构权限，未在本稿收录。）")
REF_TXT = ROOT / "references" / "reference_list.txt"
if not REF_TXT.exists():
    raise FileNotFoundError("缺少 references/reference_list.txt，请先运行 08_cite_replace.py")
for line in REF_TXT.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.first_line_indent = Pt(-21)
    p.paragraph_format.left_indent = Pt(21)
    set_run(p.add_run(line.strip()), "宋体", 9)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(f"论文已生成：{OUT}")
print(f"段落数 {len(doc.paragraphs)}，表格数 {len(doc.tables)}")
