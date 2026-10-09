export const meta = {
  name: 'china-art-episode-research',
  description: '中国艺术分集纪录片一集的调研：按作品并行查事实、图源与可动点，外加朝代特点一路，可选事实核查 → 合成调研底稿',
  whenToUse: '选定朝代与作品后、写分镜前，底稿（research/）不够用时。参数见脚本头部注释。',
  phases: [
    { title: 'Research', detail: '每件作品一路 + 朝代特点一路' },
    { title: 'Verify', detail: '（可选）展签事实与图源对抗核查' },
    { title: 'Synthesize', detail: '合成本集调研底稿' },
  ],
}
/*
【用法】（docs/PLAYBOOK.md 阶段 2；用户催速度时 verify: false）
Workflow({ scriptPath: '<KIT>/workflows/research.js', args: {
  kit:  '<KIT 本仓库绝对路径>',
  ep:   'ep03_yuan',
  dynasty: '元（1271–1368）',
  prev: '南宋：北宋人要看得真；南宋人只留最要紧的一笔',     // 上一集论点，本集要和它对照
  works: [ '赵孟頫《秀石疏林图》', '黄公望《富春山居图·无用师卷》', '倪瓒《容膝斋图》', '元青花（馆藏棚拍图）' ],
  verify: true,
}})
输出：<KIT>/episodes/<ep>/plan/RESEARCH.md（合成底稿）+ 各路原稿 <KIT>/episodes/<ep>/plan/research_*.md。
*/
if (!args || !args.kit || !args.ep || !args.dynasty || !Array.isArray(args.works) || !args.works.length) {
  throw new Error('缺参数：需要 args.kit / ep / dynasty / works（数组）。用法见脚本头部注释。')
}
const KIT = args.kit
const P = KIT + '/episodes/' + args.ep + '/plan'
const CTX = `
【项目】分集纪录片《中国传统艺术的演变》下一集：${args.dynasty}。上一集：${args.prev || '见 ' + KIT + '/docs/EPISODES.md'}。
先读 ${KIT}/docs/EPISODES.md 该朝代一行、${KIT}/docs/STANDARDS.md §1、§7，以及 ${KIT}/research/ 下的相关底稿（series/content_e*.md、early/c*.md、hall_v3/hunt_*.md 干净图源），复用已有成果，再用 WebSearch/WebFetch 补足和核实。
【口径】只写有把握的事实，出处写 URL；拿不准标"待核"。展签事实（名称、作者含"传"、年代、材质、尺寸、藏地）以馆方页面为准。图源要实测像素与许可；器物只要馆方棚拍图（纯色背景、整件入画），不要展柜实拍；台北故宫 IIIF 用 curl（Python 证书报错）。不调用任何付费 API，不读密钥文件。
`
phase('Research')
const jobs = args.works.map((w, i) => () => agent(`${CTX}
【你负责：${w}】写 ${P}/research_w${i + 1}.md：
1. 基本事实（馆方原文 + URL）：名称、作者、年代、材质、尺寸、藏地；展签建议写法（繁体竖排格式，数字用汉字）。
2. 为什么代表这个朝代成就最高的门类；最能说明朝代特点的 1–3 个局部（给出原图像素坐标或位置描述）。
3. 和上一集相比"变了什么"，在这件作品的哪里看得到。
4. 最高分辨率开放图：URL、实测像素、许可、署名格式；多张局部能否拼；是否有更干净的馆方图。
5. 画中游：哪里能"动"且只动原作像素（水、云、瀑布流动；人/船刚体位移；按浓淡/笔顺揭墨；光扫器身），哪里**不该动**；一个最惊艳的高光点子。
6. 旁白可用的一两件史实（带出处），以及措辞要留余地的地方。
返回 ≤250 字摘要。`, { label: `work:${i + 1}`, phase: 'Research' }))
jobs.push(() => agent(`${CTX}
【你负责：朝代】写 ${P}/research_dynasty.md：这个朝代成就最高的门类（学界共识，一两句理由）；2–4 个核心特点（普通观众听得懂，每个都能在本集作品上指出来）；和上一集朝代相比变了什么（具体、能拍）；可以当论点的一句话候选 3 个（和上一集论点对照）；配乐气质建议（整曲古琴/箫，只列许可干净的候选）。
返回 ≤250 字摘要。`, { label: 'dynasty', phase: 'Research' }))
const found = await parallel(jobs)

let checks = null
if (args.verify !== false) {
  phase('Verify')
  checks = await agent(`${CTX}
【你负责：核查】读 ${P}/research_*.md，逐条核对展签事实、史实、图源许可与像素（WebFetch 馆方页面、Commons API），**只报可验证的问题**，不评审美。每条：原文、问题、正确说法、来源 URL、严重程度（错/不准/可更好）。写 ${P}/research_verify.md。
返回 ≤200 字问题摘要。`, { label: 'verify', phase: 'Verify' })
}

phase('Synthesize')
const final = await agent(`${CTX}
各路摘要：
${found.map((f, i) => `【${i < args.works.length ? args.works[i] : '朝代'}】${f || '（失败）'}`).join('\n')}
核查：${checks || '（未核查）'}
【你负责：合成】读 ${P}/research_*.md，按核查意见改正，写 ${P}/RESEARCH.md（给总控写分镜用，只留最终结论）：论点候选、作品表（展签、图源、许可、关键局部坐标、高光点子、不该动的地方）、"变了什么"清单、旁白可用史实（带出处）、待核清单、配乐候选。主观取舍（选哪个论点、哪几件）列对照给用户拍板，可附推荐。
返回 ≤300 字摘要。`, { label: 'synthesize', phase: 'Synthesize' })
return { final, found, checks }
