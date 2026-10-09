# 本周 AI 资讯改用 archive 近 7 天多源

原先只读 `waytoagi-7d.json`。该文件经常只有约两天、十余条 WayToAGI 更新，却仍标注「近 7 天」，窗口名实不符。现改为下载雷达 `archive.json`，筛 `waytoagi` / `official_ai` / `aihot` / `aibase`（及其他明确 AI 源）中、按 Asia/Shanghai 滚动近 7 天（今天往前共 7 个自然日）的条目；按规范化标题与 URL 去重后，再按资讯重要度打分取 Top 10。区块元信息必须写配置窗的真实起止日，并注明「雷达 archive · AI 多源」。

## Why not waytoagi-7d alone

WayToAGI 周窗稀疏时无法支撑「近 7 天」叙事；多源 archive 才能覆盖完整滚动周，同时保留有 summary 的条目优先写分点说明。
