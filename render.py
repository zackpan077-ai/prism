# -*- coding: utf-8 -*-
"""prism - render analysis JSON into a self-contained static daily page."""
import html
import json


def esc(s: str) -> str:
    return html.escape(str(s or ""))


CSS = """
:root {
  --bg: #141414; --surface: #1c1c1c; --border: #2c2c2c;
  --text: #e6e6e6; --text2: #a0a0a0; --text3: #6e6e6e;
  --accent: #6ab0f3; --danger: #e2645a;
}
* { box-sizing: border-box; margin: 0; }
body {
  background: var(--bg); color: var(--text);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  line-height: 1.7; font-size: 15px;
}
.wrap { max-width: 860px; margin: 0 auto; padding: 48px 20px 80px; }
.brand { font-size: 13px; letter-spacing: 2px; color: var(--text3); text-transform: uppercase; }
h1 { font-size: 26px; margin: 8px 0 4px; font-weight: 650; }
.sub { color: var(--text2); }
.meta { color: var(--text3); font-size: 12.5px; margin-top: 6px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 28px 0; }
.stat { border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.stat b { font-size: 22px; font-weight: 650; display: block; }
.stat.danger b { color: var(--danger); }
.stat span { font-size: 12.5px; color: var(--text2); }
h2 { font-size: 19px; margin: 40px 0 16px; padding-top: 24px; border-top: 1px solid var(--border); }
h3 { font-size: 15.5px; margin: 22px 0 6px; font-weight: 650; }
p { color: var(--text); }
p.note { color: var(--text3); font-size: 12.5px; margin-top: 8px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 13.5px; vertical-align: top; }
th { color: var(--text3); font-weight: 500; font-size: 12.5px; }
tr:last-child td { border-bottom: none; }
td.q { font-weight: 600; }
td.n { color: var(--text2); }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.tab {
  border: 1px solid var(--border); background: none; color: var(--text2);
  border-radius: 99px; padding: 4px 14px; font-size: 13px; cursor: pointer; font-family: inherit;
}
.tab.on { background: var(--text); color: var(--bg); border-color: var(--text); }
.panel { border: 1px solid var(--border); border-radius: 10px; display: none; }
.panel.on { display: block; }
.panel-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 16px; border-bottom: 1px solid var(--border);
  font-size: 12.5px; color: var(--text2);
}
.panel-body { padding: 16px; }
.label { font-size: 12px; color: var(--text3); font-weight: 600; margin-bottom: 2px; }
.block { margin-bottom: 14px; }
.hl { padding: 10px 0; border-top: 1px solid var(--border); }
.hl:first-of-type { border-top: none; }
.hl b { font-weight: 600; display: block; }
.hl .src { color: var(--accent); font-size: 12.5px; margin-right: 10px; text-decoration: none; }
.hl .src:hover { text-decoration: underline; }
.hl .zh { color: var(--text2); font-size: 12.5px; }
.callout {
  border: 1px solid var(--border); border-left: 3px solid var(--danger);
  border-radius: 8px; padding: 14px 16px; margin-top: 40px;
}
.callout b { display: block; margin-bottom: 4px; }
.callout p { color: var(--text2); font-size: 13.5px; }
footer { margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--border); color: var(--text3); font-size: 12.5px; }
"""

JS = """
document.querySelectorAll('.tab').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.tab').forEach(function (b) { b.classList.remove('on'); });
    document.querySelectorAll('.panel').forEach(function (p) { p.classList.remove('on'); });
    btn.classList.add('on');
    document.getElementById('panel-' + btn.dataset.c).classList.add('on');
  });
});
"""


def render_page(a: dict) -> str:
    countries = a.get("countries", {})
    n_headlines = sum(len(c.get("headlines", [])) for c in countries.values())

    findings_html = ""
    for i, f in enumerate(a.get("findings", []), 1):
        findings_html += f"<h3>{i} · {esc(f['title'])}</h3><p>{esc(f['body'])}</p>"

    qc = a.get("quote_comparison") or {}
    quote_html = ""
    if qc.get("rows"):
        rows = "".join(
            f"<tr><td>{esc(r[0])}</td><td class='q'>{esc(r[1])}</td><td class='n'>{esc(r[2])}</td></tr>"
            for r in qc["rows"]
        )
        quote_html = (
            f"<h2>措辞对比</h2><p class='sub'>{esc(qc.get('intro', ''))}</p>"
            f"<table><tr><th>国家 · 媒体</th><th>标题呈现</th><th>处理方式</th></tr>{rows}</table>"
        )

    tabs, panels = "", ""
    for i, (cid, c) in enumerate(countries.items()):
        on = " on" if i == 0 else ""
        tabs += f"<button class='tab{on}' data-c='{esc(cid)}'>{esc(c.get('name', cid))}</button>"
        hls = ""
        for h in c.get("headlines", []):
            zh = f"<span class='zh'>{esc(h['zh'])}</span>" if h.get("zh") else ""
            link = esc(h.get("link", "")) or "#"
            hls += (
                f"<div class='hl'><b>{esc(h['original'])}</b>"
                f"<a class='src' href='{link}' target='_blank'>{esc(h['source'])}</a>{zh}</div>"
            )
        panels += (
            f"<div class='panel{on}' id='panel-{esc(cid)}'>"
            f"<div class='panel-head'><span>{esc(c.get('name', cid))} · 本国信息流里的这一事件</span></div>"
            f"<div class='panel-body'>"
            f"<div class='block'><div class='label'>主导框架</div><p>{esc(c.get('frame', ''))}</p></div>"
            f"<div class='block'><div class='label'>别国没有的角度</div><p>{esc(c.get('unique', ''))}</p></div>"
            f"{hls}</div></div>"
        )

    limitation = ""
    if a.get("limitation"):
        limitation = (
            f"<div class='callout'><b>本期局限</b><p>{esc(a['limitation'])}</p></div>"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prism 棱镜 · {esc(a.get('event_title') or a.get('event', ''))}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="brand">Prism 棱镜 · 每日一事件 · 十国视角</div>
  <h1>{esc(a.get('event_title') or '今日事件')}</h1>
  <p class="sub">{esc(a.get('event', ''))}</p>
  <p class="meta">{esc(a.get('date', ''))} · 数据：Google News 十国分版 RSS · 分析由 LLM 生成，所有标题可点回原文核对</p>

  <div class="stats">
    <div class="stat"><b>{len(countries)}</b><span>国家版信息流</span></div>
    <div class="stat"><b>{n_headlines}</b><span>条精选标题</span></div>
    <div class="stat"><b>{len(a.get('findings', []))}</b><span>个关键发现</span></div>
    <div class="stat danger"><b>1</b><span>个事件，多种讲法</span></div>
  </div>

  <h2>关键发现</h2>
  {findings_html}
  {quote_html}

  <h2>逐国拆解</h2>
  <div class="tabs">{tabs}</div>
  {panels}

  {limitation}

  <footer>Prism 原型 · 只索引标题与摘要，正文请点击链接阅读原文 · 分析基于标题层，未读全文</footer>
</div>
<script>{JS}</script>
</body>
</html>"""


if __name__ == "__main__":
    import sys
    from pathlib import Path
    src = Path(sys.argv[1])
    print(render_page(json.loads(src.read_text(encoding="utf-8"))))
