#!/bin/zsh
set -e
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/bookends
python3 run.py seg_s0.py /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/seg_s0.mp4
python3 run.py seg_s7.py /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/seg_s7.mp4
for f in seg_s0 seg_s7; do
  ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=width,height,r_frame_rate,nb_read_packets -of csv=p=0 /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/$f.mp4
  python3 /Users/mr.ni/claude-projects/china-art/series/tools/pan_speed_check.py /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/$f.mp4
done
echo FULL_DONE
