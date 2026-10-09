#!/bin/zsh
# S6 官窑：全段 + 开片遮罩 → 从成品截高光预览（262–272）→ 速度复核
set -e
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/s6_guan
SEGS=/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs
PREV=/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/out/preview
[ -f $SEGS/seg_s6.mp4 ] && cp $SEGS/seg_s6.mp4 $SEGS/seg_s6.mp4.bak
echo "start $(date)"
python3 seg_s6.py $SEGS/seg_s6.mp4 --mask $SEGS/seg_s6_crackle_mask.mp4
ffmpeg -y -v error -ss 16 -i $SEGS/seg_s6.mp4 -t 10 -c:v libx264 -crf 14 -pix_fmt yuv420p -movflags +faststart $PREV/s6_guan.mp4
python3 /Users/mr.ni/claude-projects/china-art/series/tools/pan_speed_check.py $SEGS/seg_s6.mp4
echo "done $(date)"
