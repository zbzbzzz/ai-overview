#!/usr/bin/env python3
"""Generate 本周 AI 速览: AI weekly repos + archive 7-day multi-source news (ADR 0009/0010/0013)."""
from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

SITE = Path("/workspace/github-trending-site")
TODAY = date(2026, 10, 10)
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
    "DietrichGebert/ponytail": {
        "tag": "懒人技能",
        "flow": ["装技能", "少写代码", "Agent 更稳"],
        "intro": "让 Agent 像懒高级工程师一样少写废话代码。",
    },
    "pbakaus/impeccable": {
        "tag": "设计语言",
        "flow": ["装技能", "约束设计", "少出烂 UI"],
        "intro": "给 AI 编程 Agent 一套前端设计语言与检测规则。",
    },
    "ifixai-ai/iFixAi": {
        "tag": "Agent 审计",
        "flow": ["跑审计", "查对齐", "判是否靠谱"],
        "intro": "独立审计 AI Agent 是否按预期工作。",
    },
    "rohitg00/ai-engineering-from-scratch": {
        "tag": "AI 工程课",
        "flow": ["学原理", "动手建", "交付项目"],
        "intro": "从零学 AI 工程：模型、Agent 到落地交付。",
    },
    "calesthio/OpenMontage": {
        "tag": "智能制片",
        "flow": ["选流水线", "Agent 制作", "出成片"],
        "intro": "开源 agentic 视频制作系统，多流水线与技能包。",
    },
    "addyosmani/agent-skills": {
        "tag": "工程技能",
        "flow": ["复制技能", "约束质量", "交付代码"],
        "intro": "面向 AI 编程 Agent 的生产级工程技能集。",
    },
    "tashfeenahmed/freellmapi": {
        "tag": "免费 LLM 网关",
        "flow": ["接网关", "路由模型", "省 token 费"],
        "intro": "聚合大量免费 LLM 接口到统一 OpenAI 兼容端点。",
    },
    "Leonxlnx/taste-skill": {
        "tag": "审美技能",
        "flow": ["装技能", "约束审美", "少出烂设计"],
        "intro": "给 Agent 加审美约束，减少千篇一律的烂前端。",
    },
    "JuliusBrussee/caveman": {
        "tag": "省 token",
        "flow": ["装代理", "压缩表述", "省上下文"],
        "intro": "用极简表述大幅削减 Agent 上下文 token。",
    },
    "666ghj/MiroFish": {
        "tag": "群体智能",
        "flow": ["组 swarm", "跑预测", "汇总结论"],
        "intro": "简洁通用的群体智能引擎，用于预测与协作。",
    },
    "NVIDIA/OpenShell": {
        "tag": "安全运行时",
        "flow": ["沙箱运行", "约束权限", "托管 Agent"],
        "intro": "面向自主 Agent 的安全私有运行时。",
    },
    "coreyhaines31/marketingskills": {
        "tag": "营销技能",
        "flow": ["装技能", "做增长", "出文案"],
        "intro": "面向 Claude Code 等 Agent 的营销与增长技能包。",
    },
    "p-e-w/heretic": {
        "tag": "模型去审查",
        "flow": ["选模型", "自动处理", "放开输出"],
        "intro": "自动去除语言模型审查限制的工具。",
    },
    "tinyhumansai/openhuman": {
        "tag": "Agent 编排",
        "flow": ["装桌面端", "拉起 Agent", "低成本跑"],
        "intro": "高性价比开源 Agent harness，可大规模并行。",
    },
    "cloudflare/cloudflare-os": {
        "tag": "Agent 工作区",
        "flow": ["接企业上下文", "跑 Workers", "协作产出"],
        "intro": "基于 Cloudflare Workers 的 Agent 生产力工作区。",
    },
    "docker/docker-agent": {
        "tag": "Agent 运行时",
        "flow": ["构建 Agent", "容器运行", "交付能力"],
        "intro": "Docker 出品的 AI Agent 构建与运行时。",
    },
    "bethington/ghidra-mcp": {
        "tag": "逆向 MCP",
        "flow": ["接 MCP", "分析二进制", "喂给 Agent"],
        "intro": "Ghidra MCP Server，给 Agent 逆向工程能力。",
    },
    "ollama/ollama": {
        "tag": "本地模型",
        "flow": ["拉模型", "本机推理", "接应用"],
        "intro": "一键本地运行开源大模型的常用运行时。",
    },
    "AtomicBot-ai/atomic-agent": {
        "tag": "本地 Agent",
        "flow": ["本机部署", "跑开源权重", "私有对话"],
        "intro": "本地优先的 AI Agent，可跑开源权重。",
    },
    "mnfst/awesome-free-llm-apis": {
        "tag": "免费 API 清单",
        "flow": ["查列表", "领 Key", "接模型"],
        "intro": "长期免费 LLM API 与 Key 的精选清单。",
    },
    "zeronsh/zeron": {
        "tag": "控制平面",
        "flow": ["接多 Agent", "统一调度", "本机操控"],
        "intro": "Claude Code / Cursor 等编程 Agent 的原生控制平面。",
    },
    "jamwithai/production-agentic-rag-course": {
        "tag": "RAG 实战课",
        "flow": ["学 RAG", "上生产", "评效果"],
        "intro": "面向生产的 Agentic RAG 课程与实践。",
    },
    "Gaurav-Gosain/tuios": {
        "tag": "终端窗管",
        "flow": ["分屏 pane", "盯 Agent", "并行干活"],
        "intro": "懂 Agent 状态的终端窗口管理器。",
    },
    "LaurieWired/GhidraMCP": {
        "tag": "Ghidra MCP",
        "flow": ["接 MCP", "逆向分析", "Agent 调用"],
        "intro": "Ghidra 的 MCP Server，方便 Agent 调用逆向能力。",
    },
    "xingkongliang/skills-manager": {
        "tag": "技能管理",
        "flow": ["同步技能", "跨工具复用", "一键组织"],
        "intro": "跨多种 AI 工具管理与同步 Agent Skills 的桌面应用。",
    },
    "androoAGI/starnet": {
        "tag": "像素工作站",
        "flow": ["开站台", "Agent 干活", "看像素进展"],
        "intro": "本地优先的像素风工作站，真实 Agent 在里面工作。",
    },
    "Tracer-Cloud/opensre": {
        "tag": "AI SRE",
        "flow": ["装工具包", "建 SRE Agent", "值守排障"],
        "intro": "开源 AI SRE Agent 工具包。",
    },
    "Robbyant/lingbot-map": {
        "tag": "三维重建",
        "flow": ["喂几何上下文", "流式重建", "出三维"],
        "intro": "面向流式三维重建的几何上下文 Transformer。",
    },
    "PurpleDoubleD/locally-uncensored": {
        "tag": "本地 AI 工作室",
        "flow": ["本机安装", "聊天出图", "编码 Agent"],
        "intro": "桌面端一体化本地 AI：聊天、生图视频与编码 Agent。",
    },
    "openai/openai-cookbook": {
        "tag": "OpenAI 菜谱",
        "flow": ["读示例", "调 API", "落地功能"],
        "intro": "OpenAI API 官方示例与实践指南。",
    },
    "anthropics/claude-cookbooks": {
        "tag": "Claude 菜谱",
        "flow": ["读笔记", "复制片段", "接入项目"],
        "intro": "Anthropic Claude 用法菜谱与可复制代码。",
    },
    "nanobrowser/nanobrowser": {
        "tag": "浏览器 Agent",
        "flow": ["装扩展", "多 Agent", "自动上网"],
        "intro": "开源浏览器扩展，用自备 LLM Key 跑网页自动化 Agent。",
    },
    "breferrari/obsidian-mind": {
        "tag": "知识记忆",
        "flow": ["连 Obsidian", "沉淀记忆", "喂给 Agent"],
        "intro": "自组织 Obsidian 库，给编程 Agent 持久记忆。",
    },
    "Agent-Field/CodeAF": {
        "tag": "开源软件厂",
        "flow": ["调度 Agent", "开源模型", "出代码"],
        "intro": "面向开源模型的软件工厂 / Agent 编排。",
    },
    "slavakurilyak/awesome-ai-agents": {
        "tag": "Agent 清单",
        "flow": ["浏览资源", "选型", "动手试"],
        "intro": "300+ Agentic AI 资源精选列表。",
    },
    "AI4Finance-Foundation/FinGPT": {
        "tag": "金融大模型",
        "flow": ["选金融模型", "微调", "落地分析"],
        "intro": "开源金融大模型 FinGPT 与训练资源。",
    },
    "lharries/whatsapp-mcp": {
        "tag": "WhatsApp MCP",
        "flow": ["接 MCP", "读消息", "Agent 交互"],
        "intro": "WhatsApp 的 MCP Server，让 Agent 读写消息。",
    },
    "ed-donner/agents": {
        "tag": "Agent 课程",
        "flow": ["跟课", "写 Agent", "部署上线"],
        "intro": "Agentic AI 工程完整课程配套仓库。",
    },
    "harshuljain13/llm-inference-at-scale": {
        "tag": "推理手册",
        "flow": ["读手册", "选方案", "上生产推理"],
        "intro": "生产级 LLM 推理与服务实践手册。",
    },
    "langchain-ai/agents-from-scratch": {
        "tag": "Agent 入门",
        "flow": ["跟教程", "加记忆", "管邮箱"],
        "intro": "从零搭建带人机协同与记忆的邮件助手 Agent。",
    },
    "ageron/handson-mlp": {
        "tag": "ML 笔记",
        "flow": ["读笔记", "跑示例", "学基础"],
        "intro": "Hands-On ML 配套 Jupyter：Sklearn 与 PyTorch。",
    },
    "rasbt/machine-learning-book": {
        "tag": "ML 书码",
        "flow": ["读章节", "跑代码", "学 PyTorch"],
        "intro": "《Machine Learning with PyTorch and Scikit-Learn》书码。",
    },
    "oracle-devrel/oracle-ai-developer-hub": {
        "tag": "Oracle AI",
        "flow": ["读资源", "接 OCI", "建应用"],
        "intro": "Oracle AI / OCI 开发者技术资源中心。",
    },
    "morluto/rea": {
        "tag": "逆向 Agent",
        "flow": ["接 Agent", "逆向分析", "复刻逻辑"],
        "intro": "用 Agent 逆向应用与原生二进制。",
    },
    "cathrynlavery/diagram-design": {
        "tag": "图表技能",
        "flow": ["装技能", "出图示", "少 Mermaid 烂图"],
        "intro": "给编程 Agent 的编辑级图表设计技能。",
    },
    "alibaba/open-code-review": {
        "tag": "代码评审",
        "flow": ["跑流水线", "LLM 评审", "落注释"],
        "intro": "阿里开源的混合架构代码评审：确定性流水线 + LLM Agent。",
    },
    "anthropics/knowledge-work-plugins": {
        "tag": "知识工作插件",
        "flow": ["装插件", "定角色", "办公协作"],
        "intro": "面向知识工作者的 Claude 插件合集。",
    },
    "BerriAI/litellm": {
        "tag": "LLM 网关",
        "flow": ["接网关", "统一 API", "计量护栏"],
        "intro": "开源 AI 网关：百余 LLM 统一调用与成本追踪。",
    },
    "twostraws/SwiftUI-Agent-Skill": {
        "tag": "SwiftUI 技能",
        "flow": ["装技能", "写 SwiftUI", "少踩坑"],
        "intro": "面向 Claude Code / Codex 的 SwiftUI Agent Skill。",
    },
    "JayWebtech/autoshorts": {
        "tag": "短视频剪辑",
        "flow": ["导入长视频", "AI 挑高光", "导出竖屏"],
        "intro": "本地优先桌面端：长视频/音频转竖屏短片，AI 排序爆款片段。",
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


.repo-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.85rem 0 0.15rem;
}
.repo-tab {
  appearance: none;
  border: 1px solid var(--mist);
  background: var(--snow);
  color: var(--navy);
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.38rem 0.78rem;
  border-radius: 999px;
  cursor: pointer;
  line-height: 1.2;
}
.repo-tab:hover { background: var(--ice); border-color: var(--aqua); }
.repo-tab[aria-selected="true"] {
  background: var(--navy);
  border-color: var(--navy);
  color: #fff;
}
.repo-tab .cnt {
  font-weight: 650;
  opacity: 0.75;
  margin-left: 0.2rem;
}
.repo-panel[hidden] { display: none !important; }
.repo-panel .cards { margin-top: 0.85rem; }
.repo-empty {
  margin-top: 0.85rem;
  padding: 1rem 1.1rem;
  background: var(--ice);
  border: 1px dashed var(--mist);
  border-radius: 12px;
  color: var(--mute);
  font-size: 0.9rem;
}

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
.news-related {
  margin-top: 0.45rem;
  font-size: 0.75rem;
  color: var(--mute);
  line-height: 1.45;
}
.news-related summary {
  cursor: pointer;
  font-weight: 700;
  color: var(--sky);
  list-style: none;
}
.news-related summary::-webkit-details-marker { display: none; }
.news-related summary::before {
  content: "▸ ";
  color: var(--aqua);
}
.news-related[open] summary::before { content: "▾ "; }
.news-related ul {
  list-style: none;
  margin: 0.35rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.news-related a {
  color: var(--navy);
  font-weight: 650;
  text-decoration: none;
}
.news-related a:hover { color: var(--sky); text-decoration: underline; }
.news-related .src {
  color: var(--mute);
  font-weight: 600;
  margin-right: 0.35rem;
}
'''



def blankify_links(html_doc: str) -> str:
    """Ensure every clickable <a> opens in a new tab."""
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        if re.search(r'\btarget\s*=\s*"_blank"', tag, re.I):
            if re.search(r'\brel\s*=', tag, re.I):
                def fix_rel(rm):
                    vals = rm.group(1).split()
                    lower = {v.lower() for v in vals}
                    for need in ("noopener", "noreferrer"):
                        if need not in lower:
                            vals.append(need)
                    return f'rel="{" ".join(vals)}"'
                return re.sub(r'\brel\s*=\s*"([^"]*)"', fix_rel, tag, count=1, flags=re.I)
            return tag[:-1] + ' rel="noopener noreferrer">'
        if re.search(r'\brel\s*=', tag, re.I):
            tag = re.sub(r'(<a\b)', r'\1 target="_blank"', tag, count=1, flags=re.I)
            def fix_rel(rm):
                vals = rm.group(1).split()
                lower = {v.lower() for v in vals}
                for need in ("noopener", "noreferrer"):
                    if need not in lower:
                        vals.append(need)
                return f'rel="{" ".join(vals)}"'
            return re.sub(r'\brel\s*=\s*"([^"]*)"', fix_rel, tag, count=1, flags=re.I)
        return re.sub(r'(<a\b)', r'\1 target="_blank" rel="noopener noreferrer"', tag, count=1, flags=re.I)
    return re.sub(r'<a\s[^>]*>', repl, html_doc, flags=re.I)


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


REPO_TYPES = ["Skill", "Agent", "模型与推理", "应用与产品", "开发工具链", "数据与评测"]
TAB_DEFS = [("总榜", None)] + [(t, t) for t in REPO_TYPES]
CACHE_PATH = SITE / "data" / "repo-type-cache.json"

TYPE_KW = {
    "Skill": [r"\bskills?\b", r"\bmcp\b", r"model context protocol", r"agent-skills"],
    "Agent": [r"\bagents?\b", r"agentic", r"multi-agent", r"智能体", r"harness", r"orchestration"],
    "模型与推理": [r"\bllm\b", r"inference", r"vllm", r"\bollama\b", r"transformer", r"embedding",
               r"deep learning", r"machine learning", r"language model", r"微调", r"推理"],
    "应用与产品": [r"desktop", r"\bapp\b", r"studio", r"chrome extension", r"end-?user",
               r"video production", r"product"],
    "开发工具链": [r"\bsdk\b", r"\bcli\b", r"devtools", r"\bplugin", r"gateway", r"runtime",
               r"cookbook", r"\bide\b", r"observ"],
    "数据与评测": [r"benchmark", r"\beval", r"dataset", r"\bcourse\b", r"notebook", r"awesome",
               r"handbook", r"审计", r"alignment", r"评测"],
}


def keyword_classify_repo(repo: dict) -> list[str]:
    blob = " ".join([
        repo.get("full") or "",
        repo.get("name") or "",
        repo.get("desc") or "",
        " ".join(repo.get("topics") or []),
        repo.get("readme_snip") or "",
    ]).lower()
    types: list[str] = []
    for t, pats in TYPE_KW.items():
        if any(re.search(p, blob, re.I) for p in pats):
            types.append(t)
    if re.search(r"\bmcp\b", blob) and "Skill" not in types:
        types.insert(0, "Skill")
    out: list[str] = []
    for t in types:
        if t not in out:
            out.append(t)
    return out or ["开发工具链"]


def load_type_cache() -> dict:
    for p in (CACHE_PATH, Path("/tmp/gt-update/repo-type-cache.json")):
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


def save_type_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify_repos(repos: list[dict], cache: dict) -> tuple[list[dict], dict, bool]:
    """Attach types. Prefer cache; keyword fallback. Executor writes model labels into cache."""
    used_kw_fallback = False
    today = TODAY.isoformat()
    for repo in repos:
        key = repo["full"]
        entry = cache.get(key)
        if entry is None:
            for ck, cv in cache.items():
                if ck.lower() == key.lower():
                    entry = cv
                    break
        types = None
        if isinstance(entry, dict):
            types = entry.get("types")
        elif isinstance(entry, list):
            types = entry
        if types:
            repo["types"] = [t for t in types if t in REPO_TYPES]
        else:
            repo["types"] = keyword_classify_repo(repo)
            used_kw_fallback = True
            cache[key] = {"types": repo["types"], "updated": today, "source": "keyword-fallback"}
        repo["types"] = [t for t in (repo.get("types") or []) if t in REPO_TYPES]
    return repos, cache, used_kw_fallback


def build_tab_lists(overall: list[dict], pool: list[dict]) -> dict[str, list[dict]]:
    """总榜与分榜共用同一 AI 大候选池；总榜按本周星序 Top 10（不再用窄周榜切片）。"""
    # overall kept for API compat / logging; ranking source is pool
    base = pool if pool else overall
    tabs: dict[str, list[dict]] = {
        "总榜": sorted(base, key=lambda r: r["week"], reverse=True)[:10]
    }
    for t in REPO_TYPES:
        members = [r for r in base if t in (r.get("types") or [])]
        members = sorted(members, key=lambda r: r["week"], reverse=True)[:10]
        tabs[t] = members
    return tabs



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


def load_news_bundles() -> list[dict] | None:
    """Load executor-confirmed 资讯束 (ADR 0013). None => merge failure / missing."""
    for p in (
        Path("/tmp/gt-update/news-bundles.json"),
        SITE / "scripts" / "news-bundles.json",
    ):
        if not p.exists():
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(raw, list) or not raw:
                continue
            out = []
            for row in raw:
                title = (row.get("title") or "").strip()
                url = (row.get("url") or "").strip()
                if not title or not url:
                    continue
                links = row.get("links") or []
                norm_links = []
                seen = set()
                for link in links:
                    lu = (link.get("url") or "").strip()
                    if not lu or lu in seen:
                        continue
                    seen.add(lu)
                    norm_links.append({
                        "label": link.get("label") or "来源",
                        "title": link.get("title") or title,
                        "url": lu,
                        "date": link.get("date") or "",
                    })
                if not any(link["url"] == url for link in norm_links):
                    norm_links.insert(0, {
                        "label": "主链",
                        "title": title,
                        "url": url,
                        "date": row.get("date") or "",
                    })
                norm_links = [link for link in norm_links if link["url"] == url] + [
                    link for link in norm_links if link["url"] != url
                ]
                bullets = list(row.get("bullets") or [])[:4]
                if len(bullets) < 2:
                    summary = (row.get("summary") or row.get("note") or "").strip()
                    bullets = (
                        news_bullets(title, summary)
                        if summary
                        else [one_sentence(title, 56), "详见原文链接。"]
                    )
                out.append({
                    "title": title,
                    "url": url,
                    "links": norm_links,
                    "bullets": bullets[:4],
                    "date": row.get("date") or "",
                    "meta": row.get("meta") or "",
                    "score": float(row["score"]) if isinstance(row.get("score"), (int, float)) else None,
                    "score_parts": row.get("score_parts"),
                    "note": row.get("summary") or row.get("note") or "",
                })
            if out:
                return out
        except Exception:
            return None
    return None


def load_news() -> tuple[list[dict], str, str, bool, bool]:
    """Return (items top10, window, gen_label, score_fallback, merge_fallback).

    Pipeline (ADR 0010/0013): radar archive, AI multi-source, rolling 7 days.
    Prefer executor 资讯束 (content-merge); else title/URL dedupe + 合并降级.
    Score bundles by executor model, Top 10.
    """
    from zoneinfo import ZoneInfo
    from urllib.parse import urlparse, urlunparse

    SH = ZoneInfo("Asia/Shanghai")
    now = datetime.now(SH)
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

    seen_u_all: set[str] = set()
    url_unique = 0
    for it in cands:
        nu = norm_url(it.get("url") or "")
        if nu and nu in seen_u_all:
            continue
        if nu:
            seen_u_all.add(nu)
        url_unique += 1

    bundles = load_news_bundles()
    merge_fallback = bundles is None
    model_scores = load_model_scores()
    score_fallback = model_scores is None

    curated_bullets: dict[str, list[str]] = {}
    curated_path = Path("/tmp/gt-update/news-top10.json")
    if curated_path.exists():
        try:
            for row in json.loads(curated_path.read_text(encoding="utf-8")):
                if row.get("title") and row.get("bullets"):
                    curated_bullets[row["title"]] = list(row["bullets"])[:4]
        except Exception:
            curated_bullets = {}

    items: list[dict] = []
    if bundles is not None:
        cand_count = url_unique
        for idx, b in enumerate(bundles):
            title = b["title"]
            summary = b.get("note") or ""
            if b.get("score") is not None:
                score = float(b["score"])
            elif model_scores is not None and title in model_scores:
                score = float(model_scores[title])
            elif (
                b.get("score_parts")
                and isinstance(b["score_parts"], dict)
                and {"industry", "actionable", "breadth"} <= set(b["score_parts"])
            ):
                score = weighted_score(b["score_parts"])
            else:
                score = rule_score(title, summary)
            bullets = b["bullets"]
            # Bundle bullets win; curated only fills if bundle bullets too short
            if len(bullets) < 2 and title in curated_bullets:
                bullets = curated_bullets[title]
            meta = b.get("meta") or ""
            if not meta:
                labels = []
                for link in b.get("links") or []:
                    lab = link.get("label") or ""
                    if lab and lab not in labels:
                        labels.append(lab)
                meta = f"{' / '.join(labels[:3]) or '多源'} · {b.get('date') or ''}"
                if len(b.get("links") or []) > 1:
                    meta += f" · {len(b['links'])} 源"
            items.append({
                "title": title,
                "url": b["url"],
                "links": b.get("links") or [
                    {"label": "主链", "title": title, "url": b["url"], "date": b.get("date") or ""}
                ],
                "note": summary,
                "meta": meta,
                "date": b.get("date") or "",
                "score": score,
                "bullets": bullets[:4],
                "_idx": idx,
            })
    else:
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
        for idx, u in enumerate(deduped):
            title = u.get("title") or ""
            summary = (u.get("summary") or "").strip()
            date_s = u["_date"]
            sid = u.get("site_id") or ""
            if model_scores is not None and title in model_scores:
                score = float(model_scores[title])
            else:
                score = rule_score(title, summary)
            if title in curated_bullets:
                bullets = curated_bullets[title]
            elif summary:
                bullets = news_bullets(title, summary)
            else:
                bullets = [one_sentence(title, 56), "详见原文标题与链接。"]
            site = SITE_LABEL.get(sid, u.get("site_name") or sid)
            url = u.get("url") or ""
            items.append({
                "title": title,
                "url": url,
                "links": [{"label": site, "title": title, "url": url, "date": date_s}],
                "note": summary,
                "meta": f"{site} · {date_s}",
                "date": date_s,
                "score": score,
                "bullets": bullets[:4],
                "_idx": idx,
            })

    items.sort(key=lambda it: (it["score"], it["date"] or ""), reverse=True)
    items = items[:10]

    mode = "资讯束" if not merge_fallback else "标题去重"
    window = (
        f"近 7 天（{win_start_s} ~ {win_end_s}）· 按重要度 Top 10"
        f" · 雷达 archive · AI 多源 · 候选 {cand_count} · {mode}"
    )

    gen = archive.get("generated_at") or ""
    try:
        dt = datetime.fromisoformat(gen.replace("Z", "+00:00")).astimezone(
            timezone(timedelta(hours=8))
        )
        gen_label = dt.strftime("%Y-%m-%d %H:%M") + " 北京时间"
    except Exception:
        gen_label = gen or TODAY.isoformat()

    return items, window, gen_label, score_fallback, merge_fallback


def render_news(items: list[dict], window: str, gen_label: str, used_fallback: bool) -> str:
    """Render Top N 资讯束; default show 重点 (top 3), expand to max 10."""
    DEFAULT_VISIBLE = 3
    cards = []
    for i, it in enumerate(items):
        badge = ""
        if i < 3:
            badge = '<span class="badge-focus">重点</span>'
        extra_cls = " news-extra" if i >= DEFAULT_VISIBLE else ""
        bullets = "\n".join(f"          <li>{esc(b)}</li>" for b in it["bullets"])
        links = it.get("links") or []
        related = ""
        extras = [link for link in links if link.get("url") and link["url"] != it["url"]]
        if extras:
            n_extra = len(extras)
            lis = []
            for link in extras:
                lab = esc(link.get("label") or "来源")
                href = esc(link["url"])
                ltitle = esc(link.get("title") or link.get("label") or "相关报道")
                lis.append(
                    f'            <li><span class="src">{lab}</span>'
                    f'<a href="{href}" target="_blank" rel="noopener noreferrer">{ltitle}</a></li>'
                )
            related = (
                f'        <details class="news-related">\n'
                f'          <summary>另 {n_extra} 篇报道</summary>\n'
                f'          <ul>\n'
                + "\n".join(lis)
                + "\n          </ul>\n"
                + "        </details>"
            )
        cards.append(
            "      <li class=\"news-card" + extra_cls + "\">\n"
            + '        <div class="news-card-head">\n'
            + f'          <a class="title" href="{esc(it["url"])}" target="_blank" rel="noopener noreferrer">{esc(it["title"])}</a>\n'
            + f"          {badge}\n"
            + "        </div>\n"
            + f'        <div class="news-meta">{esc(it["meta"])}</div>\n'
            + '        <ul class="news-note">\n'
            + bullets + "\n"
            + "        </ul>\n"
            + (related + "\n" if related else "")
            + "      </li>"
        )
    n = len(items)
    collapsed_cls = " is-collapsed" if n > DEFAULT_VISIBLE else ""
    toggle = ""
    if n > DEFAULT_VISIBLE:
        toggle = (
            '      <div class="news-toggle-wrap">\n'
            '        <button type="button" class="news-toggle" id="news-toggle" aria-expanded="false" aria-controls="news-list">展开更多</button>\n'
            "      </div>\n"
            "      <script>\n"
            "      (function () {\n"
            '        var btn = document.getElementById("news-toggle");\n'
            '        var list = document.getElementById("news-list");\n'
            "        if (!btn || !list) return;\n"
            '        btn.addEventListener("click", function () {\n'
            '          var collapsed = list.classList.toggle("is-collapsed");\n'
            '          btn.setAttribute("aria-expanded", collapsed ? "false" : "true");\n'
            '          btn.textContent = collapsed ? "展开更多" : "收起";\n'
            "        });\n"
            "      })();\n"
            "      </script>"
        )
    shown = min(DEFAULT_VISIBLE, n)
    if DEFAULT_VISIBLE == 3 and n >= 3:
        meta_extra = f" · 默认 {shown} 条（重点）"
    else:
        meta_extra = f" · 默认 {shown} 条"
    if n > DEFAULT_VISIBLE:
        meta_extra += f" · 可展开至 {n} 条"
    else:
        meta_extra += f" · 共 {n} 条"
    return (
        '    <section class="section" aria-labelledby="news-heading">\n'
        '      <div class="section-head">\n'
        '        <h2 id="news-heading">本周 AI 资讯</h2>\n'
        '        <span class="section-meta">'
        + esc(window)
        + " · 雷达 "
        + esc(gen_label)
        + ' · <a href="https://news.learnprompt.pro" target="_blank" rel="noopener noreferrer">news.learnprompt.pro</a>'
        + meta_extra
        + "</span>\n"
        + "      </div>\n"
        + f'      <ol class="news-list{collapsed_cls}" id="news-list">\n'
        + "\n".join(cards)
        + "\n"
        + "      </ol>\n"
        + (toggle + "\n" if toggle else "")
        + "    </section>"
    )


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
            <a class="name" href="https://github.com/{esc(name)}" target="_blank" rel="noopener noreferrer">{esc(name)}</a>
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

def render_repo_section(tabs: dict[str, list[dict]]) -> str:
    panels = []
    tab_btns = []
    for i, (label, _) in enumerate(TAB_DEFS):
        repos = tabs.get(label) or []
        selected = "true" if i == 0 else "false"
        tab_id = f"repo-tab-{i}"
        panel_id = f"repo-panel-{i}"
        tab_btns.append(
            f'<button type="button" class="repo-tab" role="tab" id="{tab_id}" '
            f'aria-selected="{selected}" aria-controls="{panel_id}" data-tab-index="{i}">'
            f'{esc(label)}<span class="cnt">{len(repos)}</span></button>'
        )
        max_week = max((r["week"] for r in repos), default=1) or 1
        if repos:
            cards = "\n\n".join(render_repo_card(j + 1, r, max_week) for j, r in enumerate(repos))
            body = f'<ol class="cards">\n\n{cards}\n\n    </ol>'
        else:
            body = '<p class="repo-empty">本周该分类暂无足够条目。</p>'
        hidden = "" if i == 0 else " hidden"
        panels.append(
            f'<div class="repo-panel" role="tabpanel" id="{panel_id}" '
            f'aria-labelledby="{tab_id}"{hidden}>\n{body}\n    </div>'
        )

    script = '\n      <script>\n      (function () {\n        var tabs = Array.prototype.slice.call(document.querySelectorAll(".repo-tab"));\n        var panels = Array.prototype.slice.call(document.querySelectorAll(".repo-panel"));\n        if (!tabs.length) return;\n        function activate(idx) {\n          tabs.forEach(function (btn, i) {\n            var on = i === idx;\n            btn.setAttribute("aria-selected", on ? "true" : "false");\n            if (panels[i]) {\n              if (on) panels[i].removeAttribute("hidden");\n              else panels[i].setAttribute("hidden", "");\n            }\n          });\n        }\n        tabs.forEach(function (btn) {\n          btn.addEventListener("click", function () {\n            activate(parseInt(btn.getAttribute("data-tab-index"), 10) || 0);\n          });\n        });\n      })();\n      </script>'

    return f'''    <div class="section-head" style="margin-top:1.15rem;margin-bottom:0">
      <h2>AI 周榜仓库</h2>
      <span class="section-meta">总榜 + 分榜 · 按本周新增星标 · 可多榜</span>
    </div>
    <div class="repo-tabs" role="tablist" aria-label="仓库分榜">
      {chr(10).join("      " + b for b in tab_btns)}
    </div>
{chr(10).join(panels)}
{script}'''


def render_page(tabs: dict[str, list[dict]], news_html: str, used_fallback: bool, type_fallback: bool, merge_fallback: bool = False) -> str:
    repo_html = render_repo_section(tabs)
    foot_extra = ""
    if used_fallback:
        foot_extra += " · <strong>重要度降级</strong>"
    if merge_fallback:
        foot_extra += " · <strong>合并降级</strong>"
    if type_fallback:
        foot_extra += " · <strong>分类降级</strong>"
    return f'''<!DOCTYPE html>
<!-- cache-bust: news-bundles-0013 -->
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
          <a href="history.html" target="_blank" rel="noopener noreferrer">往期速览</a>
          <a href="https://github.com/trending?since=weekly" target="_blank" rel="noopener noreferrer">GitHub Trending</a>
        </nav>
      </div>
    </header>

{news_html}

    <hr class="section-divider" />

{repo_html}

    <footer class="foot">
      <p>最新页始终等于当天 AI 周榜日快照。往期见 <a href="history.html" target="_blank" rel="noopener noreferrer">往期速览</a>。数据抓取时间：{TODAY.isoformat()}（Asia/Shanghai）。资讯按资讯束重要度排序（ADR 0013）；仓库分榜见 ADR 0012{foot_extra}。</p>
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
            f'          <li><a href="archive/{month}/github-trending-weekly-{d}.html" target="_blank" rel="noopener noreferrer">{d}</a></li>'
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
          <a href="index.html" target="_blank" rel="noopener noreferrer">最新速览</a>
          <a href="https://github.com/trending?since=weekly" target="_blank" rel="noopener noreferrer">GitHub Trending</a>
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
    history = blankify_links(history)
    (SITE / "history.html").write_text(history, encoding="utf-8")



def main() -> None:
    overall = json.loads(Path("/tmp/gt-update/repos.json").read_text(encoding="utf-8"))
    pool_path = Path("/tmp/gt-update/repos-pool.json")
    if pool_path.exists():
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
    else:
        pool = list(overall)

    by_full: dict[str, dict] = {}
    for r in pool + overall:
        k = r["full"]
        if k not in by_full or r.get("week", 0) > by_full[k].get("week", 0):
            by_full[k] = r
    pool = list(by_full.values())

    cache = load_type_cache()
    pool, cache, type_fallback = classify_repos(pool, cache)
    type_map = {r["full"]: r.get("types") or [] for r in pool}
    for r in overall:
        r["types"] = type_map.get(r["full"]) or keyword_classify_repo(r)
    save_type_cache(cache)

    tabs = build_tab_lists(overall, pool)

    news_items, window, gen_label, used_fallback, merge_fallback = load_news()
    news_html = render_news(news_items, window, gen_label, used_fallback)
    page = render_page(tabs, news_html, used_fallback, type_fallback, merge_fallback)

    month_dir = SITE / "archive" / TODAY.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    day_file = month_dir / f"github-trending-weekly-{TODAY.isoformat()}.html"
    page = blankify_links(page)
    day_file.write_text(page, encoding="utf-8")
    (SITE / "index.html").write_text(page, encoding="utf-8")
    update_history()

    scores_path = SITE / "scripts" / "news-model-scores.json"
    src = Path("/tmp/gt-update/news-model-scores.json")
    if src.exists() and not used_fallback:
        scores_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    bundles_src = Path("/tmp/gt-update/news-bundles.json")
    bundles_dst = SITE / "scripts" / "news-bundles.json"
    if bundles_src.exists() and not merge_fallback:
        bundles_dst.write_text(bundles_src.read_text(encoding="utf-8"), encoding="utf-8")

    counts = {k: len(v) for k, v in tabs.items()}
    meta = {
        "date": TODAY.isoformat(),
        "tabs": counts,
        "pool": len(pool),
        "news": len(news_items),
        "news_window": window,
        "used_fallback": used_fallback,
        "merge_fallback": merge_fallback,
        "type_fallback": type_fallback,
        "top_news": [{"title": it["title"], "score": it["score"], "date": it["date"], "sources": len(it.get("links") or [])} for it in news_items],
        "repo_names_overall": [r["full"] for r in tabs.get("总榜") or []],
        "tab_repos": {k: [r["full"] for r in v] for k, v in tabs.items()},
    }
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
