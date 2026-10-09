# 中国艺术演变 · 分集纪录片工具包

《中国传统艺术的演变》分集纪录片的制作方法、标准、代码与模板。目的是**之后直接取用，生成下一集**。

每集约 5 分钟：一集一个朝代、一个论点；每件作品先干净地看全貌，再"画中游"（2.5D 分层、揭原作之墨、光扫器身），中文旁白（云健）+ 整曲古琴。

## 已完成的两集

| 集 | 论点 | 作品 | 成片 |
|---|---|---|---|
| 北宋 | 看得真 | 溪山行旅、清明上河、千里江山、汝窑水仙盆 | 4:52 |
| 南宋 | 北宋人要看得真；南宋人只留最要紧的一笔 | 万壑松风、踏歌、寒江独钓、水图、泼墨仙人、官窑 | 4:56 |

两集用的是同一套方法（选论点 → 调研 → 分镜 → 并行分段制作 → 总装 → 客观自检 → 用户看片改版 → 发布），这套方法和用户定下的标准都写在 `docs/` 里，可以照着做任何一个朝代。下一集是**元**（南宋集片尾已预告）。

## 目录

| 目录 | 内容 |
|---|---|
| `docs/PLAYBOOK.md` | **完整制作流程**：12 个阶段，每阶段的输入、输出、谁做、验收口径、命令、耗时 |
| `docs/STANDARDS.md` | 用户定的质量标准与审美（每条注明来自哪次反馈）、否定过的做法 |
| `docs/LESSONS.md` | 踩坑与对策（8 GB 内存与渲染锁、备份、图源、转场失败案例、配乐版权……） |
| `docs/EPISODES.md` | 分集规划与进度：已完成两集、下一集（元）、后续朝代候选与调研文件 |
| `skill/SKILL.md` | Claude Code skill `china-art-episode`：用户说"做下一集"时按本仓库执行 |
| `workflows/` | 多智能体工作流模板（参数化）：`research.js` 调研、`episode_production.js` 一集制作、`revision.js` 按改版单修改 |
| `episodes/_template/` | 新一集的模板：分镜、旁白 anchors、改版单、HANDOFF、检查清单 |
| `episodes/ep01_beisong/`、`ep02_nansong/` | 两集的 `plan/`（定稿分镜、改版单、素材索引、配乐决定、成片实况）与 `code/`（各段与总装代码） |
| `engine/` | 2.5D 画中游渲染引擎（相机限速、分层视差、局部活化、长案全貌）与 `tools/pan_speed_check.py` |
| `pipeline/` | 配音（合成 → 对时 → 读音核对 → 混音）、总装（转场、字幕、配乐电平）、出片与自检脚本 |
| `research/` | 调研底稿（各朝代门类与作品、视觉参考、美学理论、干净图源、中式转场语法库），索引见 `research/README.md` |
| `scripts/` | `bootstrap.sh` 环境准备，`check_secrets.sh` 提交前查密钥 |

## 三步生成下一集

1. **对 Claude 说**："按工具包做下一集，元代。"（或"做明代那一集"。装了 skill 会自动触发 `china-art-episode`；没装就说"读 `~/claude-projects/china-art-docuseries-kit/skill/SKILL.md` 照做"。）
2. **它按 `docs/PLAYBOOK.md` 走**：定论点与作品 → 调研 → 写分镜 → 跑 `workflows/episode_production.js`（素材、配乐、旁白并行，各段并行制作，总装出片并跑客观自检）。
3. **你看小样拍板**，只在四个点上看：
   - 论点一句话 + 作品清单 → 点头；
   - 分镜摘要（每件的高光、每个转场一句话）→ 点头，或说"直接开渲"跳过；
   - 各段 ≤10 秒高光预览 → 方向不对当场说；
   - 成片 → 说哪里不对（原话就行），它写改版单、跑 `workflows/revision.js` 出新版；满意就发布。

安装 skill：

```bash
ln -s ~/claude-projects/china-art-docuseries-kit/skill ~/.claude/skills/china-art-episode
```

## 本地运行前提

- macOS（Apple Silicon，8 GB 可以跑，但重活必须排队，见 `docs/LESSONS.md` §1）、Python ≥3.10、ffmpeg/ffprobe。
- 先跑 `scripts/bootstrap.sh`：建 `.venv`，装核心包（numpy、opencv、pillow、scipy、scikit-image、edge-tts、pypinyin 等）。可选：`--asr`（faster-whisper / mlx-whisper，读音核对）、`--depth`（torch + transformers，深度估计）、`--fetch-fonts`（思源宋体 SC）、`--check`（只检查）。
- 环境变量：`CHINA_ART_ROOT`（素材与成品所在的工程目录，大文件都在这里，不在仓库里）、`EP_DIR`（当前这一集，`$CHINA_ART_ROOT/series/epNN_<拼音>`）、`FONT_DIR`、`TTS_PY`（装了 edge-tts 的 python）、`ASR_PY`（装了 whisper 的 python）。各脚本文件头有说明。
- 旁白用微软 edge-tts 在线合成，需要联网。
- 全局渲染锁：`$CHINA_ART_ROOT/series/.heavy.lock`（`lockf -k` 串行）。

## 素材与版权

- **仓库不含任何图像、音频、视频**（成片、素材、配乐、中间产物都在 `CHINA_ART_ROOT`）。换机器或素材丢了，按各集 `episodes/*/plan/assets_INDEX.md` 的来源 URL 重新下载；坐标是源文件像素，下同一个文件就能复用。配乐按 `music_DECISION.md` 重建。
- 图像来源：台北故宫 Open Data / IIIF（CC BY 4.0，须署名"國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw"）、故宫博物院名画记与书格扫描经 Wikimedia Commons（公有领域）、大都会（CC0）、东京国立博物馆 ColBase。每件的许可与署名写法在 INDEX 里。
- 配乐：Rafael Caro《梅花三弄》，Freesound 176265，CC BY 4.0，发布时署名。南宋集制作时用过的吴兆基《平沙落雁》（雨果唱片 1987 年录音）在版权期内、没有授权，发布前已换掉；许可不干净的录音不要用于公开发布。
- 发布简介里写明：画面、剪辑、字幕、旁白由 Claude 制作，旁白为 AI 合成语音；图像与配乐署名。

## 许可

代码与文档 MIT，见 [LICENSE](LICENSE)。图像、配乐等外部素材不在仓库里，各自保留原许可。

---

**English** — A production kit for a documentary series on the evolution of Chinese traditional art: one dynasty and one thesis per ~5-minute episode, each artwork shown whole first, then explored with 2.5D parallax "walking into the painting", ink reveals and light sweeps over ceramics, with synthesized Chinese narration and guqin music. Contains the 12-stage playbook, quality standards, lessons learned, the 2.5D render engine, voice/assembly pipeline, Claude Code workflows and skill, plus the full plans and code for the first two episodes (Northern and Southern Song). No images, audio or video are included. MIT.
