#!/bin/zsh
cd ~/claude-projects/china-art/series/ep02_nansong/segs/s4_shuitu
python3 s4.py look/x.mp4 --speed
python3 s4.py look/s.mp4 --stills 0,45,240,300,390,510,600,720,840,960,1110,1380,1650
echo STILLS_DONE
