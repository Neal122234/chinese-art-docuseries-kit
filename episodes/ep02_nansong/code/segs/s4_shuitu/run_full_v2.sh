#!/bin/zsh
# 第二版整段重渲（约 15–20 分钟）：nohup lockf -k ../../../.heavy.lock ./run_full_v2.sh > work/full_v2.log 2>&1 &
set -e
cd ~/claude-projects/china-art/series/ep02_nansong/segs/s4_shuitu
SEGS=~/claude-projects/china-art/series/ep02_nansong/segs
PV=~/claude-projects/china-art/series/ep02_nansong/out/preview
python3 s4.py work/v2_full.mp4 --mask work/v2_mask.mp4
[ -f $SEGS/seg_s4_v1.mp4 ] || cp $SEGS/seg_s4.mp4 $SEGS/seg_s4_v1.mp4
[ -f $SEGS/seg_s4_lines_mask_v1.mp4 ] || cp $SEGS/seg_s4_lines_mask.mp4 $SEGS/seg_s4_lines_mask_v1.mp4
cp work/v2_full.mp4 $SEGS/seg_s4.mp4
cp work/v2_mask.mp4 $SEGS/seg_s4_lines_mask.mp4
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=width,height,r_frame_rate,nb_read_packets -of csv=p=0 $SEGS/seg_s4.mp4
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=width,height,r_frame_rate,nb_read_packets -of csv=p=0 $SEGS/seg_s4_lines_mask.mp4
# 预览：十二段逐段（本段 13.4–38.0 = 全局 179.4–204.0）
ffmpeg -y -loglevel error -ss 13.4 -i $SEGS/seg_s4.mp4 -frames:v 738 -c:v libx264 -crf 16 -pix_fmt yuv420p -movflags +faststart $PV/s4_v2.mp4
python3 ~/claude-projects/china-art/series/tools/pan_speed_check.py $SEGS/seg_s4.mp4
echo FULL_DONE
