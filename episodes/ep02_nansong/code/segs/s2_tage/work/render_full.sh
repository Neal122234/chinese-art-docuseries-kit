#!/bin/zsh
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/s2_tage
OUT=/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/seg_s2.mp4
[ -f $OUT ] && cp $OUT $OUT.bak
python3 seg_s2.py --stills 890,905,920 --out review/d.png && python3 seg_s2.py --out $OUT.tmp.mp4 && mv $OUT.tmp.mp4 $OUT
ffmpeg -y -loglevel error -ss 16.8 -t 10 -i $OUT -c:v libx264 -crf 14 -pix_fmt yuv420p -movflags +faststart /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/out/preview/s2_tage.mp4
python3 /Users/mr.ni/claude-projects/china-art/series/tools/pan_speed_check.py $OUT
echo ALLDONE
