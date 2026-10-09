#!/bin/zsh
# 第二集·南宋 第二版整片（720p，配音 + 字幕烧入）：须在 heavy 锁内跑
#   nohup lockf -k ../../.heavy.lock work/final_v2.sh > work/final_v2.log 2>&1 &
# 前置：python3 assemble.py audio → (cd ../voice && python3 build_voice.py mix $PWD/work/music_mix.wav)
set -e
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/assemble
OUTF=../out/ep02_nansong_v2.mp4
[[ -f $OUTF ]] && cp $OUTF $OUTF.bak_$(date +%H%M%S)
echo "start $(date)"
python3 assemble.py video --audio ../out/audio/mix.wav --srt ../out/subs.srt --out $OUTF.part.mp4
mv $OUTF.part.mp4 $OUTF
echo VIDEO_DONE $(date)
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,duration,nb_frames,sample_rate,bit_rate -of compact $OUTF
ffprobe -v error -show_entries format=duration -of csv=p=0 $OUTF | sed 's/^/format_duration: /'
python3 -c "d=open('$OUTF','rb').read(1<<20);print('faststart:', d.find(b'moov')!=-1 and (d.find(b'mdat')==-1 or d.find(b'moov')<d.find(b'mdat')))"
ffmpeg -nostats -i $OUTF -vn -af ebur128=peak=true -f null - 2>&1 | grep -A20 "Summary" | grep -E "I:|Peak:|LRA:"
ffmpeg -v info -i $OUTF -vf blackdetect=d=0.05:pix_th=0.10 -an -f null - 2>&1 | grep -c "black_start" | sed 's/^/blackdetect_hits: /' || true
python3 ../../tools/pan_speed_check.py $OUTF > work/pancheck_v2.log 2>&1 || true
cat work/pancheck_v2.log
python3 work/verify_v2.py $OUTF
echo ALL_DONE $(date)
