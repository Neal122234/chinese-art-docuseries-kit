export const meta = {
  name: 'china-art-episode-revision',
  description: '中国艺术分集纪录片按改版单修改：每个要改的段/项一个助手并行（只重渲受影响帧段）→ 总装出新版与客观自检',
  whenToUse: '用户看完某一版给了意见、改版单 CHANGES_vN.md 已写好时。参数见脚本头部注释。',
  phases: [
    { title: 'Fix', detail: '按改版单逐项修改（段重渲 / 展签 / 旁白 / 配乐）' },
    { title: 'Assemble', detail: '换新段与新音轨、出新版、客观自检、更新 HANDOFF' },
  ],
}
/*
【用法】（docs/PLAYBOOK.md 阶段 10）
Workflow({ scriptPath: '<KIT>/workflows/revision.js', args: {
  kit:  '<KIT 本仓库绝对路径>',
  root: '<CHINA_ART_ROOT 绝对路径>',
  ep:   'ep03_yuan',
  version: 'v2',                           // 要出的新版号 → out/<ep>_<version>.mp4
  changes: 'CHANGES_v2.md',                // 改版单文件名（在 <KIT>/episodes/<ep>/plan/ 下）
  dur: 300,                                // 新版总长（不变就照旧填）
  principle: '作品是主角……',               // 这次用户原话里的原则（一两句，原话摘录；可省）
  fixes: [                                  // 每项一个助手；key 用于标签，task 写改版单第几条、改什么、输出什么、验收证据
    { key: 's1', task: '改版单第 1 条：……。重渲 seg_s1.mp4 中 a–b 帧段再拼回（帧数、首尾帧不变），抽帧确认。' },
    { key: 'voice', task: '改版单第 7 条：更新 anchors.json 里 s4 几句……重新 fit + 新句读音核对，出新 timing.json 与 subs.srt。暂不混音。' },
  ],
  assembleTask: '总长仍 300 s；s1→s2 改为……；其余转场不变。',   // 给总装助手的本轮具体要求
  phone: false,                             // 是否另压 <28 MB 手机版
}})
- 用户中途补充/改口：TaskStop 停掉本 run → 改 CHANGES 单与 args → 重新启动（或 resumeFromRunId，未改的 fix 走缓存）。
- 只有一个参数要改、助手还在跑：SendMessage 直接告诉那个助手。
*/
if (!args || !args.kit || !args.root || !args.ep || !args.version || !args.changes || !Array.isArray(args.fixes)) {
  throw new Error('缺参数：需要 args.kit / root / ep / version / changes / fixes（数组）。用法见脚本头部注释。')
}
const KIT = args.kit
const R = args.root
const S = R + '/series'
const E = S + '/' + args.ep
const PLAN = KIT + '/episodes/' + args.ep + '/plan'
const LOCK = S + '/.heavy.lock'
const V = args.version
const OUT = `${E}/out/${args.ep}_${V}.mp4`

const CTX = `
【项目】分集纪录片《中国传统艺术的演变》${args.ep} 改版（出 ${V}）。工作目录 EP_DIR=${E}/；工具包 KIT=${KIT}/。
必读：${PLAN}/${args.changes}（本轮改版单，**最重要**，照它做）、${PLAN}/SHOTLIST.md、${E}/HANDOFF.md（上一版怎么做的、各段代码与重跑命令）、${PLAN}/assets_INDEX.md、${KIT}/docs/STANDARDS.md。
【用户原则】${args.principle || '见改版单"用户原话"与"原则"两节'}。作品是主角，转场和动效只是手段；用户要速度，做完即交，不做内部评审；主观取舍不替用户决定。
【规则】只改改版单列出的东西，其余不动；段重渲只渲受影响的帧段再拼回，帧数与首尾帧不变（转场靠它）。覆盖成品前 cp 备份（不要硬链接）。Apple Silicon 8 GB 内存紧：渲染/大图/whisper/长编码必须 \`lockf -k ${LOCK} <命令>\`；>1 分钟 nohup 后台 + ≤60 秒短轮询（>3 分钟无输出会被判卡死）。只改本集目录（含本集 pipeline 副本 ${E}/pipeline/）；前几集文件、${KIT}/engine、${KIT}/pipeline 只许新增，不改已有行为。跑 pipeline 脚本前 export CHINA_ART_ROOT=${R} EP_DIR=${E}。
【展示处要严谨】改到的展签、字幕事实以馆方页面为准。
`
phase('Fix')
const fixes = await parallel(args.fixes.map(f => () => agent(`${CTX}
【你负责】${f.task}
做完用 Read 看关键帧（改动处前后各一帧）；段有重渲就跑 \`python3 ${KIT}/engine/tools/pan_speed_check.py <成品>\` 并更新该段 beats.json。
返回 ≤150 字：改了什么、输出文件、验收证据（时间码/帧/数字）、没做到的。`, { label: `fix:${f.key}`, phase: 'Fix' })))

phase('Assemble')
const final = await agent(`${CTX}
各项汇报：
${args.fixes.map((f, i) => `【${f.key}】${fixes[i] || '（失败）'}`).join('\n')}
【你负责】总装 ${V}：先看 ${E}/assemble/NOTE_FOR_ASSEMBLY.md（如果存在，以它为准）。在本集 pipeline 副本 ${E}/pipeline/ 里改（先 cp 备份上一版的 assemble.py、transfx.py 与相关文件）。本轮要求：${args.assembleTask || '按改版单'}。总长 ${args.dur ? args.dur + ' s' : '不变'}。
- 字幕/旁白有改动：先 \`python3 ${E}/pipeline/build_voice.py subs\`，再 \`python3 ${E}/pipeline/assemble.py audio\`；配乐有改动：先确认新配乐长度 = 总长、许可干净、DECISION 已更新。
- 出片：\`OUT_MP4=${OUT} VERIFY=${E}/pipeline/work/verify.py nohup lockf -k ${LOCK} ${E}/pipeline/run_all.sh > ${E}/assemble/work/final_${V}.log 2>&1 &\`（混音 → 整片 → 自检；verify 脚本按本轮改动更新作品框、参考帧、转场窗口）。${args.phone ? `另压手机版 ${E}/out/${args.ep}_${V}_手机.mp4（854×480 两遍编码，<28 MB）。` : '不压手机版。'}
- 自检（客观）：pan_speed_check、黑帧、音画同长、响度、字幕对语音；每件作品全貌干净停住时长（≥6 s）、每个转场遮挡时长（≤2 s）；改版单里每条的落实证据；抽 16 帧联系表 ${E}/out/contact_${V}.jpg 用 Read 看。
- 把改版单的改动并入 ${PLAN}/SHOTLIST.md（分镜永远是最终状态，不写"原来/改成"）；更新 ${E}/HANDOFF.md（只留最终版本）。
返回 ≤200 字：成片路径、时长、改版单逐条落实情况、自检结果、已知问题。`, { label: `assemble-${V}`, phase: 'Assemble' })
return { final, fixes }
