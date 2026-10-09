#!/usr/bin/env python3
"""Generate GitHub AI weekly snapshot + weekly AI news page."""
from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

SITE = Path("/workspace/github-trending-site")
TODAY = date(2026, 10, 9)
WEEKDAY_ZH = "一二三四五六日"
TODAY_LABEL = f"{TODAY.isoformat()} · 周{WEEKDAY_ZH[TODAY.weekday()]}"

LANG_COLORS = {
    "Shell": "#89e051",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Unknown": "#8b9bb4",
}

# Curated purpose / flow / intro — one short sentence each
META = {
    "mattpocock/skills": {
        "tag": "Agent 技能库",
        "flow": ["复制技能", "装进 Agent", "复用能力"],
        "intro": "开源 Agent Skills 合集，复制即用。",
    },
    "Panniantong/Agent-Reach": {
        "tag": "联网取证",
        "flow": ["CLI", "搜全网", "喂给 Agent"],
        "intro": "一个 CLI 让 Agent 免费搜全网，无需付费 API。",
    },
    "heygen-com/hyperframes": {
        "tag": "HTML 转视频",
        "flow": ["写 HTML", "渲染帧", "导出视频"],
        "intro": "用 HTML/CSS 写画面，再渲染成视频，适合 Agent 自动做片。",
    },
    "thedotmack/claude-mem": {
        "tag": "跨会话记忆",
        "flow": ["记录", "压缩", "下次注入"],
        "intro": "给 Agent 加跨会话长期记忆，自动压缩后再注入上下文。",
    },
    "mvschwarz/openrig": {
        "tag": "多 Agent 编排",
        "flow": ["选 Agent", "定角色", "共享协作"],
        "intro": "把多个编程 Agent 编成固定角色的长期协作团队。",
    },
    "pingdotgg/t3code": {
        "tag": "远程操控台",
        "flow": ["手机/Web", "调度本机", "驱动 Agent"],
        "intro": "用手机或网页远程调度本机 Claude Code / Cursor 等 Agent。",
    },
    "earthtojake/text-to-cad": {
        "tag": "文字转 CAD",
        "flow": ["描述需求", "Agent 建模", "导出 CAD"],
        "intro": "用自然语言生成 STEP/STL 等 CAD 模型，可进打印或加工。",
    },
    "cursor/plugins": {
        "tag": "编辑器扩展",
        "flow": ["读规范", "写插件", "增强 Cursor"],
        "intro": "Cursor 官方插件规范与插件集，用来扩展 Agent Skill。",
    },
}

# Short news overrides by title prefix
NEWS_SHORT = {
    "这几天，我都是拿手机让dot帮我干活": "用手机遥控 OpenAI Dot，后台持续跑任务。",
    "做了个地图动效 Skill": "地图轨迹 Skill，一键生成旅行路线视频。",
    "假期照片先别删": "123 条提示词，把废片修成创意照。",
    "REA：逆向工程一切": "本地逆向工具，一句话分析二进制与网站。",
    "LLM 推理的并行化策略": "多 GPU 推理并行策略选型指南。",
    "Grok Bot 玩法 01": "提示词模板，自动出 AI 早报视频。",
    "ChatGPT 上线【交互 UI】": "对话里直接出滑块、图表等交互组件。",
    "用 Muse Gadgets": "把个人 Agent 接到自制 AI 硬件。",
    "Opus 5.5 正在吃掉科普视频": "15 种风格提示词，快速做科普短视频。",
    "Nano Banana 2.1": "Google 新图模更便宜，支持 4K 与局部编辑。",
    "Mistral 发布 Mistral Large 4": "开源 MoE 多模态 Large 4 预览版上线。",
    "Google发布开源多模态向量模型": "开源多模态 embedding，文本图像进同一向量空间。",
}

CSS = r'''
:root {
  --snow: #FFFFFF;
  --ice: #EAF3FB;
  --mist: #C8DCEF;
  --navy: #0A3558;
  --sky: #1A7AB8;
  --aqua: #3B9BD4;
  --ink: #1E3348;
  --mute: #5A7085;
  --soft: #F5F9FC;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { color-scheme: light; }
body {
  background: var(--snow);
  background-image:
    radial-gradient(ellipse 80% 40% at 10% -10%, #D9ECF8 0%, transparent 55%),
    radial-gradient(ellipse 60% 30% at 100% 0%, #EAF3FB 0%, transparent 50%);
  background-attachment: fixed;
  color: var(--ink);
  font-family: "Manrope", "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", system-ui, sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--navy); text-decoration-thickness: 1px; text-underline-offset: 0.16em; }
a:hover { color: var(--sky); }
a:focus-visible {
  outline: 2px solid var(--sky);
  outline-offset: 3px;
  border-radius: 4px;
}
.wrap {
  width: min(44rem, calc(100% - 1.75rem));
  margin: 0 auto;
  padding: 1.75rem 0 3.5rem;
}
.hero {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
  margin-bottom: 1.35rem;
}
.hero-top {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.75rem 1.25rem;
}
.badge-date {
  display: inline-flex;
  align-items: baseline;
  gap: 0.45rem;
  padding: 0.35rem 0.7rem;
  background: var(--ice);
  border: 1px solid var(--mist);
  border-radius: 999px;
  color: var(--navy);
  font-size: 0.8125rem;
  font-weight: 600;
}
.badge-date .dot {
  width: 0.45rem; height: 0.45rem;
  border-radius: 50%;
  background: var(--aqua);
  display: inline-block;
}
h1 {
  font-family: "Source Serif 4", "Noto Serif SC", Georgia, serif;
  font-weight: 600;
  font-size: clamp(1.65rem, 4.5vw, 2.15rem);
  line-height: 1.2;
  color: var(--navy);
  letter-spacing: -0.02em;
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.85rem;
  font-size: 0.875rem;
  font-weight: 650;
}
.nav a {
  text-decoration: none;
  padding: 0.35rem 0.75rem;
  background: var(--snow);
  border: 1px solid var(--mist);
  border-radius: 999px;
  color: var(--navy);
}
.nav a:hover { background: var(--ice); border-color: var(--aqua); }

.cards {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.15rem;
}
.card {
  background: var(--ice);
  border: 1px solid var(--mist);
  border-radius: 16px;
  padding: 1.15rem 1.2rem 1.2rem;
  position: relative;
}
.card::before {
  content: "";
  position: absolute;
  left: 0; top: 1rem; bottom: 1rem;
  width: 3px;
  background: var(--navy);
  border-radius: 0 2px 2px 0;
}
.card-head {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding-left: 0.35rem;
}
.rank {
  flex: 0 0 auto;
  width: 2.55rem;
  height: 2.55rem;
  display: grid;
  place-items: center;
  background: var(--snow);
  border: 1.5px solid var(--navy);
  border-radius: 10px;
  font-family: "Source Serif 4", Georgia, serif;
  font-weight: 650;
  font-size: 1.05rem;
  color: var(--navy);
  font-variant-numeric: tabular-nums;
}
.card-title { min-width: 0; flex: 1; }
.name {
  font-size: 1.12rem;
  font-weight: 700;
  color: var(--navy);
  text-decoration: none;
  word-break: break-word;
  letter-spacing: -0.01em;
}
.name:hover { color: var(--sky); text-decoration: underline; }
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem 0.75rem;
  margin-top: 0.4rem;
}
.lang {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 650;
  color: var(--navy);
  background: var(--snow);
  border: 1px solid var(--mist);
  border-radius: 999px;
  padding: 0.15rem 0.55rem 0.15rem 0.4rem;
}
.lang i {
  width: 0.55rem; height: 0.55rem;
  border-radius: 50%;
  display: inline-block;
}
.pill {
  font-size: 0.75rem;
  font-weight: 650;
  color: var(--mute);
  font-variant-numeric: tabular-nums;
}
.pill strong { color: var(--ink); font-weight: 700; }
.pill.week strong { color: var(--sky); }
.purpose {
  margin: 0.95rem 0 0;
  padding: 0.75rem 0.85rem;
  background: var(--snow);
  border: 1px dashed var(--mist);
  border-radius: 12px;
}
.purpose-label {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--sky);
  margin-bottom: 0.55rem;
}
.purpose-label .tag {
  background: #DFF0FA;
  color: var(--navy);
  border: 1px solid var(--mist);
  border-radius: 6px;
  padding: 0.12rem 0.45rem;
  font-size: 0.75rem;
}
.flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}
.flow .step {
  background: var(--ice);
  border: 1px solid var(--mist);
  color: var(--navy);
  font-size: 0.75rem;
  font-weight: 650;
  padding: 0.28rem 0.55rem;
  border-radius: 8px;
}
.flow .arrow {
  color: var(--aqua);
  font-weight: 700;
  font-size: 0.85rem;
  line-height: 1;
}
.diagram {
  margin-top: 0.15rem;
  width: 100%;
  overflow-x: auto;
}
.diagram svg {
  display: block;
  width: 100%;
  max-width: 36rem;
  height: auto;
}
.intro {
  margin-top: 0.7rem;
  font-size: 0.9rem;
  color: var(--ink);
  line-height: 1.5;
  max-width: 40em;
  padding-left: 0.35rem;
}
.news-note {
  margin-top: 0.35rem;
  font-size: 0.84rem;
  color: var(--mute);
  line-height: 1.45;
}
.bar-block {
  margin-top: 0.9rem;
  padding-left: 0.35rem;
}
.bar-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.35rem;
  font-size: 0.72rem;
  font-weight: 650;
  color: var(--mute);
}
.bar-head .v { color: var(--sky); font-variant-numeric: tabular-nums; }
.bar-track {
  height: 0.65rem;
  background: #D6E7F5;
  border: 1px solid var(--mist);
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #7BC0E6, #1A7AB8);
  border-radius: 999px;
}
.foot {
  margin-top: 1.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--mist);
  font-size: 0.8125rem;
  color: var(--mute);
}
.foot a { font-weight: 700; }
@media (max-width: 520px) {
  .card { padding: 1rem; }
}
@media (prefers-reduced-motion: no-preference) {
  .card { transition: border-color 0.15s ease, background 0.15s ease; }
  .card:hover { border-color: var(--aqua); background: #E3F0FA; }
}

.section {
  margin-top: 0.35rem;
  margin-bottom: 1.5rem;
}
.section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.4rem 1rem;
  margin-bottom: 0.75rem;
}
.section-head h2 {
  font-family: "Source Serif 4", "Noto Serif SC", Georgia, serif;
  font-weight: 600;
  font-size: 1.2rem;
  color: var(--navy);
  letter-spacing: -0.01em;
}
.section-meta {
  font-size: 0.75rem;
  color: var(--mute);
  font-weight: 600;
}
.news-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.news-card {
  background: var(--snow);
  border: 1px solid var(--mist);
  border-radius: 14px;
  padding: 0.85rem 1rem;
}
.news-card a.title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--navy);
  text-decoration: none;
  line-height: 1.4;
  display: block;
}
.news-card a.title:hover { color: var(--sky); text-decoration: underline; }
.news-meta {
  margin-top: 0.3rem;
  font-size: 0.72rem;
  font-weight: 650;
  color: var(--sky);
}
.section-divider {
  height: 1px;
  background: var(--mist);
  margin: 1.35rem 0 0.25rem;
  border: 0;
}
'''


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def fmt_int(n: int) -> str:
    return f"{n:,}"


def one_sentence(text: str, max_len: int = 42) -> str:
    """Compress blurb to one short Chinese sentence."""
    text = (text or "").strip().replace("\n", " ")
    for sep in ("。", "！", "？", "；", ". ", "! ", "? "):
        if sep in text:
            part = text.split(sep)[0].strip()
            if part:
                text = part + ("。" if sep in ("。", "！", "？", "；") else "")
                break
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip("，,、；; ") + "…"
    if text and text[-1] not in "。！？…":
        text += "。"
    return text


def short_news_note(title: str, note: str) -> str:
    for key, short in NEWS_SHORT.items():
        if title.startswith(key) or key in title:
            return short
    return one_sentence(note, 40)


def flow_svg(steps: list[str]) -> str:
    """Inline SVG flowchart: rounded boxes + arrows."""
    if not steps:
        return ""
    box_h = 36
    pad_x = 14
    gap = 28
    # approximate char width ~12 for CJK
    widths = [max(56, 12 * len(s) + pad_x * 2) for s in steps]
    total_w = sum(widths) + gap * (len(steps) - 1) + 8
    total_h = box_h + 16
    x = 4
    parts = [
        f'<svg class="flow-svg" viewBox="0 0 {total_w} {total_h}" '
        f'role="img" aria-label="流程：{" → ".join(steps)}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]
    for i, (step, w) in enumerate(zip(steps, widths)):
        y = 8
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{box_h}" rx="10" '
            f'fill="#EAF3FB" stroke="#C8DCEF" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x + w/2}" y="{y + box_h/2 + 5}" text-anchor="middle" '
            f'font-family="Noto Sans SC, Manrope, sans-serif" font-size="12" '
            f'font-weight="650" fill="#0A3558">{html.escape(step)}</text>'
        )
        if i < len(steps) - 1:
            ax = x + w + 4
            ay = y + box_h / 2
            parts.append(
                f'<path d="M{ax} {ay} L{ax + gap - 10} {ay}" '
                f'stroke="#3B9BD4" stroke-width="2" fill="none"/>'
            )
            parts.append(
                f'<polygon points="{ax + gap - 10},{ay - 5} {ax + gap - 2},{ay} '
                f'{ax + gap - 10},{ay + 5}" fill="#3B9BD4"/>'
            )
        x += w + gap
    parts.append("</svg>")
    return '<div class="diagram">' + "".join(parts) + "</div>"



def load_news() -> tuple[list[dict], str, str]:
    """Prefer 7-day waytoagi feed; fallback to daily-brief."""
    way = json.load(open("/tmp/gt-update/waytoagi-7d.json"))
    updates = way.get("updates_7d") or []
    if updates:
        # take up to 12, chronological newest first (already sorted in file)
        items = []
        for u in updates[:12]:
            items.append({
                "title": u.get("title") or "",
                "url": u.get("url") or "",
                "note": (u.get("summary") or "").strip(),
                "meta": f"WayToAGI · {u.get('date')}",
                "date": u.get("date") or "",
            })
        # window label
        dates = [u.get("date") for u in updates if u.get("date")]
        if dates:
            start, end = min(dates), max(dates)
            window = f"近 7 天（{start} ~ {end}）"
        else:
            window = "近 7 天"
        gen = way.get("generated_at") or ""
        try:
            dt = datetime.fromisoformat(gen.replace("Z", "+00:00")).astimezone(
                timezone(timedelta(hours=8))
            )
            gen_label = dt.strftime("%Y-%m-%d %H:%M") + " 北京时间"
        except Exception:
            gen_label = gen
        return items, window, gen_label

    # fallback daily-brief (24h)
    brief = json.load(open("/tmp/gt-update/daily-brief.json"))
    items = []
    for it in (brief.get("items") or [])[:12]:
        title = it.get("title") or ""
        # prefer Chinese side of bilingual title
        if " / " in title:
            title = title.split(" / ")[0].strip()
        items.append({
            "title": title,
            "url": it.get("primary_url") or it.get("url") or "",
            "note": (it.get("persona_review") or "").strip(),
            "meta": it.get("source_name") or it.get("source") or "AI Radar",
            "date": "",
        })
    gen = brief.get("generated_at") or ""
    try:
        dt = datetime.fromisoformat(gen.replace("Z", "+00:00")).astimezone(
            timezone(timedelta(hours=8))
        )
        gen_label = dt.strftime("%Y-%m-%d %H:%M") + " 北京时间"
    except Exception:
        gen_label = gen
    return items, "近 24 小时（daily-brief）", gen_label


def render_news(items: list[dict], window: str, gen_label: str) -> str:
    cards = []
    for it in items:
        note = short_news_note(it["title"], it["note"])
        cards.append(
            f'''      <li class="news-card">
        <a class="title" href="{esc(it["url"])}" rel="noopener noreferrer">{esc(it["title"])}</a>
        <div class="news-meta">{esc(it["meta"])}</div>
        <p class="news-note">{esc(note)}</p>
      </li>'''
        )
    return f'''    <section class="section" aria-labelledby="news-heading">
      <div class="section-head">
        <h2 id="news-heading">本周 AI 资讯</h2>
        <span class="section-meta">{esc(window)} · 雷达 {esc(gen_label)} · <a href="https://news.learnprompt.pro" rel="noopener noreferrer">news.learnprompt.pro</a> · 共 {len(items)} 条</span>
      </div>
      <ol class="news-list">
{chr(10).join(cards)}
      </ol>
    </section>'''


def render_repo_card(rank: int, repo: dict, max_week: int) -> str:
    name = repo["full"]
    meta = META.get(name, {
        "tag": "AI 相关",
        "flow": ["了解", "试用"],
        "intro": one_sentence(repo.get("desc") or "本周周榜上的 AI / Agent 相关仓库。", 40),
    })
    color = LANG_COLORS.get(repo["lang"], LANG_COLORS["Unknown"])
    pct = int(round(100 * repo["week"] / max_week)) if max_week else 0
    diagram = flow_svg(meta["flow"])
    intro = meta["intro"]  # already one short sentence in META
    return f'''      <li class="card">
        <div class="card-head">
          <span class="rank" aria-hidden="true">{rank:02d}</span>
          <div class="card-title">
            <a class="name" href="https://github.com/{esc(name)}">{esc(name)}</a>
            <div class="meta">
              <span class="lang"><i style="background:{color}"></i>{esc(repo["lang"])}</span>
              <span class="pill">星标 <strong>★ {fmt_int(repo["stars"])}</strong></span>
              <span class="pill week">本周 <strong>+{fmt_int(repo["week"])}</strong></span>
            </div>
          </div>
        </div>
        <div class="purpose" aria-label="项目作用">
          <div class="purpose-label">作用 <span class="tag">{esc(meta["tag"])}</span></div>
          {diagram}
        </div>
        <p class="intro">{esc(intro)}</p>
        <div class="bar-block">
          <div class="bar-head"><span>本周星标</span><span class="v">+{fmt_int(repo["week"])}</span></div>
          <div class="bar-track" role="img" aria-label="本周星标占比 {pct}%">
            <div class="bar-fill" style="width:{pct}%"></div>
          </div>
        </div>
      </li>'''


def render_page(repos: list[dict], news_html: str) -> str:
    max_week = max((r["week"] for r in repos), default=1) or 1
    cards = "\n\n".join(render_repo_card(i + 1, r, max_week) for i, r in enumerate(repos[:10]))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>本周 AI 速览 · {TODAY.isoformat()}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&display=swap" rel="stylesheet" />
  <style>
{CSS}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="hero-top">
        <div>
          <div class="badge-date"><span class="dot" aria-hidden="true"></span>{esc(TODAY_LABEL)}</div>
          <h1>本周 AI 速览</h1>
        </div>
        <nav class="nav" aria-label="站点导航">
          <a href="history.html">往期速览</a>
          <a href="https://github.com/trending?since=weekly" rel="noopener noreferrer">GitHub Trending</a>
        </nav>
      </div>
    </header>

{news_html}

    <hr class="section-divider" />

    <div class="section-head" style="margin-top:1.15rem;margin-bottom:0">
      <h2>AI 周榜仓库</h2>
      <span class="section-meta">按本周新增星标排序 · 共 {len(repos[:10])} 个</span>
    </div>

    <ol class="cards">

{cards}

    </ol>

    <footer class="foot">
      <p>最新页始终等于当天 AI 周榜日快照。往期见 <a href="history.html">往期速览</a>。数据抓取时间：{TODAY.isoformat()}（Asia/Shanghai）。</p>
    </footer>
  </div>
</body>
</html>
'''


def update_history() -> None:
    """Rebuild history.html month list from archive files."""
    archive_root = SITE / "archive"
    months: dict[str, list[str]] = {}
    for p in sorted(archive_root.glob("*/github-trending-weekly-*.html")):
        m = re.search(r"github-trending-weekly-(\d{4}-\d{2}-\d{2})\.html$", p.name)
        if not m:
            continue
        day = m.group(1)
        month = day[:7]
        months.setdefault(month, []).append(day)
    for month in months:
        months[month] = sorted(set(months[month]), reverse=True)

    month_blocks = []
    for month in sorted(months.keys(), reverse=True):
        days = months[month]
        links = "\n".join(
            f'          <li><a href="archive/{month}/github-trending-weekly-{d}.html">{d}</a></li>'
            for d in days
        )
        month_blocks.append(
            f'''      <section class="month">
        <h2>{month}</h2>
        <ul class="days">
{links}
        </ul>
      </section>'''
        )

    history = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>往期速览 · 本周 AI 速览</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&display=swap" rel="stylesheet" />
  <style>
{CSS}
.month {{ margin-top: 1.5rem; }}
.month h2 {{
  font-family: "Source Serif 4", "Noto Serif SC", Georgia, serif;
  font-size: 1.15rem;
  color: var(--navy);
  margin-bottom: 0.65rem;
}}
.days {{
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}}
.days a {{
  display: inline-block;
  padding: 0.4rem 0.75rem;
  background: var(--ice);
  border: 1px solid var(--mist);
  border-radius: 999px;
  text-decoration: none;
  font-weight: 650;
  font-size: 0.875rem;
}}
.days a:hover {{ background: #D9ECF8; border-color: var(--aqua); }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="hero-top">
        <div>
          <div class="badge-date"><span class="dot" aria-hidden="true"></span>往期速览</div>
          <h1>按月浏览</h1>
        </div>
        <nav class="nav" aria-label="站点导航">
          <a href="index.html">最新速览</a>
          <a href="https://github.com/trending?since=weekly" rel="noopener noreferrer">GitHub Trending</a>
        </nav>
      </div>
    </header>
{chr(10).join(month_blocks)}
    <footer class="foot">
      <p>每天覆盖同一份日快照；按月分文件夹归档。</p>
    </footer>
  </div>
</body>
</html>
'''
    (SITE / "history.html").write_text(history, encoding="utf-8")


def main() -> None:
    repos = json.load(open("/tmp/gt-update/repos.json"))
    repos = sorted(repos, key=lambda r: r["week"], reverse=True)[:10]
    news_items, window, gen_label = load_news()
    news_html = render_news(news_items, window, gen_label)
    page = render_page(repos, news_html)

    month_dir = SITE / "archive" / TODAY.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    day_file = month_dir / f"github-trending-weekly-{TODAY.isoformat()}.html"
    day_file.write_text(page, encoding="utf-8")
    (SITE / "index.html").write_text(page, encoding="utf-8")
    update_history()

    meta = {
        "date": TODAY.isoformat(),
        "repos": len(repos),
        "news": len(news_items),
        "news_window": window,
        "repo_names": [r["full"] for r in repos],
    }
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
