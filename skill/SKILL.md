---
name: china-art-episode
description: 做《中国传统艺术的演变》分集纪录片的下一集（2.5D 画中游 + 云健旁白 + 整曲古琴，约 5 分钟）。用户说"做下一集""做元代/明代/某朝那一集""按这个流程和标准再做一集""改一下第 N 集""发第 N 集"时使用。按工具包仓库 china-art-docuseries-kit 的 PLAYBOOK、STANDARDS 和工作流模板执行。
---

# 中国艺术分集纪录片 · 下一集

## 先找到工具包
- 仓库 `KIT`：默认 `~/claude-projects/china-art-docuseries-kit`（GitHub 私有仓库 `Neal122234/china-art-docuseries-kit`）。本 skill 通常是 `KIT/skill/` 的软链接，`KIT` = 本文件所在目录的上一级。
- 素材与成品工程 `CHINA_ART_ROOT`：默认 `~/claude-projects/china-art`（大文件都在这里，不在仓库里）。换机器时先跑 `KIT/scripts/bootstrap.sh`，素材按各集 `plan/assets_INDEX.md` 重新下载。
- 开工先读（按顺序）：`KIT/docs/STANDARDS.md` → `KIT/docs/LESSONS.md` → `KIT/docs/EPISODES.md`（下一集是谁、候选作品、调研文件）→ 上一集 `KIT/episodes/<上一集>/plan/FINAL.md`（用户认可的力度、已知不足）。流程细节全在 `KIT/docs/PLAYBOOK.md`。

## 执行顺序（每步先给用户看什么）

| 步 | 做什么 | 先给用户看 / 等什么 |
|---|---|---|
| 1 选朝代与论点 | 按 EPISODES 定论点一句话（和上一集对照）、4–6 件作品（该朝成就最高的门类，不限绘画） | **一段话：论点、作品清单、预计时长、要他拍板的事**（片长、1080 否、配乐沿用 Caro 否、标题分区以后再问）。等点头 |
| 2 调研 | 底稿够就补缺；不够跑 `KIT/workflows/research.js`（催速度时 `verify: false`） | 不打扰；有主观取舍（论点候选、作品取舍）才列对照表问 |
| 3 分镜 | 总控亲自写 `KIT/episodes/epNN_<拼音>/plan/SHOTLIST.md`（照 `_template/SHOTLIST_TEMPLATE.md` 和上一集结构）+ `anchors.json`；先排作品展示时间，再加转场与高光；每个转场算可达性 | **分镜摘要**：每件作品的高光一句话、每个转场一句话、总长。用户说"直接开渲"就不等 |
| 4–9 制作 | 建 `EP_DIR`、`plan` 软链接、`cp -R KIT/pipeline EP_DIR/pipeline`；跑 `KIT/workflows/episode_production.js`（素材/配乐/旁白并行 → 每段一个助手并行 → 总装与客观自检） | **各段 ≤10 s 高光预览**一出来就发（方向不对当场改）；然后**成片 + 联系表 + 简短说明**（时长、高光时间码、已知不足、要他决定的） |
| 10 改版 | 用户原话一字不改写进 `plan/CHANGES_vN.md`（`_template/CHANGES_TEMPLATE.md`），翻成可检查的改动；跑 `KIT/workflows/revision.js`；改动并入 SHOTLIST | 新版成片 + 改版单逐条落实情况 |
| 11 发布 | video-publish skill：清单（标题、简介含章节与署名、AI 声明、分区、封面写字） | **发前确认标题、分区、封面**；发完回读结果 |
| 收尾 | 代码与文档复制进 `KIT/episodes/epNN_<拼音>/`，更新 EPISODES/LESSONS/STANDARDS，`scripts/check_secrets.sh`，提交 | 一两句汇报：做了什么、放在哪、要他决定什么 |

## 必须遵守（全文与来源见 STANDARDS.md）
- **作品为主、特效为辅**：每件全貌干净停 ≥6 s，不做小展板（立轴挂墙真实绢/绫、手卷长案、器物占主体柔和背景）；转场遮住作品 ≤1–2 s；**雾全集最多一次且不遮画**；组画逐段快而看得清（每段约 2 s），再聚焦。
- **动静结合、动效一眼可见**：每件 1–2 个手机上 1 秒内看得出的高光，来自作品本质；冲击来自画里的变化、光、层次、揭示，不靠快甩。
- **只动原作像素**：揭原作之墨、分层视差、刚体位移、沿真实纹理流动；不橡皮变形、不重画、不生成原作里没有的东西。
- **镜头限速**：720p 平移 ≤6 px/帧（推荐 2–3.3）、推拉 ≤6%/s、缓入缓出 ≥1 s、不旋转；交付前 pan_speed_check。
- **转场**：一个发现、一句话说清、≤15 s；先算限速下能否到位；全景尺度的切分必然是拼贴。
- **展示处严谨**：展签、字幕、旁白史实以馆方页面为准，拿不准不写；看不见的细节配合得上就行。
- **声音**：一集一首完整录音，不剪不拼；要公开发布的许可必须干净（现役 Rafael Caro《梅花三弄》CC BY 4.0）；旁白只用云健（`zh-CN-YunjianNeural`，pitch −4Hz，rate −12%），whisper 回听校读音，只改合成文本不改字幕。
- **底线**：不拼贴、不橡皮变形、不斑块/矩形溶解、不漂浮剪影、不糊、不整屏拖影、不快速横移、不纯黑屏、不小展板、不廉价中国风（祥云壁纸、粒子、光斑、3D 翻页）。其余放开——**标准是对标，不是笼子**；给创作助手的 brief 只写对标样板 + 这些底线。
- **机器**：8 GB 内存。重活一律 `lockf -k $CHINA_ART_ROOT/series/.heavy.lock`；>1 分钟 nohup 后台 + 短轮询；大图 memmap；备份用 cp 不用硬链接；不改上一集和公共代码的现有行为。

## 工作方式
- 用户要速度：开工报预计耗时（一集约 4–5 小时，改版约 1 小时）；不做内部评审，做完即交，用户自己验收。
- 客观的自己查（速度、黑帧、音画同长、作品可见时长、转场遮挡、字幕对语音）；审美和方向取舍交用户拍板。
- 用户针对某件作品的意见只改那一件；想推广到别处先问。
- 用户中途改口：停流程 → 改分镜/改版单 → 续跑（`resumeFromRunId`）或只重开受影响的部分（`LESSONS.md` §3）。
- 文档只留最终版本；每集只留最终成片；清理移废纸篓不 rm。
- 汇报要短。
