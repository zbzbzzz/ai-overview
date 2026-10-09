#!/usr/bin/env python3
"""Generate 本周 AI 速览: AI weekly repos + archive 7-day multi-source news (ADR 0009/0010)."""
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

# Curated 2–4 bullet notes by title prefix (from summary)
NEWS_BULLETS = {
    "这几天，我都是拿手机让dot帮我干活": [
        "OpenAI Dot 实测：用手机下发指令，就能后台持续推进项目，无需全程值守。",
        "文中有代码开发、课程校对、视频制作、作业审阅等真实落地案例。",
        "适合想搭建「持续跑任务」个人 AI 助手的人快速上手。",
    ],
    "做了个地图动效 Skill": [
        "地图动效 Skill：依托高德 API 与 Opus，自动解析真实路线、坐标与海拔。",
        "自带 11 种镜头、12 种视觉风格，支持导入 GPX，一键生成横屏或竖屏视频。",
        "适合 Vlog 片头、自驾徒步轨迹、航线飞线或业务区域分布图。",
    ],
    "假期照片先别删": [
        "AI 创意摄影手册：把普通旅行照做成充满故事感的艺术作品。",
        "含 8 大创意玩法与 43 条可复制提示词，覆盖旅行海报、微缩食物幻想、时空合影、情绪叙事等。",
        "适合假期废片二次创作、想把美照玩出花的摄影爱好者。",
    ],
    "REA：逆向工程一切": [
        "面向 AI 智能体的本地逆向工程工具，已突破 2 万 star。",
        "无需源码即可分析原生二进制、Electron、.NET 与网站；可对接 Hopper/Ghidra，配合 Cursor、Claude Code 一句话完成反编译与逻辑复刻。",
        "本机运行、不上传二进制，支持 CLI 与 MCP，适合从功能调研到代码复刻的开发者。",
    ],
    "LLM 推理的并行化策略": [
        "多 GPU 分布式推理选型指南，拆解各类并行方案的通信开销与取舍。",
        "覆盖流水线、上下文、专家、数据并行等主流策略。",
        "适合按硬件拓扑与业务负载分摊权重 / KV 缓存、避免跨设备通信拖慢推理的人。",
    ],
    "Grok Bot 玩法 01": [
        "整合三套开源 Skill：自动抓取 X 收藏、资讯站等多源信息，并严格校验真实性。",
        "输出文字简报与 90 秒横屏讲解视频，文末附可直接复制的提示词。",
        "适合 Muse、Dots 等带云电脑的 Agent，想搭建每日资讯自动产出系统的人。",
    ],
    "ChatGPT 上线【交互 UI】": [
        "OpenAI Intelligent UI：对话内直接生成可操作组件，跳出纯文本回复。",
        "支持滑块、动态图表、清单计算器，甚至简易小游戏。",
        "适合规划采购 / 旅行穿搭、理解抽象知识，或快速搭建分账、储蓄等轻应用。",
    ],
    "用 Muse Gadgets": [
        "Muse Gadgets 是「自己接硬件」工具包，不是 Meta 新出的整机硬件。",
        "开放 ESP32 固件、Linux Device SDK 与配对方式。",
        "适合把手边开发板、树莓派、屏幕、按钮、麦克风或传感器接到 Muse Agent。",
    ],
    "Opus 5.5 正在吃掉科普视频": [
        "用 Opus 5.5 做出 15 类约 10 秒可视化短片，覆盖皮影戏、3D 拆解、MG 动画、科普信息图等。",
        "文字渲染更稳、可局部修改，制作成本低于传统视频模型。",
        "文中开源全套提示词，适合快速产出高质量科普动态内容。",
    ],
    "Nano Banana 2.1": [
        "Google 新一代生图模型：支持文生图、局部编辑与多参考图融合。",
        "最高可出 4K，中文文字渲染改善，人物与产品主体更一致，价格也更低。",
        "适合想试新图模、有中文排版或主体一致性需求的创作者。",
    ],
    "Mistral 发布 Mistral Large 4": [
        "欧洲自研开放权重 MoE 多模态模型公开预览，具备百万级上下文与强代码 / 智能体能力。",
        "在漏洞复现、代码 Agent、多模态视觉定位、金融法律等任务上表现突出；月底将开放权重，可私有化部署。",
        "适合安全、科研、企业知识工作等重视 AI 主权与可控的场景。",
    ],
    "Google发布开源多模态向量模型": [
        "Google DeepMind 开放多模态 embedding：文本、代码、图像、音视频映射到同一向量空间，上下文至 8K。",
        "模块化设计搭配向量压缩，可在边缘设备轻量化部署；覆盖 RAG、素材检索、分类聚类。",
        "文中有调用示例、微调方案与工程避坑，适合落地隐私可控的跨模态检索应用。",
    ],
    "FLUX 3 Image": [
        "Black Forest Labs 推出 FLUX 3 Image，支持边界框布局生成与局部编辑。",
        "最多可用十张参考图，原生支持 2K / 4K 直出。",
        "适合需要可控构图与高分辨率出图的创作者与工作流。",
    ],
    "Comfy Agent": [
        "Comfy Agent 登陆 Comfy Cloud（本地端也将上线），用自然语言搭建与排查工作流。",
        "支持多模型对比、批量出图与素材管理，减轻节点调试负担。",
        "适合想少碰繁杂节点、快速迭代创意工作流的 ComfyUI 用户。",
    ],
    "AI音乐周刊": [
        "本周 AI 音乐周刊汇总版权新规与司法判例。",
        "收录 Modulate 融资、Suno 语音配乐、Mirelo 音效插件等产品动态。",
        "另有开源音乐框架、舞蹈驱动生成、自动评估等前沿论文速览。",
    ],
}

INDUSTRY_KW = [
    "发布", "上线", "OpenAI", "Google", "DeepMind", "Mistral", "ChatGPT",
    "模型", "预览", "开源", "权重", "Large", "FLUX", "Nano Banana",
]
ACTION_KW = [
    "Skill", "MCP", "Agent", "提示词", "CLI", "工作流", "上手", "复用",
    "工具", "SDK", "硬件", "逆向", "一键", "可直接",
]
BREADTH_KW = [
    "多模态", "4K", "交互", "全网", "开源", "云", "企业", "私有化", "边缘",
]

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
.intro {
  margin-top: 0.7rem;
  font-size: 0.9rem;
  color: var(--ink);
  line-height: 1.5;
  max-width: 40em;
  padding-left: 0.35rem;
}
.news-note {
  margin-top: 0.55rem;
  padding-left: 1.05rem;
  font-size: 0.84rem;
  color: var(--ink);
  line-height: 1.55;
}
.news-note li { margin: 0.2rem 0; }
.news-note li::marker { color: var(--sky); }
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
.news-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.4rem 0.55rem;
}
.news-card a.title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--navy);
  text-decoration: none;
  line-height: 1.4;
  flex: 1 1 12rem;
  min-width: 0;
}
.news-card a.title:hover { color: var(--sky); text-decoration: underline; }
.badge-focus {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  background: #DFF0FA;
  border: 1px solid var(--mist);
  color: var(--navy);
  font-size: 0.7rem;
  font-weight: 750;
  letter-spacing: 0.02em;
  line-height: 1.3;
}
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
.news-list.is-collapsed .news-card.news-extra { display: none; }
.news-toggle-wrap {
  display: flex;
  justify-content: center;
  margin-top: 0.85rem;
}
.news-toggle {
  appearance: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--navy);
  background: var(--snow);
  border: 1px solid var(--mist);
  border-radius: 999px;
  padding: 0.45rem 1.1rem;
  line-height: 1.3;
}
.news-toggle:hover {
  background: var(--ice);
  border-color: var(--aqua);
  color: var(--sky);
}
.news-toggle:focus-visible {
  outline: 2px solid var(--sky);
  outline-offset: 3px;
}
'''


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def fmt_int(n: int) -> str:
    return f"{n:,}"


def one_sentence(text: str, max_len: int = 42) -> str:
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


def kw_hits(text: str, kws: list[str]) -> int:
    return sum(1 for k in kws if k.lower() in text.lower())


def rule_score(title: str, summary: str) -> float:
    """Keyword fallback for 资讯重要度 (0–100)."""
    blob = f"{title} {summary}"
    industry = min(100, 28 + kw_hits(blob, INDUSTRY_KW) * 14)
    actionable = min(100, 30 + kw_hits(blob, ACTION_KW) * 12)
    breadth = min(100, 30 + kw_hits(blob, BREADTH_KW) * 12)
    # Soft boosts
    if any(x in blob for x in ("发布", "上线", "预览版")):
        industry = min(100, industry + 10)
    if any(x in blob for x in ("Skill", "MCP", "Agent", "提示词")):
        actionable = min(100, actionable + 8)
    return round(industry * 0.5 + actionable * 0.35 + breadth * 0.15, 2)


def weighted_score(parts: dict) -> float:
    return round(
        parts["industry"] * 0.5 + parts["actionable"] * 0.35 + parts["breadth"] * 0.15,
        2,
    )


def load_model_scores() -> dict[str, float] | None:
    """Load executor-assigned model scores if present. None => failure/fallback."""
    for p in (
        Path("/tmp/gt-update/news-model-scores.json"),
        SITE / "scripts" / "news-model-scores.json",
    ):
        if not p.exists():
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            out: dict[str, float] = {}
            for title, val in raw.items():
                if isinstance(val, (int, float)):
                    out[title] = float(val)
                elif isinstance(val, dict) and "score" in val:
                    out[title] = float(val["score"])
                elif isinstance(val, dict) and {"industry", "actionable", "breadth"} <= set(val):
                    out[title] = weighted_score(val)
            if out:
                return out
        except Exception:
            return None
    return None


def news_bullets(title: str, summary: str) -> list[str]:
    for key, bullets in NEWS_BULLETS.items():
        if title.startswith(key) or key in title:
            return bullets[:4]
    # Derive 2–3 bullets from summary sentences
    text = (summary or "").strip()
    parts = re.split(r"(?<=[。！？])\s*", text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return [one_sentence(text or "本周 AI 相关动态。", 60)]
    bullets = []
    for p in parts[:3]:
        bullets.append(one_sentence(p, 72))
    if len(bullets) == 1 and len(text) > 40:
        bullets.append(one_sentence(text[len(parts[0]):] or text, 72))
    return bullets[:4]


def flow_html(steps: list[str]) -> str:
    """HTML flow chips (not SVG)."""
    if not steps:
        return ""
    label = " → ".join(steps)
    bits = []
    for i, step in enumerate(steps):
        if i:
            bits.append('<span class="arrow" aria-hidden="true">→</span>')
        bits.append(f'<span class="step">{esc(step)}</span>')
    inner = "".join(bits)
    return (
        f'<div class="diagram"><div class="flow" role="img" '
        f'aria-label="流程：{esc(label)}">{inner}</div></div>'
    )


def load_news() -> tuple[list[dict], str, str, bool]:
    """Return (items top10, window, gen_label, used_fallback).

    Pipeline (ADR 0010): radar archive.json, sites {waytoagi, official_ai, aihot, aibase}
    (+ other clearly-AI sites if present in WANT), rolling last 7 days Asia/Shanghai,
    dedupe by normalized title/url, score by executor model (fallback rules), Top 10.
    """
    from zoneinfo import ZoneInfo
    from urllib.parse import urlparse, urlunparse

    SH = ZoneInfo("Asia/Shanghai")
    now = datetime.now(SH)
    # Rolling window: today-6d 00:00 .. today 23:59:59 Asia/Shanghai
    win_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    win_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    win_start_s = win_start.date().isoformat()
    win_end_s = win_end.date().isoformat()

    WANT = {"waytoagi", "official_ai", "aihot", "aibase"}
    SITE_LABEL = {
        "waytoagi": "WayToAGI",
        "aihot": "AIHot",
        "aibase": "AIBase",
        "official_ai": "Official AI",
    }

    archive_path = Path("/tmp/gt-update/archive.json")
    if not archive_path.exists():
        archive_path = Path("/tmp/archive.json")
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    raw_items = archive.get("items") or []

    def parse_ts(s: str | None):
        if not s:
            return None
        s = str(s).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            try:
                dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                try:
                    dt = datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=SH)
                except Exception:
                    return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=SH)
        return dt.astimezone(SH)

    def norm_title(t: str) -> str:
        t = (t or "").lower().strip()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[|｜·•\-—_]+", " ", t)
        return re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", "", t).strip()

    def norm_url(u: str) -> str:
        if not u:
            return ""
        try:
            p = urlparse(u.strip())
            path = p.path.rstrip("/")
            return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", "", ""))
        except Exception:
            return u.strip().lower()

    cands = []
    for it in raw_items:
        sid = it.get("site_id")
        if sid not in WANT:
            continue
        ts = parse_ts(it.get("published_at")) or parse_ts(it.get("first_seen_at"))
        if not ts or not (win_start <= ts <= win_end):
            continue
        cands.append({**it, "_ts": ts, "_date": ts.date().isoformat()})

    # Prefer items with summary when deduping (keep first after sort)
    cands.sort(key=lambda x: (0 if x.get("summary") else 1, -x["_ts"].timestamp()))
    seen_t: set[str] = set()
    seen_u: set[str] = set()
    deduped = []
    for it in cands:
        nt = norm_title(it.get("title") or "")
        nu = norm_url(it.get("url") or "")
        if nt and nt in seen_t:
            continue
        if nu and nu in seen_u:
            continue
        if nt:
            seen_t.add(nt)
        if nu:
            seen_u.add(nu)
        deduped.append(it)

    cand_count = len(deduped)

    # Optional curated bullets from /tmp/gt-update/news-top10.json (executor-written)
    curated_bullets: dict[str, list[str]] = {}
    curated_path = Path("/tmp/gt-update/news-top10.json")
    if curated_path.exists():
        try:
            for row in json.loads(curated_path.read_text(encoding="utf-8")):
                if row.get("title") and row.get("bullets"):
                    curated_bullets[row["title"]] = list(row["bullets"])[:4]
        except Exception:
            curated_bullets = {}

    model_scores = load_model_scores()
    used_fallback = model_scores is None

    items = []
    for idx, u in enumerate(deduped):
        title = u.get("title") or ""
        summary = (u.get("summary") or "").strip()
        date_s = u["_date"]
        sid = u.get("site_id") or ""
        if model_scores is not None and title in model_scores:
            score = float(model_scores[title])
        else:
            score = rule_score(title, summary)
            # Unscored items stay eligible but won't beat model-picked top unless high rule score
        if title in curated_bullets:
            bullets = curated_bullets[title]
        elif summary:
            bullets = news_bullets(title, summary)
        else:
            # title-only: 2 short bullets, no invention beyond title
            bullets = [
                one_sentence(title, 56),
                "详见原文标题与链接。",
            ]
        site = SITE_LABEL.get(sid, u.get("site_name") or sid)
        items.append({
            "title": title,
            "url": u.get("url") or "",
            "note": summary,
            "meta": f"{site} · {date_s}",
            "date": date_s,
            "score": score,
            "bullets": bullets[:4],
            "_idx": idx,
        })

    # Sort: 资讯重要度 DESC, then 平局日期序 (date DESC)
    items.sort(key=lambda it: (it["score"], it["date"] or ""), reverse=True)
    items = items[:10]

    window = (
        f"近 7 天（{win_start_s} ~ {win_end_s}）· 按重要度 Top 10"
        f" · 雷达 archive · AI 多源 · 候选 {cand_count}"
    )

    gen = archive.get("generated_at") or ""
    try:
        dt = datetime.fromisoformat(gen.replace("Z", "+00:00")).astimezone(
            timezone(timedelta(hours=8))
        )
        gen_label = dt.strftime("%Y-%m-%d %H:%M") + " 北京时间"
    except Exception:
        gen_label = gen or TODAY.isoformat()

    return items, window, gen_label, used_fallback



def render_news(items: list[dict], window: str, gen_label: str, used_fallback: bool) -> str:
    """Render Top N news; default show 重点 (top 3), button expands to all (max 10)."""
    DEFAULT_VISIBLE = 3
    cards = []
    for i, it in enumerate(items):
        badge = ""
        if i < 3:
            badge = '<span class="badge-focus">重点</span>'
        extra_cls = " news-extra" if i >= DEFAULT_VISIBLE else ""
        bullets = "\n".join(f"          <li>{esc(b)}</li>" for b in it["bullets"])
        cards.append(
            f'''      <li class="news-card{extra_cls}">
        <div class="news-card-head">
          <a class="title" href="{esc(it["url"])}" rel="noopener noreferrer">{esc(it["title"])}</a>
          {badge}
        </div>
        <div class="news-meta">{esc(it["meta"])}</div>
        <ul class="news-note">
{bullets}
        </ul>
      </li>'''
        )
    n = len(items)
    collapsed_cls = " is-collapsed" if n > DEFAULT_VISIBLE else ""
    toggle = ""
    if n > DEFAULT_VISIBLE:
        toggle = f'''      <div class="news-toggle-wrap">
        <button type="button" class="news-toggle" id="news-toggle" aria-expanded="false" aria-controls="news-list">展开更多</button>
      </div>
      <script>
      (function () {{
        var btn = document.getElementById("news-toggle");
        var list = document.getElementById("news-list");
        if (!btn || !list) return;
        btn.addEventListener("click", function () {{
          var collapsed = list.classList.toggle("is-collapsed");
          btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
          btn.textContent = collapsed ? "展开更多" : "收起";
        }});
      }})();
      </script>'''
    shown = min(DEFAULT_VISIBLE, n)
    if DEFAULT_VISIBLE == 3 and n >= 3:
        meta_extra = f" · 默认 {shown} 条（重点）"
    else:
        meta_extra = f" · 默认 {shown} 条"
    if n > DEFAULT_VISIBLE:
        meta_extra += f" · 可展开至 {n} 条"
    else:
        meta_extra += f" · 共 {n} 条"
    return f'''    <section class="section" aria-labelledby="news-heading">
      <div class="section-head">
        <h2 id="news-heading">本周 AI 资讯</h2>
        <span class="section-meta">{esc(window)} · 雷达 {esc(gen_label)} · <a href="https://news.learnprompt.pro" rel="noopener noreferrer">news.learnprompt.pro</a>{meta_extra}</span>
      </div>
      <ol class="news-list{collapsed_cls}" id="news-list">
{chr(10).join(cards)}
      </ol>
{toggle}
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
    diagram = flow_html(meta["flow"])
    intro = meta["intro"]
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


def render_page(repos: list[dict], news_html: str, used_fallback: bool) -> str:
    max_week = max((r["week"] for r in repos), default=1) or 1
    cards = "\n\n".join(render_repo_card(i + 1, r, max_week) for i, r in enumerate(repos[:10]))
    foot_extra = " · <strong>重要度降级</strong>" if used_fallback else ""
    return f'''<!DOCTYPE html>
<!-- cache-bust: news-expand-3 -->
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
      <p>最新页始终等于当天 AI 周榜日快照。往期见 <a href="history.html">往期速览</a>。数据抓取时间：{TODAY.isoformat()}（Asia/Shanghai）。资讯按重要度排序{foot_extra}。</p>
    </footer>
  </div>
</body>
</html>
'''


def update_history() -> None:
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
    repos = json.loads(Path("/tmp/gt-update/repos.json").read_text(encoding="utf-8"))
    repos = sorted(repos, key=lambda r: r["week"], reverse=True)[:10]
    news_items, window, gen_label, used_fallback = load_news()
    news_html = render_news(news_items, window, gen_label, used_fallback)
    page = render_page(repos, news_html, used_fallback)

    month_dir = SITE / "archive" / TODAY.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    day_file = month_dir / f"github-trending-weekly-{TODAY.isoformat()}.html"
    day_file.write_text(page, encoding="utf-8")
    (SITE / "index.html").write_text(page, encoding="utf-8")
    update_history()

    # Persist scores used for reproducibility in repo (optional)
    scores_path = SITE / "scripts" / "news-model-scores.json"
    src = Path("/tmp/gt-update/news-model-scores.json")
    if src.exists() and not used_fallback:
        scores_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    meta = {
        "date": TODAY.isoformat(),
        "repos": len(repos),
        "news": len(news_items),
        "news_window": window,
        "used_fallback": used_fallback,
        "top_news": [{"title": it["title"], "score": it["score"], "date": it["date"]} for it in news_items],
        "repo_names": [r["full"] for r in repos],
    }
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
