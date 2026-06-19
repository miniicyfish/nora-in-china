# -*- coding: utf-8 -*-
"""从《“娜拉”在中国》(许慧琦) epub 参考书目抽取主题相关文献，结构化输出。
书目原文逐字保留在 raw 字段；其余为叠加的分析标签层。"""
import re, json, sys, os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
# 源 EPUB（许慧琦《“娜拉”在中国》）受版权所限不随仓库分发，需自备并解压到此路径。
SRC = "/tmp/nora_epub/EPUB/xhtml/Section0016.xhtml"

# 类别标题集合（用于切分层级）
PART_HEADS = {"中文部分": "中", "英文部分": "英", "日文部分": "日", "网站": "网"}
CAT_HEADS = {"史料与史料集", "文集（包括全集、小说、书信集）", "专书", "报纸", "期刊",
             "文章", "博硕士论文", "中文网站", "英文网站"}

def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = re.sub(r"&#?\w+;", " ", s)
    return s.strip()

def to_lishi(raw):
    """台湾式『作者，《书名》』→《历史研究》大陆式『作者：《书名》』。
    仅替换书/篇名前的首个『，《』为『：《』；题名居首(无作者)者不动。"""
    if raw.startswith("《"):
        return raw
    return raw.replace("，《", "：《", 1)

t = open(SRC, encoding="utf-8").read()
paras = [clean(m) for m in re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)]
paras = [p for p in paras if p]

entries = []
part = "中"; cat = ""
for p in paras:
    if p == "参考书目":
        continue
    if p in PART_HEADS:
        part = PART_HEADS[p]; cat = ""; continue
    if p in CAT_HEADS:
        cat = p; continue
    entries.append({"part": part, "cat": cat, "raw": p})

# ---- 解析年份 / 题名 / 作者 ----
def parse_year(raw):
    ys = re.findall(r"(1[5-9]\d{2}|20\d{2})\s*年?", raw)
    ys = [int(y) for y in ys]
    return max(ys) if ys else None

def parse_year_min(raw):
    ys = re.findall(r"(1[5-9]\d{2}|20\d{2})\s*年?", raw)
    ys = [int(y) for y in ys]
    return min(ys) if ys else None

def parse_title(raw):
    m = re.search(r"《([^》]+)》", raw)
    if m: return m.group(1)
    m = re.search(r"[“\"]([^”\"]{2,})[”\"]", raw)
    return m.group(1) if m else ""

def parse_author(raw):
    head = re.split(r"[，,《「(]", raw, 1)[0].strip()
    return head if 0 < len(head) <= 30 else ""

# ---- source_layer 判定 ----
def source_layer(e):
    cat, part, year = e["cat"], e["part"], e["year"]
    if part == "网": return "网络资源"
    if cat in ("史料与史料集", "文集（包括全集、小说、书信集）", "报纸", "期刊"):
        return "一手史料"
    if cat == "博硕士论文": return "二手研究"
    if part in ("英", "日"): return "二手研究"
    # 中文 专书/文章：按年代启发 —— 1949 年前多为一手，之后多为研究
    if cat in ("专书", "文章"):
        if year and year <= 1949: return "一手史料"
        return "二手研究"
    return "二手研究"

def gtype(e):
    c = e["cat"]
    if c == "报纸": return "报纸"
    if c == "期刊": return "期刊"
    if c == "史料与史料集": return "史料集"
    if c == "文集（包括全集、小说、书信集）": return "文集"
    if c == "博硕士论文": return "学位论文"
    if c == "文章": return "文章"
    if c == "专书": return "专书"
    if e["part"] == "网": return "网络资源"
    return "其他"

# ---- 年代分期（双轨：一手史料按史料年代分期；二手研究按出版十年分桶）----
SRC_ERA_ORDER = ["晚清", "民国初年", "五四时期", "南京国民政府时期", "抗战与战后", "史料汇编（今人编印）"]
RES_ERA_ORDER = ["1980年代及以前", "1990年代", "2000年代", "2010年代", "2020年代"]

def era_src(year):
    """一手史料历史分期（事件锚定，方案甲：1919 为五四界）。"""
    if not year: return ""
    if year <= 1911: return "晚清"
    if year <= 1918: return "民国初年"
    if year <= 1927: return "五四时期"
    if year <= 1937: return "南京国民政府时期"
    if year <= 1949: return "抗战与战后"
    return "史料汇编（今人编印）"   # >1949 的一手史料 = 今人汇编/重印，year 非史料年

def era_res(year):
    """二手研究按出版十年分桶。"""
    if not year: return ""
    if year <= 1989: return "1980年代及以前"
    if year <= 1999: return "1990年代"
    if year <= 2009: return "2000年代"
    if year <= 2019: return "2010年代"
    return "2020年代"

def era_for(source_layer, year):
    if source_layer == "网络资源": return "网络资源"
    if source_layer == "一手史料": return era_src(year)
    return era_res(year)

def era_of(e):
    # 报纸/期刊：用创刊/起始年定分期（raw 多为刊行年段，如《新青年》1915—1919）
    if e["cat"] in ("报纸", "期刊"):
        return era_src(parse_year_min(e["raw"]))
    return era_for(e["source_layer"], e["year"])

# ---- 主题相关性（聚焦"娜拉/新女性建构"核心，宽松命中即收）----
# 定义性关键词：娜拉/易卜生 + 新女性形象建构话语 + 关键论争场域
THEME_KW = ["娜拉","易卜生","玩偶","傀儡家庭","Ibsen","Doll's House","A Doll","Nora",
    "终身大事","新女性","摩登女","摩登","茶花女","女杰","罗兰夫人","苏菲亚","贞德",
    "新青年","国闻周报","妇女杂志","胡适","鲁迅","蓝苹","春柳","剧人","袁振英","罗家伦",
    "出走","娜拉走后","妇女解放","女权","新性道德","贞操","自由恋爱","婚恋","个人主义",
    "跨语际","女性主义","new woman","New Woman","modern girl","modern woman",
    "feminis","Feminis","gender","Gender","女性意识","五四","新文化运动"]

# 报刊venue整体纳入：标题多不含主题词（如《申报》《大公报》），关键词过滤会误删，
# 而它们正是娜拉剧评、新女性论争、出走话题的史料载体，按类目直收为一手史料。
AUTO_INCLUDE_CAT = {"报纸", "期刊"}
# 史料集需带妇女/主题门槛——剔除国民党党务汇编等题外史料集。
WOMEN_KW = ["妇女", "女权", "女子", "女性", "新女", "女界", "女运"]

def themed(e):
    if e["cat"] in AUTO_INCLUDE_CAT:
        return True
    blob = e["raw"]
    if e["cat"] == "史料与史料集":
        return any(k in blob for k in THEME_KW + WOMEN_KW)
    return any(k in blob for k in THEME_KW)

# ---- 主题标签 ----
TAGTABLE = [
    ("娜拉译介", ["娜拉","易卜生","玩偶","傀儡","Ibsen","Doll","Nora"]),
    ("易卜生主义", ["易卜生主义","国民之敌","易卜生传"]),
    ("终身大事·剧作", ["终身大事","剧本","话剧","春柳","戏剧","剧人","演出","舞台"]),
    ("娜拉走后怎样", ["走后","出走","娜拉走后","职业","经济独立","生计"]),
    ("抗婚·自由婚恋", ["婚姻","恋爱","婚恋","离婚","贞操","新性道德","自由恋爱"]),
    ("女子教育", ["女学","女教","女子教育","女师","学生","女校"]),
    ("职业女性", ["职业","就业","女工","谋生"]),
    ("女权论述", ["女权","妇女解放","妇女运动","解放","女界"]),
    ("国族·现代性", ["国族","民族","国家","现代性","救国","文明","强国"]),
    ("影像·电影", ["电影","影戏","画报","摩登","新女性","银幕","明星","阮玲玉"]),
    ("女杰·谱系", ["女杰","罗兰","苏菲亚","茶花女","贞德","列女","传记"]),
    ("性别理论·方法", ["社会性别","Gender","性别","跨语际","女性主义","Feminis"]),
]
def tags(e):
    out = []
    for name, kws in TAGTABLE:
        if any(k in e["raw"] for k in kws):
            out.append(name)
    return out

# ---- 对应课程讲 ----
def course(e):
    out = set(); raw = e["raw"]
    if any(k in raw for k in ["社会性别","性别史","Gender","跨语际","女性主义","Feminis","方法"]):
        out.add("导论2·性别分析")
    if any(k in raw for k in ["电影","影戏","画报","摩登","银幕","新女性","明星","图画"]):
        out.add("四·影像中的妇女")
    if any(k in raw for k in ["女权","妇女解放","妇女运动","女界","何震","新青年","五四"]):
        out.add("五·女权主义在中国")
    if any(k in raw for k in ["身体","缠足","摩登","影"]):
        out.add("七·身体与影像")
    if any(k in raw for k in ["婚姻","恋爱","家庭","婚恋","离婚","贞操"]):
        out.add("八·性别与家庭")
    if any(k in raw for k in ["女学","女教","教育","女师","女校"]):
        out.add("九·教育与妇女")
    if any(k in raw for k in ["革命","左翼","蓝苹","延安","丁玲","共产"]):
        out.add("十一·革命与妇女")
    return sorted(out)

out = []
i = 0
for e in entries:
    if e["cat"] in ("报纸", "期刊"):
        continue   # 报刊venue一览已下沉为单篇报刊文章（见 paper_articles.json）
    e["year"] = parse_year(e["raw"])
    if not themed(e):
        continue
    i += 1
    e["source_layer"] = source_layer(e)
    rec = {
        "id": f"src-{i:03d}",
        "raw": e["raw"],
        "author": parse_author(e["raw"]),
        "title": parse_title(e["raw"]),
        "year": e["year"],
        "language": e["part"],
        "source_layer": e["source_layer"],
        "type": gtype(e),
        "era": era_of(e),
        "tags": tags(e),
        "course": course(e),
        "orig_cat": e["cat"],
    }
    out.append(rec)

# ---- 补充检索：我方核验的题内核心论著（不在许慧琦参考书目内）----
SUP = os.path.join(DATA, "supplement.json")
if os.path.exists(SUP):
    sup = json.load(open(SUP, encoding="utf-8"))
    for j, s in enumerate(sup, 1):
        rec = {
            "id": f"sup-{j:03d}",
            "raw": s["raw"],
            "author": s.get("author", ""),
            "title": s.get("title", ""),
            "year": s.get("year"),
            "language": s.get("language", ""),
            "source_layer": s.get("source_layer", "二手研究"),
            "type": s.get("type", "专书"),
            "era": era_for(s.get("source_layer", "二手研究"), s.get("year")),
            "tags": s.get("tags", []),
            "course": s.get("course", []),
            "orig_cat": s.get("type", "专书"),
        }
        out.append(rec)

# ---- 报刊单篇文献：自许慧琦书脚注抽得，下沉替代"报刊venue一览"----
PAP = os.path.join(DATA, "paper_articles.json")
if os.path.exists(PAP):
    pap = json.load(open(PAP, encoding="utf-8"))
    for j, p in enumerate(pap, 1):
        e2 = {"raw": p["raw"], "cat": "报刊文章", "part": "中", "year": p.get("year")}
        rec = {
            "id": f"news-{j:03d}",
            "raw": p["raw"],
            "author": p.get("author", ""),
            "title": p.get("title", ""),
            "year": p.get("year"),
            "language": "中",
            "source_layer": "一手史料",
            "type": "报刊文章",
            "era": era_src(p.get("year")),
            "tags": tags(e2),
            "course": course(e2),
            "orig_cat": "报刊文章（脚注辑录）",
        }
        out.append(rec)

# ---- 全库统一为《历史研究》大陆式著录（作者：《书名》）----
for rec in out:
    rec["raw"] = to_lishi(rec["raw"])

json.dump(out, open(os.path.join(DATA, "bibliography.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 统计 ----
from collections import Counter
print("命中主题条目:", len(out), "/ 全部条目:", len(entries))
def dist(key):
    c = Counter()
    for r in out:
        v = r[key]
        if isinstance(v, list):
            for x in v: c[x]+=1
        else:
            c[v or "(空)"]+=1
    return c.most_common()
print("\n[source_layer]", dist("source_layer"))
print("\n[type]", dist("type"))
print("\n[language]", dist("language"))
print("\n[era]", dist("era"))
print("\n[tags]")
for k,v in dist("tags"): print(f"   {k}: {v}")
print("\n[course]")
for k,v in dist("course"): print(f"   {k}: {v}")
