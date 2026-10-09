#!/bin/zsh
cd ~/claude-projects/china-art/series/ep02_nansong/segs/s5_pomo
OUT=~/claude-projects/china-art/series/ep02_nansong/segs/seg_s5.mp4
[ -f $OUT ] && cp $OUT $OUT.bak
python3 render.py $OUT.tmp.mp4 && mv $OUT.tmp.mp4 $OUT
ffmpeg -y -loglevel error -ss 20 -t 10 -i $OUT -c:v libx264 -crf 14 -pix_fmt yuv420p -movflags +faststart ~/claude-projects/china-art/series/ep02_nansong/out/preview/s5_pomo.mp4
python3 ~/claude-projects/china-art/series/tools/pan_speed_check.py $OUT
echo ALLDONE
