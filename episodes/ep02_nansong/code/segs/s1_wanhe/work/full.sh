#!/bin/zsh
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/s1_wanhe
python3 seg_s1.py --stills 880,935 --out work/v.jpg || exit 1
[ -f ../seg_s1.mp4 ] && cp ../seg_s1.mp4 work/seg_s1.prev.mp4
python3 seg_s1.py --out ../seg_s1.mp4 && echo RENDER_DONE
