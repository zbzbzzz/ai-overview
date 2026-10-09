# GitHub Trending 日快照站

每天早上抓取 GitHub Trending 周榜 Top 10，生成可浏览的网页并归档、推送通知。

## Language

**日快照**：
某一天早上抓取到的周榜 Top 10 对应的完整 HTML 页面。
_Avoid_: 日报, 日榜

**最新页**：
站点根目录的 `index.html`，内容始终等于当天日快照。
_Avoid_: 首页副本, 主页快照

**月归档**：
按自然月存放的历史日快照集合，路径为 `archive/YYYY-MM/`。
_Avoid_: 历史夹, 存档目录

**历史周榜**：
站内按月浏览往日日快照的导航能力。
_Avoid_: 归档浏览器, 历史列表页
