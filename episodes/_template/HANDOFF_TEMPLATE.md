# 第 N 集 · <朝代> · 恢复入口 / 成片实况

> 放在 `EP_DIR/HANDOFF.md`（交付后同一份内容整理成 `KIT/episodes/epNN_<拼音>/plan/FINAL.md`）。只写最终状态，不写过程和被推翻的版本。样例：`episodes/ep02_nansong/plan/FINAL.md`。

论点：**<一句话>**。分镜 `plan/SHOTLIST.md`；改版单 `plan/CHANGES_vN.md`（如有）。

## 当前状态（<日期 时间>）
- <在做什么 / 已完成什么 / 在跑的流程与 run id / 卡在哪>
- 恢复方法：<下一步命令；哪些 agent 可以走缓存，哪些要手动重渲>

## 成片
- `out/<文件名>.mp4`：<m:ss>（<DUR>.000 s，<帧数> 帧），1280×720 30 fps，H.264 crf 18 + AAC 192k 48 kHz，faststart；全片 <x> LUFS，真峰值 <x> dBTP。
- 联系表 `out/contact.jpg`（16 帧）；字幕 `out/subs.srt`（<句数> 句 → <条数> 条）；音轨 `out/audio/{mix,narration,music_duck}.wav`。
- 发布：<平台与稿件号，未发写"未发布">。

## 各段
| 段 | 文件 | 窗口 | 代码 |
|---|---|---|---|
| s0 片头 | `segs/seg_s0.mp4` | 0–<b> | `segs/bookends/` |
| s1 <作品> | `segs/seg_s1.mp4`（+ 遮罩） | <a>–<b> | `segs/s1_<名>/` |
| … | | | |

各段 `beats.json` = 实际节拍（全局秒）。

## 高光（全局时间码）
| 段 | 时间 | 内容 |
|---|---|---|
| 片头 | <m:ss.s–m:ss.s> | <…> |
| <作品> | <…> | <…> |

## 转场实现（`assemble.py` 的 `TRANS`）
1. s0→s1（<t0–t1>）：<做法与关键参数>。
2. …

## 字幕与声音
- 字幕：思源宋体 Regular 32 px，#EDE6D8 + 1 px 柔阴影 + 淡柔光晕，无底框，淡入淡出 0.3 s。
- 配音：云健（pitch −4Hz，rate −12%）；读音替换（PRON）：<原文 → 送合成文本，原因>。
- 配乐：<曲名、来源、许可>，<处理>；电平：字幕区约 −26 LUFS、呼吸段约 −20 LUFS，人声 −16 LUFS，人声下再让 4 dB。

## 自检结果
- 音画同长：<视频帧数 / 秒，音频秒>；faststart <是/否>。
- pan_speed_check：超限 <x> s，峰值 <x> 画宽/秒（限 0.143）。黑帧 <n>；帧间跳变 <n>。
- 作品全貌干净停住：<逐件时段与时长；不足 6 s 的标出>。
- 转场遮挡（混合 / 看不清）：<逐处>。
- 字幕对语音：起点差中位 <x> ms、最大 <x> ms。
- 联系表看过：<无错位、无方块字、无硬边、无雾遮画 / 或列问题>。

## 已知不足
- <做不到或没做到的，逐条；写清要补得做什么>

## 重跑（在 `EP_DIR` 下；重活走 `$CHINA_ART_ROOT/series/.heavy.lock`，长命令后台）
- 看帧：`python3 assemble.py peek <t> <t>`；短测试：`python3 assemble.py video --t0 <a> --t1 <b> --height 480 --fast --out work/t.mp4`。
- 改了字幕时刻/配音：`build_voice.py fit && build_voice.py subs` → `assemble.py audio` → 整片。
- 整片 + 自检：`nohup lockf -k $LOCK $KIT/pipeline/run_all.sh > work/final.log 2>&1 &`（`OUT_MP4`、`VERIFY` 环境变量）。
- 某段重渲：`<命令>`（段文件名不变，总装直接重跑）。
