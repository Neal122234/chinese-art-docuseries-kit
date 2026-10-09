export const meta = {
  name: 'china-art-episode-production',
  description: '中国艺术分集纪录片一集：素材/配乐/旁白并行 → 各段并行制作（重渲染排队拿锁，先出高光预览）→ 总装出片与客观自检',
  whenToUse: '分镜 SHOTLIST.md 与 anchors.json 已定稿、用户同意开渲时。参数见脚本头部注释。',
  phases: [
    { title: 'Prep', detail: '素材下载与核实 / 整曲配乐 / 云健旁白合成对时' },
    { title: 'Segments', detail: '每段一个助手并行：先出 ≤10 s 高光预览，再全段渲' },
    { title: 'Assemble', detail: '转场、字幕、混音、出片、客观自检、HANDOFF' },
  ],
}
/*
【用法】（由 china-art-episode skill / docs/PLAYBOOK.md 阶段 4–9 调用）
Workflow({ scriptPath: '<KIT>/workflows/episode_production.js', args: {
  kit:  '<KIT 本仓库绝对路径>',
  root: '<CHINA_ART_ROOT 素材与成品工程绝对路径>',      // 如 ~/claude-projects/china-art 展开后的绝对路径
  ep:   'ep03_yuan',                                  // 本集目录名：EP_DIR = root/series/<ep>，文档在 kit/episodes/<ep>/plan
  title: '第三集·元',
  dur: 300,                                           // 片长（秒），= 分镜总长 = 配乐长度
  prevEps: ['ep01_beisong', 'ep02_nansong'],          // 只读参考的前几集
  music: { mode: 'caro' },                            // 'caro' = 沿用 Rafael Caro《梅花三弄》从头取 dur 秒；'search' = 找新曲，hint 写气质与候选
  voiceFocus: '朝（zhāo/cháo）、卷（juàn）、传（chuán）……',   // 本集重点核的多音字/专名/年份（可省）
  assetsHint: '',                                     // 给素材助手的额外说明（可省）
  segTimeLimitMin: 75,                                // 每段助手的限时（分钟）
  segs: [                                             // 每段一个助手；task 写本段窗口、起止状态、高光、需导出的遮罩、输出文件名
    { key: 'bookends', task: 's0 片头（0–10）与 sN 结尾（…）。……输出 seg_s0.mp4、seg_sN.mp4。' },
    { key: 's1_xxx',   task: 's1 作者《作品》（窗口 a–b）。高光：……。输出 seg_s1.mp4。' },
  ],
  assembleNote: '',                                   // 给总装助手的额外说明（可省）
}})
- 分镜必须先写好：<KIT>/episodes/<ep>/plan/SHOTLIST.md、anchors.json；EP_DIR/plan 软链接到它。
- 续跑：Workflow({ scriptPath, resumeFromRunId })；改了哪段的 task，只有那段及其后的 agent 重跑。
- 中途改总装方案：写 EP_DIR/assemble/NOTE_FOR_ASSEMBLY.md，总装助手开工前会读、以它为准。
*/
if (!args || !args.kit || !args.root || !args.ep || !args.dur || !Array.isArray(args.segs) || !args.segs.length) {
  throw new Error('缺参数：需要 args.kit / root / ep / dur / segs（数组）。用法见脚本头部注释。')
}
const KIT = args.kit
const R = args.root
const S = R + '/series'
const E = S + '/' + args.ep
const PLAN = KIT + '/episodes/' + args.ep + '/plan'
const LOCK = S + '/.heavy.lock'
const DUR = args.dur
const TITLE = args.title || args.ep
const PREV = (args.prevEps || []).map(p => `${KIT}/episodes/${p}/`).join('、') || '（无）'
const LIMIT = args.segTimeLimitMin || 75
const MUSIC = args.music || { mode: 'caro' }

const CTX = `
【项目】分集纪录片《中国传统艺术的演变》${TITLE}。工作目录 EP_DIR=${E}/（子目录 plan/ assets/ music/ voice/ segs/ assemble/ out/；plan/ 软链接到 ${PLAN}/）。工具包仓库 KIT=${KIT}/。
必读：${PLAN}/SHOTLIST.md（本集分镜定稿：论点、段窗口、起止状态、转场、每段旁白与高光——照它做）、${PLAN}/anchors.json（旁白）、${KIT}/docs/STANDARDS.md（用户定的标准）、${KIT}/docs/LESSONS.md（踩坑）、${KIT}/engine/ENGINE.md（2.5D 引擎）。前几集可借鉴的实现（只读）：${PREV}（plan/FINAL.md 写了每个高光和转场怎么做的，code/ 是代码）。
【不要改前几集和公共代码的现有行为】${KIT}/engine、${KIT}/pipeline 只许新增文件；要改就复制到本集目录再改。
【用户标准】作品是主角：每件全貌干净停 ≥6 s、不做小展板、转场遮挡 ≤2 s、雾全集最多一次且不遮画、组画逐段快而看得清。动静结合：每件 1–2 个手机上 1 秒内看得出的"动"的高光，来自作品本质，只动原作像素（揭原作之墨、分层视差、刚体位移、沿真实纹理流动）。镜头 720p 平移 ≤6 px/帧（推荐 2–3.3）、推拉 ≤6%/s、缓入缓出每端 ≥1 s、不旋转。底线：不拼贴、不橡皮变形、不斑块/矩形溶解、不漂浮剪影、不糊、不整屏拖影、不快速横移、不纯黑屏、不小展板、不廉价中国风。其余放开，大胆做出惊艳。用户要速度：不做内部评审，做完即交；主观取舍不替用户决定。
【机器】Apple Silicon 8 GB，内存很紧。任何会占 >1 GB 内存或跑满 CPU 的命令（加载整幅高清图、torch、渲染、长片编码、whisper）必须 \`lockf -k ${LOCK} <命令>\` 串行；超过 1 分钟的命令一律 \`nohup lockf -k ${LOCK} ... > log 2>&1 &\` 后台，再用 ≤60 秒短命令轮询（一条命令 >3 分钟无输出会被判卡死）。大图 memmap/分块。覆盖成品前 cp 备份（不要硬链接）。
【环境变量】跑 pipeline 脚本（用本集副本 ${E}/pipeline/，${KIT}/pipeline 不改）前 export CHINA_ART_ROOT=${R} EP_DIR=${E}（字体目录 FONT_DIR、edge-tts 的 TTS_PY、whisper 的 ASR_PY 按 ${KIT}/scripts/bootstrap.sh 的说明设）。
【展示处要严谨】展签、字幕里的事实（作品名、作者、年代、材质、尺寸、藏地、史实）以馆方页面为准；拿不准就改成更稳妥的说法或不写，并在汇报里写出。
`

phase('Prep')
const musicTask = MUSIC.mode === 'search'
  ? `给本集选一首**整曲连贯**的录音做底，做 ${E}/music/bed_${args.ep}.wav（48 kHz 立体声，长度正好 ${DUR} s：0 起淡入 2 s，在 ${DUR - 6}–${DUR - 1} s 附近找乐句结束的低能量点升余弦淡出 ≥3 s，其后补静音；中间不剪、不拼、不循环）。气质与候选：${MUSIC.hint || '按本集论点定'}。候选都测高频底噪（最小统计法）、嘶声、爆音、频宽、时长（方法见 ${KIT}/episodes/ep02_nansong/plan/music_DECISION.md）。**要公开发布，许可必须干净**（CC BY / CC0 / PD 优先；版权期内且无授权的不能选）。没有比 Rafael Caro《梅花三弄》（Freesound 176265，CC BY 4.0）更合适且同样干净的，就用 Caro 并说明。`
  : `用 Rafael Caro《梅花三弄》（Freesound 176265，CC BY 4.0，387.9 s；本机源文件在 ${S}/music/src/ 或 ${S}/ep02_nansong/music/src/，找不到就从 https://freesound.org/s/176265/ 取 HQ 预览）做 ${E}/music/bed_${args.ep}.wav：48 kHz 立体声，长度正好 ${DUR} s，0 起升余弦淡入 2 s，在 ${DUR - 6}–${DUR - 1} s 之间找乐句尾的能量谷升余弦淡出（≥3 s），其后补数字静音；中间不剪不拼。`
const [assets, music, voice] = await parallel([
  () => agent(`${CTX}
【你负责：素材】在 ${E}/assets/ 下载并整理 SHOTLIST 里每件作品的最高分辨率开放图（原图原样留一份），写 ${PLAN}/assets_INDEX.md（照 ${KIT}/episodes/ep02_nansong/plan/assets_INDEX.md 的结构：总表、展签事实表（逐条对馆方页面、写出处）、每件的文件/像素/来源 URL/许可/署名写法/关键坐标）。
- 台北故宫 IIIF 用 curl（Python urllib 证书报错），单张约 7 MP 上限，需要更高就拼多张局部，拼完查重叠区错位；Commons 用通用浏览器 UA、间隔 ≥6 s；大都会用 collectionapi 核馆方名称/年代/窑口。器物只用馆方棚拍图（纯色背景、整件入画），不用展柜实拍。
- 大图转无头 raw（文件名带 _<W>x<H>）或 .npy，PNG 流式解码，别整张读；出缩略预览与带网格核对图。校色只做全局一个变换对到馆方参照图，参照图先核是哪一本（摹本/仿本）。
- 记录 SHOTLIST 里每个高光和转场要用的坐标（在网格图上量过）；组画按段切好并记每段边界与题名位置。
${args.assetsHint || ''}
返回 ≤200 字：各素材路径与分辨率、换过/存疑的地方、展签事实里拿不准的。`, { label: 'assets', phase: 'Prep' }),
  () => agent(`${CTX}
【你负责：配乐】${musicTask}
写 ${PLAN}/music_DECISION.md（选了什么、为什么、许可与署名的真实状态、处理步骤、实测时长与响度、无剪接证据、给总装的电平提示；如有踩拍类高光，另出起音时刻表 ${E}/music/onsets.json（全局秒））。
返回 ≤150 字。`, { label: 'music', phase: 'Prep' }),
  () => agent(`${CTX}
【你负责：云健旁白】旁白原稿在 ${PLAN}/anchors.json（[[起点秒, "字幕原文"], ...]，空格保留作停顿/拆条）。本集用 pipeline 的副本：若 ${E}/pipeline/ 还不存在，\`cp -R ${KIT}/pipeline ${E}/pipeline\`（脚本之间按同目录互相引用 synth.py、asr_*.py、pinyin_cmp.py、transfx.py，所以整个目录一起复制）；只改副本 ${E}/pipeline/build_voice.py 的文件头：DUR=${DUR}，PRON 清空后按本集重填（VOICE=zh-CN-YunjianNeural，pitch −4Hz，rate −12% 不变）。用 EP_DIR=${E} 跑 \`python3 ${E}/pipeline/build_voice.py …\`。
1. fit：合成 + 对时，每句从起点开始、句尾离下一句 ≥0.3 s；放不下就逐句提速（最快 rate +0%）或在 ±0.5 s 内挪起点；仍放不下的句子在汇报里列出并给出建议删改的字。
2. asr + variants（锁内）：whisper 回听 + 多音字同音替身比对。本集重点：${args.voiceFocus || '多音字、年份数字、人名地名作品名'}。读错的只在送去合成的文本里等长替换（PRON），字幕原文不变；whisper 把专名听成常用词的不算错。
3. subs：写 ${E}/out/subs.srt（按语音对时，超 16 字在空格处拆条）与 ${E}/voice/work/timing.json。暂不混音（总装阶段做）。
返回 ≤200 字：每句是否放得下、改过读音的词、总旁白时长。`, { label: 'voice', phase: 'Prep' }),
])
log('Prep 完成，开始分段制作。各段高光预览会陆续出现在 ' + E + '/out/preview/，主会话可以先发给用户看。')

phase('Segments')
const segRes = await parallel(args.segs.map(s => () => agent(`${CTX}
素材汇报：${assets || '（素材助手失败：自己按 SHOTLIST 与 assets_INDEX 下载所需素材）'}
配乐汇报：${music || '（无）'}
旁白汇报：${voice || '（无）'}（字幕/旁白时间以 ${E}/voice/work/timing.json 为准，没有就用 anchors.json）
【你负责】${s.task}
工作目录 ${E}/segs/${s.key}/，成品放 ${E}/segs/（1280×720 30 fps crf 12，帧 0 = 窗口起点）。引擎 ${KIT}/engine/engine.py（渲染前自动查速度），长案全貌 ${KIT}/engine/scrollview.py；引擎缺功能就在本段目录扩展，不改公共文件。
流程：先做本段最惊艳那一刻的 ≤10 秒 720p 预览 ${E}/out/preview/${s.key}.mp4，用 Read 看关键帧（手机尺寸 1 秒内要看得出在动），满意再全段渲；全段渲完跑 \`python3 ${KIT}/engine/tools/pan_speed_check.py <成品>\`（不能有超限段），抽 6–8 帧看；写 ${E}/segs/${s.key}/beats.json（高光与关键画面的实际全局时间）。起止状态必须符合 SHOTLIST 的段窗口表（转场靠它）；转场需要的遮罩按 SHOTLIST 导出。字幕不烧（总装加），展签段内加。限时约 ${LIMIT} 分钟；做不到的效果换成稳而美、同样明显的做法，不交露馅的东西。
返回 ≤200 字：成品路径、高光做法与时间、节拍偏差、已知不足。`, { label: `seg:${s.key}`, phase: 'Segments' })))

phase('Assemble')
const final = await agent(`${CTX}
各段汇报：
${args.segs.map((s, i) => `【${s.key}】${segRes[i] || '（失败）'}`).join('\n')}
旁白汇报：${voice || '（无）'}　配乐汇报：${music || '（无）'}
【你负责：总装】开工前先看 ${E}/assemble/NOTE_FOR_ASSEMBLY.md（如果存在，以它为准，它会覆盖这里的说明）。
1. 用本集 pipeline 副本 ${E}/pipeline/（旁白助手已从 ${KIT}/pipeline 整目录复制；没有就 \`cp -R ${KIT}/pipeline ${E}/pipeline\`）。只改副本：assemble.py 文件头的段表（SEG_START / SEG_FILE / SEG_NFR）、遮罩表、转场表 TRANS、DUR=${DUR}，配乐用 BED=${E}/music/bed_${args.ep}.wav；新转场在副本 transfx.py 里新增类；final.sh 副本里 pan_speed_check 的路径指回 ${KIT}/engine/tools/pan_speed_check.py（它按自身位置推 KIT，复制后会指错）。${KIT}/pipeline 本身不改。缺失的段用该段素材静帧占位并在汇报里写明。每个转场先做 ≤10 s 短测试看帧（\`python3 ${E}/pipeline/assemble.py video --t0 … --t1 … --height 480 --fast --out work/t.mp4\`、\`peek\`）。
2. 配乐与配音：\`python3 ${E}/pipeline/assemble.py audio\`（字幕区约 −26 LUFS、呼吸段约 −20 LUFS → ${E}/assemble/work/music_mix.wav）→ 由副本 run_all.sh 调 build_voice.py mix（人声 −16 LUFS，配乐在人声下再让 4 dB，真峰值 ≤ −1 dBTP）→ ${E}/out/audio/mix.wav；字幕按 ${E}/out/subs.srt 烧入（思源宋体 32 px，#EDE6D8 + 柔阴影 + 淡柔光晕）。
3. 出片 ${E}/out/${args.ep}_v1.mp4（1280×720 30 fps，H.264 crf 18，AAC 192k，faststart，${DUR}.000 s）：\`OUT_MP4=${E}/out/${args.ep}_v1.mp4 VERIFY=${E}/pipeline/work/verify.py nohup lockf -k ${LOCK} ${E}/pipeline/run_all.sh > ${E}/assemble/work/final_v1.log 2>&1 &\`。本集 verify 脚本照 ${KIT}/episodes/ep02_nansong/code/assemble/work/verify_v2.py 改，放在 ${E}/pipeline/work/verify.py（它 import 上一级目录的 assemble.py，放这里就引用本集副本；改作品框、全貌参考帧时刻、转场窗口、组画段落）。${args.assembleNote || ''}
4. 自检（客观）：pan_speed_check、黑帧、音画同长、响度、帧间跳变、字幕对语音；"作品可见"：每件作品全貌干净停住时长（≥6 s）、每个转场遮挡时长（≤2 s）、组画每段停住时长；用了雾就跑平涂检查；抽 16 帧（含每个高光与转场）拼 ${E}/out/contact.jpg 用 Read 看，明显穿帮就修。
5. 写 ${E}/HANDOFF.md（照 ${KIT}/episodes/_template/HANDOFF_TEMPLATE.md：文件、高光时间码表、转场实现、字幕与声音、自检数字、已知不足、重跑命令；只留最终版本）。
返回 ≤250 字：成片路径、时长、高光时间码、自检结果、已知问题。`, { label: 'assemble', phase: 'Assemble' })
return { final, segRes, assets, music, voice }
