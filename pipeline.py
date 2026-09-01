# -*- coding: utf-8 -*-
"""
prism - daily pipeline: fetch -> pick event -> align -> analyze -> render.

Stages (each writes an intermediate file under data/, so any stage can be re-run):

  python pipeline.py fetch     -> data/top_<date>.json        (no LLM)
  python pipeline.py plan      -> data/plan_<date>.json       (LLM call 1: pick event + localized queries)
  python pipeline.py align     -> data/event_<date>.json      (no LLM)
  python pipeline.py analyze   -> data/analysis_<date>.json   (LLM call 2: cross-country analysis)
  python pipeline.py render    -> site/<date>.html + site/index.html
  python pipeline.py all       -> run every stage in order

LLM configuration (OpenAI-compatible chat completions):
  PRISM_API_KEY    required for plan/analyze
  PRISM_BASE_URL   default https://api.openai.com/v1
                   (DeepSeek: https://api.deepseek.com/v1,
                    Moonshot: https://api.moonshot.cn/v1,
                    Zhipu:    https://open.bigmodel.cn/api/paas/v4)
  PRISM_MODEL      default gpt-4o-mini

No dependencies beyond the Python standard library.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

from fetch_news import EDITIONS, fetch_rss, search_url, run_top, DATA


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from ./.env into os.environ (no override)."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

TODAY = date.today().isoformat()
COUNTRY_IDS = [label for label, *_ in EDITIONS]


# ---------------------------------------------------------------------------
# LLM client (OpenAI-compatible, stdlib only)
# ---------------------------------------------------------------------------

def llm(system: str, user: str, max_tokens: int = 4000) -> str:
    api_key = os.environ.get("PRISM_API_KEY")
    if not api_key:
        sys.exit("PRISM_API_KEY is not set. Set it (and optionally PRISM_BASE_URL / PRISM_MODEL) first.")
    base = os.environ.get("PRISM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("PRISM_MODEL", "gpt-4o-mini")
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    return out["choices"][0]["message"]["content"]


def llm_json(system: str, user: str, max_tokens: int = 4000) -> dict:
    """Call the LLM and parse a JSON object from the reply (tolerates ``` fences)."""
    text = llm(system, user, max_tokens)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"LLM reply contained no JSON object:\n{text[:500]}")
    return json.loads(m.group(0))


# ---------------------------------------------------------------------------
# Stage: plan (LLM call 1 - pick the event, write localized queries)
# ---------------------------------------------------------------------------

PLAN_SYSTEM = """你是国际新闻编辑。你会看到同一天 10 个国家的 Google News 头条列表（各 20 条，原文语言）。
任务：
1. 找出「被最多国家共同报道」且「各国视角差异可能最大」的一个国际事件。优先选硬新闻（地缘政治、冲突、重大经济事件），避开纯体育娱乐。
2. 为每个国家版写一个用当地语言表达的、贴合当地媒体措辞的搜索词（2-4 个词，适合 Google News 搜索）。

严格输出 JSON，不要任何其他文字：
{
  "event": "事件的一句话描述（中文）",
  "event_title": "适合做页面大标题的事件名（中文，15字以内）",
  "why": "为什么选它（中文一句话）",
  "queries": {"US": "...", "UK": "...", "India": "...", "Japan": "...", "France": "...", "Germany": "...", "Brazil": "...", "Russia": "...", "Egypt": "...", "China": "..."}
}
queries 的 key 必须是这 10 个：US, UK, India, Japan, France, Germany, Brazil, Russia, Egypt, China。"""


def run_plan() -> None:
    top = json.loads((DATA / f"top_{TODAY}.json").read_text(encoding="utf-8"))
    lines = []
    for country, items in top.items():
        lines.append(f"## {country}")
        lines.extend(f"- {i['title']}" for i in items)
    plan = llm_json(PLAN_SYSTEM, "\n".join(lines))
    missing = [c for c in COUNTRY_IDS if c not in plan.get("queries", {})]
    if missing:
        raise ValueError(f"plan is missing queries for: {missing}")
    path = DATA / f"plan_{TODAY}.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"event: {plan['event']}")
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# Stage: align (search every country edition with the planned queries)
# ---------------------------------------------------------------------------

def run_align() -> None:
    plan = json.loads((DATA / f"plan_{TODAY}.json").read_text(encoding="utf-8"))
    editions = {label: (hl, gl, ceid) for label, hl, gl, ceid in EDITIONS}
    out = {"event": plan["event"], "event_title": plan.get("event_title", ""), "countries": {}}
    for label, q in plan["queries"].items():
        hl, gl, ceid = editions[label]
        try:
            items = fetch_rss(search_url(q, hl, gl, ceid))[:12]
        except Exception as e:  # keep going; analysis treats missing country as signal-less
            print(f"  {label:8s} FAILED: {e}")
            items = []
        out["countries"][label] = {"query": q, "items": items}
        print(f"  {label:8s} {len(items)} items")
    path = DATA / f"event_{TODAY}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# Stage: analyze (LLM call 2 - the actual product)
# ---------------------------------------------------------------------------

ANALYZE_SYSTEM = """你是「Prism 棱镜」的分析引擎。输入是同一事件在 10 个国家 Google News 版的报道标题（原文语言），
以及各国当天的头版头条（用于判断该事件在当地的显著度）。

分析原则（必须遵守）：
- 只做可验证的客观描述，不下"谁更客观/谁有偏见"的裁决。
- 每个论断都要能落到具体标题上（引用原文片段）。
- 「谁没报 / 谁没上头版」是最有价值的信号，必须检查。
- 关注：各国强调什么、回避什么、关键措辞差异（同一句话/同一行为的不同译法与定性词）、只有某国才有的独家角度。
- 所有分析用中文写，引用原文时保留原文并附中文翻译。

严格输出 JSON，不要任何其他文字：
{
  "findings": [
    {"title": "发现的小标题（中文）", "body": "一段完整分析（中文，可引用原文）"}
  ],
  "quote_comparison": {
    "intro": "对比的是哪句话/哪个定性（中文）",
    "rows": [["国家 · 媒体", "标题原文片段", "处理方式说明（中文）"]]
  },
  "countries": {
    "US": {
      "name": "美国",
      "frame": "主导框架，一句话（中文）",
      "unique": "别国没有的角度（中文）",
      "headlines": [{"source": "媒体名", "original": "标题原文", "zh": "中文翻译（原文即中文时留空字符串）", "link": "原文链接"}]
    }
  },
  "limitation": "本期数据的局限性提示（中文一句话）"
}
findings 给 3-5 个，每个国家 headlines 挑 2-3 条最能代表该国视角的。countries 覆盖所有有数据的国家。"""


def run_analyze() -> None:
    event = json.loads((DATA / f"event_{TODAY}.json").read_text(encoding="utf-8"))
    top = json.loads((DATA / f"top_{TODAY}.json").read_text(encoding="utf-8"))
    lines = [f"# 事件：{event['event']}", "", "# 各国对齐报道（标题 | 媒体 | 链接）"]
    for country, block in event["countries"].items():
        lines.append(f"## {country}（搜索词：{block['query']}）")
        if not block["items"]:
            lines.append("（无结果）")
        lines.extend(f"- {i['title']} | {i['source']} | {i['link']}" for i in block["items"])
    lines.append("")
    lines.append("# 各国当天头版前10条（用于判断显著度与'谁没上头版'）")
    for country, items in top.items():
        lines.append(f"## {country}")
        lines.extend(f"- {i['title']}" for i in items[:10])
    analysis = llm_json(ANALYZE_SYSTEM, "\n".join(lines), max_tokens=8000)
    analysis["event"] = event["event"]
    analysis["event_title"] = event.get("event_title", "")
    analysis["date"] = TODAY
    path = DATA / f"analysis_{TODAY}.json"
    path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"findings: {len(analysis.get('findings', []))}, countries: {len(analysis.get('countries', {}))}")
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# Stage: render
# ---------------------------------------------------------------------------

def run_render() -> None:
    from render import render_page
    analysis = json.loads((DATA / f"analysis_{TODAY}.json").read_text(encoding="utf-8"))
    html = render_page(analysis)
    site = Path(__file__).parent / "site"
    site.mkdir(exist_ok=True)
    daily = site / f"{TODAY}.html"
    daily.write_text(html, encoding="utf-8")
    (site / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {daily} (+ index.html)")


STAGES = {"fetch": run_top, "plan": run_plan, "align": run_align, "analyze": run_analyze, "render": run_render}

if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "all":
        for name, fn in STAGES.items():
            print(f"=== {name} ===")
            fn()
    elif mode in STAGES:
        STAGES[mode]()
    else:
        print(__doc__)
