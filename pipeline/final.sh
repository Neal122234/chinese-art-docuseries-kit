#!/bin/zsh
# 【工具包说明】整片出片 + 自检（以第二集·南宋 work/final_v2.sh 为准）：调 pipeline/assemble.py video 出 720p 成片（配音 + 字幕烧入），
# 再查 流信息 / 时长 / faststart / 响度 / 黑帧 / pan_speed_check / 本集 verify 脚本。覆盖前先 cp 备份旧成片。
# 输入：$EP_DIR/segs/*.mp4、$EP_DIR/out/audio/mix.wav、$EP_DIR/out/subs.srt；输出：$OUT_MP4（缺省 $EP_DIR/out/ep02_nansong_v2.mp4）+ $EP_DIR/assemble/work/pancheck_v2.log。
# 环境变量：CHINA_ART_ROOT、EP_DIR、OUT_MP4、VERIFY（缺省 $EP_DIR/assemble/work/verify_v2.py，不存在则跳过）；不设即本机原路径。
# 跑法（重活，走全局锁，后台）：nohup lockf -k $CHINA_ART_ROOT/series/.heavy.lock pipeline/final.sh > final.log 2>&1 &
# 前置：python3 pipeline/assemble.py audio → python3 pipeline/build_voice.py mix $EP_DIR/assemble/work/music_mix.wav（或直接跑 run_all.sh）
set -e
PIPE=${0:A:h}                                   # 本脚本所在的 pipeline/
KIT=${PIPE:h}
: ${CHINA_ART_ROOT:=~/claude-projects/china-art}
: ${EP_DIR:=$CHINA_ART_ROOT/series/ep02_nansong}
: ${OUT_MP4:=$EP_DIR/out/ep02_nansong_v2.mp4}
: ${VERIFY:=$EP_DIR/assemble/work/verify_v2.py}
export CHINA_ART_ROOT EP_DIR
mkdir -p $EP_DIR/assemble/work
cd $EP_DIR/assemble
OUTF=$OUT_MP4
[[ -f $OUTF ]] && cp $OUTF $OUTF.bak_$(date +%H%M%S)
echo "start $(date)"
python3 $PIPE/assemble.py video --audio $EP_DIR/out/audio/mix.wav --srt $EP_DIR/out/subs.srt --out $OUTF.part.mp4
mv $OUTF.part.mp4 $OUTF
echo VIDEO_DONE $(date)
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,duration,nb_frames,sample_rate,bit_rate -of compact $OUTF
ffprobe -v error -show_entries format=duration -of csv=p=0 $OUTF | sed 's/^/format_duration: /'
python3 -c "d=open('$OUTF','rb').read(1<<20);print('faststart:', d.find(b'moov')!=-1 and (d.find(b'mdat')==-1 or d.find(b'moov')<d.find(b'mdat')))"
ffmpeg -nostats -i $OUTF -vn -af ebur128=peak=true -f null - 2>&1 | grep -A20 "Summary" | grep -E "I:|Peak:|LRA:"
ffmpeg -v info -i $OUTF -vf blackdetect=d=0.05:pix_th=0.10 -an -f null - 2>&1 | grep -c "black_start" | sed 's/^/blackdetect_hits: /' || true
python3 $KIT/engine/tools/pan_speed_check.py $OUTF > work/pancheck_v2.log 2>&1 || true
cat work/pancheck_v2.log
if [[ -f $VERIFY ]]; then python3 $VERIFY $OUTF; else echo "VERIFY 跳过（$VERIFY 不存在）"; fi
echo ALL_DONE $(date)
