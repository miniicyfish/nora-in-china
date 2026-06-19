# -*- coding: utf-8 -*-
"""把 bibliography.json 内嵌进单文件静态页 index.html（双击即开，无需服务器）。"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, "data", "bibliography.json"), encoding="utf-8"))
DATA_JSON = json.dumps(data, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>“新女性”的建构与再现 · 以“娜拉”在中国为线索 — 资料库</title>
<style>
:root{
  --ink:#22201c; --sub:#6b645a; --line:#e3ddd2; --bg:#f6f3ec; --card:#fffdf8;
  --accent:#8a3b2e; --accent2:#3d5a6c; --chip:#efe9dd;
}
*{box-sizing:border-box}
body{margin:0;font-family:"Songti SC","Source Han Serif SC","Noto Serif CJK SC",Georgia,serif;
  color:var(--ink);background:var(--bg);line-height:1.6}
header{padding:30px 36px 18px;border-bottom:2px solid var(--accent)}
header h1{margin:0 0 4px;font-size:24px;letter-spacing:1px}
header .sub{color:var(--sub);font-size:14px}
header .meta{margin-top:8px;font-size:13px;color:var(--sub)}
.wrap{display:flex;gap:0;align-items:flex-start}
aside{width:268px;flex:none;padding:20px 18px 60px;border-right:1px solid var(--line);
  position:sticky;top:0;max-height:100vh;overflow-y:auto}
main{flex:1;padding:20px 36px 80px;min-width:0}
.search{width:100%;padding:10px 12px;font-size:15px;border:1px solid var(--line);
  border-radius:6px;background:var(--card);font-family:inherit}
.fgroup{margin-top:20px}
.fgroup h3{margin:0 0 8px;font-size:14px;color:var(--accent);font-weight:700;
  border-bottom:1px solid var(--line);padding-bottom:4px}
.fsub{font-size:12px;color:var(--accent2);font-weight:600;margin:9px 0 2px}
.opt{display:flex;align-items:center;gap:7px;font-size:13.5px;color:var(--sub);
  padding:2px 0;cursor:pointer}
.opt input{accent-color:var(--accent);cursor:pointer}
.opt .cnt{margin-left:auto;font-size:12px;color:#a39a8a}
.opt.active{color:var(--ink);font-weight:600}
.bar{display:flex;align-items:baseline;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.bar .count{font-size:15px}.bar .count b{color:var(--accent);font-size:19px}
.bar .reset{font-size:13px;color:var(--accent2);cursor:pointer;text-decoration:underline}
.sortbox{font-size:13px;color:var(--sub)}
.sortbox select{font-family:inherit;font-size:13px;padding:3px 6px;border:1px solid var(--line);
  border-radius:5px;background:var(--card);color:var(--ink);cursor:pointer}
.b.yr{background:#e7e0c8;color:#7a6a2e}
.bar .active-tags{font-size:12.5px;color:var(--sub)}
.card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent2);
  border-radius:6px;padding:13px 16px;margin-bottom:10px}
.card.s1{border-left-color:var(--accent)}
.card .raw{font-size:15px}
.card .badges{margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.b{font-size:11.5px;padding:1.5px 8px;border-radius:10px;background:var(--chip);color:var(--sub);
  font-family:system-ui,sans-serif}
.b.layer{background:#f0e0db;color:var(--accent)}
.b.layer2{background:#dde6ec;color:var(--accent2)}
.b.sup{background:#e7e0c8;color:#7a6a2e}
.b.tag{background:transparent;border:1px solid var(--line);color:var(--sub)}
.empty{color:var(--sub);padding:40px 0;text-align:center}
@media(max-width:760px){.wrap{flex-direction:column}aside{width:100%;position:static;max-height:none;
  border-right:none;border-bottom:1px solid var(--line)}main{padding:18px}}
</style>
</head>
<body>
<header>
  <h1>“新女性”的建构与再现 · 以“娜拉”在中国为线索</h1>
  <div class="sub">1900s—1930s 史料与研究专题资料库　|　中国近现代妇女与性别史专题</div>
  <div class="meta" id="meta"></div>
</header>
<div class="wrap">
  <aside>
    <input class="search" id="q" placeholder="检索题名 / 作者 / 出处…">
    <div id="facets"></div>
  </aside>
  <main>
    <div class="bar">
      <div class="count">命中 <b id="n">0</b> 条</div>
      <label class="sortbox">排序
        <select id="sort">
          <option value="default">默认（分类·年代）</option>
          <option value="asc">时间：早 → 晚</option>
          <option value="desc">时间：晚 → 早</option>
        </select></label>
      <span class="reset" id="reset">清除全部筛选</span>
      <span class="active-tags" id="actived"></span>
    </div>
    <div id="list"></div>
  </main>
</div>
<script>
const DATA = __DATA__;
const LANGMAP={"中":"中文","英":"英文","日":"日文","网":"网络"};
DATA.forEach(r=>r._lang=LANGMAP[r.language]||r.language);

// facet 定义：[字段, 标题, 是否数组]
const FACETS=[
 ["source_layer","史料层级",false],
 ["type","文献类型",false],
 ["_lang","语种",false],
 ["era","年代分期",false],
 ["tags","主题标签",true],
 ["course","对应课程讲次",true],
];
const ERA_GROUPS=[
 ["史料年代",["晚清","民国初年","五四时期","南京国民政府时期","抗战与战后","史料汇编（今人编印）"]],
 ["研究出版年代",["1980年代及以前","1990年代","2000年代","2010年代","2020年代"]],
 ["其他",["网络资源","（未注）"]],
];
const ERA_ORDER=ERA_GROUPS.flatMap(([,ks])=>ks).concat([""]);
const sel={}; FACETS.forEach(([f])=>sel[f]=new Set());
let query="";
let sortMode="default";

function values(field,isArr){
  const c={};
  DATA.forEach(r=>{
    let v=r[field]; if(v===null||v===undefined||v==="")v=isArr?null:"（未注）";
    (isArr?(v||[]):[v]).forEach(x=>{if(x!=null)c[x]=(c[x]||0)+1});
  });
  let keys=Object.keys(c);
  if(field==="era")keys.sort((a,b)=>ERA_ORDER.indexOf(a)-ERA_ORDER.indexOf(b));
  else keys.sort((a,b)=>c[b]-c[a]);
  return keys.map(k=>[k,c[k]]);
}

function makeOpt(field,k,n){
  const lab=document.createElement("label");lab.className="opt";
  lab.innerHTML=`<input type="checkbox" value="${k}"><span>${k}</span><span class="cnt">${n}</span>`;
  const cb=lab.querySelector("input");
  cb.onchange=()=>{cb.checked?sel[field].add(k):sel[field].delete(k);
    lab.classList.toggle("active",cb.checked);render();};
  return lab;
}
function buildFacets(){
  const box=document.getElementById("facets");
  FACETS.forEach(([field,title,isArr])=>{
    const g=document.createElement("div");g.className="fgroup";
    g.innerHTML=`<h3>${title}</h3>`;
    if(field==="era"){          // 年代分期：史料/研究分块呈现
      const cmap={};values(field,isArr).forEach(([k,n])=>cmap[k]=n);
      ERA_GROUPS.forEach(([gname,keys])=>{
        const present=keys.filter(k=>cmap[k]);
        if(!present.length)return;
        const sub=document.createElement("div");sub.className="fsub";sub.textContent=gname;
        g.appendChild(sub);
        present.forEach(k=>g.appendChild(makeOpt(field,k,cmap[k])));
      });
    }else{
      values(field,isArr).forEach(([k,n])=>g.appendChild(makeOpt(field,k,n)));
    }
    box.appendChild(g);
  });
}

function match(r){
  for(const [field,,isArr] of FACETS){
    const s=sel[field]; if(!s.size)continue;
    const vals=isArr?(r[field]||[]):[ (r[field]==null||r[field]==="")?"（未注）":r[field] ];
    if(![...s].some(x=>vals.includes(x)))return false;
  }
  if(query){const q=query.toLowerCase();
    if(!(r.raw||"").toLowerCase().includes(q))return false;}
  return true;
}

function render(){
  let hits=DATA.filter(match);
  if(sortMode!=="default"){      // 按 year 排序，无年份者统一置末
    hits=hits.slice().sort((a,b)=>{
      if(!a.year&&!b.year)return 0;
      if(!a.year)return 1; if(!b.year)return -1;
      return sortMode==="asc"?a.year-b.year:b.year-a.year;
    });
  }
  document.getElementById("n").textContent=hits.length;
  const ad=Object.entries(sel).flatMap(([f,s])=>[...s]).concat(query?['“'+query+'”']:[]);
  document.getElementById("actived").textContent=ad.length?("· "+ad.join(" / ")):"";
  const list=document.getElementById("list");
  if(!hits.length){list.innerHTML='<div class="empty">无匹配条目，请放宽筛选。</div>';return;}
  list.innerHTML=hits.map(r=>{
    const isOne=r.source_layer==="一手史料";
    const layerCls=isOne?"layer":"layer2";
    const tags=(r.tags||[]).map(t=>`<span class="b tag">${t}</span>`).join("");
    return `<div class="card ${isOne?'s1':''}">
      <div class="raw">${escapeHtml(r.raw)}</div>
      <div class="badges">
        <span class="b ${layerCls}">${r.source_layer}</span>
        <span class="b">${r.type}</span>
        <span class="b">${r._lang}</span>
        ${r.year?`<span class="b yr">${r.year}年</span>`:''}
        ${r.era?`<span class="b">${r.era}</span>`:''}
        ${tags}
      </div></div>`;
  }).join("");
}
function escapeHtml(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

document.getElementById("q").oninput=e=>{query=e.target.value.trim();render();};
document.getElementById("sort").onchange=e=>{sortMode=e.target.value;render();};
document.getElementById("reset").onclick=()=>{
  FACETS.forEach(([f])=>sel[f].clear());query="";document.getElementById("q").value="";
  document.querySelectorAll(".opt input:checked").forEach(cb=>cb.checked=false);
  document.querySelectorAll(".opt.active").forEach(o=>o.classList.remove("active"));
  render();
};

(function(){
  const one=DATA.filter(r=>r.source_layer==="一手史料").length;
  const two=DATA.filter(r=>r.source_layer==="二手研究").length;
  document.getElementById("meta").textContent=
    `全库 ${DATA.length} 条　·　一手史料 ${one}　·　学术研究 ${two}　·　多维筛选可叠加（组内为“或”，组间为“且”）`;
  buildFacets();render();
})();
</script>
</body>
</html>"""

html = HTML.replace("__DATA__", DATA_JSON)
out = os.path.join(BASE, "index.html")
open(out, "w", encoding="utf-8").write(html)
print("written", out, "| entries", len(data), "| size", len(html))
