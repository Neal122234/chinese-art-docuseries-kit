#!/bin/zsh
# 1080p 配音终版整片：须在 heavy 锁内跑（nohup lockf -k ../.heavy.lock work/final_v3_1080.sh > work/final_v3_1080.log 2>&1 &）
# 前提：segs_1080/ALL_DONE（各段 1080 渲完）。整片 → 音画时长 → 响度 → 黑帧 → pan_speed_check → 和 720 配音版比帧 + 联系表
set -e
cd /Users/mr.ni/claude-projects/china-art/series/assemble
OUTF=../out/pilot_beisong_v3_1080.mp4
[[ -f ../segs_1080/ALL_DONE ]] || { echo "NO_ALL_DONE：1080 各段未渲完"; exit 1; }
[[ -f $OUTF ]] && cp $OUTF $OUTF.bak_$(date +%H%M%S)
python3 assemble.py video --res 1080 --strict --audio ../out/audio/mix.wav --srt ../out/subs.srt --out $OUTF.part.mp4
mv $OUTF.part.mp4 $OUTF
echo VIDEO_DONE
ffprobe -v error -show_entries stream=codec_type,codec_name,profile,width,height,r_frame_rate,duration,nb_frames,bit_rate,sample_rate -of compact $OUTF
ffprobe -v error -show_entries format=duration -of csv=p=0 $OUTF | sed 's/^/format_duration: /'
python3 -c "import sys;d=open('$OUTF','rb').read(4096);print('faststart:', d.find(b'moov')!=-1 and (d.find(b'mdat')==-1 or d.find(b'moov')<d.find(b'mdat')))"
ffmpeg -nostats -i $OUTF -vn -af ebur128=peak=true -f null - 2>&1 | grep -A12 "Summary" | grep -E "I:|Peak:|LRA:"
ffmpeg -v info -i $OUTF -vf blackdetect=d=0.05:pix_th=0.10 -an -f null - 2>&1 | grep -c blackdetect | sed 's/^/blackdetect_hits: /' || true
python3 ../tools/pan_speed_check.py $OUTF > work/pancheck_v3_1080.log 2>&1 || true
cat work/pancheck_v3_1080.log
python3 work/check_1080.py $OUTF ../out/pilot_beisong_v3.mp4 ../out/contact_1080.jpg
echo ALL_DONE
