# 制作流程（PLAYBOOK）

一集从"选朝代"到"发布"的完整做法。两集（北宋、南宋）都是这样做出来的。质量标准在 `STANDARDS.md`，坑在 `LESSONS.md`，候选朝代在 `EPISODES.md`。

## 总览

```
1 选朝代与论点 ─▶ 2 调研 ─▶ 3 分镜（SHOTLIST + anchors）
                                   │
          ┌────────────────────────┴─────────────── workflows/episode_production.js
          ▼
   Prep（并行）：4 素材下载与核实 ｜ 5 配乐 ｜ 6 旁白合成对时
          ▼
   Segments（每段一个助手并行写代码，重渲染排队拿锁）：7 分段制作，先出 ≤10 s 高光预览
          ▼
   Assemble：8 总装（转场、字幕、混音）─▶ 9 客观自检 ─▶ 成片
          │
          ▼
10 交付给用户看 ─▶ 改版单 ─▶ workflows/revision.js ─▶ …… ─▶ 11 发布
```

**用户看什么、什么时候看**（其余不打扰）：
1. 阶段 1 结束：论点一句话 + 作品清单 + 预计时长。
2. 阶段 3 结束：分镜摘要（每件作品的高光一句话、每个转场一句话）。用户说"直接开渲"就跳过。
3. 阶段 7 中：各段 ≤10 s 高光预览（方向不对当场改）。
4. 阶段 9 后：成片（+ 联系表）。用户自己验收，不做内部评审。

**目录约定**
- `KIT` = 本仓库（文档、代码、模板，git 跟踪，不含媒体）。
- `CHINA_ART_ROOT` = 素材与成品所在的工程目录（本机是 `~/claude-projects/china-art`），大文件都在这里。
- `EP_DIR` = `$CHINA_ART_ROOT/series/epNN_<拼音>/`，子目录：`plan/ assets/ music/ voice/ segs/ assemble/ out/ pipeline/`。
- `pipeline/` 是本集的流水线副本：`cp -R $KIT/pipeline $EP_DIR/pipeline`（配音、总装、转场、出片脚本之间按同目录互相引用，所以整目录复制）。本集的 `DUR`、段表、转场表、`PRON` 都只改副本；`$KIT/pipeline` 保持上一集能重跑。
- 本集文档写在 `KIT/episodes/epNN_<拼音>/plan/`（git 跟踪），在 `EP_DIR` 里做软链接 `ln -s $KIT/episodes/epNN_<拼音>/plan $EP_DIR/plan`，pipeline 的缺省路径就能读到。交付时把本集的段代码、`pipeline/` 副本、`beats.json`、`subs.srt`、`timing.json` 复制到 `KIT/episodes/epNN_<拼音>/code/`。
- 全局渲染锁：`LOCK=$CHINA_ART_ROOT/series/.heavy.lock`。

**分工（多智能体）**
- **主会话 = 总控**：和用户说话、定论点、写分镜（创意由总控写死在分镜里：每个高光和转场的 title / 一句话 / 做法）、派工作流、看预览和联系表、写 HANDOFF。总控自己要拿出有质量的点子，不只当调度。
- **工作流助手**：素材 1、配乐 1、旁白 1（并行）→ 每段 1 个（并行，片头片尾合一个）→ 总装 1。改版时每个要改的段/项 1 个 + 总装 1。
- 给助手的 brief 公共段（CTX）照 `workflows/episode_production.js` 里的写法：项目与必读文件、"不要改上一集的文件"、用户标准（对标样板 + 否定过的底线，其余放开）、机器规则（锁、nohup、memmap、cp 备份）、"展示处要严谨"。助手只实现，细节可调但要在汇报里写明。
- 同时在跑的助手控制在一批 ≤3 路做重活；段助手可以 7 个同时写代码，但渲染一律排队拿锁。

**耗时参考**（M2 8 GB，720p）
| 环节 | 实际耗时 |
|---|---|
| 南宋主流程（Prep → 七段 → 总装出 v1） | 约 4.0 小时 |
| 南宋改版（去雾、水图重做、展签、旁白 → v2） | 约 1 小时 |
| 北宋改版（五段加高光、雾与长案重做 → v2） | 约 3 小时 |
| 整片渲染（约 300 s） | 7–8 分钟 |
| pan_speed_check（整片） | 1–3 分钟 |
| 云健配音（已有流水线，36–44 句 fit + asr + mix） | 15–40 分钟 |
| 换配乐 + 重混音 + 出片 | 约 15 分钟 |
| 1080p（各段整段重渲） | 约 3–4 小时（没做过完整一遍） |

---

## 阶段 0 · 开工准备

- **输入**：本仓库；`EPISODES.md`（下一集是谁）；上一集 `episodes/<上一集>/plan/FINAL.md`。
- **做**：
  - `scripts/bootstrap.sh --check`（环境）；缺包就 `scripts/bootstrap.sh`（+ `--asr` 读音核对、`--fetch-fonts` 思源宋体）。edge-tts、whisper 的 python 路径用 `TTS_PY`、`ASR_PY` 指定。
  - 建 `EP_DIR` 与子目录；从 `episodes/_template/` 复制模板到 `KIT/episodes/epNN_<拼音>/plan/`；做 `plan` 软链接；`cp -R $KIT/pipeline $EP_DIR/pipeline`。
  - 开 keep-awake（长流程）。
- **输出**：空的本集目录 + 模板。
- **验收**：`CHECKLIST.md` 的"开工前"一节全勾。
- **耗时**：5 分钟。

## 阶段 1 · 选朝代与论点

- **输入**：`EPISODES.md` 该朝代一行；`research/` 对应底稿；上一集的论点（本集要和它对照）。
- **做**：总控自己定（有底稿时不用开工作流）。
  - 论点一句话，能在画面上被证明（北宋"看得真"、南宋"只留最要紧的一笔"）。
  - 这个朝代成就最高的门类（不限绘画）；选 4–6 件作品，每件对应论点的一个面；至少一件"动得起来"的（有水、云、瀑布、人物行进），一件器物或书法换节奏。
  - 和上一集"变了什么"至少两条能在画面上指出来。
- **输出**：发给用户的一段话：论点、作品清单（作者/名称/藏地）、预计时长、需要用户拍板的事（`EPISODES.md` 末节）。
- **谁做**：主会话。
- **验收**：用户点头。
- **耗时**：10–20 分钟。

## 阶段 2 · 调研（门类、作品、图源、坐标）

- **输入**：选定的作品；`research/series/content_e*.md`、`research/early/c*.md`、`research/hall_v3/hunt_*.md`（干净图源）。
- **做**：已有底稿够用就只补缺；不够时开调研工作流 `workflows/research.js`（每件作品一路 + 朝代特点一路并行，可选一路核查展签事实与图源，最后合成 `plan/RESEARCH.md`）。用户催速度时 `verify: false`，事实核对放进素材阶段。
  - 每件作品：馆方名称、作者（"传"要写）、年代、材质、尺寸、藏地——以馆方页面为准；最高分辨率开放图的 URL、实测像素、许可、署名写法；哪个局部能证明论点；哪里能"动"。
  - 图源优先级：台北故宫 Open Data / IIIF（CC BY 4.0）、大都会 / 克利夫兰 / 芝加哥 / Mia（CC0/PD，器物有棚拍图）、故宫名画记经 Commons（PD，超大图）、东博 ColBase。器物要**馆方棚拍图**（纯色背景、光均匀、整件入画），不用展柜实拍。
- **输出**：调研笔记（写进 `research/` 或本集 `plan/`）；作品事实表（后面直接进 `assets_INDEX.md` 的"展签事实"）。
- **谁做**：主会话或调研工作流（每路一个助手，返回 ≤300 字摘要，全文写文件）。
- **验收**：每件作品有来源 URL + 许可 + 署名；展签事实逐条有馆方出处；拿不准的标"待核"，上屏前要么核到、要么不写。
- **耗时**：有底稿 15–30 分钟；从零开工作流 50–75 分钟。

## 阶段 3 · 分镜（SHOTLIST + anchors）

- **输入**：论点、作品事实、`episodes/_template/SHOTLIST_TEMPLATE.md`、上一集 `SHOTLIST.md`（结构照抄）。
- **做**：总控写，顺序是：
  1. **先排作品展示时间**：每件作品"全貌（干净停 ≥6 s）→ 读画 → 画中游高光 → 回全貌/交接"，每件 40–80 s；组画逐段每段约 2 s。
  2. 再排**段窗口表**：每段的全局起止秒、起始状态、结束状态；相邻两段重叠 3–9 s 给转场用；段文件帧 0 = 窗口起点。
  3. **转场**：每处一句话说清"发现"是什么；**先算可达性**（起止景别差几倍、按推拉 ≤6%/s 要几秒、窗口够不够）；需要遮罩（水面、涟漪、开片线……）的写明由哪段导出。雾一集最多一次。
  4. **每段旁白**：纪录片口吻，约 180–200 字/分钟，一句 ≤2 条字幕（每条 ≤16 字，空格处拆），20–30% 呼吸段；旁白说到哪，画面停在哪。时间 = 字幕起点（全局秒）。
  5. **高光**：每件 1–2 个一眼可见的"动"，写清做法（揭原作之墨 / 分层视差 / 刚体位移 / 沿纹理流动 / 光扫），来自作品本质。
  6. 展签文字（繁体竖排格式，数字用汉字）；片头题字与副题；结尾竖排小字与"下一章　某朝"。
  7. 把旁白抽成 `anchors.json`：`[[起点秒, "字幕原文"], ...]`（空格保留作停顿/拆条标记）。
- **输出**：`plan/SHOTLIST.md`、`plan/anchors.json`；给用户的分镜摘要。
- **谁做**：主会话（创意不外包；需要发散时可开 2–3 个创作助手各出方案，总控挑，主观取舍交用户）。
- **验收**：`CHECKLIST.md`"分镜"一节：每件全貌 ≥6 s 且不被遮；转场遮挡 ≤2 s；每个转场有可达性计算；旁白总字数 ÷ 有旁白时长 ≤ 200 字/分；雾 ≤1；段窗口首尾相接无缝隙。
- **耗时**：30–60 分钟。

## 阶段 4 · 素材下载与核实

- **输入**：`SHOTLIST.md` 的作品与图源；调研的 URL。
- **做**（工作流 Prep 阶段的"素材"助手）：
  - 下载最高分辨率原图到 `EP_DIR/assets/<作品>/`，原样保留一份不改。命令：
    - 台北故宫：`curl -s "https://digitalarchive.npm.gov.tw/Integrate/GetJson?cid=<id>&dept=P" -o manifest.json`，全图 `curl -o x.jpg "https://iiifod.npm.gov.tw/iiif/2/<部门码>%2F<label>/full/full/0/default.jpg"`（Python urllib 证书报错，只用 curl；单张约 7 MP 上限，多张局部可拼）。
    - Commons：API 取原图 URL，`curl -A "<浏览器 UA>" -C - -o x.png <url>`，间隔 ≥6 s。
    - 大都会：`https://collectionapi.metmuseum.org/public/collection/v1/objects/<id>`（看 isPublicDomain、period、medium、dimensions，拿 primaryImage + additionalImages）。
  - 大图转无头 raw（`<名>_<W>x<H>.rgb`）或 `.npy`，PNG 用流式解码；出缩略预览与带网格核对图。
  - 校色只做全局一个变换对到馆方参照（参照图也要先核是哪一本）。
  - 在网格图上量出每个高光/转场要用的坐标；组画按段切好并记每段边界与题名位置。
  - 核实展签事实（馆方页面），写进 INDEX 的"展签事实"表。
- **输出**：`EP_DIR/assets/` + `plan/assets_INDEX.md`（文件、像素、来源 URL、许可、署名写法、关键坐标、展签事实与出处、旁白相关的事实提醒）。
- **验收**：每件作品有主用文件 + 来源 + 许可 + 署名；坐标看过网格图；展签事实逐条有出处；存疑项写明。
- **耗时**：35–75 分钟（拼接大图另加 20–40 分钟）。

## 阶段 5 · 配乐（整曲，不剪不拼）

- **输入**：片长（`DUR`）；现役 Caro《梅花三弄》（387.9 s，CC BY 4.0）；候选比较方法（`episodes/ep02_nansong/plan/music_DECISION.md`）。
- **做**（"配乐"助手；沿用 Caro 时总控一条命令即可）：
  - 沿用 Caro：`ffmpeg -i freesound_176265_RafaelCaro_Meihua.hq.ogg -t <DUR> -af "afade=t=in:d=2,afade=t=out:st=<DUR-5>:d=5" -ar 48000 -ac 2 EP_DIR/music/bed_epNN.wav`；更讲究的做法是在 `DUR-6`～`DUR-2` 之间找乐句尾的能量谷，从那里升余弦淡出、后面补静音（北宋就是 290.35 s 乐句尾）。
  - 换曲：候选都测 高频底噪（最小统计法）、嘶声、爆音、频宽、时长，看能否在片长内于乐句尾自然收；**要公开发布的，许可必须干净**。
  - 需要踩拍的高光（顿足、落墨节奏），用最终配乐出起音表（全局秒）。
- **输出**：`EP_DIR/music/bed_epNN.wav`（48 kHz 立体声，长 = DUR），`plan/music_DECISION.md`（选了什么、为什么、许可与署名、电平提示）。
- **验收**：时长 = 片长到毫秒；中间无剪接（互相关可证）；许可与署名照实写；淡出落在乐句尾。
- **耗时**：沿用 Caro 5 分钟；换曲比较 30–60 分钟。

## 阶段 6 · 旁白（云健合成、对时、读音校对）

- **输入**：`plan/anchors.json`；本集副本 `EP_DIR/pipeline/build_voice.py`（只改文件头 `DUR`、`PRON`）。
- **参数**：`zh-CN-YunjianNeural`，pitch −4Hz，rate −12%；句尾离下一句 ≥0.3 s；放不下就逐句提速（每步 2%，最快 +0%）或在 ±0.5 s 内挪起点；仍放不下就报告建议删改的字。
- **命令**（在 `EP_DIR/pipeline/` 下，先 `export EP_DIR=... CHINA_ART_ROOT=...`，重活拿锁；edge-tts 与 whisper 的 python 用 `TTS_PY`、`ASR_PY` 指定）：
  ```bash
  python3 build_voice.py fit                           # 合成 + 对时，写 voice/work/timing.json，打印每句余量
  lockf -k $LOCK python3 build_voice.py asr            # whisper 回听 + 拼音比对（base 初听、large-v3-turbo 复核）
  lockf -k $LOCK python3 build_voice.py variants       # 多音字：与同音替身比 MFCC-DTW + F0
  python3 build_voice.py subs                          # 按语音对时写 out/subs.srt（超 16 字在空格处拆）
  lockf -k $LOCK python3 build_voice.py mix <配乐.wav>  # 干声/配乐再让/混音 → out/audio/{narration,music_duck,mix}.wav
  ```
  `asr`、`variants` 后面可跟句中片段，只核那几句（改稿后用）。
- **读音**：读错的只在 `PRON` 里等长替换送去合成的文本（同音字、大写数字），字幕原文不动；whisper 把专名听成常用词的不算错。重点核多音字、年份、专名（清单见 `LESSONS.md` §15）。
- **输出**：`voice/work/timing.json`（每句实际起止）、`out/subs.srt`、（总装前）人声干声。
- **谁做**：Prep 阶段的"旁白"助手（fit + asr + variants + subs）；`mix` 放到总装里做（要等配乐电平跟随）。
- **验收**：每句放得下且不重叠；读音报告无未处理的错读；字幕条数与拆分正确。
- **耗时**：15–40 分钟。

## 阶段 7 · 分段制作

- **输入**：`SHOTLIST.md`（本段窗口、起止状态、高光、展签）、`assets_INDEX.md`、`engine/ENGINE.md`、上一集同类段的代码（`episodes/*/code/segs/`：立轴挂墙、长案全貌、揭墨、光扫、涟漪、开片、组画逐段都有现成实现）。
- **引擎要点**（`engine/engine.py`，说明 `engine/ENGINE.md`）：一段 = 一个 Python 段描述（相机关键帧 + 层 + fx）；世界坐标 = 主图原图像素；相机不旋转、缩放按对数插值、每端缓入缓出 ≥1 s；**渲染前自动查速度，超速报错退出**；2× 超采样；mip 缓存 + memmap 只读可见区域；`--res 720|1080`；长案全貌用 `engine/scrollview.py`。
- **做**（每段一个助手，并行）：
  1. 读分镜与 INDEX，看上一集同类实现。
  2. **先做本段最惊艳那一刻的 ≤10 s 720p 预览** `EP_DIR/out/preview/<段>.mp4`，用 Read 看关键帧；满意再全段渲。预览发给用户看（阶段 3 的检查点）。
  3. 全段渲（1280×720 30 fps crf 12，帧 0 = 窗口起点），导出转场需要的遮罩 mp4。
  4. `python3 engine/tools/pan_speed_check.py <成品>`；抽 6–8 帧看。
  5. 写 `segs/<段>/beats.json`（高光与关键画面的实际全局时间）。
  - 限时约 75 分钟；做不到的效果换成稳而美、同样明显的做法，不交露馅的东西。
- **命令**：
  ```bash
  lockf -k $LOCK python3 $KIT/engine/engine.py seg.py out.mp4 --check              # 只查速度
  lockf -k $LOCK python3 $KIT/engine/engine.py seg.py review/x.png --stills 0,45,149 # 抽帧
  nohup lockf -k $LOCK python3 $KIT/engine/engine.py seg.py $EP_DIR/segs/seg_sN.mp4 [--frames a:b] > log 2>&1 &
  ```
- **输出**：`EP_DIR/segs/seg_sN.mp4`（+ 遮罩）、`segs/<段>/`（代码、beats.json）、`out/preview/<段>.mp4`。
- **验收**：起止状态符合段窗口表；pan_speed_check 无超限段；高光在手机尺寸 1 秒内看得出在动；全貌干净停够；只动原作像素。
- **耗时**：每段 60–120 分钟（并行，受渲染锁排队影响）。

## 阶段 8 · 总装（转场、字幕、混音）

- **输入**：各段成品与遮罩、各段汇报与 `beats.json`、`out/subs.srt`、`music/bed_epNN.wav`、本集副本 `EP_DIR/pipeline/`（`assemble.py`、`transfx.py`、`run_all.sh`、`final.sh`）。
- **做**（"总装"助手）：
  1. 改本集副本 `EP_DIR/pipeline/assemble.py` 文件头：段表（`SEG_START`/`SEG_FILE`/`SEG_NFR`）、遮罩表、转场表（`TRANS`）、`DUR`；配乐用环境变量 `BED` 指到本集配乐。新转场在副本 `transfx.py` 里**新增**类。副本 `final.sh` 按自身位置推 KIT，复制后要把 pan_speed_check 的路径指回 `$KIT/engine/tools/pan_speed_check.py`。
  2. 每个转场先做 ≤10 s 短测试看帧，再整片。
  3. 配乐电平跟随 → 混音：`assemble.py audio`（字幕区约 −26 LUFS、呼吸段约 −20 LUFS → `assemble/work/music_mix.wav`）→ `build_voice.py mix assemble/work/music_mix.wav`（人声 −16 LUFS、配乐在人声下再让 4 dB、限幅 −1.5 dBFS）。
  4. 字幕按 `out/subs.srt` 烧入（思源宋体 32 px，#EDE6D8 + 柔阴影 + 淡柔光晕）。
  5. 出片：`OUT_MP4=$EP_DIR/out/epNN_<拼音>_v1.mp4 VERIFY=$EP_DIR/pipeline/work/verify.py nohup lockf -k $LOCK $EP_DIR/pipeline/run_all.sh > final.log 2>&1 &`（混音 → 整片 → 自检）。覆盖前脚本先 cp 备份旧成片。
- **命令**（`EP_DIR` 已导出；在 `$EP_DIR/assemble/` 下跑，`work/`、`peek/` 都在这里）：
  ```bash
  python3 $EP_DIR/pipeline/assemble.py subs                                   # 打印烧入字幕 + 字形检查
  python3 $EP_DIR/pipeline/assemble.py audio                                  # 配乐电平跟随
  python3 $EP_DIR/pipeline/assemble.py peek 52 110.5 113                      # 渲指定全局秒的帧 → peek/sheet.jpg
  python3 $EP_DIR/pipeline/assemble.py video --t0 106 --t1 116 --height 480 --fast --out work/t.mp4   # 转场短测试
  python3 $EP_DIR/pipeline/assemble.py flatcheck 6                            # 转场逐帧查大面积平涂、平均亮度
  ```
- **输出**：`EP_DIR/out/epNN_<拼音>_v1.mp4`（1280×720 30 fps，H.264 crf 18，AAC 192k，faststart）、`out/audio/*.wav`、`out/contact.jpg`。
- **耗时**：40–90 分钟（整片渲染本身 7–8 分钟）。

## 阶段 9 · 客观自检（交付前必跑，只查客观项）

| 项 | 口径 | 工具 |
|---|---|---|
| 镜头速度 | 超过 1/7 画宽/秒且连续 >0.2 s 的段 = 0（无纹理渐变处孤立单帧人眼复核） | `engine/tools/pan_speed_check.py` |
| 黑帧 | 0（片尾设计的压暗除外） | ffmpeg blackdetect（final.sh 内） |
| 音画同长 | 视频帧数 × 1/30 = 音频时长 = DUR，到毫秒 | ffprobe |
| 响度 | 人声 −16 LUFS；全片约 −17～−19 LUFS；真峰值 ≤ −1 dBTP | ebur128 |
| 帧间跳变 | 无意外跳变（帧差 > max(6, 5×局部中位)） | 本集 verify 脚本 |
| 作品可见 | 每件全貌干净停住 ≥6 s（作品框内与参考全貌帧差 <1.5 灰阶，字幕带不计） | 本集 verify 脚本 |
| 转场遮挡 | 每个转场"混合"≤2 s，"看不清"尽量 ≈0 | 本集 verify 脚本 |
| 组画逐段 | 每段静止 ≥1.5 s | 本集 verify 脚本 |
| 雾（若用） | 不平涂：雾覆盖 >0.5 的 24×24 块里去绢纹后 std<1.2 的比例 ≤25%，浓淡离散度 ≥5 | `assemble.py flatcheck` / fogcheck |
| 字幕对语音 | 字幕起点与人声起音差中位 ≈0、最大 ≤50 ms | 本集 verify 脚本 |
| 联系表 | 16 帧（含每个高光与转场）用 Read 看：无错位、无方块字、无硬边、无雾遮画 | verify 脚本出图 |

- verify 脚本以 `episodes/ep02_nansong/code/assemble/work/verify_v2.py` 为模板，放在 `EP_DIR/pipeline/work/verify.py`（它 import 上一级目录的 `assemble.py`，放这里就用本集副本），改本集的作品框、参考帧时刻、转场窗口、组画段落。
- 不做审美打分。发现明显穿帮就修；做不到的写进 HANDOFF 的"已知不足"。
- **耗时**：约 10 分钟（跟着 run_all.sh 一起跑）。

## 阶段 10 · 交付与改版

- **交付**：发成片给用户（要手机看且 >30 MB 时另压 854×480 两遍编码 <28 MB；用户说不要就不压）+ 一段简短说明：时长、高光时间码、已知不足、要他决定的事。写 `EP_DIR/HANDOFF.md` 与 `plan/FINAL.md`（模板 `_template/HANDOFF_TEMPLATE.md`）：文件、高光时间码、转场实现、重跑命令、自检结果、已知不足——只留最终版本。
- **改版**：
  1. 把用户原话一字不改记进 `plan/CHANGES_vN.md`（模板 `_template/CHANGES_TEMPLATE.md`），翻译成可检查的改动（"动效不明显"→"手机上 1 秒内看出在动，量级……"）。**反馈只作用于这一集**，要推广到后续集先问。
  2. 用户补充/改口时：停掉刚开的流程，改单子，再开（见 `LESSONS.md` §3）。
  3. 跑 `workflows/revision.js`：每个要改的段/项一个助手（只重渲受影响的帧段再拼回，帧数与首尾帧不变）→ 一个总装助手出 vN+1。覆盖前 cp 备份。
  4. 改版单内容并入 `SHOTLIST.md`（分镜永远是最终状态），改版单留作记录。
- **验收**：改版单每条都有落实证据（帧、时间码、自检数字）。
- **耗时**：小改 1 小时左右；整集加力度的大改 3 小时。

## 阶段 11 · 发布

- **输入**：最终成片；`plan/FINAL.md` 的章节时间；素材与配乐署名。
- **做**：用 video-publish skill（私有仓库 video-publish-kit：一份清单 → 多平台，默认预演，`--go` 才发，B 站发完回读核对）。
  - 清单：标题（系列名「Claude的中式美学」+ 集号 + 朝代，用户定）、简介（一句论点 + 各件作品一句 + "画面、剪辑、字幕和旁白由 Claude 制作，旁白为 AI 合成语音" + 章节时间 + 图像与配乐署名）、标签、分区（北宋发的计算机技术 231，南宋发的人文历史 228，**发前问用户**）、封面（用户要求**封面要写字**：原作高清局部 + 宋体标题 + 朝代印；横版 16:9、竖版 3:4、小红书横屏视频用 4:3 封面）。
  - B 站：含 AI 生成内容的创作声明必须首次投稿时带上（投后不可改）；发完回读声明与分 P。
  - 抖音、小红书同一清单。
- **输出**：各平台稿件号写进 `plan/FINAL.md` 与 `EPISODES.md`。
- **验收**：回读结果（声明、分区、标题、章节）与清单一致。
- **耗时**：20–40 分钟（封面 3 张让用户挑另算）。

## 收尾（每集都做）

- 把本集段代码（`segs/*/` 里的 .py/.sh/beats.json）、`pipeline/` 副本、`subs.srt`、`timing.json` 复制到 `KIT/episodes/epNN_<拼音>/code/`（只复制代码与小文本，不复制媒体）；`plan/` 已在仓库里。
- 更新 `docs/EPISODES.md`（已完成表、下一集）；新踩的坑写进 `LESSONS.md`；用户新定的标准写进 `STANDARDS.md`（带来源）。
- 跑 `scripts/check_secrets.sh`，再提交。
- 废案：每集只留最终版；清理前查占用（`lsof +D`、`ps`），移废纸篓不 rm；先告诉用户哪些会丢。
