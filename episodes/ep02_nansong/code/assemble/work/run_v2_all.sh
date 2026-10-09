#!/bin/zsh
# 第二版：混音 + 整片 + 自检（一次锁内跑完）
#   nohup lockf -k ../../.heavy.lock work/run_v2_all.sh > work/final_v2.log 2>&1 &
set -e
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/voice
python3 build_voice.py mix /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/assemble/work/music_mix.wav
echo MIX_DONE $(date)
/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/assemble/work/final_v2.sh
