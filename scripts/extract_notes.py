# -*- coding: utf-8 -*-
"""从许慧琦书正文脚注(zy-footnote 属性)抽取【单篇报刊一手文献】，结构化输出。
脚注原文逐字保留；拆分一注多引、剔除叙述性夹注与专书引用、去重。"""
import re, glob, json, os

SRCDIR = "/tmp/nora_epub/EPUB/xhtml"

# ---- 1. 收集全部脚注文本（去重，保序）----
raw_notes = []
for f in sorted(glob.glob(os.path.join(SRCDIR, "Section00*.xhtml"))):
    t = open(f, encoding="utf-8").read()
    for m in re.findall(r'zy-footnote="([^"]+)"', t):
        s = m.strip()
        for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&#x3000;", " ")]:
            s = s.replace(a, b)
        raw_notes.append(s)
uniq_notes = list(dict.fromkeys(raw_notes))

# ---- 2. 把一条脚注拆成若干"引文片段" ----
LEAD = re.compile(r"^(详见|参见|另见|又见|转引自|引自|见|参|如)+")
def split_frags(note):
    # 按句号/分号切；但《》内的标点不切（先占位保护）
    prot = []
    def hold(m): prot.append(m.group(0)); return f"\x00{len(prot)-1}\x00"
    tmp = re.sub(r"《[^》]*》", hold, note)
    parts = re.split(r"[。；]", tmp)
    out = []
    for p in parts:
        p = re.sub(r"\x00(\d+)\x00", lambda m: prot[int(m.group(1))], p).strip()
        p = LEAD.sub("", p).strip()   # 每个片段都去句首引导词（如/见/参见…）
        if p:
            out.append(p)
    return out

# ---- 3. 判定一个片段是否"单篇报刊文献" ----
BOOK = re.compile(r"出版社|书局|印书馆|出版部|出版公司|大学出版|文献出版|图书馆|图书公司|书店|商务|中华书局")
PERIODICAL = re.compile(r"报|刊|志|周报|旬报|画报|月刊|半月|杂志|丛报|公报")
DATEISH = re.compile(r"\d{4}\s*年|卷\s*\d|第\s*\d+\s*卷|号\s*\d|第\s*\d+\s*[号期]|期\s*\d")
TITLE = re.compile(r"《[^》]+》")
DISCURSIVE_HEAD = re.compile(r"^(以|这些|例如|此处|当时|其中|包括|按|又如|至于|关于|有关|该|此|其|诸如|诸|凡|另|至)")
# 叙述性动词——出现则多为行文而非引文
DISCURSIVE_VERB = re.compile(r"担任|主笔|主编|主編|创办|创刊|主持|曾任|发行|改名|易名|停刊|为主|参看|详后|见上|同此|所载|登载|连载|一文|该文|此文|其文|曾于")

def is_paper_cite(frag):
    if BOOK.search(frag): return False
    if DISCURSIVE_HEAD.search(frag): return False
    if DISCURSIVE_VERB.search(frag): return False
    titles = TITLE.findall(frag)
    if not titles: return False
    # 篇名应靠前：第一个《》之前（作者）不超过 16 字，否则多为叙述句
    if frag.index("《") > 16: return False
    if not PERIODICAL.search(frag): return False
    if not DATEISH.search(frag): return False
    if len(frag) > 95: return False
    return True

# ---- 4. 解析字段 ----
def parse_year(s):
    # 取"引自/转引自"之前的部分（避免把今人史料集重印年当成文章年）
    s = re.split(r"引自|转引自", s)[0]
    ys = [int(y) for y in re.findall(r"(1[5-9]\d{2}|20\d{2})", s)]
    return max(ys) if ys else None

def parse_pub_title(frag):
    ts = TITLE.findall(frag)
    # 第一个《》通常是篇名，最后一个常是刊名（若有两个及以上）
    piece = ts[0].strip("《》") if ts else ""
    journal = ts[-1].strip("《》") if len(ts) >= 2 else ""
    return piece, journal

def parse_author(frag):
    head = re.split(r"《", frag, 1)[0]
    head = re.sub(r"[，,、]$", "", head).strip()
    return head if 0 < len(head) <= 20 else ""

# ---- 5. 主题相关性（沿用宽口径"新女性建构"）----
THEME = ["娜拉","易卜生","玩偶","傀儡","新女性","摩登","新女子","女学","女权","妇女",
    "解放","出走","恋爱","婚姻","婚","贞","烈","节","职业","女工","女子","女界","女性",
    "贤妻","良母","母性","女国民","romantic","女演员","剧","影","摩登","女明星","女作家",
    "自由","独立","教育","参政","缠足","天足","女杰","罗兰","茶花女"]
def themed(s): return any(k in s for k in THEME)

# ---- 6. 跑 ----
seen = set()
records = []
for note in uniq_notes:
    for frag in split_frags(note):
        if not is_paper_cite(frag): continue
        if not themed(frag): continue
        _y = parse_year(frag)
        if _y and _y > 1949: continue   # 民国报刊一手文献限 1949 年前（剔除混入的今人学报论文/专书）
        piece, journal = parse_pub_title(frag)
        key = re.sub(r"\s|，|,|页\d+.*", "", piece + journal)[:40]
        if key in seen: continue
        seen.add(key)
        y = parse_year(frag)
        records.append({
            "raw": frag if frag.endswith("。") else frag + "。",
            "author": parse_author(frag),
            "title": piece,
            "journal": journal,
            "year": y,
        })

records.sort(key=lambda r: (r["year"] or 9999, r["raw"]))
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
json.dump(records, open(os.path.join(DATA, "paper_articles.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("脚注去重:", len(uniq_notes), "| 抽得单篇报刊文献:", len(records))
print("--- 抽样 25 ---")
for r in records[:25]:
    print(f"  [{r['year']}] {r['raw'][:95]}")
print("--- 年代分布 ---")
from collections import Counter
c = Counter()
for r in records:
    y = r["year"]
    c["无年" if not y else ("≤1911" if y<=1911 else "1912-25" if y<=1925 else "1926-37" if y<=1937 else "1938-49" if y<=1949 else ">1949")] += 1
print(dict(c))
