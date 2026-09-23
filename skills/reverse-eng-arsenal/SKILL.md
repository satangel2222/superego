---
name: reverse-eng-arsenal
description: >-
  D:\revtools 逆向/抓取工具库的能力说明书+路由表。做"逆向复刻网站、抓公开数据、挖REST或GraphQL隐藏接口、绕反爬、代理轮换"这类活之前先查本表选对工具、按最强套装串流水线。与 browser-routing.md（浏览器工具分工）、anti-scraping（反爬/CF/各平台策略）、scrapling-official（scrapling 专属）互补，不重复。2026-07-03 全库21路本地实测校准。
---

> [!NOTE]
> 本技能由 **AG SkillHub** 自动从 Claude 深度转译并接入 Antigravity 原生规范。

# 逆向 · 抓取 工具库说明书 + 路由（D:\revtools）

> 2026-07-03 用 21 个审计员逐个本地实测（import/API/README/依赖）校准出的真实边界，不是纸面拼凑。
> 相邻的三份别混：**浏览器工具选哪个**→ `~/.claude/browser-routing.md`；**反爬/CF/各平台策略**→ `anti-scraping` skill；**scrapling 怎么用**→ `scrapling-official` skill。本表管的是"**逆向复刻/抓公开数据/挖接口**"这条线上的工具选型与组合。

## ⛔ 三条铁律（动手前必读）

0. **⛔「接管已开的真实 Chrome」有边界 —— 只能接管【我自己起的】那个，不是他的（2026-08-20 Frank 亲口）。**
   本表下面多处推荐 `patchright connectOverCDP` / DrissionPage 接管真实浏览器，**那指的是我自己
   `launch_persistent_context` 起的独立实例**（独立 user-data-dir + 自选端口）。
   ⛔ **不得接管 `9226`(openclaw/obsidian 知识库) 或 `9555`(bananaflow)** —— 他的资产，PreToolUse
   `his-browser-guard.cjs` 会硬拦。要登录态就打开登录页截图请他登，登录态存我自己 profile 复用。
   （`9333`/`9334` 是 dev-diary 专门开给程序连的，不在此限。）

1. **强登录墙站（X / 小红书 / 微博 / Airbnb 房东后台等）只用已登录真实会话**（`logged-in-platform-ops` / `opencli` / `web-access`），**绝不用本库任何反检测浏览器（camoufox/seleniumbase/patchright/uc/botasaurus/crawlee 浏览器模式）起新指纹 launch()** —— 新指纹登你自己号 = 封号（X 永久冻结有案底）。
2. **别猛探测。** 限速目标单线程慢慢来；一旦 IP 被 Cloudflare 打花（`Just a moment` / `cf-mitigated: challenge`），**本地任何反检测工具都救不了**（连 Camoufox 都拿到挑战页）——只能等冷却或配住宅代理轮换，**绝不再撞**（2026-07-03 Social Blade 血案）。

## 1. 路由表：遇到 X → 用 Y

| 遇到的场景 | 用哪个 | 为什么 |
|---|---|---|
| **接管自己已登录会话**在一般后台批量读/改数据 | **DrissionPage**（浏览器登录/过交互 → `change_mode()` 转 HTTP 带同一套 cookie 批量抓/改），或 `patchright connectOverCDP` 接管已开的真实 Chrome | 同一会话在真实浏览器↔requests 收发包间无缝流转、带登录态、不新起指纹，符合封号铁律；DrissionPage 内置 CDP Listener 还能顺手抓 XHR/fetch 响应逆向隐藏接口 |
| **强登录墙站**（X/XHS/微博/Airbnb 后台）登录态读写 | `logged-in-platform-ops` / `opencli` / `web-access` skill | 铁律：这些站只喂已登录真实会话，本库反检测浏览器一律不许对它们起新实例 |
| **抓不需登录的公开 HTML/JSON、要快** | **curl_cffi**（`impersonate="chrome"` 等） | 纯 HTTP 速度拿到浏览器级 TLS/JA3+HTTP2 指纹、无浏览器进程；anti-scraping 快路径先锋。不执行 JS，撞 CF JS 挑战再降级 |
| **撞 Cloudflare JS 挑战 / 需真实渲染 DOM 或截图** | **camoufox**（Firefox 引擎级反检测）主力；必须伪装 Chrome 内核时用 **seleniumbase** UC/CDP 或 **patchright**（叠 rebrowser-patches） | camoufox 在 Firefox 源码层改指纹、JS 检测读不到痕迹，已被 anti-scraping/雷达实际依赖；查 SpiderMonkey 的 WAF 过不去才轮到 Chromium 兜底 |
| **大规模爬很多页**（队列/去重/自动扩缩/重试/落盘） | **crawlee**（Node，HTTP 模式）或 **scrapling** spider | 唯一的规模化编排引擎，单发抓取工具给不了队列+扩缩+代理轮换+落盘；crawlee 浏览器模式走新指纹 launch，登录墙站禁用 |
| **站点常改版让 CSS/XPath 选择器失效** | **scrapling** 自适应解析（AutoMatch/find_similar/generate_css_selector） | 靠元素指纹页面改版后自动重定位，bs4/parsel 没这能力 |
| **抓页面直接要 LLM-ready 干净 markdown（喂 AI 读/做研究）** | **crawl4ai** `v0.9.3` —— ⛔ 跑它必须 **`py -3.12`**（2026-09-09 实测：`py -3`/py3.14 里**没有**，此前记的 v0.9.2@py3.14 已失效） | 独门：patchright 浏览器渲染 JS 页 → **一步转干净 markdown**（自动去广告/导航），别的工具抓 HTML 还要自己清洗；支持批量+LLM 结构化提取。用法 `from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode; async with AsyncWebCrawler() as c: r=await c.arun(url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)); r.markdown`（⛔ 不传 BYPASS 会吃缓存，第二次跑测的是缓存不是抓取）。自带 CLI `crwl <url> -o markdown`、`--deep-crawl bfs --max-pages N` 整站爬；但 CLI 每次冷启浏览器约 20s，批量一律走 Python API 的 `arun_many`（浏览器只起一次）。官方自检 `crawl4ai-doctor`。边界：重渲染比 curl_cffi 慢；登录墙站守封号铁律不起新指纹 |
| **从成品站点直接取结构化数据**（HN / dev.to / GitHub trending 等**纯 API 型**站点） | **AutoCLI** `v0.3.8`（`~/bin/autocli.exe`，Rust 单文件）—— 这类活默认用它 | 2026-09-09 实测：标称 **70 个站点**（opencli 33 个），抓 HN 前 5 条 **1.64s vs opencli 14.99s = 快 9.1 倍**。它是 `@jackwener/opencli` 的纯 Rust 重写版。⛔⛔ **但「70 个」是标称，当前实际可用的只有免扩展那部分** —— 抽样实测：✅ 免扩展直接跑 `hackernews` / `devto` / `github`；❌ `arxiv` / `douban` / `bilibili` 等报 `Chrome extension not connected`，**要先装它的 Chrome 扩展**（release 里的 `autocli-chrome-extension.zip`，**本机未装**）。⇒ 用之前先跑一次 `autocli <站点> <子命令>` 看会不会报 extension；⛔ 子命令名必须 `autocli <站点> --help` 现查（我编过 `movie-top250`/`popular`/`--limit` 全是错的）。**要登录态/被扩展挡住时才回退 opencli**（它另有 11 个 AutoCLI 没有的站点：baidu-scholar / deepseek / duckduckgo / github-trending / juejin / manus / ones / producthunt / semanticscholar / suno / discord，及 adapter/plugin/profile 机制）。 |
| **逆向没文档的 REST 后台/App → 生成接口文档** | **mitmproxy**（mitmdump）抓流量 → .flow/HAR → **mitmproxy2swagger**（读 .flow）或 **har-to-openapi**（读 HAR）转 OpenAPI 3.0 | mitmproxy 是唯一能解密并录下手机 App/桌面客户端（DevTools 够不到）真实流量的；两个转换器把真实流量机械固化成 spec 当逆向底图/喂 codegen |
| **GraphQL 端点 introspection 被关、要还原隐藏 schema** | **clairvoyance**（blind introspection，靠服务器报错 oracle+词表重建 schema） | 内省被禁也能逐字段猜出 query/mutation/参数，别的工具做不到；但依赖目标返回 "Did you mean" 式详细报错 |
| **GraphQL introspection 开着、要枚举全部操作/看 schema 全貌** | **gqlspection**（schema JSON → 可直接发的 query/mutation codegen）+ **graphql-voyager**（schema 关系图可视化） | gqlspection 把"能问什么"列成带嵌套字段+参数的成品查询体；voyager 画成图肉眼定位可挖字段。与 clairvoyance 互补（开/关内省两场景） |
| **需要代理池轮换换 IP** | **crawlee**（ProxyConfiguration+session 池）或 **scrapling** spider 做轮换；**camoufox** 开 `geoip=True` 按代理出口 IP 自动对齐时区/locale | 编排层负责轮换本身；camoufox 补上"换了 IP 但时区/语言不匹配露馅"这块 |
| **现成 puppeteer/playwright 脚本被 CF/DataDome 靠 CDP 泄露识别** | **rebrowser-patches** 给 puppeteer-core/playwright-core 源码打补丁去泄露，或换 **patchright**（drop-in 替代） | 库/driver 层去掉自动化红旗、保留原 API 零改造；只补 CDP 层，仍需叠代理+真实指纹+登录 session |
| **必须落在 Selenium 生态又要反检测 / 把爬虫做成成品桌面 App 或上 K8s** | **undetected-chromedriver**（Selenium drop-in、去 cdc_ 哨兵）/ **botasaurus**（装饰器 all-in-one，自带纯 CDP undetected Chrome + 一键打包） | 各占独特框架生态位：前者补已有 selenium 代码的指纹，后者把并行/缓存/profiles/落盘/打包全接线好交付成品 |

## 2. 最强套装：一条逆向流水线（一件占一环、零重叠）

**接管会话 → 抓包 → 转 spec → 挖 GraphQL → 反爬+代理轮换**，10 件串成：

1. **接管会话 + 采集** — `DrissionPage` 真实 Chrome 登录/过交互，`change_mode()` 转 HTTP 带同 cookie 批量取数；内置 CDP Listener 抓 XHR/fetch 响应。
2. **抓包**（App/桌面客户端等 DevTools 够不到的）— `mitmproxy`（mitmdump）解密录成 `.flow`/HAR。
3. **转 spec** — `mitmproxy2swagger`（Python 吃 .flow）或 `har-to-openapi`（Node 吃 HAR）把真实流量固化成 OpenAPI 3.0。
4. **挖 GraphQL** — 内省关了用 `clairvoyance` 盲还原 schema；开着用 `gqlspection` 生成成品 query、`graphql-voyager` 画图定位可挖字段。
5. **反爬护体 + 代理轮换 + 规模化扇出** — `curl_cffi` 快路径直抓、撞 CF 降级 `camoufox` 渲染；`crawlee`（ProxyConfiguration）吃逆向出的 spec 做代理轮换+批量扇出落盘。

**为什么这套最强**：正好一件占一环、零功能重叠；其中 `curl_cffi`+`camoufox` 已被 anti-scraping 的 fetch.py 与漫剧雷达 collect.py 生产在用、`mitmproxy` 被 `mitmproxy2swagger` 硬依赖——是**实际验证跑通的活链条**，不是纸面拼盘。REST 侧（mitmproxy2swagger/har-to-openapi）与 GraphQL 侧（clairvoyance/gqlspection/voyager）双通道互补，遇 REST 或 GraphQL 都有对口出口。

> 注：`botasaurus` 是自成一体的 all-in-one 框架（一个人覆盖抓取+反检测+落盘+打包），**不进这条流水线、要它就整包单干**。

## 3. 工具能力卡（本地实测）

**接管会话 / 双模**
- **DrissionPage** `v4.1.1.4` ✅ — 独门：一个 `WebPage` 对象把真实 Chromium 与 requests 收发包合体，`change_mode()` 带同 cookie 切换；内置 CDP Listener 抓 XHR/fetch。opencli（外部桥）给不了这个。边界：不是主打隐身，反检测「文档声称、未实战」。

**纯 HTTP / TLS 伪装**
- **curl_cffi** `v0.15.0(venv) / 0.7.4(全局)` ✅ **载重** — 独门：无浏览器发浏览器级 TLS/JA3+HTTP2 指纹，极快。0.15＞0.7（新版指纹更新鲜）。边界：不执行 JS，撞 CF JS 挑战要降级浏览器。

**反检测浏览器**
- **camoufox** `v0.4.11` ✅ **载重** — 独门：Firefox C++/源码层改指纹，JS 检测读不到痕迹；`geoip=True` 按代理 IP 对齐时区/locale。边界：伪装不成 Chrome，查 SpiderMonkey 的站过不去（换 Chromium 系兜底）；破不了 IP 信誉级 CF。
- **seleniumbase** `v4.50.4` ✅ — Chromium 系 UC/CDP 反检测，Selenium 生态。绕过能力「文档声称、未实战」。
- **undetected-chromedriver** `v3.5.5` ✅ — Selenium drop-in、去 cdc_ 哨兵，补已有 selenium 代码的指纹。
- **patchright** `(node)` ✅ — patched/undetected Playwright drop-in；connectOverCDP 接管真实 Chrome。
- **rebrowser-patches** `(node)` ✅ — 给 puppeteer/playwright-core **源码打补丁**去 CDP 泄露（不是运行时库）。
- **botasaurus** `v4.0.97` ✅ — all-in-one 框架（装饰器+纯 CDP undetected Chrome+缓存/profiles/落盘/一键打包）。绕过「过 EVERY bot test」是营销、未实战；`import botasaurus.request` 首次会联网拉二进制。
- **nodriver** `v0.50.3` ✅ **已修**（2026-07-03 把 cdp/network.py:1345 坏字节 0xb1→UTF-8 ±，import 通过）— 纯 CDP 驱动真实 Chrome、异步、UC 接班。

**爬虫框架 / 规模化编排**
- **crawlee** `(node)` ✅ — 队列/去重/扩缩/重试/ProxyConfiguration 代理轮换/结构化落盘。浏览器模式走新指纹，登录墙禁用。
- **scrapling** `v0.4.9` ✅ **载重**（scrapling-official skill 整套围建）— 独门：自愈解析器（改版后按元素指纹自动重定位）+ 一体化 spider。边界：`StealthyFetcher` 反检测已于 2026-07-03 装 `scrapling[all]` 补全依赖（import 通过）；实际 launch 浏览器仍需下载引擎二进制，且守封号铁律不对登录站起新指纹。

**抓包 → 转 spec**
- **mitmproxy** `v12.2.3` ✅ **载重**（mitmproxy2swagger 硬依赖）— 唯一能解密并录下手机 App/桌面客户端真实流量的中间人代理。
- **mitmproxy2swagger** `v0.15.0` ✅ — 吃 `.flow` → OpenAPI 3.0（两遍式选端点）。
- **har-to-openapi** `(node)` ✅ — 吃 HAR → OpenAPI，轻量可脚本化。

**GraphQL 挖掘**
- **clairvoyance** `v2.5.5` ✅ — 独门：introspection 关闭也能靠报错 oracle+词表盲还原 schema。依赖目标返回详细报错。
- **gqlspection** `v0.2.3` ✅ — schema JSON → 可直接发的 query/mutation codegen。边界：喂 `mutationType:null` 的 schema 会崩（Alpha，用前包 try）；只在 introspection 开着有意义。
- **graphql-voyager** `v2.1.0` ✅ — schema 关系图可视化。边界：主 lib 是浏览器 bundle（node 里 `require` 报 `self is not defined`），要跑在浏览器/webpack 或用它的 `/middleware`。

**域内 API 客户端**
- **airbnb（airbnb-python）** ✅ import 通 — Airbnb 私有移动端 API 旧客户端，旧端点大概率失效，仅当接口清单参考。
- ~~bnbhostapi / booking.com_crawler~~ — **已于 2026-07-03 删除**（死包、被 logged-in-platform-ops/通用抓取完全取代、grep 零依赖）。

## 4. 装在哪 · 怎么调

- **Python 工具**（venv，独立隔离，不污染系统）：`D:\revtools\venv\Scripts\python.exe`；包在 `D:\revtools\venv\Lib\site-packages`。
  - `anti-scraping` 的 `fetch.grab()` 用的是**全局** python3.14 的 `curl_cffi 0.7.4`+`camoufox`（雷达也走它）——**这两个全局包是载重件，别删**。
- **Node 工具**：`D:\revtools\node\node_modules`（crawlee/patchright/har-to-openapi/graphql-voyager/rebrowser-patches）。
- **克隆仓库**：`D:\revtools\repos`（空——原 bnbhostapi/booking.com_crawler 已删）。

## 5. 健康状态（2026-07-03 实测）

- 🔒 **载重件，绝不能删**（删了连锁弄坏 skill/雷达）：`camoufox`、`curl_cffi`、`scrapling`、`mitmproxy`。
- ✅ **已处理（2026-07-03）**：`bnbhostapi`+`booking.com_crawler` 已删；`nodriver` 坏字节已修（import 通）；`scrapling[all]` 已补全反检测依赖；`gqlspection` null-mutation 已加 guard。
- ✅ **其余各占独特生态位，不是冗余，整体留。** 全锁在独立 venv/node_modules，跟系统/项目零冲突。


## 6. ⭐ Ghidra 12.1.3 —— 二进制/固件/APK-native 反编译(2026-09-17 装,已验证)

- **本体**: `D:\revtools\ghidra\ghidra_12.1.3_PUBLIC`(JDK 21 已满足)。GUI 走 `ghidraRun.bat`,自动化走 headless。
- **一键反编译成 C 伪代码**(我能自动 invoke,零 GUI):
  ```
  py -3.12 D:\revtools\ghidra\ghidra_decompile.py <二进制/exe/dll/so/固件> [输出.c]
  ```
  实测: `where.exe`→100 函数/160KB、`hostname.exe`→35 函数。跑完自动清临时项目。
- ⛔ **用它的场景 = 【编译后的产物】**(exe/dll/so/固件/APK 的 native 层)。**源码项目(Node/Python/Go)用 codegraph,别用 Ghidra** —— Ghidra 对源码没用,它是把机器码还原成 C。
- ⛔ **坑(已在 wrapper 里处理好,别重踩)**: ①Ghidra 12 去掉了内置 Jython,postScript 必须用 `.java`(原生)或装 PyGhidra;
  ②`scriptPath` 必须指【只放脚本的干净子目录】`gh-scripts`,混 Ghidra 本体目录会 OSGi 编译失败(`class could not be found`)。
- 反编译脚本: `D:\revtools\ghidra\gh-scripts\DecompileAll.java`(改逆向逻辑改它)。


## 7. ⭐ APK 逆向完整链(2026-09-17 装齐,全部验证过)

⛔ **逆 APK 是【分层】的,别只用一个工具**。APK 大头是 Java/Kotlin,Ghidra 只管 native 那一小层:

| 目的 | 工具(最强) | 本机调法 |
|---|---|---|
| **看 Java/Kotlin 源码**(最常用) | **jadx 1.5.6** | `D:\revtools\jadx-1.5.6\bin\jadx.bat <apk> -d <出目录>`(旧 1.4.7 在 `D:\revtools\jadx`,已被这个取代) |
| **解包/改 smali/重打包**(破解/改行为) | **apktool 3.0.3** | `D:\revtools\apktool\apktool.bat d <apk>`(解包) / `b <目录>`(重打包) |
| **动态 hook/绕检测/脱壳**(加固/反调试) | **frida 17.18.0** | `frida` / `frida-trace`(pip 装在 py-3.12);配 `frida-server` 推到设备 |
| **native `.so` 层**(C/C++ 算法) | **Ghidra 12.1.3** | `py -3.12 D:\revtools\ghidra\ghidra_decompile.py <so文件>` |

**标准顺序**: 先 `jadx` 看源码理解逻辑 → 要改就 `apktool` 解包改 smali 重打包 → 遇到加固壳/反调试/要看运行时就上 `frida` → 碰到 native 里的关键算法才用 `Ghidra`。
⚠️ 商业更强的: Java 层 JEB、native 层 IDA Pro(都收费,没装)。开源这套(jadx+apktool+frida+ghidra)已是免费最强组合。
⚠️ 完整实操流程见 reverse-skill 包的 `apk-reverse` / `mobile-reverse` skill(走 reverse-skill-router 路由)。
⛔ Defender 会误报逆向库(前科: PayloadsAllTheThings 被报 Trojan),APK 逆向产物同理,别被吓到。