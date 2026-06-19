# -*- coding: utf-8 -*-
"""从 bibliography.json 生成书目正文（分类目+逐字保留 raw），输出 markdown 片段。
导言与重点解题由人工撰写，单独拼合。本脚本只负责"分类清单"这一机械层。"""
import json, os
from collections import Counter, defaultdict

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
d = json.load(open(os.path.join(DATA, "bibliography.json"), encoding="utf-8"))

def by(pred):
    return [r for r in d if pred(r)]

def render(items, key=lambda r: (r["year"] or 9999, r["raw"])):
    items = sorted(items, key=key)
    lines = []
    for r in items:
        lines.append(f"- {r['raw']}")
    return "\n".join(lines)

out = []
W = out.append

# ===== 1 一手史料 =====
W("## 一、一手史料\n")

W("### 1.1 史料集与汇编\n")
W(render(by(lambda r: r["type"] == "史料集")) + "\n")

# 剧本译本：文集中带"娜拉译介"标签者（易卜生剧本中译）
yiben = by(lambda r: r["type"] == "文集" and "娜拉译介" in r["tags"])
W("### 1.2 剧本译本（《娜拉》／《玩偶之家》中译）\n")
W(render(yiben) + "\n")

# 文集·全集·书信·小说：其余文集
wenji = by(lambda r: r["type"] == "文集" and "娜拉译介" not in r["tags"])
W("### 1.3 文集·全集·书信·小说\n")
W(render(wenji) + "\n")

# 民国专书·时人论著：source_layer 一手 的专书
minguo_zs = by(lambda r: r["type"] == "专书" and r["source_layer"] == "一手史料")
W("### 1.4 民国专书·时人论著\n")
W(render(minguo_zs) + "\n")

# 报刊单篇文献（自正文脚注辑录，依《历史研究》著录规范）
pap = by(lambda r: r["type"] == "报刊文章")
W("### 1.5 报刊单篇文献（时论·剧评·译介·论争）\n")
W(f"> 共 **{len(pap)}** 篇，自相关研究论著的征引脚注中爬梳辑录而得——"
  "娜拉剧目的剧评与本事、\"新女性\"论争的时论、出走与婚恋话题的读者来信等，"
  "皆其荦荦大者。著录依《历史研究》规范，按年代分期排列、年内以刊行先后为序。\n")
ERA_ORDER = ["晚清", "民国初年", "五四时期", "南京国民政府时期", "抗战与战后"]
for ename in ERA_ORDER:
    seg = [r for r in pap if r["era"] == ename]
    if not seg:
        continue
    W(f"**{ename}（{len(seg)}）**\n")
    W(render(seg) + "\n")
rest = [r for r in pap if r["era"] not in ERA_ORDER]
if rest:
    W(f"**年代未详（{len(rest)}）**\n")
    W(render(rest) + "\n")

# ===== 2 学术研究 =====
W("## 二、学术研究\n")

cn_zs = by(lambda r: r["type"] == "专书" and r["language"] == "中" and r["source_layer"] == "二手研究")
W("### 2.1 中文专书\n")
W(render(cn_zs) + "\n")

cn_lw = by(lambda r: r["type"] == "文章" and r["language"] == "中")
W("### 2.2 中文论文\n")
W(render(cn_lw) + "\n")

en = by(lambda r: r["language"] == "英" and r["type"] in ("专书", "文章"))
W("### 2.3 英文论著\n")
W(render(en) + "\n")

jp = by(lambda r: r["language"] == "日")
W("### 2.4 日文论著\n")
W(render(jp) + "\n")

xw = by(lambda r: r["type"] == "学位论文")
W("### 2.5 学位论文\n")
W(render(xw) + "\n")

# ===== 3 网络资源 =====
W("## 三、网络资源\n")
W(render(by(lambda r: r["type"] == "网络资源"), key=lambda r: r["raw"]) + "\n")

# ===== 附 统计概览 =====
def dist(key):
    c = Counter()
    for r in d:
        v = r[key]
        if isinstance(v, list):
            for x in v: c[x] += 1
        else:
            c[v or "(空)"] += 1
    return c.most_common()

stats = []
S = stats.append
S("## 附录：统计概览\n")
S(f"全库 **{len(d)}** 条。\n")
S("**史料层级**：" + "；".join(f"{k} {v}" for k, v in dist("source_layer")) + "\n")
S("**文献类型**：" + "；".join(f"{k} {v}" for k, v in dist("type")) + "\n")
S("**语种**：" + "；".join(f"{k} {v}" for k, v in dist("language")) + "\n")
S("**年代分期**：" + "；".join(f"{k} {v}" for k, v in dist("era")) + "\n")
S("**主题标签**：" + "；".join(f"{k} {v}" for k, v in dist("tags")) + "\n")
S("**对应课程讲次**：" + "；".join(f"{k} {v}" for k, v in dist("course")) + "\n")

open(os.path.join(DATA, "_bib_body.md"), "w", encoding="utf-8").write("\n".join(out))
open(os.path.join(DATA, "_bib_stats.md"), "w", encoding="utf-8").write("\n".join(stats))
print("written _bib_body.md, _bib_stats.md")
for k, v in dist("source_layer"): print(k, v)
